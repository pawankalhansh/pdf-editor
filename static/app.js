// ===== PDF Editor Pro — Full Frontend Application =====
(() => {
'use strict';

const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);
const fmtSize = b => b < 1024 ? b+' B' : b < 1048576 ? (b/1024).toFixed(1)+' KB' : (b/1048576).toFixed(1)+' MB';

// ===== STATE =====
const state = { files: {}, currentTool: null };

// ===== TOAST =====
function toast(msg, type='info') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  $('#toastContainer').appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ===== PROGRESS =====
function showProgress(title='Processing...', desc='This may take a moment') {
  $('#progressTitle').textContent = title;
  $('#progressDesc').textContent = desc;
  $('#progressOverlay').style.display = 'flex';
}
function hideProgress() { $('#progressOverlay').style.display = 'none'; }

// ===== RESULT =====
function showResult(files, opts={}) {
  const area = $('#resultArea');
  const body = $('#resultBody');
  $('#resultTitle').textContent = opts.title || '✅ Done';
  body.innerHTML = '';
  
  if (opts.html) {
      body.innerHTML += opts.html;
  }
  
  if (opts.stats) {
    let h = '<div class="result-stats">';
    opts.stats.forEach(s => h += `<div class="result-stat"><span class="rs-label">${s.label}</span><span class="rs-val${s.green?' green':''}">${s.value}</span></div>`);
    h += '</div>';
    body.innerHTML += h;
  }
  files.forEach(f => {
    body.innerHTML += `<div class="result-file"><span class="rf-icon">${f.icon||'📄'}</span><div class="rf-info"><h4>${f.name}</h4><p>${fmtSize(f.size)}</p></div><a class="btn-download" href="/api/download/${encodeURIComponent(f.path)}" download>⬇ Download</a></div>`;
  });
  
  const btnDownloadAll = $('#btnDownloadAll');
  if (btnDownloadAll) {
      btnDownloadAll.style.display = files.length > 0 ? 'inline-block' : 'none';
  }
  
  area.style.display = 'block';
  area.scrollIntoView({behavior:'smooth',block:'nearest'});
}
$('#resultClose')?.addEventListener('click', () => $('#resultArea').style.display = 'none');

$('#splitBackBtn')?.addEventListener('click', () => {
    $('#splitWorkspace').style.display = 'none';
    $('#mainGrid').style.display = 'flex';
    $('#categoryBar').style.display = 'flex';
    $('#splitIframe').src = ''; // Clear iframe memory
});

// ===== UPLOAD HELPER =====
async function uploadFiles(files) {
  const fd = new FormData();
  for (const f of files) fd.append('file', f);
  const r = await fetch('/api/upload', {method:'POST',body:fd});
  if (!r.ok) { const e = await r.json(); throw new Error(e.error||'Upload failed'); }
  return (await r.json()).files;
}

// ===== CATEGORY TABS =====
$$('.cat-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    $$('.cat-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const cat = tab.dataset.cat;
    $$('.tool-card').forEach(card => {
       if (cat === 'all' || card.dataset.category === cat) {
           card.style.display = 'flex';
       } else {
           card.style.display = 'none';
       }
    });
  });
});

// ===== TOOL CARDS → OPEN WORKSPACE =====
$$('.tool-card').forEach(card => {
  card.addEventListener('click', () => openTool(card.dataset.tool));
});

const showHome = (e) => {
  if (e) e.preventDefault();
  $('#homeView').style.display = 'block';
  $('#toolsView').style.display = 'none';
  $('#workspace').style.display = 'none';
  state.currentTool = null;
  $$('.nav-link').forEach(n => n.classList.remove('active'));
  $('#navHome')?.classList.add('active');
};

const showTools = (e) => {
  if (e) e.preventDefault();
  $('#homeView').style.display = 'none';
  $('#toolsView').style.display = 'block';
  $('#workspace').style.display = 'none';
  state.currentTool = null;
  $$('.nav-link').forEach(n => n.classList.remove('active'));
  $('#navTools')?.classList.add('active');
};

$('#backBtn').addEventListener('click', showTools);
$('#navHome')?.addEventListener('click', showHome);
$('#navTools')?.addEventListener('click', showTools);
$('#btnExploreTools')?.addEventListener('click', showTools);

// Init
showHome();

