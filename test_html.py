import fitz

def convert_html_to_pdf(html_content, output_path):
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 545, 792)
    leftover = page.insert_htmlbox(rect, html_content)
    while leftover:
        page = doc.new_page()
        leftover = page.insert_htmlbox(rect, leftover)
    doc.save(output_path)
    doc.close()
    return output_path

convert_html_to_pdf("<h1>Hello World</h1><p>This is a test of HTML to PDF.</p>", "html_test.pdf")
print("Done")
