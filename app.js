(function(){
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const chooseBtn = document.getElementById('chooseBtn');
  const fileInfo = document.getElementById('fileInfo');
  const fileNameEl = document.getElementById('fileName');
  const convertBtn = document.getElementById('convertBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  const processing = document.getElementById('processing');
  const uploadScreen = document.getElementById('upload-screen');
  const downloadScreen = document.getElementById('download-screen');
  const downloadLink = document.getElementById('downloadLink');
  const downloadName = document.getElementById('downloadName');
  const againBtn = document.getElementById('againBtn');

  let currentFile = null;
  let currentObjectUrl = null;

  function show(el){ el.classList.remove('hidden'); }
  function hide(el){ el.classList.add('hidden'); }

  function setFile(file){
    currentFile = file;
    fileNameEl.textContent = file.name;
    show(fileInfo);
  }

  // Click handlers
  chooseBtn.addEventListener('click', ()=> fileInput.click());
  dropzone.addEventListener('click', ()=> fileInput.click());

  fileInput.addEventListener('change', (e)=>{
    if(e.target.files && e.target.files[0]){
      setFile(e.target.files[0]);
    }
  });

  cancelBtn.addEventListener('click', ()=>{
    fileInput.value = '';
    currentFile = null;
    hide(fileInfo);
  });

  convertBtn.addEventListener('click', ()=>{
    if(!currentFile) return;
    hide(fileInfo);
    show(processing);

    // Simulate conversion work
    setTimeout(()=>{
      hide(processing);
      // build a simple QTI-like XML payload
      const safeName = (currentFile.name || 'file').replace(/\s+/g,'_');
      const xml = generateQtiXml(safeName);
      const blob = new Blob([xml], {type: 'application/xml'});
      if(currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = URL.createObjectURL(blob);
      downloadLink.href = currentObjectUrl;
      // prefer .qti filename
      const outName = (safeName.replace(/\.(pdf|docx)$/i,'') || 'converted') + '.qti';
      downloadLink.download = outName;
      downloadName.textContent = outName;

      hide(uploadScreen);
      show(downloadScreen);

    }, 900); // short fake delay
  });

  againBtn.addEventListener('click', ()=>{
    // cleanup
    if(currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = null;
    fileInput.value = '';
    currentFile = null;
    hide(downloadScreen);
    show(uploadScreen);
    hide(fileInfo);
  });

  // Drag & drop handlers
  ['dragenter','dragover'].forEach(evt => {
    dropzone.addEventListener(evt, (e)=>{
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });
  ['dragleave','drop'].forEach(evt => {
    dropzone.addEventListener(evt, (e)=>{
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e)=>{
    const dt = e.dataTransfer;
    if(dt && dt.files && dt.files[0]){
      const f = dt.files[0];
      // accept only pdf/docx
      if(!/\.pdf$/i.test(f.name) && !/\.docx$/i.test(f.name)){
        alert('Please drop a PDF or DOCX file.');
        return;
      }
      setFile(f);
    }
  });

  // simple QTI generator (placeholder)
  function generateQtiXml(name){
    const now = new Date().toISOString();
    return `<?xml version="1.0" encoding="UTF-8"?>\n<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">\n  <assessment title="Converted from ${escapeXml(name)}">\n    <section ident="s1">\n      <item ident="item_${Math.random().toString(36).slice(2,9)}">\n        <itemmetadata>\n          <qtimetadata>\n            <qtimetadatafield>\n              <fieldlabel>sourceFile</fieldlabel>\n              <fieldentry>${escapeXml(name)}</fieldentry>\n            </qtimetadatafield>\n            <qtimetadatafield>\n              <fieldlabel>converted</fieldlabel>\n              <fieldentry>${now}</fieldentry>\n            </qtimetadatafield>\n          </qtimetadata>\n        </itemmetadata>\n        <itembody>\n          <p>Placeholder content: converted from ${escapeXml(name)}</p>\n        </itembody>\n      </item>\n    </section>\n  </assessment>\n</questestinterop>`;
  }

  function escapeXml(unsafe){
    return String(unsafe).replace(/[<>&"']/g, function(c){
      switch(c){case '<':return '&lt;';case '>':return '&gt;';case '&':return '&amp;';case '"':return '&quot;';case "'":return '&apos;'}
    });
  }

})();