// ===== TOOL DEFINITIONS =====
const TOOLS = {
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
      try {
          const r = await fetch('/api/summarize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
          const data = await r.json();
          if (!r.ok) throw new Error(data.error);
          
          $('#progressOverlay').style.display = 'none';
          $('#workspace').style.display = 'none';
          $('#splitWorkspace').style.display = 'block';
          $('#splitIframe').src = '/api/view/' + encodeURIComponent(f[0].path);
          $('#splitTitle').textContent = 'AI Summarize';
          
          const lines = data.summary.split('\n').filter(l=>l.trim());
          let ul = '<ul style="padding-left:20px; margin-top:15px; color:var(--text-secondary);">';
          lines.forEach(l => {
              let text = l.startsWith('- ') ? l.substring(2) : l;
              if (text.length > 0) ul += `<li style="margin-bottom:12px;">${text}</li>`;
          });
          ul += '</ul>';
          
          $('#splitContent').innerHTML = `
            <div style="margin-bottom:20px;">
                <h4 style="margin:0 0 5px 0; color:var(--text); font-size:1.5rem; font-weight:700;">${f[0].name.replace('.pdf','')}</h4>
                ${ul}
            </div>
          `;
      } catch (e) {
          $('#progressOverlay').style.display = 'none';
          showToast('Error: ' + e.message, 'error');
      }
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
      const html = `<div style="text-align:left; background:#fff; padding:20px; border-radius:8px; border:1px solid #ddd; max-height:400px; overflow-y:auto;"><h4 style="margin-top:0;">Translation</h4><p style="white-space:pre-wrap; line-height:1.6;">${data.translated}</p></div>`;
      showResult([], {title:'✅ Document Translated', html: html});
    }
  },

  // ---- EDIT ----

  'edit-pdf': {
    title: '✏️ Edit PDF',
    desc: 'Add text and images anywhere on your PDF pages.',
    accept: '.pdf', multi: false,
    options: `
      <div id="canvasEditorBox" style="display:none; margin:-40px; margin-top:20px;">
        <!-- 3-column iLovePDF-style layout -->
        <div style="display:flex; height:75vh; border:1px solid var(--border); border-radius:8px; overflow:hidden; background:#2c2c2c;">
          
          <!-- LEFT: Page Thumbnails Sidebar -->
          <div id="cePageSidebar" style="width:100px; background:#1a1a2e; border-right:1px solid #333; overflow-y:auto; padding:10px 8px; flex-shrink:0;"></div>
          
          <!-- CENTER: PDF Preview -->
          <div style="flex:1; display:flex; flex-direction:column; background:#525252; position:relative;">
            <!-- Toolbar -->
            <div style="display:flex; justify-content:center; gap:8px; padding:8px; background:#3a3a3a; border-bottom:1px solid #555;">
              <button class="ce-tool-btn" id="ceBtnText" title="Add Text">T₊ Add Text</button>
              <button class="ce-tool-btn" id="ceBtnImage" title="Add Image">🖼 Add Image</button>
              <input type="file" id="ceImageUpload" accept=".png,.jpg,.jpeg" style="display:none;">
            </div>
            <!-- Page preview area -->
            <div style="flex:1; overflow:auto; display:flex; align-items:center; justify-content:center; padding:20px;">
              <div style="position:relative; display:inline-block; box-shadow:0 4px 20px rgba(0,0,0,0.4);" id="ceCanvasArea">
                <img id="cePreviewImg" style="display:block; max-width:100%; max-height:60vh; height:auto; pointer-events:none; user-select:none; background:#fff;">
                <div id="ceOverlays" style="position:absolute; inset:0; pointer-events:none; text-align:left; overflow:hidden;"></div>
              </div>
            </div>
            <!-- Bottom nav bar -->
            <div style="display:flex; align-items:center; justify-content:center; gap:12px; padding:8px 16px; background:#333; border-top:1px solid #555;">
              <button class="ce-nav-btn" id="cePrevPage">‹</button>
              <input type="number" id="cePageInput" value="1" min="1" style="width:45px; text-align:center; padding:4px; border-radius:4px; border:1px solid #555; background:#444; color:#fff; font-size:0.9rem;">
              <span style="color:#aaa; font-size:0.85rem;">/ <span id="ceTotalPages">1</span></span>
              <button class="ce-nav-btn" id="ceNextPage">›</button>
              <span style="color:#666; margin:0 5px;">|</span>
              <span id="ceZoomLevel" style="color:#ccc; font-size:0.85rem;">100%</span>
            </div>
          </div>
          
          <!-- RIGHT: Text Styles Panel -->
          <div id="ceStylePanel" style="width:220px; background:#fff; border-left:1px solid var(--border); padding:20px; flex-shrink:0; overflow-y:auto;">
            <h4 style="margin:0 0 16px; font-size:1rem; font-weight:700; color:var(--text-primary);">Text Styles</h4>
            <div style="display:flex; gap:8px; margin-bottom:12px;">
              <select id="ceFontFamily" style="flex:1; padding:6px; font-size:0.85rem; border:1px solid #ccc; border-radius:4px;">
                <option value="Helvetica">Helvetica</option>
                <option value="Times-Roman">Times</option>
                <option value="Courier">Courier</option>
              </select>
              <input type="number" id="ceFontSize" value="16" min="6" max="120" style="width:50px; padding:6px; border:1px solid #ccc; border-radius:4px; font-size:0.85rem;">
            </div>
            <div style="display:flex; gap:4px; margin-bottom:16px;">
              <button class="ce-style-btn" id="ceBold" title="Bold"><b>B</b></button>
              <button class="ce-style-btn" id="ceItalic" title="Italic"><i>I</i></button>
              <button class="ce-style-btn" id="ceUnderline" title="Underline"><u>U</u></button>
              <span style="width:1px; background:#ddd; margin:0 4px;"></span>
              <button class="ce-style-btn active" id="ceAlignLeft" title="Left">≡</button>
              <button class="ce-style-btn" id="ceAlignCenter" title="Center">☰</button>
              <button class="ce-style-btn" id="ceAlignRight" title="Right">≡</button>
            </div>
            <h4 style="margin:0 0 10px; font-size:0.9rem; font-weight:600;">Current Color</h4>
            <div style="display:flex; gap:8px; margin-bottom:16px; align-items:center;">
              <input type="color" id="ceColor" value="#000000" style="width:32px; height:32px; border:none; cursor:pointer; border-radius:4px;">
              <span style="width:28px; height:28px; border-radius:50%; background:#000; border:2px solid #ddd; cursor:pointer;" id="ceColorBlack"></span>
              <span style="width:28px; height:28px; border-radius:50%; background:#fff; border:2px solid #ddd; cursor:pointer;" id="ceColorWhite"></span>
            </div>
            
            <div style="border-top:1px solid #eee; padding-top:16px; margin-top:auto;">
              <button class="btn-primary" id="runBtn" style="width:100%; margin-top:0; border-radius:8px; background:#E74C3C; padding:14px; font-size:1rem;">Save changes ➜</button>
            </div>
          </div>
        </div>
      </div>
    `,
    onFileLoad: (f) => {
      let elements = []; 
      let currentScaleX = 1, currentScaleY = 1;
      let pdfW = 595.28, pdfH = 841.89;
      let currentPage = 1;
      let totalPages = f[0].pages || 1;
      let selectedEl = null;
      
      const box = $('#canvasEditorBox');
      const img = $('#cePreviewImg');
      const overlays = $('#ceOverlays');
      const sidebar = $('#cePageSidebar');
      
      // Style for selected element
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
      
      // Update selected element's styles from panel
      const updateSelectedStyle = () => {
          if (!selectedEl) return;
          const el = selectedEl._data;
          el.fontSize = +$('#ceFontSize').value;
          el.color = $('#ceColor').value;
          selectedEl.style.fontSize = (el.fontSize * currentScaleY) + 'px';
          selectedEl.style.color = el.color;
      };
      
      // Wire style panel events
      $('#ceFontSize')?.addEventListener('change', updateSelectedStyle);
      $('#ceColor')?.addEventListener('input', updateSelectedStyle);
      $('#ceColorBlack')?.addEventListener('click', () => { $('#ceColor').value = '#000000'; updateSelectedStyle(); });
      $('#ceColorWhite')?.addEventListener('click', () => { $('#ceColor').value = '#ffffff'; updateSelectedStyle(); });
      $('#ceBold')?.addEventListener('click', () => { if(selectedEl) document.execCommand('bold'); });
      $('#ceItalic')?.addEventListener('click', () => { if(selectedEl) document.execCommand('italic'); });
      $('#ceUnderline')?.addEventListener('click', () => { if(selectedEl) document.execCommand('underline'); });

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
                  div.style.border = '1px solid transparent';
                  div.style.minWidth = '50px';
                  div.style.cursor = 'text';
                  div.style.fontFamily = 'sans-serif';
                  div.style.whiteSpace = 'nowrap';
                  div.style.padding = '2px 4px';
                  div.style.borderRadius = '2px';
                  div.style.outline = 'none';
                  
                  div.onfocus = () => {
                      div.style.border = '2px solid #1473E6';
                      div.style.boxShadow = '0 0 0 3px rgba(20,115,230,0.2)';
                      selectedEl = div;
                      $('#ceFontSize').value = el.fontSize;
                      $('#ceColor').value = el.color;
                  };
                  div.onblur = () => {
                      div.style.border = '1px solid transparent';
                      div.style.boxShadow = 'none';
                  };
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
                  div.style.border = '1px solid transparent';
                  
                  div.onfocus = () => div.style.border = '2px solid #1473E6';
                  div.onblur = () => div.style.border = '1px solid transparent';
                  
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
      
      // Build page thumbnails in sidebar
      const buildThumbnails = () => {
          sidebar.innerHTML = '';
          for (let i = 1; i <= totalPages; i++) {
              const thumb = document.createElement('div');
              thumb.style.cssText = 'margin-bottom:10px; cursor:pointer; border:2px solid transparent; border-radius:4px; overflow:hidden; transition:border-color 0.2s;';
              if (i === currentPage) thumb.style.borderColor = '#1473E6';
              thumb.innerHTML = `<img src="/api/preview/${encodeURIComponent(f[0].path)}?page=${i-1}" style="width:100%; display:block; background:#fff;"><div style="text-align:center; font-size:0.7rem; color:#aaa; padding:4px 0;">${i}</div>`;
              thumb.onclick = () => { currentPage = i; loadPage(i); };
              sidebar.appendChild(thumb);
          }
      };
      
      const loadPage = async (pageNum) => {
          currentPage = pageNum;
          $('#cePageInput').value = pageNum;
          img.src = '/api/preview/' + encodeURIComponent(f[0].path) + '?page=' + (pageNum-1) + '&t=' + Date.now();
          img.onload = async () => {
             if (f[0].page_sizes && f[0].page_sizes.length) {
                let sz = f[0].page_sizes[pageNum-1] || f[0].page_sizes[0];
                pdfW = sz.width_in * 72;
                pdfH = sz.height_in * 72;
             }
             const iRect = img.getBoundingClientRect();
             currentScaleX = iRect.width / pdfW;
             currentScaleY = iRect.height / pdfH;
             
             // Fetch existing text blocks from PDF for this page
             try {
                 const resp = await fetch('/api/extract-text-blocks', {
                     method: 'POST',
                     headers: {'Content-Type': 'application/json'},
                     body: JSON.stringify({filename: f[0].path, page: pageNum - 1})
                 });
                 const data = await resp.json();
                 if (data.blocks && data.blocks.length > 0) {
                     // Remove old existing-text blocks for this page from elements
                     elements = elements.filter(el => !(el._isExisting && el.page_num === pageNum - 1));
                     // Add extracted blocks as editable elements
                     data.blocks.forEach(block => {
                         elements.push({
                             type: 'text',
                             _isExisting: true,
                             text: block.text,
                             page_num: pageNum - 1,
                             x: block.x,
                             y: block.y,
                             fontSize: block.fontSize,
                             color: block.color,
                             font: block.font
                         });
                     });
                     f[0]._canvasElements = elements;
                 }
             } catch(e) { console.warn('Could not extract text blocks:', e); }
             
             renderElements(pageNum);
          };
          // Update sidebar selection
          sidebar.querySelectorAll('div').forEach((t, idx) => {
              if (t.querySelector('img')) {
                  t.style.borderColor = (Math.floor(idx) === pageNum - 1) ? '#1473E6' : 'transparent';
              }
          });
      };
      
      box.style.display = 'block';
      $('#ceTotalPages').textContent = totalPages;
      buildThumbnails();
      loadPage(1);
      
      // Page navigation
      $('#cePrevPage').onclick = (e) => { e.preventDefault(); if (currentPage > 1) loadPage(currentPage - 1); };
      $('#ceNextPage').onclick = (e) => { e.preventDefault(); if (currentPage < totalPages) loadPage(currentPage + 1); };
      $('#cePageInput').onchange = () => { let p = Math.max(1, Math.min(totalPages, +$('#cePageInput').value)); loadPage(p); };
      
      // Add text
      $('#ceBtnText').onclick = (e) => {
          e.preventDefault();
          elements.push({
              type: 'text', text: 'New Text', page_num: currentPage - 1,
              x: 100, y: 100, fontSize: +$('#ceFontSize').value, color: $('#ceColor').value
          });
          renderElements(currentPage);
      };
      
      // Add image
      $('#ceBtnImage').onclick = (e) => { e.preventDefault(); $('#ceImageUpload').click(); };
      $('#ceImageUpload').onchange = async (e) => {
          const file = e.target.files[0];
          if(!file) return;
          const fd = new FormData();
          fd.append('file', file);
          const resp = await fetch('/api/upload', {method:'POST', body:fd});
          const data = await resp.json();
          elements.push({
              type: 'image', page_num: currentPage - 1,
              x: 100, y: 100, width: 200, height: 200,
              image_filename: data.filename,
              preview_url: URL.createObjectURL(file)
          });
          renderElements(currentPage);
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
  'watermark': {
    title: '💧 Add Watermark',
    desc: 'Add a text watermark to every page of the PDF.',
    accept: '.pdf', multi: false,
    options: `
      <div class="form-row">
        <div class="form-group"><label>Watermark Text</label><input type="text" id="opt-wm-text" value="CONFIDENTIAL" placeholder="Watermark text"></div>
        <div class="form-group"><label>Font Size</label><input type="number" id="opt-wm-size" value="60" min="12" max="200"></div>
      </div>`,
    run: async (f) => {
      showProgress('Adding watermark...');
      const r = await api('/api/watermark',{filename:f[0].path,text:$('#opt-wm-text').value,font_size:+$('#opt-wm-size').value});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'💧'}],{title:'✅ Watermark Added'});
    }
  },
  'page-numbers': {
    title: '🔢 Add Page Numbers',
    desc: 'Insert page numbers on every page.',
    accept: '.pdf', multi: false,
    options: `
      <div class="form-row">
        <div class="form-group"><label>Position</label>
          <select id="opt-pn-pos"><option value="bottom-center">Bottom Center</option><option value="bottom-right">Bottom Right</option><option value="bottom-left">Bottom Left</option><option value="top-center">Top Center</option><option value="top-right">Top Right</option><option value="top-left">Top Left</option></select></div>
        <div class="form-group"><label>Start Number</label><input type="number" id="opt-pn-start" value="1" min="1"></div>
        <div class="form-group"><label>Font Size</label><input type="number" id="opt-pn-size" value="10" min="6" max="36"></div>
      </div>`,
    run: async (f) => {
      showProgress('Adding page numbers...');
      const r = await api('/api/add-page-numbers',{filename:f[0].path,position:$('#opt-pn-pos').value,start_num:+$('#opt-pn-start').value,font_size:+$('#opt-pn-size').value});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🔢'}],{title:'✅ Page Numbers Added'});
    }
  },
  'metadata': {
    title: 'ℹ️ Edit PDF Metadata',
    desc: 'View and edit title, author, subject, keywords.',
    accept: '.pdf', multi: false,
    options: `
      <div class="form-row"><div class="form-group"><label>Title</label><input type="text" id="opt-meta-title" placeholder="Document title"></div>
        <div class="form-group"><label>Author</label><input type="text" id="opt-meta-author" placeholder="Author name"></div></div>
      <div class="form-row"><div class="form-group"><label>Subject</label><input type="text" id="opt-meta-subject" placeholder="Subject"></div>
        <div class="form-group"><label>Keywords</label><input type="text" id="opt-meta-keywords" placeholder="keyword1, keyword2"></div></div>`,
    onFileLoad: async (f) => {
      try {
        const resp = await fetch('/api/metadata',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:f[0].path})});
        const data = await resp.json();
        if (data.metadata) {
          $('#opt-meta-title').value = data.metadata.title || '';
          $('#opt-meta-author').value = data.metadata.author || '';
          $('#opt-meta-subject').value = data.metadata.subject || '';
          $('#opt-meta-keywords').value = data.metadata.keywords || '';
        }
      } catch(e) {}
    },
    run: async (f) => {
      showProgress('Updating metadata...');
      const r = await api('/api/edit-metadata',{filename:f[0].path,title:$('#opt-meta-title').value,author:$('#opt-meta-author').value,subject:$('#opt-meta-subject').value,keywords:$('#opt-meta-keywords').value});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'ℹ️'}],{title:'✅ Metadata Updated'});
    }
  },
  // ---- PAGES ----
  'merge': {
    title: '📎 Merge PDFs',
    desc: 'Combine multiple PDF files into one.',
    accept: '.pdf', multi: true,
    options: '',
    run: async (f) => {
      if (f.length < 2) return toast('Need at least 2 PDFs','error');
      showProgress('Merging PDFs...',`Combining ${f.length} files`);
      const r = await api('/api/merge',{filenames:f.map(x=>x.path)});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'📎'}],{title:`✅ ${f.length} PDFs Merged`});
    }
  },
  'split': {
    title: '✂️ Split PDF',
    desc: 'Split a PDF into individual pages.',
    accept: '.pdf', multi: false,
    options: '',
    run: async (f) => {
      showProgress('Splitting...',`Extracting ${f[0].pages||'all'} pages`);
      const r = await api('/api/split',{filename:f[0].path});
      showResult(r.files.map(x=>({name:x.name,path:x.path,size:x.size,icon:'📄'})),{title:`✅ Split into ${r.files.length} Pages`});
    }
  },
  'rotate': {
    title: '🔁 Rotate PDF',
    desc: 'Rotate all pages by 90°, 180°, or 270°.',
    accept: '.pdf', multi: false,
    options: `
      <div id="rotatePreviewBox" style="display:none; text-align:center; margin-bottom:20px;">
          <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:10px;">Live Preview (First Page)</p>
          <div style="display:inline-block; padding:10px; max-width:100%; height:250px; border:1px solid var(--border); border-radius:var(--r-md); background:#f8f9fa;">
              <img id="rotatePreviewImg" style="max-height:100%; max-width:100%; object-fit:contain; transition:transform 0.4s cubic-bezier(0.4, 0, 0.2, 1); pointer-events:none; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));">
          </div>
      </div>
      <div class="form-group"><label>Angle</label><div class="pill-group" data-name="angle"><button class="pill active" data-val="90">90° CW</button><button class="pill" data-val="180">180°</button><button class="pill" data-val="270">270° CW</button></div></div>`,
    onFileLoad: (f) => {
        const box = $('#rotatePreviewBox');
        const img = $('#rotatePreviewImg');
        img.style.transform = 'rotate(90deg)';
        img.src = '/api/preview/' + encodeURIComponent(f[0].path);
        img.onload = () => box.style.display = 'block';
        
        $$('[data-name="angle"] .pill').forEach(btn => {
            btn.addEventListener('click', () => {
                img.style.transform = `rotate(${btn.dataset.val}deg)`;
            });
        });
    },
    run: async (f) => {
      const angle = $$('[data-name="angle"] .pill.active')[0]?.dataset.val || '90';
      showProgress(`Rotating ${angle}°...`);
      const r = await api('/api/rotate',{filename:f[0].path,angle:+angle});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🔁'}],{title:`✅ Rotated ${angle}°`});
    }
  },
  'crop': {
    title: '🖼️ Crop PDF',
    desc: 'Visually trim margins from all pages. Drag the edges of the box on the preview below.',
    accept: '.pdf', multi: false,
    options: `
      <div id="cropPreviewBox" style="display:none; position:relative; max-width:100%; margin: 20px auto; overflow:hidden; background:#fff; text-align:center;">
        <div style="position:relative; display:inline-block;">
          <img id="cropPreviewImg" style="display:block; max-width:100%; height:auto; pointer-events:none;">
          <div id="cropBox" style="position:absolute; left:10px; top:10px; right:10px; bottom:10px; border:2px dashed var(--accent); box-shadow:0 0 0 9999px rgba(0,0,0,0.5); cursor:move;">
             <div class="crop-handle" data-dir="nw" style="position:absolute; top:-5px; left:-5px; width:12px; height:12px; background:var(--accent); cursor:nwse-resize; border-radius:50%;"></div>
             <div class="crop-handle" data-dir="ne" style="position:absolute; top:-5px; right:-5px; width:12px; height:12px; background:var(--accent); cursor:nesw-resize; border-radius:50%;"></div>
             <div class="crop-handle" data-dir="sw" style="position:absolute; bottom:-5px; left:-5px; width:12px; height:12px; background:var(--accent); cursor:nesw-resize; border-radius:50%;"></div>
             <div class="crop-handle" data-dir="se" style="position:absolute; bottom:-5px; right:-5px; width:12px; height:12px; background:var(--accent); cursor:nwse-resize; border-radius:50%;"></div>
          </div>
        </div>
      </div>
      <div class="form-row" style="display:none;">
        <div class="form-group"><label>Left (pt)</label><input type="number" id="opt-crop-l" value="0" min="0"></div>
        <div class="form-group"><label>Top (pt)</label><input type="number" id="opt-crop-t" value="0" min="0"></div>
        <div class="form-group"><label>Right (pt)</label><input type="number" id="opt-crop-r" value="0" min="0"></div>
        <div class="form-group"><label>Bottom (pt)</label><input type="number" id="opt-crop-b" value="0" min="0"></div>
      </div>`,
    onFileLoad: (f) => {
      const box = $('#cropPreviewBox');
      const img = $('#cropPreviewImg');
      img.src = '/api/preview/' + encodeURIComponent(f[0].path);
      img.onload = () => {
         box.style.display = 'block';
         initCropBox(img, f[0]);
      };
    },
    run: async (f) => {
      showProgress('Cropping...');
      const r = await api('/api/crop',{filename:f[0].path,left:+$('#opt-crop-l').value,top:+$('#opt-crop-t').value,right:+$('#opt-crop-r').value,bottom:+$('#opt-crop-b').value});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🖼️'}],{title:'✅ PDF Cropped'});
    }
  },
  'delete-pages': {
    title: '🗑️ Delete Pages',
    desc: 'Remove specific pages. Enter page numbers (1-based, comma-separated).',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Pages to delete (e.g., 1,3,5)</label><input type="text" id="opt-del-pages" placeholder="1, 3, 5"></div>`,
    run: async (f) => {
      const pages = $('#opt-del-pages').value.split(',').map(s=>parseInt(s.trim())-1).filter(n=>!isNaN(n));
      if (!pages.length) return toast('Enter page numbers','error');
      showProgress('Deleting pages...');
      const r = await api('/api/delete-pages',{filename:f[0].path,pages});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🗑️'}],{title:`✅ ${pages.length} Page(s) Deleted`});
    }
  },
  'extract-pages': {
    title: '📑 Extract Pages',
    desc: 'Extract specific pages into a new PDF.',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Pages to extract (e.g., 1,2,5)</label><input type="text" id="opt-ext-pages" placeholder="1, 2, 5"></div>`,
    run: async (f) => {
      const pages = $('#opt-ext-pages').value.split(',').map(s=>parseInt(s.trim())-1).filter(n=>!isNaN(n));
      if (!pages.length) return toast('Enter page numbers','error');
      showProgress('Extracting pages...');
      const r = await api('/api/extract-pages',{filename:f[0].path,pages});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'📑'}],{title:`✅ ${pages.length} Page(s) Extracted`});
    }
  },
  'reorder': {
    title: '🔃 Reorder Pages',
    desc: 'Enter new page order (1-based, comma-separated).',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>New order (e.g., 3,1,2,4)</label><input type="text" id="opt-reorder" placeholder="3, 1, 2, 4"><span class="hint">List all pages in desired order</span></div>`,
    run: async (f) => {
      const order = $('#opt-reorder').value.split(',').map(s=>parseInt(s.trim())-1).filter(n=>!isNaN(n));
      if (!order.length) return toast('Enter page order','error');
      showProgress('Reordering...');
      const r = await api('/api/reorder',{filename:f[0].path,order});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🔃'}],{title:'✅ Pages Reordered'});
    }
  },
  'insert-pages': {
    title: '📥 Insert Pages from Another PDF',
    desc: 'Insert pages from a second PDF at a specific position.',
    accept: '.pdf', multi: false,
    extraUpload: {label:'PDF to insert',accept:'.pdf',id:'extra-insert'},
    options: `<div class="form-group"><label>Insert at position (page number, 1-based)</label><input type="number" id="opt-ins-pos" value="1" min="1"></div>`,
    run: async (f) => {
      const ins = state.files['extra-insert'];
      if (!ins?.length) return toast('Upload the PDF to insert','error');
      showProgress('Inserting pages...');
      const r = await api('/api/insert-pages',{base_filename:f[0].path,insert_filename:ins[0].path,position:+$('#opt-ins-pos').value-1});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'📥'}],{title:'✅ Pages Inserted'});
    }
  },
  // ---- CONVERT ----
  'compress': {
    title: '📦 Compress PDF',
    desc: 'Reduce file size by re-rendering at lower quality.',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Quality</label><span class="hint">Lower = smaller file</span><div class="slider-group"><input type="range" class="slider" id="opt-quality" min="10" max="95" value="75"><span class="slider-val" id="val-quality">75</span></div></div>`,
    run: async (f) => {
      showProgress('Compressing...',`Quality: ${$('#opt-quality').value}%`);
      const r = await api('/api/compress',{filename:f[0].path,quality:+$('#opt-quality').value});
      showResult([{name:r.output,path:r.output,size:r.new_size,icon:'📦'}],{title:'✅ Compressed',stats:[{label:'Original',value:fmtSize(r.original_size)},{label:'Compressed',value:fmtSize(r.new_size)},{label:'Reduction',value:r.reduction+'%',green:true}]});
    }
  },
  'pdf-to-img': {
    title: '🖼️ PDF → Images',
    desc: 'Convert each page to PNG or JPEG.',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Format</label><div class="pill-group" data-name="imgfmt"><button class="pill active" data-val="png">PNG</button><button class="pill" data-val="jpeg">JPEG</button></div></div>`,
    run: async (f) => {
      const fmt = $$('[data-name="imgfmt"] .pill.active')[0]?.dataset.val || 'png';
      showProgress('Converting...');
      const r = await api('/api/to-images',{filename:f[0].path,format:fmt,dpi:200});
      showResult(r.files.map(x=>({name:x.name,path:x.path,size:x.size,icon:'🖼️'})),{title:`✅ ${r.files.length} ${fmt.toUpperCase()} Images`});
    }
  },
  'img-to-pdf': {
    title: '📄 Images → PDF',
    desc: 'Combine images into a single PDF.',
    accept: '.png,.jpg,.jpeg,.bmp,.tiff,.gif', multi: true,
    options: '',
    run: async (f) => {
      if (!f.length) return toast('Upload images first','error');
      showProgress('Converting...');
      const r = await api('/api/images-to-pdf',{filenames:f.map(x=>x.path)});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'📄'}],{title:`✅ ${f.length} Images → PDF`});
    }
  },
  'pdf-to-word': {
    title: '📝 PDF → Word',
    desc: 'Export PDF text content as a .docx Word document.',
    accept: '.pdf', multi: false, options: '',
    run: async (f) => { showProgress('Converting to Word...'); const r = await api('/api/pdf-to-word',{filename:f[0].path}); showResult([{name:r.output,path:r.output,size:r.size,icon:'📝'}],{title:'✅ Word Document Created'}); }
  },
  'pdf-to-excel': {
    title: '📊 PDF → Excel',
    desc: 'Extract tables and text into .xlsx spreadsheet.',
    accept: '.pdf', multi: false, options: '',
    run: async (f) => { showProgress('Converting to Excel...'); const r = await api('/api/pdf-to-excel',{filename:f[0].path}); showResult([{name:r.output,path:r.output,size:r.size,icon:'📊'}],{title:'✅ Excel Spreadsheet Created'}); }
  },
  'pdf-to-pptx': {
    title: '🎯 PDF → PowerPoint',
    desc: 'Convert each page to a slide in .pptx presentation.',
    accept: '.pdf', multi: false, options: '',
    run: async (f) => { showProgress('Converting to PowerPoint...'); const r = await api('/api/pdf-to-pptx',{filename:f[0].path}); showResult([{name:r.output,path:r.output,size:r.size,icon:'🎯'}],{title:'✅ PowerPoint Created'}); }
  },
  'ocr': {
    title: '🔍 OCR — Scanned to Searchable',
    desc: 'Recognize text in scanned PDFs using Tesseract OCR.',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Language</label><select id="opt-ocr-lang"><option value="eng">English</option><option value="hin">Hindi</option><option value="fra">French</option><option value="deu">German</option><option value="spa">Spanish</option></select></div>`,
    run: async (f) => { showProgress('Running OCR...','This may take a while for large documents'); const r = await api('/api/ocr',{filename:f[0].path,lang:$('#opt-ocr-lang').value}); showResult([{name:r.output,path:r.output,size:r.size,icon:'🔍'}],{title:'✅ OCR Complete'}); }
  },
  // ---- SIGN & PROTECT ----
  'sign': {
    title: '✍️ Fill & Sign',
    desc: 'Draw your signature and stamp it on a PDF page.',
    accept: '.pdf', multi: false,
    options: `
      <div class="form-group"><label>Draw your signature below</label></div>
      <div class="sig-canvas-wrap"><canvas id="sigCanvas" width="500" height="160"></canvas></div>
      <div class="sig-actions"><button id="sigClear">Clear</button><button id="sigUndo">Undo</button></div>
      <div class="form-row">
        <div class="form-group"><label>Page (1-based)</label><input type="number" id="opt-sig-page" value="1" min="1"></div>
        <div class="form-group"><label>X</label><input type="number" id="opt-sig-x" value="350"></div>
        <div class="form-group"><label>Y</label><input type="number" id="opt-sig-y" value="700"></div>
        <div class="form-group"><label>Width</label><input type="number" id="opt-sig-w" value="150"></div>
      </div>`,
    onMount: () => initSignatureCanvas(),
    run: async (f) => {
      const canvas = $('#sigCanvas');
      if (!canvas) return toast('Signature canvas not found','error');
      // Get signature as blob
      const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
      if (!blob || blob.size < 500) return toast('Please draw a signature first','error');
      showProgress('Applying signature...');
      const fd = new FormData();
      fd.append('signature', blob, 'signature.png');
      fd.append('filename', f[0].path);
      fd.append('page_num', +$('#opt-sig-page').value - 1);
      fd.append('x', +$('#opt-sig-x').value);
      fd.append('y', +$('#opt-sig-y').value);
      fd.append('width', +$('#opt-sig-w').value);
      fd.append('height', Math.round(+$('#opt-sig-w').value * 0.5));
      const resp = await fetch('/api/sign', {method:'POST', body:fd});
      const r = await resp.json();
      if (!resp.ok) throw new Error(r.error);
      showResult([{name:r.output,path:r.output,size:r.size,icon:'✍️'}],{title:'✅ Signature Applied'});
    }
  },
  'protect': {
    title: '🔐 Password Protect PDF',
    desc: 'Encrypt your PDF with a password.',
    accept: '.pdf', multi: false,
    options: `
      <div class="form-row">
        <div class="form-group"><label>User Password (to open)</label><input type="password" id="opt-user-pw" placeholder="Password to open PDF"></div>
        <div class="form-group"><label>Owner Password (optional)</label><input type="password" id="opt-owner-pw" placeholder="Restrictions password"></div>
      </div>`,
    run: async (f) => {
      const pw = $('#opt-user-pw').value;
      if (!pw) return toast('Enter a password','error');
      showProgress('Encrypting...');
      const r = await api('/api/protect',{filename:f[0].path,user_password:pw,owner_password:$('#opt-owner-pw').value||pw});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🔐'}],{title:'✅ PDF Protected'});
    }
  },
  'unlock': {
    title: '🔓 Unlock PDF',
    desc: 'Remove password protection (requires current password).',
    accept: '.pdf', multi: false,
    options: `<div class="form-group"><label>Current Password</label><input type="password" id="opt-unlock-pw" placeholder="Enter the PDF password"></div>`,
    run: async (f) => {
      const pw = $('#opt-unlock-pw').value;
      if (!pw) return toast('Enter the password','error');
      showProgress('Unlocking...');
      const r = await api('/api/unlock',{filename:f[0].path,password:pw});
      showResult([{name:r.output,path:r.output,size:r.size,icon:'🔓'}],{title:'✅ PDF Unlocked'});
    }
  },
  // ---- TOOLS ----
  'compare': {
    title: '🔍 Compare PDFs',
    desc: 'Upload two PDFs and see side-by-side page comparison.',
    accept: '.pdf', multi: false,
    extraUpload: {label:'Second PDF to compare',accept:'.pdf',id:'extra-compare'},
    options: '',
    run: async (f) => {
      const f2 = state.files['extra-compare'];
      if (!f2?.length) return toast('Upload the second PDF','error');
      showProgress('Comparing...');
      const r = await api('/api/compare',{filename1:f[0].path,filename2:f2[0].path});
      showResult(r.files.map(x=>({name:x.name,path:x.path,size:x.size,icon:'🔍'})),{title:`✅ Compared — ${r.files.length} Page(s)`});
    }
  }
};

