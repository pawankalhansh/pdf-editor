import sys
import os

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<div class="tool-grid-container">'
end_marker = '</main>'

new_html = """        <div class="tool-grid-container">
            <!-- Organize PDF Category -->
            <div class="tool-grid active" id="grid-organize">
                <button class="tool-card" data-tool="merge"><span class="tc-icon">➕</span><div class="tc-text"><span class="tc-name">Merge PDF</span><span class="tc-desc">Combine multiple PDFs</span></div></button>
                <button class="tool-card" data-tool="split"><span class="tc-icon">✂️</span><div class="tc-text"><span class="tc-name">Split PDF</span><span class="tc-desc">Separate into individual pages</span></div></button>
                <button class="tool-card" data-tool="delete-pages"><span class="tc-icon">🗑️</span><div class="tc-text"><span class="tc-name">Remove pages</span><span class="tc-desc">Delete specific pages</span></div></button>
                <button class="tool-card" data-tool="extract-pages"><span class="tc-icon">📤</span><div class="tc-text"><span class="tc-name">Extract pages</span><span class="tc-desc">Pull specific pages out</span></div></button>
                <button class="tool-card" data-tool="reorder"><span class="tc-icon">🔄</span><div class="tc-text"><span class="tc-name">Organize PDF</span><span class="tc-desc">Sort or arrange pages</span></div></button>
                <button class="tool-card" data-tool="scan"><span class="tc-icon">📱</span><div class="tc-text"><span class="tc-name">Scan to PDF</span><span class="tc-desc">Capture using webcam</span></div></button>
            </div>

            <!-- Optimize PDF Category -->
            <div class="tool-grid active" id="grid-optimize">
                <button class="tool-card" data-tool="compress"><span class="tc-icon">📉</span><div class="tc-text"><span class="tc-name">Compress PDF</span><span class="tc-desc">Reduce file size securely</span></div></button>
                <button class="tool-card" data-tool="repair"><span class="tc-icon">🛠️</span><div class="tc-text"><span class="tc-name">Repair PDF</span><span class="tc-desc">Fix corrupted documents</span></div></button>
            </div>

            <!-- Convert to PDF Category -->
            <div class="tool-grid active" id="grid-to-pdf">
                <button class="tool-card" data-tool="img-to-pdf"><span class="tc-icon">🖼️</span><div class="tc-text"><span class="tc-name">JPG to PDF</span><span class="tc-desc">Images to PDF format</span></div></button>
                <button class="tool-card" data-tool="word-to-pdf"><span class="tc-icon">📝</span><div class="tc-text"><span class="tc-name">Word to PDF</span><span class="tc-desc">DOC/DOCX to PDF</span></div></button>
                <button class="tool-card" data-tool="pptx-to-pdf"><span class="tc-icon">📊</span><div class="tc-text"><span class="tc-name">PowerPoint to PDF</span><span class="tc-desc">PPT/PPTX to PDF</span></div></button>
                <button class="tool-card" data-tool="excel-to-pdf"><span class="tc-icon">📈</span><div class="tc-text"><span class="tc-name">Excel to PDF</span><span class="tc-desc">XLS/XLSX to PDF</span></div></button>
                <button class="tool-card" data-tool="html-to-pdf"><span class="tc-icon">🌐</span><div class="tc-text"><span class="tc-name">HTML to PDF</span><span class="tc-desc">Webpage or code to PDF</span></div></button>
            </div>

            <!-- Convert from PDF Category -->
            <div class="tool-grid active" id="grid-from-pdf">
                <button class="tool-card" data-tool="pdf-to-img"><span class="tc-icon">📸</span><div class="tc-text"><span class="tc-name">PDF to JPG</span><span class="tc-desc">Extract images from PDF</span></div></button>
                <button class="tool-card" data-tool="pdf-to-word"><span class="tc-icon">📝</span><div class="tc-text"><span class="tc-name">PDF to Word</span><span class="tc-desc">Convert to editable Word</span></div></button>
                <button class="tool-card" data-tool="pdf-to-pptx"><span class="tc-icon">📊</span><div class="tc-text"><span class="tc-name">PDF to PowerPoint</span><span class="tc-desc">Convert to editable PPT</span></div></button>
                <button class="tool-card" data-tool="pdf-to-excel"><span class="tc-icon">📈</span><div class="tc-text"><span class="tc-name">PDF to Excel</span><span class="tc-desc">Convert to spreadsheet</span></div></button>
                <button class="tool-card" data-tool="pdf-to-pdfa"><span class="tc-icon">🏛️</span><div class="tc-text"><span class="tc-name">PDF to PDF/A</span><span class="tc-desc">Convert for archiving</span></div></button>
            </div>

            <!-- Edit PDF Category -->
            <div class="tool-grid active" id="grid-edit">
                <button class="tool-card" data-tool="edit-pdf"><span class="tc-icon">✏️</span><div class="tc-text"><span class="tc-name">Edit PDF</span><span class="tc-desc">Add text, images, shapes</span></div></button>
                <button class="tool-card" data-tool="decolor"><span class="tc-icon">⚪</span><div class="tc-text"><span class="tc-name">Remove Background</span><span class="tc-desc">Make backgrounds white</span></div></button>
                <button class="tool-card" data-tool="page-numbers"><span class="tc-icon">123</span><div class="tc-text"><span class="tc-name">Page Numbers</span><span class="tc-desc">Add page numbers</span></div></button>
                <button class="tool-card" data-tool="watermark"><span class="tc-icon">©️</span><div class="tc-text"><span class="tc-name">Add Watermark</span><span class="tc-desc">Apply text watermark</span></div></button>
                <button class="tool-card" data-tool="rotate"><span class="tc-icon">🔁</span><div class="tc-text"><span class="tc-name">Rotate PDF</span><span class="tc-desc">Rotate pages easily</span></div></button>
            </div>

            <!-- PDF Security Category -->
            <div class="tool-grid active" id="grid-security">
                <button class="tool-card" data-tool="unlock"><span class="tc-icon">🔓</span><div class="tc-text"><span class="tc-name">Unlock PDF</span><span class="tc-desc">Remove passwords</span></div></button>
                <button class="tool-card" data-tool="protect"><span class="tc-icon">🔒</span><div class="tc-text"><span class="tc-name">Protect PDF</span><span class="tc-desc">Add password encryption</span></div></button>
                <button class="tool-card" data-tool="sign"><span class="tc-icon">✍️</span><div class="tc-text"><span class="tc-name">Sign PDF</span><span class="tc-desc">Add your signature</span></div></button>
                <button class="tool-card" data-tool="redact"><span class="tc-icon">⬛</span><div class="tc-text"><span class="tc-name">Redact PDF</span><span class="tc-desc">Permanent blackout</span></div></button>
            </div>
            
            <!-- PDF Intelligence Category -->
            <div class="tool-grid active" id="grid-intelligence">
                <button class="tool-card" data-tool="ocr"><span class="tc-icon">👁️</span><div class="tc-text"><span class="tc-name">OCR PDF</span><span class="tc-desc">Make text searchable</span></div></button>
                <button class="tool-card" data-tool="compare"><span class="tc-icon">⚖️</span><div class="tc-text"><span class="tc-name">Compare PDF</span><span class="tc-desc">Find document differences</span></div></button>
                <button class="tool-card" data-tool="summarize"><span class="tc-icon">🧠</span><div class="tc-text"><span class="tc-name">AI Summarizer</span><span class="tc-desc">Extract key points</span></div></button>
                <button class="tool-card" data-tool="translate"><span class="tc-icon">🌍</span><div class="tc-text"><span class="tc-name">Translate PDF</span><span class="tc-desc">Translate document language</span></div></button>
            </div>
            
        </div>
        
"""

start_pos = html.find(start_marker)
end_pos = html.find(end_marker)
new_html_content = html[:start_pos] + new_html + html[end_pos:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html_content)

print("Updated index.html")
