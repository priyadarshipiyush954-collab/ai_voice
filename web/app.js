/* ============================================================
 *  Ether AI Voice — Frontend Controller
 *  Production-quality vanilla JS · No frameworks · No Spotify
 * ============================================================ */

'use strict';

/* ────────────────────────────────────────────────────────────
 *  §0  Application State
 * ──────────────────────────────────────────────────────────── */

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
  recognition: null
};

/* ────────────────────────────────────────────────────────────
 *  §1  Floating Particles Canvas Animation
 * ──────────────────────────────────────────────────────────── */

function initParticles() {
  const canvas = document.getElementById('particlesCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const PARTICLE_COUNT_MIN = 60;
  const PARTICLE_COUNT_MAX = 80;
  const CONNECTION_DISTANCE = 120;
  const LINE_OPACITY = 0.05;
  const prefersReducedMotion =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let particles = [];
  let animId = null;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticles() {
    const count =
      PARTICLE_COUNT_MIN +
      Math.floor(Math.random() * (PARTICLE_COUNT_MAX - PARTICLE_COUNT_MIN + 1));
    particles = [];
    for (let i = 0; i < count; i++) {
      const opacity = 0.15 + Math.random() * 0.2; // 0.15 – 0.35
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: 1 + Math.random() * 2, // 1 – 3 px
        vx: (Math.random() - 0.5) * 0.6, // -0.3 – 0.3
        vy: (Math.random() - 0.5) * 0.6,
        opacity
      });
    }
  }

  function drawStatic() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(79, 70, 229, ${p.opacity})`;
      ctx.fill();
    }
    // Draw connection lines once
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        if (dx * dx + dy * dy < CONNECTION_DISTANCE * CONNECTION_DISTANCE) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(79, 70, 229, ${LINE_OPACITY})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;

      // Wrap around edges
      if (p.x < -p.r) p.x = canvas.width + p.r;
      else if (p.x > canvas.width + p.r) p.x = -p.r;
      if (p.y < -p.r) p.y = canvas.height + p.r;
      else if (p.y > canvas.height + p.r) p.y = -p.r;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(79, 70, 229, ${p.opacity})`;
      ctx.fill();
    }

    // Connection lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        if (dx * dx + dy * dy < CONNECTION_DISTANCE * CONNECTION_DISTANCE) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(79, 70, 229, ${LINE_OPACITY})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    animId = requestAnimationFrame(animate);
  }

  resize();
  createParticles();

  window.addEventListener('resize', () => {
    resize();
    createParticles();
    if (prefersReducedMotion) drawStatic();
  });

  if (prefersReducedMotion) {
    drawStatic();
  } else {
    animate();
  }
}

/* ────────────────────────────────────────────────────────────
 *  §2  Scroll Reveal Animations (IntersectionObserver)
 * ──────────────────────────────────────────────────────────── */

/** @type {IntersectionObserver|null} */
let revealObserver = null;

function initScrollReveal() {
  if (!('IntersectionObserver' in window)) {
    // Fallback: make everything visible immediately
    document.querySelectorAll('.anim-card-reveal').forEach(el => el.classList.add('visible'));
    return;
  }

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    },
    { threshold: 0.15 }
  );

  document.querySelectorAll('.anim-card-reveal').forEach(el => revealObserver.observe(el));
}

/** Re-observe elements (e.g. after tab switch) */
function reobserveRevealElements(container) {
  if (!revealObserver) return;
  const scope = container || document;
  scope.querySelectorAll('.anim-card-reveal').forEach(el => {
    if (!el.classList.contains('visible')) {
      revealObserver.observe(el);
    }
  });
}

/* ────────────────────────────────────────────────────────────
 *  §3  Stat Counter Animation
 * ──────────────────────────────────────────────────────────── */

function initStatCounters() {
  const counters = document.querySelectorAll('.stat-number[data-count]');
  if (!counters.length) return;

  if (!('IntersectionObserver' in window)) {
    counters.forEach(el => {
      const target = parseInt(el.getAttribute('data-count'), 10) || 0;
      const suffix = el.getAttribute('data-suffix') || '';
      el.textContent = target + suffix;
    });
    return;
  }

  function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
  }

  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        counterObserver.unobserve(el); // run once
        const target = parseInt(el.getAttribute('data-count'), 10) || 0;
        const suffix = el.getAttribute('data-suffix') || '';
        const duration = 1500; // ms
        const start = performance.now();

        function step(now) {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          const value = Math.round(easeOutQuart(progress) * target);
          el.textContent = value + suffix;
          if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
      });
    },
    { threshold: 0.5 }
  );

  counters.forEach(el => counterObserver.observe(el));
}