// ===== API CALL HELPER =====
async function api(url, body) {
  const r = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || 'Request failed');
  return d;
}

// ===== OPEN TOOL =====
// Tools with custom visual previews that should NOT get auto-thumbnails
const CUSTOM_PREVIEW_TOOLS = ['edit-pdf','redact','crop','summarize','scan','rotate','sign','metadata','insert-pages','compare'];

function openTool(toolId) {
  const tool = TOOLS[toolId];
  if (!tool) return;
  state.currentTool = toolId;
  state.files = {};

  // Hide grids, show workspace
  $('#homeView').style.display = 'none';
  $('#toolsView').style.display = 'none';
  $('#workspace').style.display = '';
  $('#resultArea').style.display = 'none';
  $('#splitWorkspace').style.display = 'none';

  const ws = $('#toolWorkspace');
  let html = `<div class="tw-header"><h2>${tool.title}</h2><p>${tool.desc}</p></div>`;

  // Upload zone
  html += `<div class="upload-zone" id="uz-main"><span class="uz-icon">📂</span><h3>Drop your file${tool.multi?'s':''} here</h3><p>or click to browse</p><input type="file" id="fi-main" accept="${tool.accept}" ${tool.multi?'multiple':''} hidden></div>`;
  
  // Thumbnail grid area (for multi-file or general thumbnails)
  html += `<div class="thumb-grid" id="tg-main" style="display:none;"></div>`;
  // Text fallback list
  html += `<div class="file-list" id="fl-main"></div>`;

  // Split workspace container (hidden until file uploaded for single-file PDF tools)
  html += `<div id="ws-split-container" style="display:none;"></div>`;

  // Extra upload (for tools that need a second file)
  if (tool.extraUpload) {
    html += `<div class="form-section" id="extra-upload-section"><div class="form-group"><label>${tool.extraUpload.label}</label></div><div class="upload-zone" id="uz-extra" style="padding:24px"><span class="uz-icon">📂</span><h3>Drop file here</h3><input type="file" id="fi-extra" accept="${tool.extraUpload.accept}" hidden></div><div class="file-list" id="fl-extra"></div></div>`;
  }

  // Options - only add Run button if tool options don't already include one
  const hasRunBtn = (tool.options || '').includes('id="runBtn"');
  html += `<div class="form-section" id="opts-section">${tool.options || ''}${hasRunBtn ? '' : '<button class="btn-primary" id="runBtn">▶ Run</button>'}</div>`;

  ws.innerHTML = html;

  // Wire upload zone
  wireUpload('uz-main','fi-main','fl-main','main',tool);
  if (tool.extraUpload) wireUpload('uz-extra','fi-extra','fl-extra',tool.extraUpload.id,tool);

  // Wire pill groups
  ws.querySelectorAll('.pill-group').forEach(g => {
    g.querySelectorAll('.pill').forEach(p => {
      p.addEventListener('click', () => {
        g.querySelectorAll('.pill').forEach(x=>x.classList.remove('active'));
        p.classList.add('active');
      });
    });
  });

  // Wire sliders
  ws.querySelectorAll('.slider').forEach(s => {
    const valEl = ws.querySelector('#val-'+s.id.replace('opt-',''));
    if (valEl) { s.addEventListener('input',()=>valEl.textContent=s.value); }
  });

  // Run button
  $('#runBtn').addEventListener('click', async () => {
    const f = state.files['main'] || [];
    if (!f.length && !tool.multi) return toast('Upload a file first','error');
    try {
      await tool.run(f);
      hideProgress();
    } catch(e) {
      hideProgress();
      toast('Error: '+e.message,'error');
    }
  });

  // Mount callback
  if (tool.onMount) setTimeout(tool.onMount, 50);
}

