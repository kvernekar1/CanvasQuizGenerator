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

  chooseBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
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

  convertBtn.addEventListener('click', async () => {
    if(!currentFile) return;
    hide(fileInfo);
    show(processing);

    try {
      const formData = new FormData();
      formData.append('file', currentFile);

      const response = await fetch('/convert', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(err || 'Conversion failed');
      }

      const taskData = await response.json();
      const taskId = taskData.task_id;

      let resultReady = false;
      let resultResponse = null;
      const maxAttempts = 120; 
      let attempts = 0;

      while (!resultReady && attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 1000));
        attempts++;

        resultResponse = await fetch(`/result/${taskId}`);
        if (!resultResponse.ok) {
          throw new Error('Failed to check result status');
        }

        const resultData = await resultResponse.json();
        if (resultData.status === 'complete') {
          resultReady = true;
        } else if (resultData.status === 'error') {
          throw new Error(resultData.error || 'Conversion error');
        }
      }

      if (!resultReady) {
        throw new Error('Conversion timed out after 2 minutes');
      }

      const blob = await resultResponse.blob();
      if(currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = URL.createObjectURL(blob);

      const outName = "canvas_quiz.zip";
      downloadLink.href = currentObjectUrl;
      downloadLink.download = outName;
      downloadName.textContent = outName;

      hide(processing);
      hide(uploadScreen);
      show(downloadScreen);
    } catch(err) {
      hide(processing);
      show(fileInfo);
      alert('Error during conversion: ' + err.message);
    }
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