/* ────────────────────────────────────────────────────────────
 *  §4  Navigation Tabs
 * ──────────────────────────────────────────────────────────── */

function initTabs() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active from all tabs
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      // Set clicked tab active
      tab.classList.add('active');

      const target = tab.getAttribute('data-tab');
      // Hide all panes, show target
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
      });
      const targetPane = document.getElementById(target);
      if (targetPane) {
        targetPane.classList.add('active');
        // Re-observe reveal animations in newly visible pane
        reobserveRevealElements(targetPane);
      }
    });
  });
}

/* ────────────────────────────────────────────────────────────
 *  §5  Feature Chip Clicks
 * ──────────────────────────────────────────────────────────── */

function initFeatureChips() {
  document.querySelectorAll('.chip[data-prompt]').forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) executeVoiceQuery(prompt);
    });
  });
}

/** Central dispatcher for text-based queries (from chips, commands, etc.) */
function executeVoiceQuery(query) {
  if (!query || !query.trim()) return;
  executeWebAnalysis(query.trim());
}

/* ────────────────────────────────────────────────────────────
 *  §6  Web Audio Waveform Visualizer
 * ──────────────────────────────────────────────────────────── */

function initAudioContext() {
  return new Promise(async (resolve, reject) => {
    try {
      if (state.audioContext && state.audioContext.state !== 'closed') {
        resolve();
        return;
      }

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      state.audioContext = new AudioCtx();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      state.micStream = stream;

      state.analyser = state.audioContext.createAnalyser();
      state.analyser.fftSize = 256;

      const source = state.audioContext.createMediaStreamSource(stream);
      source.connect(state.analyser);

      drawVisualizer();
      resolve();
    } catch (err) {
      console.error('[Audio] Failed to init audio context:', err);
      reject(err);
    }
  });
}

function drawVisualizer() {
  const canvas = document.getElementById('waveformCanvas');
  if (!canvas || !state.analyser) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const overlay = document.getElementById('visualizerOverlay');

  const bufferLength = state.analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function draw() {
    requestAnimationFrame(draw);

    state.analyser.getByteFrequencyData(dataArray);

    // Responsive canvas sizing
    const rect = canvas.parentElement
      ? canvas.parentElement.getBoundingClientRect()
      : canvas.getBoundingClientRect();
    if (canvas.width !== Math.floor(rect.width) || canvas.height !== Math.floor(rect.height)) {
      canvas.width = Math.floor(rect.width);
      canvas.height = Math.floor(rect.height);
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 1.5;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i];
      const barHeight = (v / 255) * canvas.height * 0.85;

      if (state.isListening) {
        // Red spectrum when listening
        const r = 200 + Math.floor((v / 255) * 55);
        const g = 30 + Math.floor((v / 255) * 30);
        const b = 30;
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      } else {
        // Indigo spectrum
        const r = 60 + Math.floor((v / 255) * 19);
        const g = 50 + Math.floor((v / 255) * 20);
        const b = 180 + Math.floor((v / 255) * 49);
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      }

      ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
      x += barWidth;
    }

    // Update acoustic meters from audio data
    updateAcousticMeters(dataArray, bufferLength);

    // Hide overlay once actively receiving audio
    if (overlay && overlay.style.display !== 'none') {
      const hasSignal = dataArray.some(v => v > 10);
      if (hasSignal) {
        overlay.style.display = 'none';
      }
    }
  }

  draw();
}