// ===== WIRE UPLOAD ZONE =====
function wireUpload(zoneId, inputId, listId, stateKey, tool) {
  const zone = $(`#${zoneId}`);
  const input = $(`#${inputId}`);
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag-over'); if(e.dataTransfer.files.length) handleUpload(e.dataTransfer.files, stateKey, listId, tool); });
  input.addEventListener('change', () => { if(input.files.length) handleUpload(input.files, stateKey, listId, tool); });
}

async function handleUpload(files, stateKey, listId, tool) {
  try {
    toast('Uploading...','info');
    const uploaded = await uploadFiles(files);
    if (!state.files[stateKey]) state.files[stateKey] = [];
    if (stateKey === 'main' && !tool.multi) {
      state.files[stateKey] = uploaded;
    } else {
      state.files[stateKey].push(...uploaded);
    }
    toast('Uploaded!','success');
    
    const isPdf = stateKey === 'main' && tool.accept && tool.accept.includes('.pdf');
    const hasCustomPreview = CUSTOM_PREVIEW_TOOLS.includes(state.currentTool);
    
    if (isPdf && !hasCustomPreview && stateKey === 'main') {
      // Show iLovePDF-style layout
      if (tool.multi) {
        renderThumbGrid(stateKey, tool);
      } else {
        renderSplitView(stateKey, tool);
      }
    } else {
      // Fallback: normal text list
      renderFileList(stateKey, listId, tool);
    }

    // Show options section (for tools that don't use split view)
    if (hasCustomPreview || !isPdf || stateKey !== 'main') {
        const opts = $('#opts-section');
        if (opts) opts.classList.add('visible');
    }
    const extraSec = $('#extra-upload-section');
    if (extraSec) extraSec.classList.add('visible');

    // Callback
    if (stateKey === 'main' && tool.onFileLoad) tool.onFileLoad(state.files[stateKey]);
  } catch(e) { toast(e.message,'error'); }
}

