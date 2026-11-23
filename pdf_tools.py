import fitz  # PyMuPDF
from PIL import Image, ImageChops
import io
import os
import img2pdf

def get_pdf_text_blocks(input_path, page_num):
    doc = fitz.open(input_path)
    page = doc[page_num]
    blocks = page.get_text("dict")["blocks"]
    spans = []
    for b in blocks:
        if b.get("type", 1) == 0:  # text block
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    text = s.get("text", "").strip()
                    if text:
                        spans.append({
                            "bbox": s["bbox"], # (x0, y0, x1, y1)
                            "text": text,
                            "size": s["size"],
                            "color": s["color"],
                            "font": s["font"]
                        })
    doc.close()
    return spans

def apply_live_text_edits(input_path, output_path, edits):
    doc = fitz.open(input_path)
    
    # Group edits by page
    page_edits = {}
    for edit in edits:
        pn = edit["page_num"]
        if pn not in page_edits:
            page_edits[pn] = []
        page_edits[pn].append(edit)
        
    for page_num, p_edits in page_edits.items():
        page = doc[page_num]
        
        # Step 1: Add redactions for all edits on this page
        for edit in p_edits:
            bbox = edit["bbox"]
            rect = fitz.Rect(*bbox)
            # Expand slightly to cover anti-aliasing edges
            rect = rect + (-1, -1, 1, 1)
            page.add_redact_annot(rect, fill=(1, 1, 1))
            
        # Apply all redactions on this page at once
        page.apply_redactions()
        
        # Step 2: Insert new text boxes
        for edit in p_edits:
            new_text = edit["new_text"]
            if new_text.strip():
                bbox = edit["bbox"]
                font_size = edit.get("font_size", 12)
                # Ensure the box is tall enough for the font size to prevent clipping
                rect = fitz.Rect(bbox[0], bbox[1], bbox[2] + 200, bbox[1] + font_size * 1.5)
                page.insert_textbox(rect, new_text, fontsize=font_size, fontname="helv", color=(0,0,0), align=0)
                
    doc.save(output_path)
    doc.close()
    return output_path

def apply_canvas_edits(input_path, output_path, elements):
    doc = fitz.open(input_path)
    
    # First, handle redactions for modified existing elements
    for el in elements:
        page_num = el.get("page_num", 0)
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]
        if el.get("is_modified_existing") and el.get("orig_bbox"):
            ob = el["orig_bbox"]
            rect = fitz.Rect(ob[0] - 1, ob[1] - 1, ob[2] + 1, ob[3] + 1)
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

    for el in elements:
        page_num = el.get("page_num", 0)
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]
        
        if el["type"] == "text":
            text = el.get("text", "")
            if not text:
                continue
            x = float(el.get("x", 72))
            y = float(el.get("y", 72))
            fs = float(el.get("fontSize", 16))
            color = el.get("color", "#000000")
            c_tuple = (0, 0, 0)
            if color.startswith("#") and len(color) == 7:
                c_tuple = (int(color[1:3], 16)/255.0, int(color[3:5], 16)/255.0, int(color[5:7], 16)/255.0)
            
            baseline_y = float(el.get("origin_y", y + fs * 0.85))
            page.insert_text(fitz.Point(x, baseline_y), text, fontsize=fs, fontname="helv", color=c_tuple)
        
        elif el["type"] == "image":
            img_path = el.get("image_path")
            if img_path and os.path.exists(img_path):
                x = float(el["x"])
                y = float(el["y"])
                w = float(el["width"])
                h = float(el["height"])
                rect = fitz.Rect(x, y, x + w, y + h)
                page.insert_image(rect, filename=img_path)
                
    doc.save(output_path)
    doc.close()
    return output_path

def convert_word_to_pdf(input_path, output_path):
    from docx2pdf import convert
    convert(input_path, output_path)
    return output_path

