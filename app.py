import os
import io
import uuid
import json
import time
import shutil

import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

import pdf_tools

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(folder, max_age_hours=2):
    """Remove files older than max_age_hours."""
    now = time.time()
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path) and (now - os.path.getmtime(path)) > max_age_hours * 3600:
            os.remove(path)
        elif os.path.isdir(path) and (now - os.path.getmtime(path)) > max_age_hours * 3600:
            shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    cleanup_old_files(UPLOAD_FOLDER)
    cleanup_old_files(OUTPUT_FOLDER)

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    files = request.files.getlist('file')
    uploaded = []

    for file in files:
        if file and allowed_file(file.filename):
            file_id = str(uuid.uuid4())[:8]
            filename = secure_filename(file.filename)
            save_name = f"{file_id}_{filename}"
            save_path = os.path.join(UPLOAD_FOLDER, save_name)
            file.save(save_path)

            file_info = {
                'id': file_id,
                'name': filename,
                'path': save_name,
                'size': os.path.getsize(save_path),
            }

            if filename.lower().endswith('.pdf'):
                try:
                    info = pdf_tools.get_pdf_info(save_path)
                    file_info['pages'] = info['pages']
                    file_info['page_sizes'] = info['page_sizes']
                except Exception:
                    file_info['pages'] = 0

            uploaded.append(file_info)

    if not uploaded:
        return jsonify({'error': 'No valid files uploaded'}), 400

    return jsonify({'files': uploaded})


@app.route('/api/decolor', methods=['POST'])
def api_decolor():
    data = request.json
    filename = data.get('filename')
    threshold = data.get('threshold', 60)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"decolored_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.decolor_pdf(input_path, output_path, threshold=int(threshold))
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/merge', methods=['POST'])
def api_merge():
    data = request.json
    filenames = data.get('filenames', [])

    input_paths = []
    for f in filenames:
        path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.exists(path):
            input_paths.append(path)

    if len(input_paths) < 2:
        return jsonify({'error': 'Need at least 2 files to merge'}), 400

    output_name = f"merged_{uuid.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.merge_pdfs(input_paths, output_path)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-text-blocks', methods=['GET'])
def api_get_text_blocks():
    filename = request.args.get('filename')
    page_num = int(request.args.get('page', 0))
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
        
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
        
    try:
        spans = pdf_tools.get_pdf_text_blocks(input_path, page_num)
        return jsonify({'spans': spans})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/edit-text-live', methods=['POST'])