// ===== SPLIT VIEW (single file: thumbnail left, options right) =====
function renderSplitView(stateKey, tool) {
    const files = state.files[stateKey] || [];
    if (!files.length) return;
    const f = files[0];
    
    // Hide upload zone and text list
    const uz = $('#uz-main');
    if (uz) uz.style.display = 'none';
    const fl = $('#fl-main');
    if (fl) fl.style.display = 'none';
    const opts = $('#opts-section');
    if (opts) opts.style.display = 'none';
    
    const container = $('#ws-split-container');
    if (!container) return;
    
    const toolTitle = tool.title.replace(/^[^\s]+\s/, ''); // Remove emoji
    const optionsHtml = tool.options || '';
    
    container.innerHTML = `
      <div class="ws-split">
        <div class="ws-preview-area">
          <div class="ws-single-thumb">
            <img src="/api/preview/${encodeURIComponent(f.path)}" alt="Preview">
            <div class="thumb-label">${f.name}</div>
          </div>
        </div>
        <div class="ws-options-area">
          <h3>${toolTitle}</h3>
          <div id="split-opts">${optionsHtml}</div>
          <button class="btn-primary" id="splitRunBtn">${toolTitle} ➜</button>
        </div>
      </div>
    `;
    container.style.display = 'block';
    
    // Wire pill groups in split view
    container.querySelectorAll('.pill-group').forEach(g => {
      g.querySelectorAll('.pill').forEach(p => {
        p.addEventListener('click', () => {
          g.querySelectorAll('.pill').forEach(x=>x.classList.remove('active'));
          p.classList.add('active');
        });
      });
    });
    
    // Wire sliders in split view
    container.querySelectorAll('.slider').forEach(s => {
      const valEl = container.querySelector('#val-'+s.id.replace('opt-',''));
      if (valEl) { s.addEventListener('input',()=>valEl.textContent=s.value); }
    });
    
    // Wire run button
    container.querySelector('#splitRunBtn').addEventListener('click', async () => {
      const f = state.files['main'] || [];
      if (!f.length) return toast('Upload a file first','error');
      try {
        await tool.run(f);
        hideProgress();
      } catch(e) {
        hideProgress();
        toast('Error: '+e.message,'error');
      }
    });
}

