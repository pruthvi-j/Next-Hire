/**
 * NEXT HIRE - Voice Mock Interview & Question Engine Controller (Phases 5 & 6)
 * MCA Academic Project
 */

let activeInterview = null;
let currentQuestionIndex = 0; // 0-based index
let recognition = null;
let isRecording = false;
let isSpeaking = false;
let speechSynth = window.speechSynthesis || null;

document.addEventListener('DOMContentLoaded', async () => {
  // Session check
  const user = await checkAuth(true);
  if (!user) return;

  initSpeechRecognition();
  await loadSetupOptions();
  bindEvents();
});

/**
 * Initializes browser Web Speech Recognition with fallback
 */
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;

  if (!SpeechRecognition) {
    console.warn('[Web Speech API] Speech recognition is not supported in this browser.');
    const notice = document.getElementById('mic-permission-notice');
    if (notice) {
      notice.textContent = 'ℹ️ Speech recognition is not supported in this browser. You can type your answer directly.';
      notice.style.display = 'block';
    }
    return;
  }

  try {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isRecording = true;
      setVoiceStatus('listening');
      const micBtn = document.getElementById('mic-toggle-btn');
      if (micBtn) micBtn.classList.add('recording');
      setWaveAnimation('listening');
      const hint = document.getElementById('mic-action-hint');
      if (hint) hint.textContent = 'Listening... Click microphone to stop';
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      const transcriptBox = document.getElementById('answer-transcript');
      if (transcriptBox) {
        if (finalTranscript) {
          transcriptBox.value = (transcriptBox.value + ' ' + finalTranscript).trim();
          setVoiceStatus('captured');
        } else if (interimTranscript) {
          setVoiceStatus('processing');
        }
      }
    };

    recognition.onerror = (event) => {
      console.warn('[Web Speech API] Error:', event.error);
      const notice = document.getElementById('mic-permission-notice');
      if (event.error === 'not-allowed') {
        if (notice) {
          notice.textContent = '⚠️ Microphone access was denied. Please allow microphone permissions or type your answer directly.';
          notice.style.display = 'block';
        }
        showToast('Microphone access denied. You can type your answer.', 'error');
      } else if (event.error !== 'no-speech') {
        showToast(`Voice recognition error: ${event.error}`, 'error');
      }
      stopVoiceRecording();
    };

    recognition.onend = () => {
      stopVoiceRecording();
    };
  } catch (err) {
    console.error('Failed to construct SpeechRecognition:', err);
  }
}

/**
 * Toggles microphone recording
 */
function toggleVoiceRecording() {
  if (!recognition) {
    showToast('Speech recognition unavailable. Please type your response.', 'info');
    document.getElementById('answer-transcript').focus();
    return;
  }

  if (isRecording) {
    try {
      recognition.stop();
    } catch (e) {
      console.warn(e);
    }
    stopVoiceRecording();
  } else {
    try {
      document.getElementById('mic-permission-notice').style.display = 'none';
      recognition.start();
    } catch (err) {
      console.warn('Error starting speech recognition:', err);
      // If already started, stop then restart
      try {
        recognition.stop();
        setTimeout(() => recognition.start(), 200);
      } catch (e) {
        console.error(e);
      }
    }
  }
}

function stopVoiceRecording() {
  isRecording = false;
  const micBtn = document.getElementById('mic-toggle-btn');
  if (micBtn) micBtn.classList.remove('recording');
  setWaveAnimation('off');
  const hint = document.getElementById('mic-action-hint');
  if (hint) hint.textContent = 'Click microphone to begin speaking';

  const transcriptBox = document.getElementById('answer-transcript');
  if (transcriptBox && transcriptBox.value.trim().length > 0) {
    setVoiceStatus('captured');
  } else {
    setVoiceStatus('ready');
  }
}

/**
 * Sets visual voice status pill: 'ready', 'listening', 'processing', 'captured'
 */
function setVoiceStatus(status) {
  const pill = document.getElementById('voice-status-pill');
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  if (!pill) return;

  pill.className = `voice-status-indicator status-${status}`;

  if (status === 'listening') {
    dot.textContent = '🔴';
    label.textContent = 'Listening';
  } else if (status === 'processing') {
    dot.textContent = '🟡';
    label.textContent = 'Processing';
  } else if (status === 'captured') {
    dot.textContent = '🟢';
    label.textContent = 'Answer captured';
  } else {
    dot.textContent = '⚪';
    label.textContent = 'Ready';
  }
}

/**
 * Sets waveform animation states: 'speaking', 'listening', 'off'
 */
function setWaveAnimation(mode) {
  const bars = document.querySelectorAll('.wave-bar');
  bars.forEach(bar => {
    bar.className = 'wave-bar';
    if (mode === 'speaking') {
      bar.classList.add('speaking');
    } else if (mode === 'listening') {
      bar.classList.add('listening');
    }
  });
}

/**
 * Text-to-Speech synthesizer reading the current question
 */
