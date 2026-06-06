import sys
import os

with open('app.py', 'a', encoding='utf-8') as f:
    f.write("""

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
    data = request.json
    filename = data.get('filename')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        summary = pdf_tools.summarize_pdf(input_path)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.json
    filename = data.get('filename')
    lang = data.get('lang', 'hi')
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        translated = pdf_tools.translate_pdf(input_path, lang)
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
""")
print("Done appending to app.py")