// ===== THUMBNAIL GRID (multi-file: merge, etc.) =====
function renderThumbGrid(stateKey, tool) {
    const files = state.files[stateKey] || [];
    const grid = $('#tg-main');
    if (!grid) return;
    
    grid.innerHTML = '';
    files.forEach((f, i) => {
        const isPdf = f.name.toLowerCase().endsWith('.pdf');
        const imgSrc = isPdf ? `/api/preview/${encodeURIComponent(f.path)}` : '';
        const pages = f.pages ? `${f.pages} pages` : '';
        
        const card = document.createElement('div');
        card.className = 'thumb-card';
        card.draggable = true;
        card.dataset.idx = i;
        card.innerHTML = `
          <div class="thumb-img-wrap">
            ${isPdf ? `<img src="${imgSrc}" alt="Page 1">` : `<span style="font-size:3rem;">📄</span>`}
          </div>
          <div class="thumb-info">
            <span class="thumb-name" title="${f.name}">${f.name}</span>
            ${pages ? `<span class="thumb-pages">${pages}</span>` : ''}
          </div>
          <button class="thumb-remove" data-idx="${i}">✕</button>
        `;
        grid.appendChild(card);
    });
    
    grid.style.display = 'flex';
    
    // Wire remove buttons
    grid.querySelectorAll('.thumb-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        state.files[stateKey].splice(+btn.dataset.idx, 1);
        renderThumbGrid(stateKey, tool);
      });
    });
    
    // Wire drag and drop for reordering
    let dragIdx = null;
    grid.querySelectorAll('.thumb-card').forEach(card => {
      card.addEventListener('dragstart', (e) => {
        dragIdx = +card.dataset.idx;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      card.addEventListener('dragend', () => {
        card.classList.remove('dragging');
        dragIdx = null;
      });
      card.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
      });
      card.addEventListener('drop', (e) => {
        e.preventDefault();
        const dropIdx = +card.dataset.idx;
        if (dragIdx !== null && dragIdx !== dropIdx) {
          const arr = state.files[stateKey];
          const [moved] = arr.splice(dragIdx, 1);
          arr.splice(dropIdx, 0, moved);
          renderThumbGrid(stateKey, tool);
        }
      });
    });
    
    // Show options
    const opts = $('#opts-section');
    if (opts) opts.classList.add('visible');
}

