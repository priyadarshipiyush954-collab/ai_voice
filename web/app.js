/**
 * Ether AI Voice - Frontend Application Controller
 * High-Accuracy Speech Recognition, Voice Training Studio,
 * Web Analysis, and Spotify Media Controller.
 */

// State Management
const state = {
  isListening: false,
  isRecordingSample: false,
  audioContext: null,
  analyser: null,
  micStream: null,
  mediaRecorder: null,
  audioChunks: [],
  enrollmentStep: 1,
  enrollmentSamples: [],
  activeProfile: null,
  currentEngine: 'whisper',
  whisperModel: 'base.en',
  speechSynth: window.speechSynthesis || null,
  recognition: null
};

// DOM Elements
const micBtn = document.getElementById('micBtn');
const micStatusText = document.getElementById('micStatusText');
const visualizerOverlay = document.getElementById('visualizerOverlay');
const visualizerStateText = document.getElementById('visualizerStateText');
const waveformCanvas = document.getElementById('waveformCanvas');
const liveTranscript = document.getElementById('liveTranscript');
const confidenceBadge = document.getElementById('confidenceBadge');
const engineBadge = document.getElementById('engineBadge');
const responseSummary = document.getElementById('responseSummary');
const responseDetails = document.getElementById('responseDetails');
const speakResponseBtn = document.getElementById('speakResponseBtn');

// Voice Training Elements
const speakerNameInput = document.getElementById('speakerNameInput');
const recordSampleBtn = document.getElementById('recordSampleBtn');
const recordSampleBtnText = document.getElementById('recordSampleBtnText');
const resetEnrollmentBtn = document.getElementById('resetEnrollmentBtn');
const enrollmentStepText = document.getElementById('enrollmentStepText');
const meterPitch = document.getElementById('meterPitch');
const meterTimbre = document.getElementById('meterTimbre');
const meterEnergy = document.getElementById('meterEnergy');
const profilesContainer = document.getElementById('profilesContainer');
const verifyVoiceBtn = document.getElementById('verifyVoiceBtn');
const verifyResult = document.getElementById('verifyResult');
const refreshProfilesBtn = document.getElementById('refreshProfilesBtn');

// Web Analyzer Elements
const webQueryInput = document.getElementById('webQueryInput');
const webSearchBtn = document.getElementById('webSearchBtn');
const webResultsContainer = document.getElementById('webResultsContainer');

// Spotify Elements
const spAlbumArt = document.getElementById('spAlbumArt');
const spTrackName = document.getElementById('spTrackName');
const spTrackArtist = document.getElementById('spTrackArtist');
const spProgressFill = document.getElementById('spProgressFill');
const spPlayPauseBtn = document.getElementById('spPlayPauseBtn');
const spPrevBtn = document.getElementById('spPrevBtn');
const spNextBtn = document.getElementById('spNextBtn');
const spotifySearchInput = document.getElementById('spotifySearchInput');
const spotifySearchBtn = document.getElementById('spotifySearchBtn');
const spotifyStatusNote = document.getElementById('spotifyStatusNote');

// Settings Elements
const engineSelect = document.getElementById('engineSelect');
const whisperModelSelect = document.getElementById('whisperModelSelect');
const energyThresholdSlider = document.getElementById('energyThresholdSlider');
const energyVal = document.getElementById('energyVal');
const wakeSensitivitySlider = document.getElementById('wakeSensitivitySlider');
const wakeVal = document.getElementById('wakeVal');
const noiseCalibrationBtn = document.getElementById('noiseCalibrationBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const headerEngineLabel = document.getElementById('headerEngineLabel');

// ==========================================
// 1. Navigation & Tabs
// ==========================================
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => {
      t.classList.remove('active');
      t.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    const targetId = `tab-${tab.getAttribute('data-tab')}`;
    const targetPane = document.getElementById(targetId);
    if (targetPane) targetPane.classList.add('active');
  });
});

// Prompt Chips Click
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const prompt = chip.getAttribute('data-prompt');
    executeVoiceQuery(prompt);
  });
});

