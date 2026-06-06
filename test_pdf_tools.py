import os
import fitz
import pdf_tools
from PIL import Image

def create_dummy_pdf(path, pages=3):
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text(fitz.Point(72, 72), f"This is page {i+1}", fontsize=20)
        page.draw_rect(fitz.Rect(100, 100, 200, 200), color=(1, 0, 0), fill=(1, 0.8, 0.8))
    doc.save(path)
    doc.close()

def create_dummy_image(path):
    img = Image.new('RGB', (200, 100), color = 'red')
    img.save(path)

def test_all():
    os.makedirs('test_output', exist_ok=True)
    
    pdf1 = 'test_output/dummy1.pdf'
    pdf2 = 'test_output/dummy2.pdf'
    img1 = 'test_output/dummy_img.png'
    
    create_dummy_pdf(pdf1, 3)
    create_dummy_pdf(pdf2, 1)
    create_dummy_image(img1)
    
    try:
        print("Testing decolor_pdf...")
        pdf_tools.decolor_pdf(pdf1, 'test_output/decolor.pdf')
        print("Testing merge_pdfs...")
        pdf_tools.merge_pdfs([pdf1, pdf2], 'test_output/merge.pdf')
        print("Testing split_pdf...")
        pdf_tools.split_pdf(pdf1, 'test_output')
        print("Testing rotate_pdf...")
        pdf_tools.rotate_pdf(pdf1, 'test_output/rotate.pdf')
        print("Testing compress_pdf...")
        pdf_tools.compress_pdf(pdf1, 'test_output/compress.pdf')
        print("Testing pdf_to_images...")
        pdf_tools.pdf_to_images(pdf1, 'test_output')
        print("Testing images_to_pdf...")
        pdf_tools.images_to_pdf([img1], 'test_output/images_to.pdf')
        print("Testing get_pdf_info...")
        pdf_tools.get_pdf_info(pdf1)
        
        print("Testing add_text_to_pdf...")
        pdf_tools.add_text_to_pdf(pdf1, 'test_output/add_text.pdf', 'Hello World')
        print("Testing add_image_to_pdf...")
        pdf_tools.add_image_to_pdf(pdf1, 'test_output/add_img.pdf', img1)
        print("Testing add_page_numbers...")
        pdf_tools.add_page_numbers(pdf1, 'test_output/page_numbers.pdf')
        print("Testing crop_pdf...")
        pdf_tools.crop_pdf(pdf1, 'test_output/crop.pdf', 10, 10, 10, 10)
        print("Testing delete_pages...")
        pdf_tools.delete_pages(pdf1, 'test_output/delete.pdf', [1])
        print("Testing reorder_pages...")
        pdf_tools.reorder_pages(pdf1, 'test_output/reorder.pdf', [2, 0, 1])
        print("Testing extract_pages...")
        pdf_tools.extract_pages(pdf1, 'test_output/extract.pdf', [0, 2])
        print("Testing insert_pages...")
        pdf_tools.insert_pages(pdf1, pdf2, 'test_output/insert.pdf', 1)
        print("Testing add_watermark...")
        pdf_tools.add_watermark(pdf1, 'test_output/watermark.pdf')
        print("Testing pdf_to_word...")
        pdf_tools.pdf_to_word(pdf1, 'test_output/word.docx')
        print("Testing pdf_to_excel...")
        pdf_tools.pdf_to_excel(pdf1, 'test_output/excel.xlsx')
        print("Testing pdf_to_pptx...")
        pdf_tools.pdf_to_pptx(pdf1, 'test_output/pptx.pptx')
        print("Testing protect_pdf...")
        pdf_tools.protect_pdf(pdf1, 'test_output/protect.pdf', 'pass')
        print("Testing unlock_pdf...")
        pdf_tools.unlock_pdf('test_output/protect.pdf', 'test_output/unlock.pdf', 'pass')
        print("Testing compare_pdfs...")
        pdf_tools.compare_pdfs(pdf1, pdf1, 'test_output')
        print("Testing edit_metadata...")
        pdf_tools.edit_metadata(pdf1, 'test_output/metadata.pdf', {'title': 'Test'})
        print("Testing sign_pdf...")
        pdf_tools.sign_pdf(pdf1, 'test_output/sign.pdf', img1)
        print("ALL TESTS PASSED")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED: {e}")

if __name__ == '__main__':
    test_all()