def convert_excel_to_pdf(input_path, output_path):
    import comtypes.client
    import os
    import pythoncom
    pythoncom.CoInitialize()
    excel = comtypes.client.CreateObject("Excel.Application")
    excel.Visible = False
    try:
        wb = excel.Workbooks.Open(os.path.abspath(input_path))
        wb.ExportAsFixedFormat(0, os.path.abspath(output_path))
        wb.Close()
    finally:
        excel.Quit()
        pythoncom.CoUninitialize()
    return output_path

def convert_ppt_to_pdf(input_path, output_path):
    import comtypes.client
    import os
    import pythoncom
    pythoncom.CoInitialize()
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    try:
        presentation = powerpoint.Presentations.Open(os.path.abspath(input_path), WithWindow=False)
        presentation.SaveAs(os.path.abspath(output_path), 32)
        presentation.Close()
    finally:
        powerpoint.Quit()
        pythoncom.CoUninitialize()
    return output_path




# ---------------------------------------------------------------------------
# Original functions
# ---------------------------------------------------------------------------

def decolor_pdf(input_path, output_path, threshold=60):
    """Remove colored backgrounds from PDF, keeping black/gray text.

    Converts each page to an image, then for each pixel:
    - If the pixel is gray/black (R,G,B close together and below brightness threshold or all channels similar), keep it
    - Otherwise set to white

    This is deterministic - same input always produces same output.
    """
    doc = fitz.open(input_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render at 300 DPI for quality
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Process pixels
        pixels = img.load()
        width, height = img.size

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # Check if pixel is "gray" (all channels close together)
                max_diff = max(r, g, b) - min(r, g, b)

                if max_diff > threshold:
                    # This pixel has significant color - make it white
                    pixels[x, y] = (255, 255, 255)
                # else: keep the pixel as-is (it's gray/black)

        images.append(img)

    doc.close()

    # Save all images as PDF
    if images:
        images[0].save(
            output_path, 'PDF', save_all=True, append_images=images[1:], resolution=300
        )

    return output_path


def merge_pdfs(input_paths, output_path):
    """Merge multiple PDFs into one."""
    result = fitz.open()
    for path in input_paths:
        doc = fitz.open(path)
        result.insert_pdf(doc)
        doc.close()
    result.save(output_path)
    result.close()
    return output_path


def split_pdf(input_path, output_dir):
    """Split a PDF into individual pages."""
    doc = fitz.open(input_path)
    output_files = []
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    for i in range(len(doc)):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        out_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
        new_doc.save(out_path)
        new_doc.close()
        output_files.append(out_path)

    doc.close()
    return output_files


def rotate_pdf(input_path, output_path, angle=90):
    """Rotate all pages of a PDF by the given angle."""
    doc = fitz.open(input_path)
    for page in doc:
        page.set_rotation((page.rotation + angle) % 360)
    doc.save(output_path)
    doc.close()
    return output_path


def compress_pdf(input_path, output_path, quality=75):
    """Compress a PDF by re-rendering pages at lower quality."""
    doc = fitz.open(input_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(150 / 72, 150 / 72)  # 150 DPI for compression
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Compress via JPEG
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=quality)
        buf.seek(0)
        img = Image.open(buf)
        images.append(img.copy())
        buf.close()

    doc.close()

    if images:
        images[0].save(
            output_path, 'PDF', save_all=True, append_images=images[1:], resolution=150
        )

    return output_path


def pdf_to_images(input_path, output_dir, fmt='png', dpi=200):
    """Convert PDF pages to images."""
    doc = fitz.open(input_path)
    output_files = []
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        out_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.{fmt}")
        pix.save(out_path)
        output_files.append(out_path)

    doc.close()
    return output_files


def images_to_pdf(image_paths, output_path):
    """Convert images to a PDF."""
    pdf_bytes = img2pdf.convert(image_paths)
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    return output_path


def get_pdf_info(input_path):
    """Get metadata about a PDF."""
    doc = fitz.open(input_path)
    info = {
        'pages': len(doc),
        'metadata': doc.metadata,
        'file_size': os.path.getsize(input_path),
        'page_sizes': [],
    }
    for page in doc:
        rect = page.rect
        info['page_sizes'].append(
            {
                'width': round(rect.width * 25.4 / 72, 1),  # mm
                'height': round(rect.height * 25.4 / 72, 1),
                'width_in': round(rect.width / 72, 2),
                'height_in': round(rect.height / 72, 2),
            }
        )
    doc.close()
    return info


# ---------------------------------------------------------------------------
# New functions
# ---------------------------------------------------------------------------

def add_text_to_pdf(input_path, output_path, text, page_num=0, x=72, y=72,
                    font_size=12, font_name='helv', color=(0, 0, 0)):
    """Insert text at specific coordinates on a PDF page.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the modified PDF.
        text: The text string to insert.
        page_num: 0-indexed page number to add text to.
        x: Horizontal position in points from the left edge.
        y: Vertical position in points from the top edge.
        font_size: Font size in points.
        font_name: PyMuPDF font name (e.g. 'helv', 'tiro', 'cour').
        color: Tuple of (R, G, B) floats 0-1 or ints 0-255.
    """
    doc = fitz.open(input_path)
    page = doc[page_num]
    page.insert_text(
        fitz.Point(x, y),
        text,
        fontsize=font_size,
        fontname=font_name,
        color=color,
        overlay=True,
    )
    doc.save(output_path)
    doc.close()
    return output_path


def add_image_to_pdf(input_path, output_path, image_path, page_num=0,
                     x=72, y=72, width=200, height=None):
    """Insert an image onto a PDF page.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the modified PDF.
        image_path: Path to the image file to insert.
        page_num: 0-indexed page number.
        x: Left edge of the image rectangle in points.
        y: Top edge of the image rectangle in points.
        width: Width of the image in points.
        height: Height of the image in points. If None, calculated to
                preserve the original aspect ratio.
    """
    doc = fitz.open(input_path)
    page = doc[page_num]

    if height is None:
        # Determine aspect ratio from the source image
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        height = width * orig_h / orig_w
        img.close()

    rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(rect, filename=image_path)
    doc.save(output_path)
    doc.close()
    return output_path


def add_page_numbers(input_path, output_path, position='bottom-center',
                     start_num=1, font_size=10):
    """Add page numbers to every page of a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the numbered PDF.
        position: One of 'bottom-left', 'bottom-center', 'bottom-right',
                  'top-left', 'top-center', 'top-right'.
        start_num: The number to begin counting from.
        font_size: Font size for the page number text.
    """
    doc = fitz.open(input_path)
    font = fitz.Font('helv')

    for i, page in enumerate(doc):
        rect = page.rect
        num_text = str(start_num + i)
        text_width = font.text_length(num_text, fontsize=font_size)
        margin = 36  # half-inch margin from edges

        # Calculate x coordinate
        if position.endswith('left'):
            x = rect.x0 + margin
        elif position.endswith('right'):
            x = rect.x1 - margin - text_width
        else:  # center
            x = (rect.width - text_width) / 2

        # Calculate y coordinate
        if position.startswith('top'):
            y = rect.y0 + margin + font_size
        else:  # bottom
            y = rect.y1 - margin

        page.insert_text(
            fitz.Point(x, y),
            num_text,
            fontsize=font_size,
            fontname='helv',
            color=(0, 0, 0),
            overlay=True,
        )

    doc.save(output_path)
    doc.close()
    return output_path


def visual_norm_to_visual_rect(page, norm):
    """Convert normalized UI box {x, y, w, h} to visual page.rect coordinates."""
    r = page.rect
    x0 = max(0.0, min(1.0, float(norm.get("x", 0.0)))) * r.width
    y0 = max(0.0, min(1.0, float(norm.get("y", 0.0)))) * r.height
    x1 = max(0.0, min(1.0, float(norm.get("x", 0.0)) + float(norm.get("w", 1.0)))) * r.width
    y1 = max(0.0, min(1.0, float(norm.get("y", 0.0)) + float(norm.get("h", 1.0)))) * r.height
    vis = fitz.Rect(x0, y0, x1, y1) & r
    if vis.is_empty or vis.width < 5 or vis.height < 5:
        raise ValueError("Crop region is too small or invalid.")
    return vis


def detect_content_crop_norm(page, padding_pt=8.0):
    """Auto-Trim Whitespace helper returning normalized visual coordinates."""
    union = fitz.Rect()
    try:
        for _, bbox in page.get_bboxlog():
            union |= fitz.Rect(bbox)
    except Exception:
        pass
    if union.is_empty:
        return {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    pr = page.rect
    padded = (union + (-padding_pt, -padding_pt, padding_pt, padding_pt)) & pr
    return {
        "x": round(padded.x0 / pr.width, 4),
        "y": round(padded.y0 / pr.height, 4),
        "w": round(padded.width / pr.width, 4),
        "h": round(padded.height / pr.height, 4),
    }


def crop_pdf(input_path, output_path, left=0, top=0, right=0, bottom=0, payload=None):
    """Crop margins from pages of a PDF with full derotation, normalized coordinates, and multi-mode support."""
    src = fitz.open(input_path)

    # Build normalized payload if not provided
    if not payload:
        first_rect = src[0].rect if len(src) else fitz.Rect(0, 0, 595.28, 841.89)
        pw, ph = max(1.0, first_rect.width), max(1.0, first_rect.height)
        norm_x = float(left or 0) / pw
        norm_y = float(top or 0) / ph
        norm_w = max(0.05, 1.0 - norm_x - (float(right or 0) / pw))
        norm_h = max(0.05, 1.0 - norm_y - (float(bottom or 0) / ph))
        payload = {
            "mode": "standard",
            "scope": "all",
            "default_crop": {"x": norm_x, "y": norm_y, "w": norm_w, "h": norm_h},
            "page_overrides": {}
        }

    mode = payload.get("mode", "standard")
    scope = payload.get("scope", "all")
    overrides = payload.get("page_overrides", {})
    default_crop = payload.get("default_crop", {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
    current_idx = int(payload.get("current_page", 0))

    for idx, page in enumerate(src):
        should_crop = (scope == "all") or (idx == current_idx) or (str(idx) in overrides)
        if not should_crop:
            continue

        norm = overrides.get(str(idx), default_crop)
        vis_rect = visual_norm_to_visual_rect(page, norm)

        if mode == "hard":
            pr = page.rect
            outer_bands = [
                fitz.Rect(0, 0, pr.width, vis_rect.y0),
                fitz.Rect(0, vis_rect.y1, pr.width, pr.height),
                fitz.Rect(0, vis_rect.y0, vis_rect.x0, vis_rect.y1),
                fitz.Rect(vis_rect.x1, vis_rect.y0, pr.width, vis_rect.y1),
            ]
            for band in outer_bands:
                if band.width > 0.5 and band.height > 0.5:
                    page.add_redact_annot(band, fill=None)
            page.apply_redactions(
                images=getattr(fitz, "PDF_REDACT_IMAGE_PIXELS", 2),
                graphics=getattr(fitz, "PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED", 2),
            )

        # Map visual rect -> unrotated space -> offset by existing cropbox origin
        unrot = vis_rect * page.derotation_matrix
        pos = page.cropbox_position
        target_box = (unrot + (pos.x, pos.y, pos.x, pos.y)) & page.mediabox

        # Clear conflicting secondary boxes so all viewers/printers obey CropBox
        for box_key in ("TrimBox", "BleedBox", "ArtBox"):
            try:
                src.xref_set_key(page.xref, box_key, "null")
            except Exception:
                pass

        page.set_cropbox(target_box)
        page.set_mediabox(target_box)

    src.save(output_path, garbage=4, deflate=True)
    src.close()
    return output_path
    return output_path


def delete_pages(input_path, output_path, page_numbers):
    """Delete specified pages from a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the PDF with pages removed.
        page_numbers: List of 0-indexed page numbers to delete.
    """
    doc = fitz.open(input_path)
    doc.delete_pages(page_numbers)
    doc.save(output_path)
    doc.close()
    return output_path


def reorder_pages(input_path, output_path, new_order):
    """Rearrange pages of a PDF in a custom order.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the reordered PDF.
        new_order: List of 0-indexed page numbers representing the
                   desired order.  e.g. [2, 0, 1] puts the third page
                   first, then the first, then the second.
    """
    doc = fitz.open(input_path)
    result = fitz.open()
    for page_num in new_order:
        result.insert_pdf(doc, from_page=page_num, to_page=page_num)
    doc.close()
    result.save(output_path)
    result.close()
    return output_path


def extract_pages(input_path, output_path, page_numbers):
    """Extract specific pages from a PDF into a new PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the extracted pages.
        page_numbers: List of 0-indexed page numbers to extract.
    """
    doc = fitz.open(input_path)
    result = fitz.open()
    for page_num in page_numbers:
        result.insert_pdf(doc, from_page=page_num, to_page=page_num)
    doc.close()
    result.save(output_path)
    result.close()
    return output_path


def insert_pages(base_path, insert_path, output_path, position=0):
    """Insert all pages from one PDF into another at a given position.

    Args:
        base_path: Path to the base PDF.
        insert_path: Path to the PDF whose pages will be inserted.
        output_path: Path to save the combined PDF.
        position: 0-indexed page position in the base PDF where the
                  inserted pages should appear.  0 means the very
                  beginning.
    """
    base_doc = fitz.open(base_path)
    insert_doc = fitz.open(insert_path)
    result = fitz.open()

    # Pages before the insertion point
    if position > 0:
        result.insert_pdf(base_doc, from_page=0, to_page=position - 1)

    # Insert the entire second document
    result.insert_pdf(insert_doc)

    # Remaining pages from the base document
    if position < len(base_doc):
        result.insert_pdf(base_doc, from_page=position, to_page=len(base_doc) - 1)

    base_doc.close()
    insert_doc.close()
    result.save(output_path)
    result.close()
    return output_path


def add_watermark(input_path, output_path, text='CONFIDENTIAL', font_size=60,
                  color=(0.7, 0.7, 0.7)):
    """Add a centered text watermark on every page of a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the watermarked PDF.
        text: Watermark text string.
        font_size: Font size for the watermark.
        color: Tuple of (R, G, B) floats 0-1 for the watermark color.
    """
    doc = fitz.open(input_path)
    for page in doc:
        rect = page.rect
        font = fitz.Font('helv')
        tw = font.text_length(text, fontsize=font_size)
        x = (rect.width - tw) / 2
        y = rect.height / 2
        page.insert_text(
            fitz.Point(x, y),
            text,
            fontsize=font_size,
            fontname='helv',
            color=color,
            overlay=True,
        )
    doc.save(output_path)
    doc.close()
    return output_path


def pdf_to_word(input_path, output_path):
    """Extract text from a PDF and save as a Word (.docx) document.

    Requires the ``python-docx`` package.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the .docx file.
    """
    from docx import Document as DocxDocument
    from docx.shared import Pt

    doc = fitz.open(input_path)
    word_doc = DocxDocument()

    for page_num in range(len(doc)):
        page = doc[page_num]
        if page_num > 0:
            word_doc.add_page_break()
        text = page.get_text('text')
        for para_text in text.split('\n'):
            if para_text.strip():
                p = word_doc.add_paragraph(para_text)
                p.style.font.size = Pt(11)

    doc.close()
    word_doc.save(output_path)
    return output_path


def pdf_to_excel(input_path, output_path):
    """Extract tables and text from a PDF into an Excel (.xlsx) workbook.

    Each page becomes a separate worksheet. If structured tables are
    detected they are extracted directly; otherwise text is written
    line-by-line in the first column.

    Requires the ``openpyxl`` package.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the .xlsx file.
    """
    from openpyxl import Workbook

    doc = fitz.open(input_path)
    wb = Workbook()

    for page_num in range(len(doc)):
        page = doc[page_num]
        if page_num == 0:
            ws = wb.active
            ws.title = f'Page {page_num + 1}'
        else:
            ws = wb.create_sheet(title=f'Page {page_num + 1}')

        # Try to extract tables first
        tables = page.find_tables()
        if tables and len(tables.tables) > 0:
            row_offset = 1
            for table in tables:
                data = table.extract()
                for r, row in enumerate(data):
                    for c, cell in enumerate(row):
                        ws.cell(row=row_offset + r, column=c + 1, value=cell or '')
                row_offset += len(data) + 1
        else:
            # Fallback: extract text line by line
            text = page.get_text('text')
            for r, line in enumerate(text.split('\n')):
                if line.strip():
                    ws.cell(row=r + 1, column=1, value=line)

    doc.close()
    wb.save(output_path)
    return output_path


def pdf_to_pptx(input_path, output_path, dpi=150):
    """Convert each PDF page into a slide in a PowerPoint (.pptx) file.

    Pages are rendered as images and placed full-slide on blank layouts.

    Requires the ``python-pptx`` package.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the .pptx file.
        dpi: Resolution for rendering pages.
    """
    from pptx import Presentation
    from pptx.util import Inches

    doc = fitz.open(input_path)
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # blank layout

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('png')

        slide = prs.slides.add_slide(blank_layout)
        img_stream = io.BytesIO(img_bytes)
        slide.shapes.add_picture(
            img_stream, Inches(0), Inches(0),
            prs.slide_width, prs.slide_height,
        )

    doc.close()
    prs.save(output_path)
    return output_path


def protect_pdf(input_path, output_path, user_password='', owner_password=''):
    """Encrypt a PDF with AES-256 encryption.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the encrypted PDF.
        user_password: Password required to open the PDF. Empty string
                       means the PDF can be opened without a password
                       but is still encrypted.
        owner_password: Owner password for full permissions. Defaults to
                        the user_password if not provided.
    """
    doc = fitz.open(input_path)
    perm = fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY | fitz.PDF_PERM_ANNOTATE
    doc.save(
        output_path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=user_password,
        owner_pw=owner_password if owner_password else user_password,
        permissions=perm,
    )
    doc.close()
    return output_path


def unlock_pdf(input_path, output_path, password):
    """Remove password protection from an encrypted PDF.

    Args:
        input_path: Path to the encrypted PDF.
        output_path: Path to save the unlocked PDF.
        password: The password needed to decrypt the PDF.

    Raises:
        ValueError: If the supplied password is incorrect.
    """
    doc = fitz.open(input_path)
    if doc.is_encrypted:
        if not doc.authenticate(password):
            raise ValueError('Incorrect password')
    doc.save(output_path)
    doc.close()
    return output_path


def compare_pdfs(path1, path2, output_dir, dpi=150):
    """Render two PDFs and create side-by-side comparison images.

    For each page a combined image is produced with the first PDF's
    rendering on the left and the second PDF's rendering on the right.

    Args:
        path1: Path to the first PDF.
        path2: Path to the second PDF.
        output_dir: Directory to save the comparison images.
        dpi: Resolution for rendering pages.

    Returns:
        List of file paths to the generated comparison images.
    """
    os.makedirs(output_dir, exist_ok=True)

    doc1 = fitz.open(path1)
    doc2 = fitz.open(path2)
    max_pages = max(len(doc1), len(doc2))
    results = []

    for i in range(max_pages):
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        if i < len(doc1):
            pix1 = doc1[i].get_pixmap(matrix=mat)
            img1 = Image.frombytes('RGB', [pix1.width, pix1.height], pix1.samples)
        else:
            img1 = Image.new('RGB', (100, 100), 'white')

        if i < len(doc2):
            pix2 = doc2[i].get_pixmap(matrix=mat)
            img2 = Image.frombytes('RGB', [pix2.width, pix2.height], pix2.samples)
        else:
            img2 = Image.new('RGB', (100, 100), 'white')

        # Resize to same dimensions
        w = max(img1.width, img2.width)
        h = max(img1.height, img2.height)
        canvas1 = Image.new('RGB', (w, h), 'white')
        canvas1.paste(img1, (0, 0))
        canvas2 = Image.new('RGB', (w, h), 'white')
        canvas2.paste(img2, (0, 0))

        # Create a combined image: left = doc1, right = doc2
        combined_w = w * 2 + 20
        combined = Image.new('RGB', (combined_w, h), (30, 30, 30))
        combined.paste(canvas1, (0, 0))
        combined.paste(canvas2, (w + 20, 0))

        out_path = os.path.join(output_dir, f'compare_page_{i + 1}.png')
        combined.save(out_path)
        results.append(out_path)

    doc1.close()
    doc2.close()
    return results


def edit_metadata(input_path, output_path, metadata_dict):
    """Edit PDF metadata fields.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the PDF with updated metadata.
        metadata_dict: Dictionary of metadata keys to update.
                       Valid keys include 'title', 'author', 'subject',
                       'keywords', 'creator', 'producer'.
    """
    doc = fitz.open(input_path)
    current = doc.metadata
    for key in metadata_dict:
        if key in current:
            current[key] = metadata_dict[key]
    doc.set_metadata(current)
    doc.save(output_path)
    doc.close()
    return output_path


def ocr_pdf(input_path, output_path, lang='eng'):
    """OCR a scanned PDF to produce a searchable PDF using pure-Python RapidOCR (with Tesseract fallback)."""
    import fitz
    import numpy as np

    has_rapidocr = False
    ocr_engine = None
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr_engine = RapidOCR()
        has_rapidocr = True
    except Exception:
        has_rapidocr = False

    doc = fitz.open(input_path)
    result_doc = fitz.open()

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat)

        new_page = result_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, pixmap=pix)

        if has_rapidocr and ocr_engine is not None:
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img_np = img_np[:, :, :3]
            results, _ = ocr_engine(img_np)
            if results:
                scale_x = page.rect.width / pix.width
                scale_y = page.rect.height / pix.height
                for box, text, conf in results:
                    bx = box[0][0] * scale_x
                    by = box[0][1] * scale_y
                    bw = (box[1][0] - box[0][0]) * scale_x
                    bh = (box[2][1] - box[1][1]) * scale_y
                    fontsize = max(8, bh * 0.8)
                    new_page.insert_text(fitz.Point(bx, by + bh), text, fontsize=fontsize, render_mode=3)
        else:
            try:
                import pytesseract
                from PIL import Image
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang=lang)
                if text.strip():
                    new_page.insert_text(fitz.Point(72, 72), text, fontsize=1, color=(1, 1, 1), overlay=True)
            except Exception:
                extracted = page.get_text()
                if extracted.strip():
                    new_page.insert_text(fitz.Point(72, 72), extracted, fontsize=1, color=(1, 1, 1), overlay=True)

    doc.close()
    result_doc.save(output_path, deflate=True)
    result_doc.close()
    return output_path


def pdf_to_markdown(input_path, output_path):
    """Convert PDF document into clean Markdown format."""
    try:
        import pymupdf4llm
        md_text = pymupdf4llm.to_markdown(input_path)
    except Exception:
        import fitz
        doc = fitz.open(input_path)
        md_text = ""
        for page in doc:
            md_text += page.get_text() + "\n\n"
        doc.close()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return output_path


def get_pdf_form_fields(input_path):
    """Extract interactive form fields from a PDF."""
    import fitz
    doc = fitz.open(input_path)
    fields = []
    for page_idx, page in enumerate(doc):
        for widget in page.widgets():
            fields.append({
                'page': page_idx + 1,
                'name': widget.field_name or f"field_{len(fields)+1}",
                'value': widget.field_value or '',
                'type': widget.field_type_string
            })
    doc.close()
    return fields


def fill_pdf_form(input_path, output_path, field_values):
    """Fill interactive PDF form fields with submitted key-value data."""
    import fitz
    doc = fitz.open(input_path)
    for page in doc:
        for widget in page.widgets():
            name = widget.field_name
            if name in field_values:
                val = field_values[name]
                if isinstance(val, bool) or str(val).lower() in ['true', 'false']:
                    widget.field_value = "Yes" if (val is True or str(val).lower() == 'true') else "Off"
                else:
                    widget.field_value = str(val)
                widget.update()
    doc.save(output_path, deflate=True)
    doc.close()
    return output_path


def sign_pdf(input_path, output_path, signature_image_path, page_num=0,
             x=72, y=72, width=150, height=75):
    """Stamp a signature image onto a PDF page.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to save the signed PDF.
        signature_image_path: Path to the signature image file.
        page_num: 0-indexed page number to place the signature on.
        x: Left edge of the signature rectangle in points.
        y: Top edge of the signature rectangle in points.
        width: Width of the signature image in points.
        height: Height of the signature image in points.
    """
    doc = fitz.open(input_path)
    page = doc[page_num]
    rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(rect, filename=signature_image_path)
    doc.save(output_path)
    doc.close()
    return output_path


def convert_html_to_pdf(html_input, output_path):
    from xhtml2pdf import pisa
    import requests
    if html_input.startswith("http://") or html_input.startswith("https://"):
        try:
            html_content = requests.get(html_input).text
        except Exception as e:
            raise ValueError(f"Failed to fetch URL: {e}")
    else:
        html_content = html_input
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(html_content, dest=result_file)
    if pisa_status.err:
        raise ValueError("Failed to generate PDF from HTML")
    return output_path

def repair_pdf(input_path, output_path):
    import fitz
    doc = fitz.open(input_path)
    doc.save(output_path, deflate=True, clean=True)
    doc.close()
    return output_path

def redact_pdf(input_path, output_path, rects):
    import fitz
    doc = fitz.open(input_path)
    for r in rects:
        page_num = int(r.get('page_num', 0))
        if page_num < len(doc):
            page = doc[page_num]
            rect = fitz.Rect(r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])
            page.add_redact_annot(rect, fill=(0,0,0))
            page.apply_redactions()
    doc.save(output_path)
    doc.close()
    return output_path

def summarize_pdf(input_path):
    import fitz
    doc = fitz.open(input_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    if not text.strip(): return "No readable text found in PDF."
    
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        stemmer = Stemmer("english")
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words("english")
        
        summary = []
        for sentence in summarizer(parser.document, 10):
            summary.append(str(sentence))
        return " ".join(summary)
    except Exception as e:
        return f"Summarization error: {str(e)}"

def translate_pdf(input_path, dest_lang="hi"):
    import fitz
    doc = fitz.open(input_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    if not text.strip(): return "No readable text found in PDF."
    
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='auto', target=dest_lang)
        chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
        translated = ""
        for chunk in chunks:
            translated += translator.translate(chunk) + "\n"
        return translated
    except Exception as e:
        return f"Translation error: {str(e)}"

def convert_to_pdfa(input_path, output_path):
    import fitz
    doc = fitz.open(input_path)
    doc.save(output_path, deflate=True)
    doc.close()
    return output_path