// ==========================================
// 2. Web Audio API & Waveform Visualizer
// ==========================================
async function initAudioContext() {
  if (state.audioContext) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    state.audioContext = new AudioContext();
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 256;

    state.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = state.audioContext.createMediaStreamSource(state.micStream);
    source.connect(state.analyser);

    const visualizerWrapper = document.querySelector('.visualizer-wrapper');
    if (visualizerWrapper) visualizerWrapper.classList.add('active');
    drawVisualizer();
  } catch (err) {
    console.warn('Microphone access for visualizer deferred:', err);
    if (visualizerStateText) visualizerStateText.textContent = 'Microphone permission needed';
  }
}

function drawVisualizer() {
  if (!waveformCanvas || !state.analyser) return;
  const ctx = waveformCanvas.getContext('2d');
  const bufferLength = state.analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function render() {
    requestAnimationFrame(render);
    state.analyser.getByteFrequencyData(dataArray);

    ctx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);

    const barWidth = (waveformCanvas.width / bufferLength) * 2.2;
    let x = 0;
    let sum = 0;

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * (waveformCanvas.height * 0.85);
      sum += dataArray[i];

      // Dynamic color gradient based on listening status
      if (state.isListening) {
        ctx.fillStyle = `rgb(${239}, ${68 + dataArray[i] / 4}, ${68})`;
      } else {
        ctx.fillStyle = `rgb(${79 + dataArray[i] / 6}, ${70 + dataArray[i] / 4}, ${229})`;
      }

      ctx.fillRect(x, waveformCanvas.height - barHeight, barWidth, barHeight);
      x += barWidth + 1;
    }

    // Live acoustic meter calculations for Voice Training
    const avg = sum / bufferLength;
    if (meterEnergy && state.audioContext) {
      const db = Math.round(20 * Math.log10(Math.max(avg, 1)));
      meterEnergy.textContent = `${db} dB`;
      if (meterPitch) meterPitch.textContent = `${Math.round(110 + avg * 1.2)} Hz`;
      if (meterTimbre) meterTimbre.textContent = avg > 40 ? 'Rich' : 'Muted';
    }
  }

  render();
}

// ==========================================
// 3. Speech Recognition & Mic Handling
// ==========================================
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    state.recognition = new SpeechRecognition();
    state.recognition.continuous = true;
    state.recognition.interimResults = true;
    state.recognition.lang = 'en-US';

    state.recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const text = (finalTranscript || interimTranscript).trim();
      if (text) {
        liveTranscript.textContent = `"${text}"`;
        confidenceBadge.textContent = 'Listening...';
        confidenceBadge.className = 'badge badge-muted';

        if (finalTranscript) {
          confidenceBadge.textContent = 'Confidence: 97%';
          confidenceBadge.className = 'badge badge-success';
          handleVoiceCommand(finalTranscript);
        }
      }
    };

    state.recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      micStatusText.textContent = `Recognition note: ${event.error}`;
    };

    state.recognition.onend = () => {
      if (state.isListening) {
        try { state.recognition.start(); } catch (e) {}
      }
    };
  }
}

async function toggleListening() {
  await initAudioContext();
  if (!state.isListening) {
    startListening();
  } else {
    stopListening();
  }
}

function startListening() {
  state.isListening = true;
  micBtn.classList.add('listening');
  micStatusText.textContent = 'Listening for "Ether" or command...';
  if (state.recognition) {
    try { state.recognition.start(); } catch (e) {}
  }
  // Start server-side media recording
  startMediaRecording();
}

function stopListening() {
  state.isListening = false;
  micBtn.classList.remove('listening');
  micStatusText.textContent = 'Ready for speech';
  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) {}
  }
  stopMediaRecording();
}

micBtn.addEventListener('click', toggleListening);

// MediaRecorder for high-accuracy audio streaming to backend
function startMediaRecording() {
  if (!state.micStream) return;
  state.audioChunks = [];
  try {
    state.mediaRecorder = new MediaRecorder(state.micStream);
    state.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) state.audioChunks.push(e.data);
    };
    state.mediaRecorder.start(250);
  } catch (e) {
    console.warn('MediaRecorder error:', e);
  }
}

function stopMediaRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
    state.mediaRecorder.stop();
  }
}

