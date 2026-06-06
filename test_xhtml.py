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

convert_html_to_pdf("<h1>Hello World from xhtml2pdf</h1>", "test_xhtml.pdf")
print("Done xhtml2pdf")