function updateAcousticMeters(dataArray, bufferLength) {
  // Pitch — weighted towards lower frequencies
  const meterPitch = document.getElementById('meterPitch');
  // Timbre — mid-range frequencies
  const meterTimbre = document.getElementById('meterTimbre');
  // Energy — overall RMS-like value
  const meterEnergy = document.getElementById('meterEnergy');

  if (!meterPitch && !meterTimbre && !meterEnergy) return;

  let lowSum = 0;
  let midSum = 0;
  let totalSum = 0;
  const quarter = Math.floor(bufferLength / 4);

  for (let i = 0; i < bufferLength; i++) {
    const v = dataArray[i];
    totalSum += v;
    if (i < quarter) lowSum += v;
    else if (i < quarter * 3) midSum += v;
  }

  const pitchPct = Math.min(100, Math.round((lowSum / (quarter * 255)) * 100));
  const timbrePct = Math.min(100, Math.round((midSum / (quarter * 2 * 255)) * 100));
  const energyPct = Math.min(100, Math.round((totalSum / (bufferLength * 255)) * 100));

  if (meterPitch) meterPitch.style.width = pitchPct + '%';
  if (meterTimbre) meterTimbre.style.width = timbrePct + '%';
  if (meterEnergy) meterEnergy.style.width = energyPct + '%';
}

/* ────────────────────────────────────────────────────────────
 *  §7  Speech Recognition (Web Speech API)
 * ──────────────────────────────────────────────────────────── */

function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn('[Speech] Web Speech API not supported');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  const liveTranscript = document.getElementById('liveTranscript');
  const confidenceBadge = document.getElementById('confidenceBadge');
  const engineBadge = document.getElementById('engineBadge');

  recognition.onresult = (event) => {
    let interimText = '';
    let finalText = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      const transcript = result[0].transcript;

      if (result.isFinal) {
        finalText += transcript;
        // Update confidence
        const confidence = Math.round((result[0].confidence || 0) * 100);
        if (confidenceBadge) confidenceBadge.textContent = confidence + '%';
      } else {
        interimText += transcript;
      }
    }

    // Show live transcript (prefer interim, show final when done)
    if (liveTranscript) {
      liveTranscript.textContent = interimText || finalText || '…';
    }

    if (finalText) {
      handleVoiceCommand(finalText.trim());
    }
  };

  recognition.onerror = (event) => {
    console.error('[Speech] Recognition error:', event.error);
    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
      state.isListening = false;
      updateMicUI();
    }
  };

  recognition.onend = () => {
    // Auto-restart if still supposed to be listening
    if (state.isListening) {
      try {
        recognition.start();
      } catch (_) {
        /* already started */
      }
    }
  };

  state.recognition = recognition;

  if (engineBadge) engineBadge.textContent = state.currentEngine;

  // Mic button
  const micBtn = document.getElementById('micBtn');
  if (micBtn) micBtn.addEventListener('click', toggleListening);
}

function toggleListening() {
  if (state.isListening) {
    stopListening();
  } else {
    startListening();
  }
}

async function startListening() {
  try {
    await initAudioContext();
  } catch (_) {
    /* audio init may fail — speech recognition can still work */
  }

  if (state.recognition) {
    try {
      state.recognition.start();
    } catch (_) {
      /* may already be started */
    }
  }

  // Also prepare MediaRecorder for server-side streaming
  if (state.micStream && !state.mediaRecorder) {
    try {
      state.mediaRecorder = new MediaRecorder(state.micStream);
      state.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) state.audioChunks.push(e.data);
      };
    } catch (err) {
      console.warn('[Audio] MediaRecorder init failed:', err);
    }
  }

  state.isListening = true;
  updateMicUI();
}

function stopListening() {
  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (_) {
      /* already stopped */
    }
  }
  state.isListening = false;
  updateMicUI();
}

function updateMicUI() {
  const micBtn = document.getElementById('micBtn');
  const micStatusText = document.getElementById('micStatusText');
  const visualizerStateText = document.getElementById('visualizerStateText');
  const headerEngineLabel = document.getElementById('headerEngineLabel');

  if (micBtn) {
    micBtn.classList.toggle('listening', state.isListening);
    micBtn.setAttribute('aria-pressed', String(state.isListening));
  }
  if (micStatusText) {
    micStatusText.textContent = state.isListening ? 'Listening…' : 'Click to start';
  }
  if (visualizerStateText) {
    visualizerStateText.textContent = state.isListening ? 'LIVE' : 'STANDBY';
  }
  if (headerEngineLabel) {
    headerEngineLabel.textContent = state.currentEngine;
  }
}