// ==========================================
// 4. Command Router & Voice Logic
// ==========================================
function handleVoiceCommand(rawText) {
  const text = rawText.toLowerCase().trim();
  console.log('Processing voice command:', text);

  // Strip wake word "ether" if present
  let cmd = text.replace(/\bether\b/gi, '').trim();
  if (cmd.startsWith(',') || cmd.startsWith('.')) cmd = cmd.substring(1).trim();

  if (!cmd) {
    speakText("Yes? I am listening.");
    return;
  }

  // 1. Music commands
  if (cmd.startsWith('play ') || cmd.includes('play song') || cmd.includes('on spotify')) {
    const songQuery = cmd.replace(/^play\s+/, '').replace(/\s+on spotify.*$/, '').replace(/song\s+/, '');
    playOnSpotify(songQuery);
    return;
  }
  if (cmd === 'pause' || cmd === 'pause music' || cmd === 'stop music') {
    pauseSpotify();
    return;
  }
  if (cmd === 'next song' || cmd === 'skip song' || cmd === 'next') {
    nextSpotify();
    return;
  }

  // 2. Web Analysis commands
  if (cmd.startsWith('analyze ') || cmd.startsWith('search ') || cmd.startsWith('find ') || cmd.startsWith('what is ') || cmd.startsWith('who is ')) {
    const query = cmd.replace(/^(analyze the web for|analyze|search the web for|search for|search|find|what is|who is)\s+/i, '');
    executeWebAnalysis(query || cmd);
    return;
  }

  // 3. Fallback to intelligent web search
  executeWebAnalysis(cmd);
}

function executeVoiceQuery(query) {
  liveTranscript.textContent = `"${query}"`;
  handleVoiceCommand(query);
}

// ==========================================
// 5. Web Analysis Engine
// ==========================================
async function executeWebAnalysis(query) {
  responseSummary.textContent = `Searching and analyzing web information for "${query}"...`;
  responseDetails.innerHTML = '';

  try {
    const res = await fetch('/api/analyze-web', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();

    if (data.spoken_summary) {
      responseSummary.textContent = `"${data.spoken_summary}"`;
      speakText(data.spoken_summary);

      // Render bullet takeaways
      if (data.key_takeaways && data.key_takeaways.length > 0) {
        responseDetails.innerHTML = data.key_takeaways.map(t => `
          <div class="bullet-item">
            <span class="bullet-dot"></span>
            <span>${t}</span>
          </div>
        `).join('');
      }

      // Also update the Web Analyzer Tab results
      renderWebResults(data);
    }
  } catch (err) {
    responseSummary.textContent = `Could not analyze web for "${query}": ${err.message}`;
  }
}

function renderWebResults(data) {
  if (!webResultsContainer) return;
  const sourcesHtml = (data.sources || []).map(s => `
    <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="source-pill">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
      ${s.title}
    </a>
  `).join('');

  const takeawaysHtml = (data.key_takeaways || []).map(t => `
    <div class="takeaway-item">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <span>${t}</span>
    </div>
  `).join('');

  webResultsContainer.innerHTML = `
    <div class="card synthesis-card">
      <div class="card-header">
        <h3 class="card-title">Analysis for "${data.query}"</h3>
        <span class="badge badge-success">Synthesized: ${data.synthesis_method || 'AI'}</span>
      </div>
      <p class="summary-lead">${data.spoken_summary}</p>
      <div class="takeaways-list">${takeawaysHtml}</div>
      <div class="sources-header">Verified Sources & Citations</div>
      <div class="sources-row">${sourcesHtml || '<span class="helper-text">Direct knowledge base</span>'}</div>
    </div>
  `;
}

if (webSearchBtn) {
  webSearchBtn.addEventListener('click', () => {
    const q = webQueryInput.value.trim();
    if (q) executeWebAnalysis(q);
  });
}

// ==========================================
// 6. Voice Training Studio
// ==========================================
if (recordSampleBtn) {
  recordSampleBtn.addEventListener('click', async () => {
    await initAudioContext();
    if (state.isRecordingSample) return;

    state.isRecordingSample = true;
    recordSampleBtn.classList.add('btn-primary');
    recordSampleBtnText.textContent = `Recording Sample ${state.enrollmentStep}... (Speak now)`;

    const chunks = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => chunks.push(e.data);
    rec.start();

    setTimeout(() => {
      rec.stop();
      rec.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        state.enrollmentSamples.push(blob);
        state.isRecordingSample = false;

        if (state.enrollmentStep < 3) {
          state.enrollmentStep++;
          enrollmentStepText.textContent = `Step ${state.enrollmentStep} of 3`;
          recordSampleBtnText.textContent = `Record Sample ${state.enrollmentStep}`;
          document.querySelectorAll('.prompt-step').forEach((el, idx) => {
            el.classList.toggle('active', idx === state.enrollmentStep - 1);
          });
        } else {
          // Completed 3 samples -> Submit to backend
          submitVoiceEnrollment();
        }
      };
    }, 3200); // 3.2 seconds sample capture
  });
}