function speakCurrentQuestion() {
  if (!speechSynth) {
    showToast('Text-to-Speech is not supported in this browser.', 'info');
    return;
  }

  const questionEl = document.getElementById('question-text-display');
  const text = questionEl ? questionEl.textContent.trim() : '';
  if (!text) return;

  if (speechSynth.speaking) {
    speechSynth.cancel();
    setWaveAnimation('off');
    isSpeaking = false;
    document.getElementById('speak-question-btn').innerHTML = '<span>🔊 Listen Question</span>';
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95; // Clear academic pacing
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    isSpeaking = true;
    setWaveAnimation('speaking');
    document.getElementById('speak-question-btn').innerHTML = '<span>⏹ Stop Audio</span>';
  };

  utterance.onend = () => {
    isSpeaking = false;
    setWaveAnimation('off');
    document.getElementById('speak-question-btn').innerHTML = '<span>🔊 Listen Question</span>';
  };

  utterance.onerror = () => {
    isSpeaking = false;
    setWaveAnimation('off');
    document.getElementById('speak-question-btn').innerHTML = '<span>🔊 Listen Question</span>';
  };

  speechSynth.speak(utterance);
}

/**
 * Loads interview setup options from GET /api/interview/setup-options
 */
async function loadSetupOptions() {
  try {
    const response = await fetch(`${API_BASE}/api/interview/setup-options`, {
      method: 'GET',
      credentials: 'include'
    });

    if (response.ok) {
      const result = await response.json();
      if (result.status === 'success' && result.data) {
        const roles = result.data.roles || [];
        const roleSelect = document.getElementById('setup-role-select');
        if (roleSelect && roles.length > 0) {
          roleSelect.innerHTML = '';
          roles.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = `${r.role_name} (${r.skills.length} skills)`;
            roleSelect.appendChild(opt);
          });

          // Pre-select role if user has a selection from Phase 4
          if (result.data.selected_role) {
            roleSelect.value = result.data.selected_role.role_id;
          }
        }
      }
    }
  } catch (err) {
    console.error('Error fetching setup options:', err);
  }
}

/**
 * Launches the interview session via POST /api/interview/start
 */
async function startInterviewSession(roleId, difficulty, numQuestions) {
  const startBtn = document.getElementById('start-chamber-btn');
  if (startBtn) {
    startBtn.disabled = true;
    startBtn.innerHTML = '<span>Querying MySQL Question Bank...</span>';
  }

  try {
    const response = await fetch(`${API_BASE}/api/interview/start`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        role_id: roleId,
        difficulty: difficulty,
        num_questions: numQuestions
      })
    });

    const result = await response.json();

    if (response.ok && result.status === 'success') {
      activeInterview = result.data;
      currentQuestionIndex = 0;

      // Switch views: Hide setup, show chamber
      document.getElementById('setup-section').style.display = 'none';
      document.getElementById('completed-section').style.display = 'none';
      document.getElementById('chamber-section').style.display = 'block';

      // Update meta header
      document.getElementById('chamber-role-title').textContent = activeInterview.role_name;
      document.getElementById('chamber-diff-badge').textContent = activeInterview.difficulty;

      renderCurrentQuestion();
      showToast('Interview chamber initialized with unique questions from MySQL.', 'success');
    } else {
      showAlert('chamber-alert', result.message || 'Failed to initialize mock interview.', 'danger');
    }
  } catch (err) {
    console.error('Interview launch error:', err);
    showAlert('chamber-alert', 'Network error while connecting to question engine.', 'danger');
  } finally {
    if (startBtn) {
      startBtn.disabled = false;
      startBtn.innerHTML = '<span>Start Technical Voice Interview &rarr;</span>';
    }
  }
}

/**
 * Renders the active question in the chamber
 */
function renderCurrentQuestion() {
  if (!activeInterview || !activeInterview.questions || activeInterview.questions.length === 0) return;

  const total = activeInterview.questions.length;
  const current = activeInterview.questions[currentQuestionIndex];
  if (!current) return;

  // Stop any previous speech
  if (speechSynth && speechSynth.speaking) {
    speechSynth.cancel();
  }
  stopVoiceRecording();

  // Progress update
  document.getElementById('question-progress-text').textContent = `Question ${currentQuestionIndex + 1} / ${total}`;
  const progressPct = Math.round(((currentQuestionIndex + 1) / total) * 100);
  document.getElementById('session-progress-bar').style.width = `${progressPct}%`;

  // Question details
  document.getElementById('q-lang-badge').textContent = current.language || 'General';
  document.getElementById('q-topic-badge').textContent = current.topic || 'Core Concept';
  document.getElementById('q-code-label').textContent = `Code: ${current.question_code}`;
  document.getElementById('question-text-display').textContent = current.question_text;

  // Clear or load answer
  const transcriptBox = document.getElementById('answer-transcript');
  transcriptBox.value = current.answer_text || '';
  setVoiceStatus(current.answer_text ? 'captured' : 'ready');

  // Update button text if last question
  const nextBtn = document.getElementById('next-question-btn');
  if (nextBtn) {
    if (currentQuestionIndex === total - 1) {
      nextBtn.innerHTML = '<span>Complete Interview &check;</span>';
    } else {
      nextBtn.innerHTML = '<span>Next Question &rarr;</span>';
    }
  }

  // Scroll to question top
  document.getElementById('chamber-section').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Saves candidate answer for the current question via POST /api/interview/<id>/answer
 */
async function saveCurrentAnswer(silent = false) {
  if (!activeInterview) return false;

  const current = activeInterview.questions[currentQuestionIndex];
  if (!current) return false;

  const transcriptBox = document.getElementById('answer-transcript');
  const answerText = transcriptBox ? transcriptBox.value.trim() : '';

  try {
    const response = await fetch(`${API_BASE}/api/interview/${activeInterview.interview_id}/answer`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        question_id: current.id || current.question_id,
        answer_text: answerText
      })
    });

    const result = await response.json();
    if (response.ok && result.status === 'success') {
      current.answer_text = answerText;
      if (!silent) {
        showToast('Answer successfully stored in database.', 'success');
      }
      return true;
    } else {
      if (!silent) {
        showAlert('chamber-alert', result.message || 'Could not save answer.', 'danger');
      }
      return false;
    }
  } catch (err) {
    console.error('Answer saving error:', err);
    if (!silent) {
      showAlert('chamber-alert', 'Network error saving answer.', 'danger');
    }
    return false;
  }
}