/* ────────────────────────────────────────────────────────────
 *  §8  Command Router
 * ──────────────────────────────────────────────────────────── */

function handleVoiceCommand(raw) {
  if (!raw) return;
  // Strip wake word "ether" (case insensitive, at start)
  let cmd = raw.replace(/^ether[\s,.:!?]*/i, '').trim();
  if (!cmd) return;

  const lower = cmd.toLowerCase();

  // Web analysis triggers
  if (
    lower.startsWith('analyze') ||
    lower.startsWith('analyse') ||
    lower.startsWith('search') ||
    lower.startsWith('find') ||
    lower.startsWith('what is') ||
    lower.startsWith('who is')
  ) {
    executeWebAnalysis(cmd);
    return;
  }

  // Everything else → web analysis as fallback (no Spotify)
  executeWebAnalysis(cmd);
}

/* ────────────────────────────────────────────────────────────
 *  §9  Web Analysis Engine
 * ──────────────────────────────────────────────────────────── */

async function executeWebAnalysis(query) {
  if (!query) return;

  const responseSummary = document.getElementById('responseSummary');
  const responseDetails = document.getElementById('responseDetails');

  if (responseSummary) responseSummary.textContent = 'Analyzing…';
  if (responseDetails) responseDetails.innerHTML = '';

  try {
    const res = await fetch('/api/analyze-web', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();

    // Update console tab
    if (responseSummary) {
      responseSummary.textContent = data.summary || 'No summary available.';
    }
    if (responseDetails && Array.isArray(data.details)) {
      responseDetails.innerHTML = data.details
        .map(d => `<li>${escapeHTML(d)}</li>`)
        .join('');
    } else if (responseDetails && data.details) {
      responseDetails.innerHTML = `<li>${escapeHTML(String(data.details))}</li>`;
    }

    // Speak the summary
    speakText(data.summary || '');

    // Render in web results tab
    renderWebResults(data);
  } catch (err) {
    console.error('[Web] Analysis failed:', err);
    if (responseSummary) responseSummary.textContent = 'Analysis failed. Please try again.';
  }
}

function renderWebResults(data) {
  const container = document.getElementById('webResultsContainer');
  const emptyState = document.getElementById('webEmptyState');
  if (!container) return;

  // Hide empty state
  if (emptyState) emptyState.style.display = 'none';

  // Build synthesis card
  const card = document.createElement('div');
  card.className = 'glass-card web-result-card';

  // Summary
  const summaryEl = document.createElement('p');
  summaryEl.className = 'result-summary';
  summaryEl.textContent = data.summary || 'No summary.';
  card.appendChild(summaryEl);

  // Takeaways
  if (Array.isArray(data.takeaways) && data.takeaways.length) {
    const list = document.createElement('ul');
    list.className = 'result-takeaways';
    data.takeaways.forEach(t => {
      const li = document.createElement('li');
      li.innerHTML = `<span class="checkmark">✓</span> ${escapeHTML(t)}`;
      list.appendChild(li);
    });
    card.appendChild(list);
  } else if (Array.isArray(data.details) && data.details.length) {
    // Fallback to details as takeaways
    const list = document.createElement('ul');
    list.className = 'result-takeaways';
    data.details.forEach(d => {
      const li = document.createElement('li');
      li.innerHTML = `<span class="checkmark">✓</span> ${escapeHTML(d)}`;
      list.appendChild(li);
    });
    card.appendChild(list);
  }

  // Source pills
  if (Array.isArray(data.sources) && data.sources.length) {
    const pillsWrap = document.createElement('div');
    pillsWrap.className = 'source-pills';
    data.sources.forEach(src => {
      const pill = document.createElement('a');
      pill.className = 'source-pill';
      pill.href = src.url || '#';
      pill.target = '_blank';
      pill.rel = 'noopener noreferrer';
      pill.textContent = src.title || src.url || 'Source';
      pillsWrap.appendChild(pill);
    });
    card.appendChild(pillsWrap);
  }

  // Timestamp
  const ts = document.createElement('time');
  ts.className = 'result-timestamp';
  ts.textContent = new Date().toLocaleTimeString();
  card.appendChild(ts);

  // Prepend (newest first)
  container.prepend(card);
}

function initWebSearch() {
  const webSearchBtn = document.getElementById('webSearchBtn');
  const webQueryInput = document.getElementById('webQueryInput');

  function triggerSearch() {
    if (!webQueryInput) return;
    const query = webQueryInput.value.trim();
    if (query) {
      executeWebAnalysis(query);
      webQueryInput.value = '';
    }
  }

  if (webSearchBtn) webSearchBtn.addEventListener('click', triggerSearch);
  if (webQueryInput) {
    webQueryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerSearch();
      }
    });
  }
}

