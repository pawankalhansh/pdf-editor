import sys
with open('static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find("  'edit-text': {")
end_idx = content.find("  'watermark': {")

new_block = """  'edit-pdf': {
    title: '✏️ Edit PDF (Canvas)',
    desc: 'Unified workspace: Add text and images anywhere on the page.',
    accept: '.pdf', multi: false,
    options: `
      <div id="canvasEditorBox" style="display:none; position:relative; width:100%; margin: 20px auto; background:#EFEFEF; text-align:center; padding: 20px; border-radius:var(--r-md); border:1px solid var(--border);">
        <div style="display:flex; justify-content:center; gap:10px; margin-bottom:15px;">
           <button class="btn-ghost" id="ceBtnText" style="background:#fff; border:1px solid var(--border); border-radius:4px; padding:6px 12px; cursor:pointer;">+ Add Text</button>
           <button class="btn-ghost" id="ceBtnImage" style="background:#fff; border:1px solid var(--border); border-radius:4px; padding:6px 12px; cursor:pointer;">+ Add Image</button>
           <input type="file" id="ceImageUpload" accept=".png,.jpg,.jpeg" style="display:none;">
        </div>
        <p style="margin-bottom:12px; font-weight:600; color:var(--text-secondary);">Page <span id="ce-page-num">1</span></p>
        <div style="position:relative; display:inline-block; box-shadow:0 2px 8px rgba(0,0,0,0.1); overflow:hidden;" id="ceCanvasArea">
          <img id="cePreviewImg" style="display:block; max-width:100%; height:auto; pointer-events:none; user-select:none;">
          <div id="ceOverlays" style="position:absolute; inset:0; pointer-events:none; text-align:left; overflow:hidden;"></div>
        </div>
        <div class="form-row" style="margin-top:20px; justify-content:center; align-items:flex-end;">
          <div class="form-group" style="margin-bottom:0;"><label>Page (1-based)</label><input type="number" id="opt-page" value="1" min="1" style="max-width:100px;"></div>
          <button class="btn-ghost" id="ceBtnLoadPage" style="border:1px solid var(--border); padding:8px 16px; border-radius:var(--r-sm); background:#fff; cursor:pointer;">Go to Page</button>
        </div>
      </div>
    `,
    onFileLoad: (f) => {
      let elements = []; 
      let currentScaleX = 1, currentScaleY = 1;
      let pdfW = 595.28, pdfH = 841.89; 
      
      const box = $('#canvasEditorBox');
      const img = $('#cePreviewImg');
      const overlays = $('#ceOverlays');
      
      let activeEl = null;
      let startX, startY, initialLeft, initialTop;
      
      document.onmousemove = (e) => {
          if (!activeEl) return;
          let newLeft = initialLeft + (e.clientX - startX);
          let newTop = initialTop + (e.clientY - startY);
          activeEl.style.left = newLeft + 'px';
          activeEl.style.top = newTop + 'px';
          activeEl._data.x = newLeft / currentScaleX;
          activeEl._data.y = newTop / currentScaleY;
      };
      
      document.onmouseup = () => {
          if (activeEl) {
              activeEl.style.cursor = activeEl._data.type === 'text' ? 'text' : 'grab';
              activeEl = null;
          }
      };

      const renderElements = (pageNum) => {
          overlays.innerHTML = '';
          elements.filter(el => el.page_num === pageNum - 1).forEach(el => {
              const div = document.createElement('div');
              div._data = el;
              div.style.position = 'absolute';
              div.style.left = (el.x * currentScaleX) + 'px';
              div.style.top = (el.y * currentScaleY) + 'px';
              div.style.pointerEvents = 'auto';
              
              if (el.type === 'text') {
                  div.contentEditable = true;
                  div.innerText = el.text;
                  div.style.fontSize = (el.fontSize * currentScaleY) + 'px';
                  div.style.color = el.color;
                  div.style.border = '1px dashed #999';
                  div.style.minWidth = '50px';
                  div.style.cursor = 'text';
                  div.style.fontFamily = 'sans-serif';
                  div.style.whiteSpace = 'nowrap';
                  div.style.padding = '2px';
                  div.style.background = 'rgba(255,255,255,0.5)';
                  
                  div.onfocus = () => div.style.border = '1px dashed var(--accent)';
                  div.onblur = () => div.style.border = '1px dashed #999';
                  div.oninput = () => { el.text = div.innerText; };
                  
                  div.onmousedown = (e) => {
                      if (document.activeElement !== div) {
                          activeEl = div;
                          startX = e.clientX;
                          startY = e.clientY;
                          initialLeft = parseFloat(div.style.left || 0);
                          initialTop = parseFloat(div.style.top || 0);
                          div.style.cursor = 'grabbing';
                      }
                  };
              } else if (el.type === 'image') {
                  div.style.width = (el.width * currentScaleX) + 'px';
                  div.style.height = (el.height * currentScaleY) + 'px';
                  div.style.backgroundImage = 'url(' + el.preview_url + ')';
                  div.style.backgroundSize = 'contain';
                  div.style.backgroundRepeat = 'no-repeat';
                  div.style.cursor = 'grab';
                  
                  div.onmousedown = (e) => {
                      activeEl = div;
                      startX = e.clientX;
                      startY = e.clientY;
                      initialLeft = parseFloat(div.style.left || 0);
                      initialTop = parseFloat(div.style.top || 0);
                      div.style.cursor = 'grabbing';
                      e.preventDefault();
                  };
              }
              
              div.ondblclick = () => {
                  if(confirm('Delete this element?')) {
                      elements = elements.filter(e => e !== el);
                      div.remove();
                      f[0]._canvasElements = elements;
                  }
              };
              
              overlays.appendChild(div);
          });
      };
      
      const loadPage = async (pageNum) => {
          $('#ce-page-num').textContent = pageNum;
          img.src = '/api/preview/' + encodeURIComponent(f[0].path) + '?page=' + (pageNum-1) + '&t=' + Date.now();
          img.onload = () => {
             if (f[0].page_sizes && f[0].page_sizes.length) {
                let sz = f[0].page_sizes[pageNum-1] || f[0].page_sizes[0];
                pdfW = sz.width_in * 72;
                pdfH = sz.height_in * 72;
             }
             const iRect = img.getBoundingClientRect();
             currentScaleX = iRect.width / pdfW;
             currentScaleY = iRect.height / pdfH;
             renderElements(pageNum);
          };
      };
      
      box.style.display = 'block';
      loadPage(1);
      
      $('#ceBtnLoadPage').onclick = (e) => { e.preventDefault(); loadPage(+$('#opt-page').value); };
      
      $('#ceBtnText').onclick = (e) => {
          e.preventDefault();
          let p = +$('#opt-page').value;
          elements.push({
              type: 'text', text: 'New Text', page_num: p - 1,
              x: 100, y: 100, fontSize: 16, color: '#000000'
          });
          renderElements(p);
      };
      
      $('#ceBtnImage').onclick = (e) => { e.preventDefault(); $('#ceImageUpload').click(); };
      $('#ceImageUpload').onchange = async (e) => {
          const file = e.target.files[0];
          if(!file) return;
          const fd = new FormData();
          fd.append('file', file);
          const resp = await fetch('/api/upload', {method:'POST', body:fd});
          const data = await resp.json();
          let p = +$('#opt-page').value;
          elements.push({
              type: 'image', page_num: p - 1,
              x: 100, y: 100, width: 200, height: 200,
              image_filename: data.filename,
              preview_url: URL.createObjectURL(file)
          });
          renderElements(p);
      };
      
      f[0]._canvasElements = elements;
    },
    run: async (f) => {
      let elements = f[0]._canvasElements || [];
      if (elements.length === 0) return toast('No elements added','info');
      showProgress('Applying edits...');
      const resp = await fetch('/api/canvas-edit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path,elements:elements})});
      const r = await resp.json();
      if (!resp.ok) throw new Error(r.error);
      showResult([{name:r.output,path:r.output,size:r.size,icon:'✏️'}],{title:'✅ PDF Edited'});
    }
  },
"""

new_content = content[:start_idx] + new_block + content[end_idx:]
with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Done")
