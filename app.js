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
  //const downloadName = document.getElementById('downloadName');
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

  chooseBtn.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', (e) => {
    if(e.target.files && e.target.files[0]){
      setFile(e.target.files[0]);
    }
  });

  cancelBtn.addEventListener('click', () => {
    fileInput.value = '';
    currentFile = null;
    hide(fileInfo);
  });

  convertBtn.addEventListener('click',  async () => {
    if(!currentFile) return;
    hide(fileInfo);
    show(processing);
    const response = await fetch("/convert", {
       method: "POST",
       body: currentFile,
       headers: {
         "Content-Type": "application/octet-stream",
         "X-Filename": currentFile.name
       }
    });
    const QTIfile = response.blob()
    downloadLink.href = URL.createObjectURL(QTIfile);
    downloadLink.click()
  });

  againBtn.addEventListener('click', () => {
    if(currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
    downloadLink.href = '#';
    currentObjectUrl = null;
    fileInput.value = '';
    currentFile = null;
    hide(downloadScreen);
    show(uploadScreen);
    hide(fileInfo);
  });

  ['dragenter','dragover'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });
  
  ['dragleave','drop'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if(dt && dt.files && dt.files[0]){
      const f = dt.files[0];
      if(!/\.pdf$/i.test(f.name) && !/\.docx$/i.test(f.name)){
        alert('Please drop a PDF or DOCX file.');
        return;
      }
      setFile(f);
    }
  });

})();