/**
 * Advances to the next question or completes the interview
 */
async function handleNextQuestion() {
  // Auto-save current answer if typed
  await saveCurrentAnswer(true);

  const total = activeInterview.questions.length;
  if (currentQuestionIndex < total - 1) {
    currentQuestionIndex++;
    renderCurrentQuestion();
  } else {
    // Complete interview
    await completeInterviewSession();
  }
}

/**
 * Finalizes the interview via POST /api/interview/<id>/complete
 */
async function completeInterviewSession() {
  if (!activeInterview) return;

  try {
    await fetch(`${API_BASE}/api/interview/${activeInterview.interview_id}/complete`, {
      method: 'POST',
      credentials: 'include'
    });
  } catch (e) {
    console.warn(e);
  }

  if (speechSynth && speechSynth.speaking) {
    speechSynth.cancel();
  }
  stopVoiceRecording();

  document.getElementById('chamber-section').style.display = 'none';
  const completedSection = document.getElementById('completed-section');
  if (completedSection) {
    document.getElementById('completed-total-q').textContent = `${activeInterview.questions.length} / ${activeInterview.questions.length}`;
    document.getElementById('completed-role-name').textContent = activeInterview.role_name;
    const viewResLink = document.getElementById('view-results-link');
    if (viewResLink && activeInterview) {
      viewResLink.href = `result.html?id=${activeInterview.interview_id}`;
    }
    completedSection.style.display = 'block';
    completedSection.scrollIntoView({ behavior: 'smooth' });
  }
  showToast('Mock Interview concluded & evaluated successfully!', 'success');
}

/**
 * Binds UI listeners
 */
function bindEvents() {
  // Setup Form Submit
  const setupForm = document.getElementById('interview-setup-form');
  if (setupForm) {
    setupForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const roleId = document.getElementById('setup-role-select').value;
      const difficulty = document.getElementById('setup-difficulty-select').value;
      const numQuestions = document.getElementById('setup-questions-count').value;
      startInterviewSession(roleId, difficulty, numQuestions);
    });
  }

  // Microphone toggle button
  const micBtn = document.getElementById('mic-toggle-btn');
  if (micBtn) {
    micBtn.addEventListener('click', toggleVoiceRecording);
  }

  // Speak question button
  const speakBtn = document.getElementById('speak-question-btn');
  if (speakBtn) {
    speakBtn.addEventListener('click', speakCurrentQuestion);
  }

  // Clear transcript button
  const clearBtn = document.getElementById('clear-transcript-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      const transcriptBox = document.getElementById('answer-transcript');
      if (transcriptBox) {
        transcriptBox.value = '';
        setVoiceStatus('ready');
      }
    });
  }

  // Save answer button
  const saveBtn = document.getElementById('submit-answer-btn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => saveCurrentAnswer(false));
  }

  // Next question button
  const nextBtn = document.getElementById('next-question-btn');
  if (nextBtn) {
    nextBtn.addEventListener('click', handleNextQuestion);
  }

  // Exit interview button
  const exitBtn = document.getElementById('exit-interview-btn');
  if (exitBtn) {
    exitBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to exit the interview chamber? Your saved answers will be preserved.')) {
        if (speechSynth && speechSynth.speaking) speechSynth.cancel();
        stopVoiceRecording();
        document.getElementById('chamber-section').style.display = 'none';
        document.getElementById('setup-section').style.display = 'block';
      }
    });
  }

  // Retake button
  const retakeBtn = document.getElementById('retake-interview-btn');
  if (retakeBtn) {
    retakeBtn.addEventListener('click', () => {
      document.getElementById('completed-section').style.display = 'none';
      document.getElementById('setup-section').style.display = 'block';
    });
  }
}