def api_edit_text_live():
    data = request.json
    filename = data.get('filename')
    edits = data.get('edits', [])
    
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
        
    output_name = f"edited_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    
    try:
        pdf_tools.apply_live_text_edits(input_path, output_path, edits)
        size = os.path.getsize(output_path)
        return jsonify({
            'output': output_name,
            'size': size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/canvas-edit', methods=['POST'])
def api_canvas_edit():
    data = request.json
    filename = data.get('filename')
    elements = data.get('elements', [])
    
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
        
    output_name = f"canvas_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    
    try:
        for el in elements:
            if el["type"] == "image":
                el["image_path"] = os.path.join(UPLOAD_FOLDER, el["image_filename"])
                
        pdf_tools.apply_canvas_edits(input_path, output_path, elements)
        size = os.path.getsize(output_path)
        return jsonify({
            'output': output_name,
            'size': size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-text-blocks', methods=['POST'])
def api_extract_text_blocks():
    """Extract text blocks with positions from a specific page of the PDF."""
    data = request.json
    filename = data.get('filename')
    page_num = data.get('page', 0)
    
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        import fitz
        doc = fitz.open(input_path)
        if page_num < 0 or page_num >= len(doc):
            return jsonify({'error': 'Invalid page number'}), 400
        
        page = doc[page_num]
        blocks = []
        
        # Extract text with detailed info using "dict" mode
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        
        for block in text_dict.get("blocks", []):
            if block["type"] != 0:  # 0 = text block
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    font_size = span.get("size", 12)
                    font_name = span.get("font", "Helvetica")
                    color_int = span.get("color", 0)
                    
                    # Convert color integer to hex
                    r = (color_int >> 16) & 0xFF
                    g = (color_int >> 8) & 0xFF
                    b = color_int & 0xFF
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    
                    blocks.append({
                        'text': text,
                        'x': bbox[0],
                        'y': bbox[1],
                        'w': bbox[2] - bbox[0],
                        'h': bbox[3] - bbox[1],
                        'fontSize': round(font_size, 1),
                        'font': font_name,
                        'color': color_hex,
                        'origin_y': span.get("origin", [0, bbox[1]])[1] if "origin" in span else bbox[1]
                    })
        
        doc.close()
        return jsonify({'blocks': blocks, 'page': page_num})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/split', methods=['POST'])
def api_split():
    data = request.json
    filename = data.get('filename')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    split_dir = os.path.join(OUTPUT_FOLDER, f"split_{uuid.uuid4().hex[:8]}")
    os.makedirs(split_dir, exist_ok=True)

    try:
        output_files = pdf_tools.split_pdf(input_path, split_dir)
        results = []
        for f in output_files:
            results.append({
                'name': os.path.basename(f),
                'path': os.path.relpath(f, OUTPUT_FOLDER).replace('\\', '/'),
                'size': os.path.getsize(f),
            })
        return jsonify({'files': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rotate', methods=['POST'])
def api_rotate():
    data = request.json
    filename = data.get('filename')
    angle = data.get('angle', 90)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"rotated_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.rotate_pdf(input_path, output_path, angle=int(angle))
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compress', methods=['POST'])
def api_compress():
    data = request.json
    filename = data.get('filename')
    quality = data.get('quality', 75)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"compressed_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.compress_pdf(input_path, output_path, quality=int(quality))
        orig_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        return jsonify({
            'output': output_name,
            'original_size': orig_size,
            'new_size': new_size,
            'reduction': round((1 - new_size / orig_size) * 100, 1),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/to-images', methods=['POST'])
def api_to_images():
    data = request.json
    filename = data.get('filename')
    fmt = data.get('format', 'png')
    dpi = data.get('dpi', 200)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    img_dir = os.path.join(OUTPUT_FOLDER, f"images_{uuid.uuid4().hex[:8]}")
    os.makedirs(img_dir, exist_ok=True)

    try:
        output_files = pdf_tools.pdf_to_images(input_path, img_dir, fmt=fmt, dpi=int(dpi))
        results = []
        for f in output_files:
            results.append({
                'name': os.path.basename(f),
                'path': os.path.relpath(f, OUTPUT_FOLDER).replace('\\', '/'),
                'size': os.path.getsize(f),
            })
        return jsonify({'files': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/images-to-pdf', methods=['POST'])
def api_images_to_pdf():
    data = request.json
    filenames = data.get('filenames', [])

    input_paths = []
    for f in filenames:
        path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.exists(path):
            input_paths.append(path)

    if not input_paths:
        return jsonify({'error': 'No valid image files'}), 400

    output_name = f"converted_{uuid.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.images_to_pdf(input_paths, output_path)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Preview & download
# ---------------------------------------------------------------------------

@app.route('/api/preview/<filename>')
def preview(filename):
    # Check in uploads first, then output
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    if os.path.exists(upload_path):
        file_path = upload_path
    elif os.path.exists(output_path):
        file_path = output_path
    else:
        return jsonify({'error': 'File not found'}), 404

    if file_path.lower().endswith('.pdf'):
        try:
            page_num = int(request.args.get('page', 0))
            doc = fitz.open(file_path)
            if page_num < 0 or page_num >= len(doc):
                page_num = 0
            page = doc[page_num]
            mat = fitz.Matrix(1.5, 1.5)  # ~108 DPI for preview
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes('png')
            doc.close()
            return send_file(io.BytesIO(img_bytes), mimetype='image/png')
        except Exception:
            return jsonify({'error': 'Preview failed'}), 500
    else:
        return send_file(file_path)


@app.route('/api/download/<path:filename>')
def download(filename):
    # Check output folder first (including subdirectories), then uploads
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    elif os.path.exists(upload_path):
        return send_file(upload_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/view/<path:filename>')
def view_file(filename):
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=False)
    elif os.path.exists(upload_path):
        return send_file(upload_path, as_attachment=False)
    else:
        return jsonify({'error': 'File not found'}), 404


# ---------------------------------------------------------------------------
# NEW ROUTES — Text & image overlay
# ---------------------------------------------------------------------------

@app.route('/api/add-text', methods=['POST'])
def api_add_text():
    data = request.json
    filename = data.get('filename')
    text = data.get('text', '')
    page_num = data.get('page_num', 0)
    x = data.get('x', 50)
    y = data.get('y', 50)
    font_size = data.get('font_size', 12)
    color = data.get('color', '#000000')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"text_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.add_text_to_pdf(input_path, output_path, text, page_num, x, y, font_size)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/add-image', methods=['POST'])
def api_add_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['file']
    filename = request.form.get('filename')
    page_num = int(request.form.get('page_num', 0))
    x = float(request.form.get('x', 50))
    y = float(request.form.get('y', 50))
    width = float(request.form.get('width', 200))

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    # Save uploaded image to uploads
    img_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(image_file.filename)}"
    image_path = os.path.join(UPLOAD_FOLDER, img_name)
    image_file.save(image_path)

    output_name = f"img_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.add_image_to_pdf(input_path, output_path, image_path, page_num, x, y, width)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# NEW ROUTES — Page numbers, crop, delete, reorder, extract, insert
# ---------------------------------------------------------------------------

@app.route('/api/add-page-numbers', methods=['POST'])
def api_add_page_numbers():
    data = request.json
    filename = data.get('filename')
    position = data.get('position', 'bottom-center')
    start_num = data.get('start_num', 1)
    font_size = data.get('font_size', 12)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"numbered_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.add_page_numbers(input_path, output_path, position, start_num, font_size)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crop', methods=['POST'])
def api_crop():
    data = request.json
    filename = data.get('filename')
    left = data.get('left', 0)
    top = data.get('top', 0)
    right = data.get('right', 0)
    bottom = data.get('bottom', 0)

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"cropped_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.crop_pdf(input_path, output_path, left, top, right, bottom)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete-pages', methods=['POST'])
def api_delete_pages():
    data = request.json
    filename = data.get('filename')
    pages = data.get('pages', [])

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"deleted_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.delete_pages(input_path, output_path, pages)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reorder', methods=['POST'])
def api_reorder():
    data = request.json
    filename = data.get('filename')
    order = data.get('order', [])

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"reordered_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.reorder_pages(input_path, output_path, order)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-pages', methods=['POST'])
def api_extract_pages():
    data = request.json
    filename = data.get('filename')
    pages = data.get('pages', [])

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"extracted_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.extract_pages(input_path, output_path, pages)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insert-pages', methods=['POST'])
def api_insert_pages():
    data = request.json
    base_filename = data.get('base_filename')
    insert_filename = data.get('insert_filename')
    position = data.get('position', 0)

    base_path = os.path.join(UPLOAD_FOLDER, base_filename)
    insert_path = os.path.join(UPLOAD_FOLDER, insert_filename)

    if not os.path.exists(base_path):
        return jsonify({'error': 'Base file not found'}), 404
    if not os.path.exists(insert_path):
        return jsonify({'error': 'Insert file not found'}), 404

    output_name = f"inserted_{base_filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.insert_pages(base_path, insert_path, output_path, position)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# NEW ROUTES — Watermark, conversions, security
# ---------------------------------------------------------------------------

@app.route('/api/watermark', methods=['POST'])
def api_watermark():
    data = request.json
    filename = data.get('filename')
    text = data.get('text', 'WATERMARK')
    font_size = data.get('font_size', 48)
    color = data.get('color', '#cccccc')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    # Convert hex color string to RGB tuple in 0-1 range
    color_hex = color.lstrip('#')
    color_tuple = (
        int(color_hex[0:2], 16) / 255.0,
        int(color_hex[2:4], 16) / 255.0,
        int(color_hex[4:6], 16) / 255.0,
    )

    output_name = f"watermarked_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.add_watermark(input_path, output_path, text, font_size, color_tuple)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/word-to-pdf', methods=['POST'])
def api_word_to_pdf():
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path): return jsonify({'error':'File not found'}), 404
    base = os.path.splitext(filename)[0]
    output_name = f"{base}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.convert_word_to_pdf(input_path, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/redact', methods=['POST'])
def api_redact():
    data = request.json
    filename = data.get('filename')
    rects = data.get('rects', [])
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_name = f"redacted_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.redact_pdf(input_path, output_path, rects)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    try:
        data = request.json
        filename = data.get('filename')
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        summary = pdf_tools.summarize_pdf(input_path)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def api_translate():
    try:
        data = request.json
        filename = data.get('filename')
        lang = data.get('lang', 'hi')
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        translated = pdf_tools.translate_pdf(input_path, dest_lang=lang)
        return jsonify({'translated': translated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf-to-pdfa', methods=['POST'])
def api_pdf_to_pdfa():
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_name = f"pdfa_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.convert_to_pdfa(input_path, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/excel-to-pdf', methods=['POST'])
def api_excel_to_pdf():
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path): return jsonify({'error':'File not found'}), 404
    base = os.path.splitext(filename)[0]
    output_name = f"{base}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.convert_excel_to_pdf(input_path, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pptx-to-pdf', methods=['POST'])
def api_pptx_to_pdf():
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path): return jsonify({'error':'File not found'}), 404
    base = os.path.splitext(filename)[0]
    output_name = f"{base}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.convert_ppt_to_pdf(input_path, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf-to-word', methods=['POST'])
def api_pdf_to_word():
    data = request.json
    filename = data.get('filename')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    base = os.path.splitext(filename)[0]
    output_name = f"{base}.docx"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.pdf_to_word(input_path, output_path)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf-to-excel', methods=['POST'])
def api_pdf_to_excel():
    data = request.json
    filename = data.get('filename')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    base = os.path.splitext(filename)[0]
    output_name = f"{base}.xlsx"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.pdf_to_excel(input_path, output_path)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf-to-pptx', methods=['POST'])
def api_pdf_to_pptx():
    data = request.json
    filename = data.get('filename')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    base = os.path.splitext(filename)[0]
    output_name = f"{base}.pptx"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.pdf_to_pptx(input_path, output_path)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/protect', methods=['POST'])
def api_protect():
    data = request.json
    filename = data.get('filename')
    user_password = data.get('user_password', '')
    owner_password = data.get('owner_password', '')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"protected_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.protect_pdf(input_path, output_path, user_password, owner_password)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/unlock', methods=['POST'])
def api_unlock():
    data = request.json
    filename = data.get('filename')
    password = data.get('password', '')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"unlocked_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.unlock_pdf(input_path, output_path, password)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# NEW ROUTES — Compare, metadata, OCR, sign, thumbnails
# ---------------------------------------------------------------------------

@app.route('/api/compare', methods=['POST'])
def api_compare():
    data = request.json
    filename1 = data.get('filename1')
    filename2 = data.get('filename2')

    path1 = os.path.join(UPLOAD_FOLDER, filename1)
    path2 = os.path.join(UPLOAD_FOLDER, filename2)

    if not os.path.exists(path1):
        return jsonify({'error': 'First file not found'}), 404
    if not os.path.exists(path2):
        return jsonify({'error': 'Second file not found'}), 404

    output_dir = os.path.join(OUTPUT_FOLDER, f"compare_{uuid.uuid4().hex[:8]}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        pdf_tools.compare_pdfs(path1, path2, output_dir)
        results = []
        for f in sorted(os.listdir(output_dir)):
            fpath = os.path.join(output_dir, f)
            if os.path.isfile(fpath):
                results.append({
                    'name': f,
                    'path': os.path.relpath(fpath, OUTPUT_FOLDER).replace('\\', '/'),
                    'size': os.path.getsize(fpath),
                })
        return jsonify({'files': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metadata', methods=['POST'])
def api_metadata():
    data = request.json
    filename = data.get('filename')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        info = pdf_tools.get_pdf_info(input_path)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/edit-metadata', methods=['POST'])
def api_edit_metadata():
    data = request.json
    filename = data.get('filename')
    metadata = {
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'subject': data.get('subject', ''),
        'keywords': data.get('keywords', ''),
    }

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"meta_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.edit_metadata(input_path, output_path, metadata)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    data = request.json
    filename = data.get('filename')
    lang = data.get('lang', 'eng')

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_name = f"ocr_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.ocr_pdf(input_path, output_path, lang)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sign', methods=['POST'])
def api_sign():
    if 'signature' not in request.files:
        return jsonify({'error': 'No signature image provided'}), 400

    sig_file = request.files['signature']
    filename = request.form.get('filename')
    page_num = int(request.form.get('page_num', 0))
    x = float(request.form.get('x', 50))
    y = float(request.form.get('y', 50))
    width = float(request.form.get('width', 150))
    height = float(request.form.get('height', 50))

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    # Save signature image
    sig_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(sig_file.filename)}"
    sig_path = os.path.join(UPLOAD_FOLDER, sig_name)
    sig_file.save(sig_path)

    output_name = f"signed_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    try:
        pdf_tools.sign_pdf(input_path, output_path, sig_path, page_num, x, y, width, height)
        size = os.path.getsize(output_path)
        return jsonify({'output': output_name, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/page-thumbnails/<filename>')
def api_page_thumbnails(filename):
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    thumb_dir = os.path.join(OUTPUT_FOLDER, f"thumbs_{uuid.uuid4().hex[:8]}")
    os.makedirs(thumb_dir, exist_ok=True)

    try:
        doc = fitz.open(input_path)
        pages = []
        for i in range(len(doc)):
            page = doc[i]
            mat = fitz.Matrix(72 / 72, 72 / 72)  # 72 DPI
            pix = page.get_pixmap(matrix=mat)
            thumb_name = f"page_{i + 1}.png"
            thumb_path = os.path.join(thumb_dir, thumb_name)
            pix.save(thumb_path)
            rel_path = os.path.relpath(thumb_path, OUTPUT_FOLDER).replace('\\', '/')
            pages.append({
                'page_num': i + 1,
                'thumbnail_url': f"/api/download/{rel_path}",
            })
        doc.close()
        return jsonify({'pages': pages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@app.route('/api/html-to-pdf', methods=['POST'])
def api_html_to_pdf():
    data = request.json
    html_input = data.get('html')
    output_name = f"html_{uuid.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.convert_html_to_pdf(html_input, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/repair', methods=['POST'])
def api_repair():
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_name = f"repaired_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    try:
        pdf_tools.repair_pdf(input_path, output_path)
        return jsonify({'output': output_name, 'size': os.path.getsize(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