function renderFileList(stateKey, listId, tool) {
  const list = $(`#${listId}`);
  const files = state.files[stateKey] || [];
  if (!list) return;
  list.innerHTML = '';
  files.forEach((f, i) => {
    const pages = f.pages ? ` · ${f.pages}p` : '';
    list.innerHTML += `<div class="file-list-item"><span class="fl-num">${i+1}</span><span class="fl-name">${f.name}</span><span class="fl-size">${fmtSize(f.size)}${pages}</span><button class="fl-remove" data-idx="${i}">✕</button></div>`;
  });
  list.querySelectorAll('.fl-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      state.files[stateKey].splice(+btn.dataset.idx, 1);
      renderFileList(stateKey, listId, tool);
    });
  });
}

// ===== SIGNATURE CANVAS =====
function initSignatureCanvas() {
  const canvas = $('#sigCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let drawing = false;
  let paths = [];
  let currentPath = [];

  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#1a1a2e';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  function getPos(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    return [x * canvas.width / rect.width, y * canvas.height / rect.height];
  }

  function startDraw(e) { e.preventDefault(); drawing = true; currentPath = [getPos(e)]; }
  function draw(e) {
    if (!drawing) return;
    e.preventDefault();
    const p = getPos(e);
    currentPath.push(p);
    ctx.beginPath();
    ctx.moveTo(currentPath[currentPath.length-2][0], currentPath[currentPath.length-2][1]);
    ctx.lineTo(p[0], p[1]);
    ctx.stroke();
  }
  function endDraw() { if (drawing) { drawing = false; paths.push([...currentPath]); currentPath = []; } }

  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('mousemove', draw);
  canvas.addEventListener('mouseup', endDraw);
  canvas.addEventListener('mouseleave', endDraw);
  canvas.addEventListener('touchstart', startDraw, {passive:false});
  canvas.addEventListener('touchmove', draw, {passive:false});
  canvas.addEventListener('touchend', endDraw);

  function redraw() {
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 2.5;
    paths.forEach(path => {
      if (path.length < 2) return;
      ctx.beginPath();
      ctx.moveTo(path[0][0], path[0][1]);
      for (let i = 1; i < path.length; i++) ctx.lineTo(path[i][0], path[i][1]);
      ctx.stroke();
    });
  }

  $('#sigClear')?.addEventListener('click', () => { paths = []; redraw(); });
  $('#sigUndo')?.addEventListener('click', () => { paths.pop(); redraw(); });
}

