// ── State ──────────────────────────────────────────────────────────────────────
let currentMode = 'live';
let cameraActive = false;

// ── Mode switching ─────────────────────────────────────────────────────────────
function switchMode(mode) {
  if (mode === currentMode) return;

  // If switching away from live while camera is on, stop it
  if (currentMode === 'live' && cameraActive) stopCamera();

  currentMode = mode;

  // Tab active state
  document.getElementById('tabLive').classList.toggle('active', mode === 'live');
  document.getElementById('tabImage').classList.toggle('active', mode === 'image');
  document.querySelectorAll('[role="tab"]').forEach(t =>
    t.setAttribute('aria-selected', t.id === `tab${cap(mode)}`)
  );

  // Panel visibility
  document.getElementById('panelLive').classList.toggle('hidden', mode !== 'live');
  document.getElementById('panelImage').classList.toggle('hidden', mode !== 'image');
}

function cap(str) { return str.charAt(0).toUpperCase() + str.slice(1); }

// ── Live camera ────────────────────────────────────────────────────────────────
function startCamera() {
  cameraActive = true;

  const stream = document.getElementById('liveStream');
  const idle = document.getElementById('liveIdle');
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');

  // Point the img src at the Flask streaming endpoint
  stream.src = '/video_feed';
  stream.classList.remove('hidden');
  idle.classList.add('hidden');

  btnStart.classList.add('hidden');
  btnStop.classList.remove('hidden');

  setStatus('DETECTION ACTIVE', true);
  updateStat('statMode', 'LIVE STREAM');
  updateStat('statSource', 'WEBCAM [0]');
}

function stopCamera() {
  cameraActive = false;

  const stream = document.getElementById('liveStream');
  const idle = document.getElementById('liveIdle');
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');

  // Stop the MJPEG stream by clearing src
  stream.src = '';
  stream.classList.add('hidden');
  idle.classList.remove('hidden');

  btnStart.classList.remove('hidden');
  btnStop.classList.add('hidden');

  setStatus('SYSTEM READY', false);
  updateStat('statMode', '—');
  updateStat('statSource', '—');
}

// ── Image upload ───────────────────────────────────────────────────────────────
function previewFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  applyPreview(file);
}

function applyPreview(file) {
  const reader = new FileReader();
  const preview = document.getElementById('previewImg');
  const dropContent = document.getElementById('dropContent');
  const fileName = document.getElementById('fileName');
  const btnAnalyze = document.getElementById('btnAnalyze');

  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.classList.remove('hidden');
    dropContent.style.display = 'none';
  };
  reader.readAsDataURL(file);

  fileName.textContent = file.name;
  btnAnalyze.disabled = false;
}

// Drag & drop
function handleDragOver(event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'copy';
  document.getElementById('dropZone').classList.add('dragover');
}

function handleDragLeave(event) {
  document.getElementById('dropZone').classList.remove('dragover');
}

function handleDrop(event) {
  event.preventDefault();
  document.getElementById('dropZone').classList.remove('dragover');

  const file = event.dataTransfer.files[0];
  if (!file) return;

  // Validate type
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
  if (!allowed.includes(file.type)) {
    showInlineError('Invalid file type. Please drop a JPG, PNG, GIF, BMP, or WEBP image.');
    return;
  }

  // Set into file input for form submission
  const dt = new DataTransfer();
  dt.items.add(file);
  document.getElementById('fileInput').files = dt.files;

  applyPreview(file);
}

// ── Status bar helpers ─────────────────────────────────────────────────────────
function setStatus(label, active) {
  document.getElementById('statusLabel').textContent = label;
  document.getElementById('statusDot').classList.toggle('active', active);
}

function updateStat(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── Inline error (image panel) ─────────────────────────────────────────────────
function showInlineError(msg) {
  let box = document.getElementById('inlineError');
  if (!box) {
    box = document.createElement('div');
    box.id = 'inlineError';
    box.className = 'flash-msg';
    document.getElementById('uploadForm').after(box);
  }
  box.textContent = '⚠ ' + msg;
  setTimeout(() => { if (box) box.remove(); }, 5000);
}

// ── Form submit feedback ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('uploadForm');
  const btnAnal = document.getElementById('btnAnalyze');

  if (form) {
    form.addEventListener('submit', (e) => {
      if (!document.getElementById('fileInput').files.length) {
        e.preventDefault();
        showInlineError('Please select an image before analyzing.');
        return;
      }
      if (btnAnal) {
        btnAnal.textContent = '⟳  ANALYZING…';
        btnAnal.disabled = true;
      }
      setStatus('PROCESSING IMAGE', true);
    });
  }

  // If a result image is present on load (after Flask redirect), switch to image tab
  if (document.querySelector('.result-block')) {
    switchMode('image');
    setStatus('ANALYSIS COMPLETE', false);
  }
});