/* ────────────────────────────────────────────────────────────
 *  §10  Voice Training Studio
 * ──────────────────────────────────────────────────────────── */

function initVoiceTraining() {
  const recordSampleBtn = document.getElementById('recordSampleBtn');
  const recordSampleBtnText = document.getElementById('recordSampleBtnText');
  const resetEnrollmentBtn = document.getElementById('resetEnrollmentBtn');
  const enrollmentStepText = document.getElementById('enrollmentStepText');
  const verifyVoiceBtn = document.getElementById('verifyVoiceBtn');
  const verifyResult = document.getElementById('verifyResult');
  const refreshProfilesBtn = document.getElementById('refreshProfilesBtn');

  // Record sample button
  if (recordSampleBtn) {
    recordSampleBtn.addEventListener('click', async () => {
      if (state.isRecordingSample) return;
      state.isRecordingSample = true;

      if (recordSampleBtnText) recordSampleBtnText.textContent = 'Recording…';
      recordSampleBtn.disabled = true;

      try {
        await initAudioContext();

        const recorder = new MediaRecorder(state.micStream);
        const chunks = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
        };

        recorder.onstop = () => {
          const blob = new Blob(chunks, { type: 'audio/webm' });
          state.enrollmentSamples.push(blob);

          if (state.enrollmentStep < 3) {
            state.enrollmentStep++;
            updateEnrollmentUI();
          } else {
            // All 3 samples collected
            updateEnrollmentUI();
            submitVoiceEnrollment();
          }

          state.isRecordingSample = false;
          recordSampleBtn.disabled = false;
          if (recordSampleBtnText) recordSampleBtnText.textContent = 'Record Sample';
        };

        recorder.start();
        // Record for 3.2 seconds
        setTimeout(() => {
          if (recorder.state === 'recording') recorder.stop();
        }, 3200);
      } catch (err) {
        console.error('[Training] Record sample failed:', err);
        state.isRecordingSample = false;
        recordSampleBtn.disabled = false;
        if (recordSampleBtnText) recordSampleBtnText.textContent = 'Record Sample';
      }
    });
  }

  // Reset enrollment
  if (resetEnrollmentBtn) {
    resetEnrollmentBtn.addEventListener('click', resetEnrollment);
  }

  // Verify voice button
  if (verifyVoiceBtn) {
    verifyVoiceBtn.addEventListener('click', async () => {
      if (verifyResult) verifyResult.textContent = 'Recording verification sample…';
      verifyVoiceBtn.disabled = true;

      try {
        await initAudioContext();

        const recorder = new MediaRecorder(state.micStream);
        const chunks = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
        };

        recorder.onstop = async () => {
          const blob = new Blob(chunks, { type: 'audio/webm' });
          if (verifyResult) verifyResult.textContent = 'Verifying…';

          try {
            const formData = new FormData();
            formData.append('audio', blob, 'verify.webm');
            const res = await fetch('/api/verify-voice', {
              method: 'POST',
              body: formData
            });
            const data = await res.json();

            if (verifyResult) {
              verifyResult.textContent = data.match
                ? `✓ Match: ${data.speaker || 'Identified'} (${Math.round((data.confidence || 0) * 100)}%)`
                : `✗ No match found (${Math.round((data.confidence || 0) * 100)}% confidence)`;
              verifyResult.className = data.match ? 'verify-match' : 'verify-nomatch';
            }
          } catch (err) {
            console.error('[Training] Verification failed:', err);
            if (verifyResult) verifyResult.textContent = 'Verification failed.';
          }
          verifyVoiceBtn.disabled = false;
        };

        recorder.start();
        // Record for 2.8 seconds
        setTimeout(() => {
          if (recorder.state === 'recording') recorder.stop();
        }, 2800);
      } catch (err) {
        console.error('[Training] Verify init failed:', err);
        verifyVoiceBtn.disabled = false;
        if (verifyResult) verifyResult.textContent = 'Microphone access failed.';
      }
    });
  }

  // Refresh profiles
  if (refreshProfilesBtn) {
    refreshProfilesBtn.addEventListener('click', loadVoiceProfiles);
  }

  function updateEnrollmentUI() {
    if (enrollmentStepText) {
      enrollmentStepText.textContent = `Step ${state.enrollmentStep} of 3`;
    }
  }
}