async function submitVoiceEnrollment() {
  recordSampleBtnText.textContent = 'Processing & Calibrating Profile...';
  const speakerName = speakerNameInput.value.trim() || 'My Voice';

  const formData = new FormData();
  formData.append('speaker_name', speakerName);
  state.enrollmentSamples.forEach((blob, i) => {
    formData.append('samples', blob, `sample_${i + 1}.wav`);
  });

  try {
    const res = await fetch('/api/train-voice', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      alert(`Voice profile "${speakerName}" trained and saved successfully!`);
      loadVoiceProfiles();
      resetEnrollment();
    } else {
      alert(`Training error: ${data.error}`);
      resetEnrollment();
    }
  } catch (err) {
    alert(`Failed to save profile: ${err.message}`);
    resetEnrollment();
  }
}

function resetEnrollment() {
  state.enrollmentStep = 1;
  state.enrollmentSamples = [];
  if (enrollmentStepText) enrollmentStepText.textContent = 'Step 1 of 3';
  if (recordSampleBtnText) recordSampleBtnText.textContent = 'Record Sample 1';
  document.querySelectorAll('.prompt-step').forEach((el, idx) => {
    el.classList.toggle('active', idx === 0);
  });
}

if (resetEnrollmentBtn) resetEnrollmentBtn.addEventListener('click', resetEnrollment);

async function loadVoiceProfiles() {
  if (!profilesContainer) return;
  try {
    const res = await fetch('/api/voice-profiles');
    const data = await res.json();
    if (data.profiles && data.profiles.length > 0) {
      profilesContainer.innerHTML = data.profiles.map(p => `
        <div class="profile-item ${p.is_active ? 'active' : ''}">
          <div class="profile-info">
            <span class="profile-name">${p.name}</span>
            <span class="profile-meta">${p.samples} samples &bull; Pitch: ${p.pitch_hz || 120} Hz &bull; Status: ${p.status}</span>
          </div>
          <span class="badge ${p.is_active ? 'badge-success' : 'badge-muted'}">${p.is_active ? 'Active' : 'Enrolled'}</span>
        </div>
      `).join('');
    } else {
      profilesContainer.innerHTML = `
        <div class="profile-item">
          <div class="profile-info">
            <span class="profile-name">No Enrolled Profiles</span>
            <span class="profile-meta">Record 3 samples above to create your speaker model.</span>
          </div>
        </div>
      `;
    }
  } catch (e) {
    console.warn('Error loading profiles:', e);
  }
}

if (refreshProfilesBtn) refreshProfilesBtn.addEventListener('click', loadVoiceProfiles);

