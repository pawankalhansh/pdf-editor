import sys

with open('static/app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

tools_block = """
  'word-to-pdf': {
    title: '📝 Word to PDF',
    desc: 'Convert Word DOC/DOCX to PDF.',
    accept: '.doc,.docx', multi: false,
    run: async (f) => {
      showProgress('Converting Word to PDF...');
      const r = await fetch('/api/word-to-pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'📝'}], {title:'✅ Word Converted'});
    }
  },
  'excel-to-pdf': {
    title: '📈 Excel to PDF',
    desc: 'Convert Excel XLS/XLSX to PDF.',
    accept: '.xls,.xlsx', multi: false,
    run: async (f) => {
      showProgress('Converting Excel to PDF...');
      const r = await fetch('/api/excel-to-pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'📈'}], {title:'✅ Excel Converted'});
    }
  },
  'pptx-to-pdf': {
    title: '📊 PowerPoint to PDF',
    desc: 'Convert PowerPoint PPT/PPTX to PDF.',
    accept: '.ppt,.pptx', multi: false,
    run: async (f) => {
      showProgress('Converting PowerPoint to PDF...');
      const r = await fetch('/api/pptx-to-pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'📊'}], {title:'✅ PowerPoint Converted'});
    }
  },
  'html-to-pdf': {
    title: '🌐 HTML to PDF',
    desc: 'Convert webpage URL or HTML code to PDF.',
    accept: '', multi: false,
    options: `<div class="form-group"><label>Website URL or HTML Code</label><textarea id="opt-html" rows="3" placeholder="https://example.com or <h1>Hello</h1>"></textarea></div>`,
    run: async (f) => {
      let htmlContent = document.getElementById('opt-html').value;
      if (!htmlContent.trim()) throw new Error("Please enter a URL or HTML content.");
      showProgress('Rendering HTML to PDF...');
      const r = await fetch('/api/html-to-pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({html:htmlContent})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'🌐'}], {title:'✅ HTML Rendered'});
    }
  },
  'pdf-to-pdfa': {
    title: '🏛️ PDF to PDF/A',
    desc: 'Convert PDF to PDF/A format for long term archiving.',
    accept: '.pdf', multi: false,
    run: async (f) => {
      showProgress('Converting to PDF/A archive format...');
      const r = await fetch('/api/pdf-to-pdfa', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'🏛️'}], {title:'✅ PDF/A Generated'});
    }
  },
  'repair': {
    title: '🛠️ Repair PDF',
    desc: 'Fix corrupted or damaged PDF documents.',
    accept: '.pdf', multi: false,
    run: async (f) => {
      showProgress('Attempting to repair document structure...');
      const r = await fetch('/api/repair', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'🛠️'}], {title:'✅ PDF Repaired'});
    }
  },
  'scan': {
    title: '📱 Scan to PDF',
    desc: 'Use your webcam to capture a document and save as PDF.',
    accept: '', multi: false,
    options: `
      <div id="scanBox" style="text-align:center; padding:15px; border:2px dashed var(--border); border-radius:8px;">
         <video id="scanVideo" style="width:100%; max-width:400px; display:none;" autoplay playsinline></video>
         <canvas id="scanCanvas" style="display:none;"></canvas>
         <div id="scanPhotos" style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-top:10px;"></div>
         <button class="btn-primary" id="btnStartScan" style="margin-top:15px;">Start Camera</button>
         <button class="btn-primary" id="btnCapture" style="margin-top:15px; display:none;">📸 Capture Page</button>
      </div>
    `,
    onFileLoad: (f) => {
      let stream = null;
      let photos = [];
      document.getElementById('btnStartScan').onclick = async (e) => {
         e.preventDefault();
         try {
             stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}});
             document.getElementById('scanVideo').srcObject = stream;
             document.getElementById('scanVideo').style.display = 'block';
             document.getElementById('btnStartScan').style.display = 'none';
             document.getElementById('btnCapture').style.display = 'inline-block';
         } catch(err) {
             alert('Camera access denied or unavailable.');
         }
      };
      document.getElementById('btnCapture').onclick = (e) => {
         e.preventDefault();
         let video = document.getElementById('scanVideo');
         let canvas = document.getElementById('scanCanvas');
         canvas.width = video.videoWidth;
         canvas.height = video.videoHeight;
         canvas.getContext('2d').drawImage(video, 0, 0);
         let dataUrl = canvas.toDataURL('image/jpeg');
         photos.push(dataUrl);
         let img = document.createElement('img');
         img.src = dataUrl;
         img.style.height = '80px';
         img.style.border = '1px solid #ccc';
         document.getElementById('scanPhotos').appendChild(img);
         f[0] = { _scans: photos }; // fake file object
      };
    },
    run: async (f) => {
      let photos = (f[0] && f[0]._scans) ? f[0]._scans : [];
      if (photos.length === 0) throw new Error("Please capture at least one photo.");
      showProgress('Uploading and converting scans...');
      // Convert base64 to blobs
      const formData = new FormData();
      for(let i=0; i<photos.length; i++) {
          let res = await fetch(photos[i]);
          let blob = await res.blob();
          formData.append('file', blob, `scan_${i}.jpg`);
      }
      const rUp = await fetch('/api/upload', {method:'POST', body:formData});
      const dUp = await rUp.json();
      if (!rUp.ok) throw new Error(dUp.error);
      
      let filenames = dUp.files.map(x => x.path);
      const rConv = await fetch('/api/images-to-pdf', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filenames:filenames})});
      const dConv = await rConv.json();
      if (!rConv.ok) throw new Error(dConv.error);
      showResult([{name:dConv.output,path:dConv.output,size:dConv.size,icon:'📱'}], {title:'✅ Scans Converted to PDF'});
    }
  },
  'redact': {
    title: '⬛ Redact PDF',
    desc: 'Permanently black out sensitive information.',
    accept: '.pdf', multi: false,
    options: `
      <div id="redactBox" style="text-align:center;">
         <p style="margin-bottom:10px;">Page <span id="rd-page-num">1</span></p>
         <div style="position:relative; display:inline-block; border:1px solid #ccc; cursor:crosshair;" id="rdArea">
            <img id="rdImg" style="display:block; max-width:100%; pointer-events:none;">
            <div id="rdOverlays" style="position:absolute; inset:0;"></div>
         </div>
         <div class="form-row" style="margin-top:15px; justify-content:center;">
            <div class="form-group"><label>Page</label><input type="number" id="rd-page" value="1" min="1" style="max-width:80px;"></div>
            <button class="btn-ghost" id="btnRdPage">Go</button>
         </div>
      </div>
    `,
    onFileLoad: (f) => {
      let rects = [];
      let currentScaleX = 1, currentScaleY = 1;
      let pdfW = 595, pdfH = 842;
      
      const loadPage = (pageNum) => {
          document.getElementById('rd-page-num').textContent = pageNum;
          let img = document.getElementById('rdImg');
          img.src = '/api/preview/' + encodeURIComponent(f[0].path) + '?page=' + (pageNum-1) + '&t=' + Date.now();
          img.onload = () => {
              if (f[0].page_sizes && f[0].page_sizes.length) {
                  let sz = f[0].page_sizes[pageNum-1] || f[0].page_sizes[0];
                  pdfW = sz.width_in * 72; pdfH = sz.height_in * 72;
              }
              const iRect = img.getBoundingClientRect();
              currentScaleX = iRect.width / pdfW;
              currentScaleY = iRect.height / pdfH;
              renderRects(pageNum);
          };
      };
      
      const renderRects = (pageNum) => {
          let overlays = document.getElementById('rdOverlays');
          overlays.innerHTML = '';
          rects.filter(r => r.page_num === pageNum - 1).forEach(r => {
             let div = document.createElement('div');
             div.style.position = 'absolute';
             div.style.left = (r.x * currentScaleX) + 'px';
             div.style.top = (r.y * currentScaleY) + 'px';
             div.style.width = (r.w * currentScaleX) + 'px';
             div.style.height = (r.h * currentScaleY) + 'px';
             div.style.backgroundColor = 'black';
             div.style.opacity = '0.8';
             div.ondblclick = () => {
                 rects = rects.filter(x => x !== r);
                 renderRects(pageNum);
             };
             overlays.appendChild(div);
          });
      };
      
      loadPage(1);
      document.getElementById('btnRdPage').onclick = (e) => { e.preventDefault(); loadPage(+document.getElementById('rd-page').value); };
      
      let area = document.getElementById('rdArea');
      let isDrawing = false;
      let startX = 0, startY = 0;
      let drawDiv = null;
      
      area.onmousedown = (e) => {
          if (e.target !== area && e.target !== document.getElementById('rdOverlays')) return;
          isDrawing = true;
          let rect = area.getBoundingClientRect();
          startX = e.clientX - rect.left;
          startY = e.clientY - rect.top;
          drawDiv = document.createElement('div');
          drawDiv.style.position = 'absolute';
          drawDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
          drawDiv.style.left = startX + 'px';
          drawDiv.style.top = startY + 'px';
          document.getElementById('rdOverlays').appendChild(drawDiv);
      };
      area.onmousemove = (e) => {
          if(!isDrawing) return;
          let rect = area.getBoundingClientRect();
          let currentX = e.clientX - rect.left;
          let currentY = e.clientY - rect.top;
          drawDiv.style.width = Math.abs(currentX - startX) + 'px';
          drawDiv.style.height = Math.abs(currentY - startY) + 'px';
          drawDiv.style.left = Math.min(startX, currentX) + 'px';
          drawDiv.style.top = Math.min(startY, currentY) + 'px';
      };
      area.onmouseup = () => {
          if(!isDrawing) return;
          isDrawing = false;
          let p = +document.getElementById('rd-page').value;
          rects.push({
              page_num: p - 1,
              x: parseFloat(drawDiv.style.left) / currentScaleX,
              y: parseFloat(drawDiv.style.top) / currentScaleY,
              w: parseFloat(drawDiv.style.width) / currentScaleX,
              h: parseFloat(drawDiv.style.height) / currentScaleY
          });
          drawDiv.remove();
          renderRects(p);
      };
      f[0]._rects = rects;
    },
    run: async (f) => {
      let rects = f[0]._rects || [];
      if (rects.length === 0) return toast('Draw some boxes to redact first.','info');
      showProgress('Applying redactions...');
      const r = await fetch('/api/redact', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path, rects:rects})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      showResult([{name:data.output,path:data.output,size:data.size,icon:'⬛'}], {title:'✅ PDF Redacted'});
    }
  },
  'summarize': {
    title: '🧠 AI Summarizer',
    desc: 'Extract key points from long PDFs.',
    accept: '.pdf', multi: false,
    run: async (f) => {
      showProgress('Analyzing and summarizing document...');
      const r = await fetch('/api/summarize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      let resDiv = document.getElementById('result-files');
      resDiv.innerHTML = `<div style="text-align:left; background:#fff; padding:20px; border-radius:8px; border:1px solid #ddd;"><h4 style="margin-top:0;">Summary</h4><p style="white-space:pre-wrap; line-height:1.6;">${data.summary}</p></div>`;
      showResult([], {title:'✅ Document Summarized'});
    }
  },
  'translate': {
    title: '🌍 Translate PDF',
    desc: 'Translate document text to another language.',
    accept: '.pdf', multi: false,
    options: `
       <div class="form-group">
          <label>Target Language</label>
          <select id="opt-lang">
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="zh-CN">Chinese (Simplified)</option>
              <option value="ja">Japanese</option>
              <option value="hi">Hindi</option>
          </select>
       </div>
    `,
    run: async (f) => {
      let lang = document.getElementById('opt-lang').value;
      showProgress('Translating document...');
      const r = await fetch('/api/translate', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path, lang:lang})});
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      let resDiv = document.getElementById('result-files');
      resDiv.innerHTML = `<div style="text-align:left; background:#fff; padding:20px; border-radius:8px; border:1px solid #ddd; max-height:400px; overflow-y:auto;"><h4 style="margin-top:0;">Translation</h4><p style="white-space:pre-wrap; line-height:1.6;">${data.translated}</p></div>`;
      showResult([], {title:'✅ Document Translated'});
    }
  },
"""

idx = js_content.find("const TOOLS = {") + len("const TOOLS = {")
new_js = js_content[:idx] + tools_block + js_content[idx:]

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(new_js)

print("Updated app.js")