function resetEnrollment() {
  state.enrollmentStep = 1;
  state.enrollmentSamples = [];
  const enrollmentStepText = document.getElementById('enrollmentStepText');
  if (enrollmentStepText) enrollmentStepText.textContent = 'Step 1 of 3';
}

async function submitVoiceEnrollment() {
  const speakerNameInput = document.getElementById('speakerNameInput');
  const enrollmentStepText = document.getElementById('enrollmentStepText');
  const name = speakerNameInput ? speakerNameInput.value.trim() : '';

  if (!name) {
    if (enrollmentStepText) enrollmentStepText.textContent = 'Please enter a speaker name.';
    resetEnrollment();
    return;
  }

  if (enrollmentStepText) enrollmentStepText.textContent = 'Submitting…';

  try {
    const formData = new FormData();
    formData.append('name', name);
    state.enrollmentSamples.forEach((blob, i) => {
      formData.append(`sample_${i}`, blob, `sample_${i}.webm`);
    });

    const res = await fetch('/api/train-voice', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    if (enrollmentStepText) {
      enrollmentStepText.textContent = data.message || 'Enrollment complete!';
    }

    // Refresh profiles
    loadVoiceProfiles();
  } catch (err) {
    console.error('[Training] Enrollment submission failed:', err);
    if (enrollmentStepText) enrollmentStepText.textContent = 'Enrollment failed.';
  }

  // Reset for next enrollment
  state.enrollmentSamples = [];
  state.enrollmentStep = 1;
}

async function loadVoiceProfiles() {
  const profilesContainer = document.getElementById('profilesContainer');
  if (!profilesContainer) return;

  try {
    const res = await fetch('/api/voice-profiles');
    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const profiles = await res.json();

    if (!Array.isArray(profiles) || profiles.length === 0) {
      profilesContainer.innerHTML =
        '<p class="empty-text">No voice profiles enrolled yet.</p>';
      return;
    }

    profilesContainer.innerHTML = profiles
      .map(
        (p) => `
        <div class="profile-item glass-card" data-profile-id="${escapeAttr(p.id || '')}">
          <span class="profile-name">${escapeHTML(p.name || 'Unknown')}</span>
          <span class="profile-meta">${escapeHTML(p.samples ? p.samples + ' samples' : '')}</span>
        </div>`
      )
      .join('');
  } catch (err) {
    console.error('[Training] Failed to load profiles:', err);
    profilesContainer.innerHTML =
      '<p class="empty-text">Failed to load profiles.</p>';
  }
}

/* ────────────────────────────────────────────────────────────
 *  §11  Text-to-Speech (TTS)
 * ──────────────────────────────────────────────────────────── */

function speakText(text) {
  if (!text) return;

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    u.pitch = 1.0;
    window.speechSynthesis.speak(u);
  } else {
    // Fallback to backend TTS
    fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    }).catch(err => console.error('[TTS] Backend speak failed:', err));
  }
}

function initTTS() {
  const speakResponseBtn = document.getElementById('speakResponseBtn');
  const responseSummary = document.getElementById('responseSummary');

  if (speakResponseBtn) {
    speakResponseBtn.addEventListener('click', () => {
      if (responseSummary) speakText(responseSummary.textContent);
    });
  }
}

/* ────────────────────────────────────────────────────────────
 *  §12  Settings
 * ──────────────────────────────────────────────────────────── */