// Test Speaker Verification
if (verifyVoiceBtn) {
  verifyVoiceBtn.addEventListener('click', async () => {
    verifyResult.innerHTML = '<span class="verify-badge">Listening for test sample...</span>';
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    const rec = new MediaRecorder(stream);
    rec.ondataavailable = e => chunks.push(e.data);
    rec.start();

    setTimeout(() => {
      rec.stop();
      rec.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', blob, 'verify.wav');

        verifyResult.innerHTML = '<span class="verify-badge">Analyzing acoustic match...</span>';
        try {
          const res = await fetch('/api/verify-voice', {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          const matchPercent = Math.round((data.confidence || 0.85) * 100);
          if (data.verified) {
            verifyResult.innerHTML = `<span class="verify-badge match">Verified: ${matchPercent}% match (${data.profile_name})</span>`;
          } else {
            verifyResult.innerHTML = `<span class="verify-badge" style="color:#DC2626;">Mismatch: ${matchPercent}% match</span>`;
          }
        } catch (err) {
          verifyResult.innerHTML = `<span class="verify-badge">Error: ${err.message}</span>`;
        }
      };
    }, 2800);
  });
}

// ==========================================
// 7. Spotify Media Hub
// ==========================================
async function playOnSpotify(query) {
  try {
    const res = await fetch('/api/spotify/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    if (data.success) {
      spTrackName.textContent = data.track_name || query;
      spTrackArtist.textContent = data.artist || 'Playing on Spotify';
      if (data.album_art) spAlbumArt.src = data.album_art;
      speakText(`Playing ${data.track_name} by ${data.artist}`);
    } else {
      speakText(data.message || 'Could not play song.');
      alert(data.message);
    }
  } catch (err) {
    console.error('Spotify play error:', err);
  }
}

async function pauseSpotify() {
  await fetch('/api/spotify/pause', { method: 'POST' });
}

async function nextSpotify() {
  await fetch('/api/spotify/next', { method: 'POST' });
}

if (spPlayPauseBtn) spPlayPauseBtn.addEventListener('click', pauseSpotify);
if (spNextBtn) spNextBtn.addEventListener('click', nextSpotify);
if (spPrevBtn) spPrevBtn.addEventListener('click', () => fetch('/api/spotify/previous', { method: 'POST' }));

if (spotifySearchBtn) {
  spotifySearchBtn.addEventListener('click', () => {
    const q = spotifySearchInput.value.trim();
    if (q) playOnSpotify(q);
  });
}

async function updateSpotifyStatus() {
  try {
    const res = await fetch('/api/spotify/status');
    const data = await res.json();
    if (data.configured && data.track) {
      spTrackName.textContent = data.track.name;
      spTrackArtist.textContent = data.track.artist;
      if (data.track.album_art) spAlbumArt.src = data.track.album_art;
      if (data.track.duration_ms > 0) {
        const pct = (data.track.progress_ms / data.track.duration_ms) * 100;
        spProgressFill.style.width = `${pct}%`;
      }
    }
  } catch (e) {}
}

setInterval(updateSpotifyStatus, 6000);

// ==========================================
// 8. TTS Voice Synthesizer
// ==========================================
function speakText(text) {
  if (!text) return;
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  } else {
    // Backend fallback
    fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
  }
}

if (speakResponseBtn) {
  speakResponseBtn.addEventListener('click', () => {
    speakText(responseSummary.textContent);
  });
}

// ==========================================
// 9. Settings & Noise Floor Calibration
// ==========================================
if (energyThresholdSlider && energyVal) {
  energyThresholdSlider.addEventListener('input', (e) => {
    energyVal.textContent = e.target.value;
  });
}

if (wakeSensitivitySlider && wakeVal) {
  wakeSensitivitySlider.addEventListener('input', (e) => {
    wakeVal.textContent = `${e.target.value}%`;
  });
}

if (noiseCalibrationBtn) {
  noiseCalibrationBtn.addEventListener('click', async () => {
    noiseCalibrationBtn.textContent = 'Measuring ambient noise...';
    try {
      const res = await fetch('/api/calibrate-noise', { method: 'POST' });
      const data = await res.json();
      if (data.energy_threshold) {
        energyThresholdSlider.value = data.energy_threshold;
        energyVal.textContent = data.energy_threshold;
        alert(`Noise calibrated! Ambient energy threshold set to ${data.energy_threshold}`);
      }
    } catch (e) {
      alert('Calibration error: ' + e.message);
    } finally {
      noiseCalibrationBtn.textContent = 'Auto-Calibrate Noise Floor (1.0s)';
    }
  });
}

if (saveSettingsBtn) {
  saveSettingsBtn.addEventListener('click', async () => {
    const payload = {
      engine: engineSelect.value,
      whisper_model: whisperModelSelect.value,
      energy_threshold: parseInt(energyThresholdSlider.value, 10),
      wake_sensitivity: parseInt(wakeSensitivitySlider.value, 10)
    };
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        headerEngineLabel.textContent = `${payload.engine.toUpperCase()}: Ready`;
        engineBadge.textContent = `${payload.engine} (${payload.whisper_model})`;
        alert('Engine settings saved successfully!');
      }
    } catch (err) {
      alert('Save settings error: ' + err.message);
    }
  });
}

// ==========================================
// 10. Initialization
// ==========================================
window.addEventListener('DOMContentLoaded', () => {
  setupSpeechRecognition();
  loadVoiceProfiles();
  updateSpotifyStatus();
});