// ===== CROP BOX =====
function initCropBox(img, fileInfo) {
  const cb = $('#cropBox');
  // default A4 dimensions
  let pdfW = 595.28, pdfH = 841.89; 
  if (fileInfo.page_sizes && fileInfo.page_sizes.length) {
    pdfW = fileInfo.page_sizes[0].width_in * 72;
    pdfH = fileInfo.page_sizes[0].height_in * 72;
  }
  
  let isDragging = false;
  let startX, startY, startRect;
  let activeHandle = null;

  function updateInputs() {
     const iW = img.offsetWidth;
     const iH = img.offsetHeight;
     const scaleX = pdfW / iW;
     const scaleY = pdfH / iH;
     
     const leftPx = parseFloat(cb.style.left || 0);
     const topPx = parseFloat(cb.style.top || 0);
     const rightPx = parseFloat(cb.style.right || 0);
     const bottomPx = parseFloat(cb.style.bottom || 0);
     
     $('#opt-crop-l').value = Math.max(0, Math.round(leftPx * scaleX));
     $('#opt-crop-t').value = Math.max(0, Math.round(topPx * scaleY));
     $('#opt-crop-r').value = Math.max(0, Math.round(rightPx * scaleX));
     $('#opt-crop-b').value = Math.max(0, Math.round(bottomPx * scaleY));
  }

  function onDown(e) {
     if (e.target.classList.contains('crop-handle')) {
        activeHandle = e.target.dataset.dir;
     } else if (e.target === cb) {
        activeHandle = 'move';
     } else {
        return;
     }
     isDragging = true;
     startX = e.clientX || e.touches?.[0].clientX;
     startY = e.clientY || e.touches?.[0].clientY;
     startRect = {
        l: parseFloat(cb.style.left || 0),
        t: parseFloat(cb.style.top || 0),
        r: parseFloat(cb.style.right || 0),
        b: parseFloat(cb.style.bottom || 0)
     };
     e.preventDefault();
  }

  function onMove(e) {
     if (!isDragging) return;
     const cx = e.clientX || e.touches?.[0].clientX;
     const cy = e.clientY || e.touches?.[0].clientY;
     const dx = cx - startX;
     const dy = cy - startY;
     
     const iW = img.offsetWidth;
     const iH = img.offsetHeight;

     if (activeHandle === 'move') {
        let newL = startRect.l + dx;
        let newT = startRect.t + dy;
        let newR = startRect.r - dx;
        let newB = startRect.b - dy;
        
        // Boundaries
        if (newL < 0) { newR += newL; newL = 0; }
        if (newT < 0) { newB += newT; newT = 0; }
        if (newR < 0) { newL += newR; newR = 0; }
        if (newB < 0) { newT += newB; newB = 0; }
        
        cb.style.left = newL + 'px';
        cb.style.top = newT + 'px';
        cb.style.right = newR + 'px';
        cb.style.bottom = newB + 'px';
     } else {
        if (activeHandle.includes('w')) {
           cb.style.left = Math.max(0, Math.min(iW - parseFloat(cb.style.right) - 20, startRect.l + dx)) + 'px';
        }
        if (activeHandle.includes('e')) {
           cb.style.right = Math.max(0, Math.min(iW - parseFloat(cb.style.left) - 20, startRect.r - dx)) + 'px';
        }
        if (activeHandle.includes('n')) {
           cb.style.top = Math.max(0, Math.min(iH - parseFloat(cb.style.bottom) - 20, startRect.t + dy)) + 'px';
        }
        if (activeHandle.includes('s')) {
           cb.style.bottom = Math.max(0, Math.min(iH - parseFloat(cb.style.top) - 20, startRect.b - dy)) + 'px';
        }
     }
     updateInputs();
  }

  function onUp() { isDragging = false; activeHandle = null; }

  cb.addEventListener('mousedown', onDown);
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
  cb.addEventListener('touchstart', onDown, {passive:false});
  document.addEventListener('touchmove', onMove, {passive:false});
  document.addEventListener('touchend', onUp);
  
  // reset box initially
  cb.style.left = '0px'; cb.style.top = '0px'; cb.style.right = '0px'; cb.style.bottom = '0px';
  updateInputs();
}

console.log('🎨 PDF Editor Pro loaded — 20+ tools ready');
})();