function initSettings() {
  const engineSelect = document.getElementById('engineSelect');
  const whisperModelSelect = document.getElementById('whisperModelSelect');
  const energyThresholdSlider = document.getElementById('energyThresholdSlider');
  const energyVal = document.getElementById('energyVal');
  const wakeSensitivitySlider = document.getElementById('wakeSensitivitySlider');
  const wakeVal = document.getElementById('wakeVal');
  const noiseCalibrationBtn = document.getElementById('noiseCalibrationBtn');
  const saveSettingsBtn = document.getElementById('saveSettingsBtn');

  // Engine select → show/hide whisper model group
  if (engineSelect) {
    engineSelect.addEventListener('change', () => {
      state.currentEngine = engineSelect.value;
      const whisperModelGroup = document.getElementById('whisperModelGroup');
      if (whisperModelGroup) {
        whisperModelGroup.style.display =
          state.currentEngine === 'whisper' ? '' : 'none';
      }

      // Update badges
      const engineBadge = document.getElementById('engineBadge');
      if (engineBadge) engineBadge.textContent = state.currentEngine;
      const headerEngineLabel = document.getElementById('headerEngineLabel');
      if (headerEngineLabel) headerEngineLabel.textContent = state.currentEngine;
    });
  }

  // Energy threshold slider
  if (energyThresholdSlider && energyVal) {
    energyThresholdSlider.addEventListener('input', () => {
      energyVal.textContent = energyThresholdSlider.value;
    });
  }

  // Wake sensitivity slider
  if (wakeSensitivitySlider && wakeVal) {
    wakeSensitivitySlider.addEventListener('input', () => {
      wakeVal.textContent = wakeSensitivitySlider.value + '%';
    });
  }

  // Noise calibration
  if (noiseCalibrationBtn) {
    noiseCalibrationBtn.addEventListener('click', async () => {
      noiseCalibrationBtn.disabled = true;
      noiseCalibrationBtn.textContent = 'Calibrating…';

      try {
        const res = await fetch('/api/calibrate-noise', { method: 'POST' });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();

        if (energyThresholdSlider && data.threshold != null) {
          energyThresholdSlider.value = data.threshold;
          if (energyVal) energyVal.textContent = data.threshold;
        }

        noiseCalibrationBtn.textContent = 'Calibrated ✓';
        setTimeout(() => {
          noiseCalibrationBtn.textContent = 'Calibrate Noise';
        }, 2000);
      } catch (err) {
        console.error('[Settings] Calibration failed:', err);
        noiseCalibrationBtn.textContent = 'Calibration Failed';
        setTimeout(() => {
          noiseCalibrationBtn.textContent = 'Calibrate Noise';
        }, 2000);
      }
      noiseCalibrationBtn.disabled = false;
    });
  }

  // Save settings
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', async () => {
      saveSettingsBtn.disabled = true;
      saveSettingsBtn.textContent = 'Saving…';

      const payload = {
        engine: engineSelect ? engineSelect.value : state.currentEngine,
        whisperModel: whisperModelSelect
          ? whisperModelSelect.value
          : state.whisperModel,
        energyThreshold: energyThresholdSlider
          ? Number(energyThresholdSlider.value)
          : 300,
        wakeSensitivity: wakeSensitivitySlider
          ? Number(wakeSensitivitySlider.value)
          : 50
      };

      try {
        const res = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        state.currentEngine = payload.engine;
        state.whisperModel = payload.whisperModel;

        saveSettingsBtn.textContent = 'Saved ✓';
        setTimeout(() => {
          saveSettingsBtn.textContent = 'Save Settings';
        }, 2000);
      } catch (err) {
        console.error('[Settings] Save failed:', err);
        saveSettingsBtn.textContent = 'Save Failed';
        setTimeout(() => {
          saveSettingsBtn.textContent = 'Save Settings';
        }, 2000);
      }
      saveSettingsBtn.disabled = false;
    });
  }
}

/* ────────────────────────────────────────────────────────────
 *  §13  Utility Helpers
 * ──────────────────────────────────────────────────────────── */

function escapeHTML(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

function escapeAttr(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/* ────────────────────────────────────────────────────────────
 *  §14  Initialization
 * ──────────────────────────────────────────────────────────── */

window.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initScrollReveal();
  initStatCounters();
  initTabs();
  initFeatureChips();
  setupSpeechRecognition();
  initWebSearch();
  initVoiceTraining();
  initTTS();
  initSettings();
  loadVoiceProfiles();
});
