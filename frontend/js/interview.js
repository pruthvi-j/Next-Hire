/**
 * NEXT HIRE - Conversational Siri-Style AI Voice Interview Chamber Controller
 * MCA Academic Project - Real Two-Way Voice Conversation (Phases 5 & 6)
 */

// Voice State Enum
const VoiceState = {
  IDLE: 'idle',
  SPEAKING: 'speaking',
  LISTENING: 'listening',
  THINKING: 'thinking'
};

let currentVoiceState = VoiceState.IDLE;
let candidateName = 'Candidate';
let activeInterview = null;
let currentQuestionIndex = 0; // 0-based index
let isGreetingReadyCheck = false;

// Speech Recognition (STT)
let recognition = null;
let isRecording = false;

// Speech Synthesis (TTS)
let speechSynth = window.speechSynthesis || null;
let activeUtterance = null;
let isSpeaking = false;
let preferredVoice = null;
let availableVoices = [];

// Audio Context & Analyser for Real-Time Amplitude
let audioCtx = null;
let analyserNode = null;
let micStream = null;
let visualizerFrameId = null;
let currentVolume = 0;
let userSpeakingTimeout = null;

// Conversation & Silence Timers
let silenceTimer = null;
let isEvaluating = false;
let speechKeepAliveInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Session check
  const user = await checkAuth(true);
  if (!user) return;

  if (user.name) {
    candidateName = user.name.split(' ')[0] || user.name;
  }

  initSpeechSynthesis();
  initSpeechRecognition();
  initWaveformVisualizer();
  await loadSetupOptions();
  bindEvents();
});

/**
 * Initializes and configures the Web Speech Synthesis (TTS) Engine
 */
function initSpeechSynthesis() {
  if (!speechSynth) {
    console.warn('[TTS] SpeechSynthesis is not supported in this browser.');
    return;
  }

  function loadVoices() {
    availableVoices = speechSynth.getVoices() || [];
    if (availableVoices.length > 0) {
      // Prioritize natural English voices
      preferredVoice = availableVoices.find(v => 
        (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Jenny') || 
         v.name.includes('Zira') || v.name.includes('Aria') || v.name.includes('Samantha') || 
         v.name.includes('David')) && v.lang.startsWith('en')
      ) || availableVoices.find(v => v.lang === 'en-US')
        || availableVoices.find(v => v.lang.startsWith('en'))
        || availableVoices[0];

      console.log(`[TTS] Voices loaded (${availableVoices.length}). Preferred: ${preferredVoice ? preferredVoice.name : 'Default'}`);
    }
  }

  loadVoices();
  if (speechSynth.onvoiceschanged !== undefined) {
    speechSynth.onvoiceschanged = loadVoices;
  }
}

/**
 * Global Voice State Controller
 * Manages Orb sizing, animations, glowing auras, waveform, and status text
 */
function setVoiceState(state, customMessage = null) {
  currentVoiceState = state;
  const stage = document.getElementById('chamber-hero-stage');
  const orb = document.getElementById('ai-orb');
  const aura = document.getElementById('orb-ambient-aura');
  const subtext = document.getElementById('voice-subtext');
  const pill = document.getElementById('voice-status-pill');
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  const micBtn = document.getElementById('mic-toggle-btn');
  const micIcon = document.getElementById('mic-btn-icon');
  const micHint = document.getElementById('mic-action-hint');
  const doneBtn = document.getElementById('done-speaking-btn');
  const waveform = document.getElementById('siri-waveform');

  if (stage) stage.setAttribute('data-voice-state', state);

  // Update Orb classes
  if (orb) {
    orb.classList.remove('state-idle', 'state-listening', 'state-thinking', 'state-analyzing', 'state-speaking');
    orb.classList.add(`state-${state}`);
    orb.style.removeProperty('--orb-scale');
  }

  // Update Ambient Aura
  if (aura) {
    aura.classList.remove('aura-idle', 'aura-listening', 'aura-thinking', 'aura-analyzing', 'aura-speaking');
    aura.classList.add(`aura-${state}`);
  }

  // Sync state switcher buttons if present
  const stateBtns = document.querySelectorAll('.orb-state-btn');
  stateBtns.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.state === state);
  });

  // Update Waveform container mode
  if (waveform) {
    waveform.classList.remove('active-listening', 'active-speaking', 'active-thinking');
    if (state === VoiceState.LISTENING) waveform.classList.add('active-listening');
    else if (state === VoiceState.SPEAKING) waveform.classList.add('active-speaking');
    else if (state === VoiceState.THINKING) waveform.classList.add('active-thinking');
  }

  // Update Status Pill, Label, Mic Button, and Subtext
  switch (state) {
    case VoiceState.SPEAKING:
      if (pill) pill.className = 'voice-status-indicator status-speaking';
      if (dot) dot.textContent = '🟣';
      if (label) label.textContent = 'JARVIS Speaking';
      if (subtext) subtext.textContent = customMessage || 'JARVIS is speaking...';
      if (micBtn) {
        micBtn.classList.remove('recording');
        micBtn.setAttribute('aria-pressed', 'false');
      }
      if (micIcon) micIcon.innerHTML = '🎙';
      if (micHint) micHint.textContent = 'Listening will activate automatically when JARVIS finishes speaking';
      if (doneBtn) doneBtn.style.display = 'none';
      setWaveAnimation('speaking');
      break;

    case VoiceState.LISTENING:
      if (pill) pill.className = 'voice-status-indicator status-listening';
      if (dot) dot.textContent = '🔴';
      if (label) label.textContent = 'JARVIS Listening';
      if (subtext) subtext.textContent = customMessage || 'JARVIS is listening...';
      if (micBtn) {
        micBtn.classList.add('recording');
        micBtn.setAttribute('aria-pressed', 'true');
      }
      if (micIcon) micIcon.innerHTML = '<span class="rec-dot">●</span> 🎙';
      if (micHint) {
        micHint.textContent = isGreetingReadyCheck
          ? 'Say "Yes, I\'m ready" or click the button above to begin'
          : 'Speak your answer naturally. JARVIS auto-submits upon pause';
      }
      if (doneBtn) doneBtn.style.display = isGreetingReadyCheck ? 'none' : 'inline-flex';
      setWaveAnimation('listening');
      break;

    case VoiceState.THINKING:
      if (pill) pill.className = 'voice-status-indicator status-processing';
      if (dot) dot.textContent = '🟡';
      if (label) label.textContent = 'JARVIS Analyzing';
      if (subtext) subtext.textContent = customMessage || 'JARVIS is analyzing your answer...';
      if (micBtn) {
        micBtn.classList.remove('recording');
        micBtn.setAttribute('aria-pressed', 'false');
      }
      if (micIcon) micIcon.innerHTML = '🎙';
      if (micHint) micHint.textContent = 'JARVIS is evaluating response against key technical concepts...';
      if (doneBtn) doneBtn.style.display = 'none';
      setWaveAnimation('off');
      break;

    case VoiceState.IDLE:
    default:
      if (micBtn) {
        micBtn.classList.remove('recording');
        micBtn.setAttribute('aria-pressed', 'false');
      }
      if (micIcon) micIcon.innerHTML = '🎙';
      if (micHint) micHint.textContent = 'Click microphone to speak to JARVIS, or type your answer directly';
      if (doneBtn) doneBtn.style.display = 'none';

      const transcriptBox = document.getElementById('answer-transcript');
      const hasAnswer = transcriptBox && transcriptBox.value.trim().length > 0;

      if (pill) {
        if (hasAnswer) {
          pill.className = 'voice-status-indicator status-captured';
          if (dot) dot.textContent = '🟢';
          if (label) label.textContent = 'Answer captured';
          if (subtext) subtext.textContent = customMessage || 'Answer captured & ready';
        } else {
          pill.className = 'voice-status-indicator status-ready';
          if (dot) dot.textContent = '⚪';
          if (label) label.textContent = 'JARVIS Ready';
          if (subtext) subtext.textContent = customMessage || 'JARVIS is ready when you are';
        }
      }
      setWaveAnimation('off');
      break;
  }
  
  // UI Panel Management for Cinematic Chat
  const activeUserTurn = document.getElementById('active-user-turn');
  const activeJarvisTurn = document.getElementById('active-jarvis-turn');
  const analyzingIndicator = document.getElementById('analyzing-indicator');

  if (activeJarvisTurn) activeJarvisTurn.style.display = 'flex';
  
  if (state === VoiceState.LISTENING || state === VoiceState.THINKING || state === VoiceState.IDLE && hasAnswer) {
      if (activeUserTurn) activeUserTurn.style.display = 'flex';
  }
  
  if (state === VoiceState.THINKING) {
      if (analyzingIndicator) analyzingIndicator.style.display = 'block';
  } else {
      if (analyzingIndicator) analyzingIndicator.style.display = 'none';
  }

  // Hook for 3D JARVIS
  if (window.Jarvis3D) {
      window.Jarvis3D.setState(state);
  }
}

function archiveCurrentTurn() {
  const historyContainer = document.getElementById('chat-history-container');
  const liveUserTranscript = document.getElementById('live-user-transcript');
  const liveJarvisResponse = document.getElementById('live-jarvis-response');
  
  if (!historyContainer) return;

  const jText = liveJarvisResponse ? liveJarvisResponse.textContent.trim() : '';
  const uText = liveUserTranscript ? liveUserTranscript.textContent.trim() : '';

  if (jText || uText) {
    const group = document.createElement('div');
    group.className = 'chat-message-group';
    group.style.marginBottom = '1rem';

    if (jText) {
      group.innerHTML += `<div class="jarvis-turn chat-message-group" style="margin-bottom:0.5rem;"><span class="chat-label">JARVIS</span><p class="chat-text">${jText}</p></div>`;
    }
    if (uText) {
      group.innerHTML += `<div class="user-turn chat-message-group"><span class="chat-label">YOU</span><p class="chat-text">${uText}</p></div>`;
    }
    
    historyContainer.appendChild(group);
    historyContainer.scrollTop = historyContainer.scrollHeight;
  }

  if (liveJarvisResponse) liveJarvisResponse.innerHTML = '';
  if (liveUserTranscript) liveUserTranscript.innerHTML = '';
  
  const activeUserTurn = document.getElementById('active-user-turn');
  if (activeUserTurn) activeUserTurn.style.display = 'none';
}

/**
 * Text-to-Speech: Speaks text aloud with JARVIS Voice, then executes onComplete
 * IMPORTANT: Strictly stops STT beforehand to prevent JARVIS from listening to itself.
 */
function speakJarvis(text, onComplete = null) {
  if (!speechSynth) {
    console.warn('[JARVIS TTS] SpeechSynthesis not available in this browser.');
    if (onComplete) onComplete();
    return;
  }

  // PREVENT SPEECH CONFLICT: Stop listening before speaking!
  stopVoiceListening(false);

  // Cancel any prior speech
  speechSynth.cancel();
  if (speechKeepAliveInterval) clearInterval(speechKeepAliveInterval);

  console.log(`[JARVIS TTS] Speaking question: "${text.slice(0, 65)}..."`);

  activeUtterance = new SpeechSynthesisUtterance(text);
  if (preferredVoice) {
    activeUtterance.voice = preferredVoice;
  }
  activeUtterance.lang = 'en-US';
  activeUtterance.rate = 0.96; // Paced academic cadence
  activeUtterance.pitch = 1.0;
  activeUtterance.volume = 1.0;

  isSpeaking = true;
  setVoiceState(VoiceState.SPEAKING, 'JARVIS is speaking...');
  
  archiveCurrentTurn();
  
  const liveResponse = document.getElementById('live-jarvis-response');
  const jarvisCursor = document.getElementById('jarvis-cursor');
  
  if (liveResponse) liveResponse.innerHTML = '';
  if (jarvisCursor) jarvisCursor.style.display = 'inline';
  
  let fallbackTimer = null;
  
  // Word boundary event for progressive text display
  activeUtterance.onboundary = (event) => {
    if (event.name === 'word') {
       if (liveResponse) {
          const currentText = text.substring(0, event.charIndex + event.charLength);
          liveResponse.innerHTML = currentText;
       }
    }
  };

  activeUtterance.onstart = () => {
    console.log('[JARVIS TTS] Speech started');
    // Fallback animation if onboundary isn't firing
    if (liveResponse && liveResponse.innerHTML === '') {
        const words = text.split(' ');
        let wIdx = 0;
        const speed = Math.max(300, (text.length / 15) * 100); 
        fallbackTimer = setInterval(() => {
           if (!isSpeaking) {
               clearInterval(fallbackTimer);
               return;
           }
           if (wIdx < words.length) {
               liveResponse.innerHTML = words.slice(0, wIdx + 1).join(' ');
               wIdx++;
           } else {
               clearInterval(fallbackTimer);
           }
        }, speed / words.length);
    }
  };

  // Chrome keepalive: Prevents Chrome TTS engine from stalling on long sentences
  speechKeepAliveInterval = setInterval(() => {
    if (isSpeaking && speechSynth.speaking) {
      speechSynth.resume();
    } else {
      clearInterval(speechKeepAliveInterval);
    }
  }, 3000);

  activeUtterance.onstart = () => {
    console.log('[JARVIS TTS] Speech started');
  };

  activeUtterance.onend = () => {
    clearInterval(speechKeepAliveInterval);
    if (fallbackTimer) clearInterval(fallbackTimer);
    console.log('[JARVIS TTS] Speech ended');
    isSpeaking = false;
    activeUtterance = null;
    
    if (liveResponse) liveResponse.innerHTML = text;
    if (jarvisCursor) jarvisCursor.style.display = 'none';

    if (onComplete) {
      // Natural brief conversational beat before opening candidate microphone
      setTimeout(() => {
        onComplete();
      }, 400);
    }
  };

  activeUtterance.onerror = (event) => {
    clearInterval(speechKeepAliveInterval);
    if (fallbackTimer) clearInterval(fallbackTimer);
    console.warn('[JARVIS TTS] Speech error or canceled:', event.error);
    isSpeaking = false;
    activeUtterance = null;
    if (liveResponse) liveResponse.innerHTML = text;
    if (jarvisCursor) jarvisCursor.style.display = 'none';
    if (onComplete) onComplete();
  };

  speechSynth.speak(activeUtterance);

  // Resume immediately to overcome browser autoplay pause
  if (speechSynth.paused) {
    speechSynth.resume();
  }
}

// Backwards compatibility alias
const speakNextHire = speakJarvis;

/**
 * Initializes browser Web Speech Recognition with error handling
 */
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;

  if (!SpeechRecognition) {
    console.warn('[Web Speech API] Speech recognition is not supported in this browser.');
    const notice = document.getElementById('mic-permission-notice');
    if (notice) {
      notice.textContent = 'ℹ️ Speech recognition is not supported in this browser. You can enter your answers using text.';
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
      console.log('[JARVIS STT] Listening started');
      setVoiceState(VoiceState.LISTENING, 'JARVIS is listening...');
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

      onUserSpeakingActivity();

      // Handshake check for conversational greeting:
      if (isGreetingReadyCheck) {
        const spoken = (finalTranscript + ' ' + interimTranscript).trim().toLowerCase();
        console.log(`[JARVIS GREETING] Candidate utterance: "${spoken}"`);
        if (spoken.includes('ready') || spoken.includes('yes') || spoken.includes('start') || 
            spoken.includes('sure') || spoken.includes('begin') || spoken.includes('yeah') || 
            spoken.includes('yep') || spoken.includes('ok') || spoken.includes('fine') || spoken.includes('go')) {
          console.log('[JARVIS GREETING] Candidate confirmed readiness via voice.');
          handleCandidateConfirmedReady();
          return;
        }
      }

      const transcriptBox = document.getElementById('answer-transcript');
      const liveUserTranscript = document.getElementById('live-user-transcript');

      if (!isGreetingReadyCheck) {
        if (finalTranscript && transcriptBox) {
          transcriptBox.value = (transcriptBox.value + ' ' + finalTranscript).trim();
          console.log(`[JARVIS ANSWER] Transcript received: "${finalTranscript.trim()}"`);
        }
      }

      if (liveUserTranscript) {
         let currentFinal = transcriptBox ? transcriptBox.value : '';
         if (isGreetingReadyCheck) {
             currentFinal = finalTranscript;
         }
         liveUserTranscript.textContent = (currentFinal + ' ' + interimTranscript).trim();
      }

      // Conversational Silence Detection:
      // If candidate stops speaking for 2.8s after uttering an answer, auto-submit!
      if (silenceTimer) clearTimeout(silenceTimer);

      const currentText = transcriptBox ? transcriptBox.value.trim() : '';
      if (!isGreetingReadyCheck && currentText.length >= 6) {
        silenceTimer = setTimeout(() => {
          console.log('[JARVIS STT] Candidate paused speaking (silence detected). Automatically submitting answer.');
          submitAnswerAndContinue();
        }, 2800);
      }
    };

    recognition.onerror = (event) => {
      console.warn('[Web Speech API] Recognition error:', event.error);
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

      stopVoiceListening(false);
    };

    recognition.onend = () => {
      if (isRecording) {
        // If recognition closed unexpectedly while still in listening state, restart unless evaluating
        if (!isSpeaking && !isEvaluating && currentVoiceState === VoiceState.LISTENING) {
          try {
            recognition.start();
          } catch (e) {
            stopVoiceListening(false);
          }
        } else {
          stopVoiceListening(false);
        }
      }
    };
  } catch (err) {
    console.error('Failed to construct SpeechRecognition:', err);
  }
}

/**
 * Starts listening to candidate's voice answer
 */
async function startVoiceListening() {
  if (isSpeaking) {
    console.warn('[JARVIS STT] Refusing to start listening while JARVIS is speaking.');
    return;
  }

  if (!recognition) {
    showToast('Speech recognition unavailable. Please type your response.', 'info');
    document.getElementById('answer-transcript').focus();
    return;
  }

  if (isRecording) return;

  try {
    document.getElementById('mic-permission-notice').style.display = 'none';

    // Start Audio Analyser for real-time amplitude animation
    await startAudioAnalyser();

    recognition.start();
    isRecording = true;
    setVoiceState(VoiceState.LISTENING, 'JARVIS is listening...');
  } catch (err) {
    console.warn('Error starting speech recognition:', err);
    try {
      recognition.stop();
      setTimeout(() => {
        if (!isSpeaking) {
          recognition.start();
          isRecording = true;
          setVoiceState(VoiceState.LISTENING, 'JARVIS is listening...');
        }
      }, 250);
    } catch (e) {
      console.error(e);
    }
  }
}

/**
 * Stops listening to candidate's voice answer
 */
function stopVoiceListening(returnToIdle = true) {
  if (silenceTimer) clearTimeout(silenceTimer);

  if (isRecording) {
    isRecording = false;
    console.log('[JARVIS STT] Listening stopped');
    try {
      if (recognition) recognition.stop();
    } catch (e) {
      console.warn(e);
    }
  }

  stopAudioAnalyser();

  if (returnToIdle && currentVoiceState === VoiceState.LISTENING) {
    const transcriptBox = document.getElementById('answer-transcript');
    const hasAnswer = transcriptBox && transcriptBox.value.trim().length > 0;
    setVoiceState(VoiceState.IDLE, hasAnswer ? 'Answer captured & ready' : 'Ready when you are');
  }
}

/**
 * Toggles microphone manually via Floating Mic Button
 */
async function toggleVoiceRecording() {
  if (isSpeaking) {
    // If JARVIS is speaking, cancel speech and start listening
    if (speechSynth) speechSynth.cancel();
    isSpeaking = false;
    startVoiceListening();
    return;
  }

  if (isRecording) {
    // If candidate was recording, stop and submit
    const transcriptBox = document.getElementById('answer-transcript');
    if (transcriptBox && transcriptBox.value.trim().length > 0) {
      submitAnswerAndContinue();
    } else {
      stopVoiceListening(true);
    }
  } else {
    startVoiceListening();
  }
}

/**
 * Handles active speaking bursts to animate the Orb scale dynamically
 */
function onUserSpeakingActivity() {
  if (currentVoiceState !== VoiceState.LISTENING) return;

  const orb = document.getElementById('ai-orb');
  if (orb) {
    orb.style.setProperty('--orb-scale', (1.0 + Math.random() * 0.09).toFixed(3));
  }

  if (userSpeakingTimeout) clearTimeout(userSpeakingTimeout);
  userSpeakingTimeout = setTimeout(() => {
    if (orb) orb.style.setProperty('--orb-scale', '1');
  }, 400);
}

/**
 * Submits the current candidate answer to backend evaluation,
 * plays a natural interviewer transition, and proceeds to the next question.
 */
async function submitAnswerAndContinue() {
  if (isEvaluating) return;
  isEvaluating = true;

  if (silenceTimer) clearTimeout(silenceTimer);

  // 1. Stop listening
  stopVoiceListening(false);

  // 2. Transition Orb to PROCESSING / ANALYZING
  setVoiceState(VoiceState.THINKING, 'JARVIS is analyzing your answer...');
  console.log('[JARVIS AI] Evaluating answer');

  // 3. Save candidate answer to existing backend endpoint
  await saveCurrentAnswer(true);

  // 4. Select a natural MCA interviewer transition based on response depth
  const transcriptBox = document.getElementById('answer-transcript');
  const answerText = transcriptBox ? transcriptBox.value.trim() : '';
  const wordCount = answerText.split(/\s+/).filter(Boolean).length;

  let transitionDisplay = "JARVIS: Let's move to the next question.";
  let spokenTransition = "Let's move to the next question.";

  if (wordCount > 18) {
    const deepTransitions = [
      { display: "JARVIS: That's a thorough explanation. Let's move to the next question.", spoken: "That's a thorough explanation. Let's move to the next question." },
      { display: "JARVIS: Good technical detail. Now let's explore the next concept.", spoken: "Good technical detail. Now let's explore the next concept." },
      { display: "JARVIS: Thank you for that detailed answer. Let's continue.", spoken: "Thank you for that detailed answer. Let's continue." },
      { display: "JARVIS: Great explanation. Moving forward to the next question.", spoken: "Great explanation. Moving forward to the next question." }
    ];
    const pick = deepTransitions[Math.floor(Math.random() * deepTransitions.length)];
    transitionDisplay = pick.display;
    spokenTransition = pick.spoken;
  } else if (wordCount >= 4) {
    const midTransitions = [
      { display: "JARVIS: Good attempt. Let's move to the next question.", spoken: "Good attempt. Let's move to the next question." },
      { display: "JARVIS: Thank you. Let's proceed to the next question.", spoken: "Thank you. Let's proceed to the next question." },
      { display: "JARVIS: Understood. Moving on to the next topic.", spoken: "Understood. Moving on to the next topic." },
      { display: "JARVIS: Let's move to the next question.", spoken: "Let's move to the next question." }
    ];
    const pick = midTransitions[Math.floor(Math.random() * midTransitions.length)];
    transitionDisplay = pick.display;
    spokenTransition = pick.spoken;
  } else {
    transitionDisplay = "JARVIS: Let's move to the next question.";
    spokenTransition = "Let's move to the next question.";
  }

  console.log(`[JARVIS NEXT] Transition: "${transitionDisplay}"`);

  const total = activeInterview ? activeInterview.questions.length : 0;
  if (currentQuestionIndex < total - 1) {
    currentQuestionIndex++;
    isEvaluating = false;
    renderCurrentQuestion(transitionDisplay, spokenTransition);
  } else {
    isEvaluating = false;
    // Interview completed
    const finalFarewell = `Thank you ${candidateName}. You have completed all questions in your technical interview. JARVIS and NextHire are now generating your multi-dimensional evaluation scorecard.`;
    speakJarvis(finalFarewell, () => {
      completeInterviewSession();
    });
  }
}

/**
 * Initializes Web Audio API to capture microphone stream amplitude
 */
async function startAudioAnalyser() {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;

    if (!audioCtx) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) audioCtx = new AudioCtxClass();
    }

    if (audioCtx && audioCtx.state === 'suspended') {
      await audioCtx.resume();
    }

    if (!micStream) {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    }

    if (audioCtx && micStream && !analyserNode) {
      analyserNode = audioCtx.createAnalyser();
      analyserNode.fftSize = 64;
      const source = audioCtx.createMediaStreamSource(micStream);
      source.connect(analyserNode);
    }
  } catch (e) {
    console.warn('[Web Audio] Analyser fallback to procedural animation:', e);
  }
}

/**
 * Stops Web Audio stream and analyser
 */
function stopAudioAnalyser() {
  if (micStream) {
    micStream.getTracks().forEach(track => track.stop());
    micStream = null;
  }
  analyserNode = null;
  currentVolume = 0;
}

/**
 * Voice-Reactive Orb Animation loop
 * Updates the JARVIS orb scale smoothly using real frequency data from the microphone
 */
function initWaveformVisualizer() {
  const dataArray = new Uint8Array(32);

  function renderWaveform(time) {
    if (currentVoiceState === VoiceState.LISTENING) {
      let freqEnergy = 0;
      if (analyserNode) {
        analyserNode.getByteFrequencyData(dataArray);
        let sum = 0;
        // Average the lower frequency bins which carry most of the human voice energy
        for (let i = 0; i < 16; i++) sum += dataArray[i];
        freqEnergy = sum / 16; // 0 to 255
      }

      // Noise gate: ignore very low amplitude (e.g. background noise)
      const normEnergy = freqEnergy > 15 ? freqEnergy / 255 : 0;
      
      // Smooth interpolation for fluid organic movement
      currentVolume += (normEnergy - currentVolume) * 0.12;

      // Update Orb scale dynamically
      const orb = document.getElementById('ai-orb');
      if (orb) {
        // Base scale 1.00. Max scale offset 0.07 (loud).
        const scaleOffset = currentVolume * 0.08;
        const finalScale = 1.00 + Math.min(scaleOffset, 0.07);
        orb.style.setProperty('--orb-scale', finalScale.toFixed(3));
      }
    } else {
      // When not listening, slowly ease currentVolume back to 0
      if (currentVolume > 0.01) {
        currentVolume += (0 - currentVolume) * 0.1;
      } else {
        currentVolume = 0;
      }
    }
    
    if (window.Jarvis3D) {
      window.Jarvis3D.updateVolume(currentVolume);
    }

    visualizerFrameId = requestAnimationFrame(renderWaveform);
  }

  visualizerFrameId = requestAnimationFrame(renderWaveform);
}

/**
 * Legacy compatibility functions
 */
function setVoiceStatus(status) {
  if (status === 'listening') setVoiceState(VoiceState.LISTENING);
  else if (status === 'processing') setVoiceState(VoiceState.THINKING);
  else if (status === 'captured') setVoiceState(VoiceState.IDLE, 'Answer captured');
  else setVoiceState(VoiceState.IDLE, 'Ready when you are');
}

function setWaveAnimation(mode) {
  const bars = document.querySelectorAll('.wave-bar');
  bars.forEach(bar => {
    bar.className = 'wave-bar';
    if (mode === 'speaking') bar.classList.add('speaking');
    else if (mode === 'listening') bar.classList.add('listening');
  });
}

/**
 * Manual Listen Question Button click handler
 */
function speakCurrentQuestion() {
  if (!activeInterview || !activeInterview.questions) return;
  const current = activeInterview.questions[currentQuestionIndex];
  if (!current) return;

  if (isSpeaking) {
    if (speechSynth) speechSynth.cancel();
    isSpeaking = false;
    setVoiceState(VoiceState.IDLE, 'JARVIS is ready when you are');
    document.getElementById('speak-question-btn').innerHTML = '<span>🔊 Listen Question</span>';
    return;
  }

  document.getElementById('speak-question-btn').innerHTML = '<span>⏹ Stop Audio</span>';
  speakJarvis(current.question_text, () => {
    const btn = document.getElementById('speak-question-btn');
    if (btn) btn.innerHTML = '<span>🔊 Listen Question</span>';
    // After replaying question, start listening for answer
    startVoiceListening();
  });
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

  // User gesture unlock for audio and voices
  if (speechSynth) {
    speechSynth.resume();
    populateVoicesIfReady();
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

      showToast('Interview chamber initialized with unique questions from MySQL.', 'success');

      // Begin the live two-way conversational flow with JARVIS greeting & ready check!
      startJarvisGreetingFlow();
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

function populateVoicesIfReady() {
  if (!preferredVoice && speechSynth) {
    const vList = speechSynth.getVoices() || [];
    if (vList.length > 0) {
      preferredVoice = vList.find(v => 
        (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Jenny') || 
         v.name.includes('Zira') || v.name.includes('Aria') || v.name.includes('David')) && v.lang.startsWith('en')
      ) || vList.find(v => v.lang.startsWith('en')) || vList[0];
    }
  }
}

/**
 * Starts the Siri-style conversational greeting between JARVIS and Candidate:
 * JARVIS: "Hello Candidate. Welcome to NextHire. Are you ready to begin?"
 * USER: "Yes, I'm ready."
 * JARVIS: "Great. Let's start with your first question."
 */
function startJarvisGreetingFlow() {
  if (!activeInterview || !activeInterview.questions || activeInterview.questions.length === 0) return;

  isGreetingReadyCheck = true;
  currentQuestionIndex = 0;

  // Stop any prior speech or listening
  if (speechSynth && speechSynth.speaking) {
    speechSynth.cancel();
  }
  stopVoiceListening(false);

  // Configure UI elements for initial handshake
  const readyBox = document.getElementById('ready-handshake-box');
  const progressText = document.getElementById('question-progress-text');
  const progressBar = document.getElementById('session-progress-bar');
  const questionDisplay = document.getElementById('question-text-display');
  const bubbleHint = document.getElementById('ai-bubble-state-hint');
  const langBadge = document.getElementById('q-lang-badge');
  const topicBadge = document.getElementById('q-topic-badge');
  const codeLabel = document.getElementById('q-code-label');
  const transcriptBox = document.getElementById('answer-transcript');

  if (readyBox) readyBox.style.display = 'block';
  if (progressText) progressText.textContent = 'Voice Initialization';
  if (progressBar) progressBar.style.width = '10%';
  if (bubbleHint) bubbleHint.textContent = 'Readiness Handshake';
  if (langBadge) langBadge.textContent = 'JARVIS';
  if (topicBadge) topicBadge.textContent = 'Ready Check';
  if (codeLabel) codeLabel.textContent = 'Voice Assistant';
  if (transcriptBox) transcriptBox.value = '';

  // Scroll smoothly to chamber
  document.getElementById('chamber-section').scrollIntoView({ behavior: 'smooth' });

  const greetingUtterance = `Hello ${candidateName}. Welcome to NextHire. Are you ready to begin?`;
  if (questionDisplay) {
    questionDisplay.textContent = greetingUtterance;
  }

  // JARVIS speaks greeting aloud
  speakJarvis(greetingUtterance, () => {
    // Open mic for candidate's voice answer: "Yes, I'm ready"
    startVoiceListening();
  });
}

/**
 * Handles candidate confirmation ("Yes, I'm ready")
 */
function handleCandidateConfirmedReady() {
  if (!isGreetingReadyCheck) return;
  isGreetingReadyCheck = false;

  stopVoiceListening(false);

  const readyBox = document.getElementById('ready-handshake-box');
  if (readyBox) readyBox.style.display = 'none';

  const questionDisplay = document.getElementById('question-text-display');
  const bubbleHint = document.getElementById('ai-bubble-state-hint');
  if (bubbleHint) bubbleHint.textContent = 'Starting Interview';

  const startResponse = "Great. Let's start with your first question.";
  if (questionDisplay) {
    questionDisplay.textContent = startResponse;
  }

  // Spoken by JARVIS: "Great. Let's start with your first question."
  speakJarvis(startResponse, () => {
    // Move immediately to Question 1
    renderCurrentQuestion(null, null);
  });
}

/**
 * Renders the active question in the chamber and automatically speaks it,
 * followed by opening the microphone for the candidate's answer.
 */
function renderCurrentQuestion(transitionDisplay = null, spokenTransition = null) {
  if (!activeInterview || !activeInterview.questions || activeInterview.questions.length === 0) return;

  const total = activeInterview.questions.length;
  const current = activeInterview.questions[currentQuestionIndex];
  if (!current) return;

  // Stop any previous speech & recording safely
  if (speechSynth && speechSynth.speaking) {
    speechSynth.cancel();
  }
  stopVoiceListening(false);

  // Ensure ready check is reset
  isGreetingReadyCheck = false;
  const readyBox = document.getElementById('ready-handshake-box');
  if (readyBox) readyBox.style.display = 'none';

  // Progress update
  document.getElementById('question-progress-text').textContent = `Question ${currentQuestionIndex + 1} / ${total}`;
  const progressPct = Math.round(((currentQuestionIndex + 1) / total) * 100);
  document.getElementById('session-progress-bar').style.width = `${progressPct}%`;

  // Question metadata badges & prompt display (Text stays visible on screen!)
  document.getElementById('q-lang-badge').textContent = current.language || 'General';
  document.getElementById('q-topic-badge').textContent = current.topic || 'Core Concept';
  document.getElementById('q-code-label').textContent = `Code: ${current.question_code}`;

  const bubbleHint = document.getElementById('ai-bubble-state-hint');
  if (bubbleHint) bubbleHint.textContent = `Technical Question ${currentQuestionIndex + 1} of ${total}`;

  const questionDisplay = document.getElementById('question-text-display');
  if (questionDisplay) questionDisplay.textContent = current.question_text;

  // Clear answer field for live transcription
  const transcriptBox = document.getElementById('answer-transcript');
  if (transcriptBox) transcriptBox.value = '';
  setVoiceState(VoiceState.IDLE, 'JARVIS is ready when you are');

  // Update button text if last question
  const nextBtn = document.getElementById('next-question-btn');
  if (nextBtn) {
    if (currentQuestionIndex === total - 1) {
      nextBtn.innerHTML = '<span>Complete Interview &check;</span>';
    } else {
      nextBtn.innerHTML = '<span>Next Question &rarr;</span>';
    }
  }

  // Scroll smoothly to chamber
  document.getElementById('chamber-section').scrollIntoView({ behavior: 'smooth' });

  // CONVERSATIONAL VOICE SEQUENCE:
  let speechMessage = '';
  if (spokenTransition) {
    speechMessage = `${spokenTransition} ${current.question_text}`;
    setVoiceState(VoiceState.SPEAKING, transitionDisplay || "JARVIS: Let's move to the next question.");
  } else {
    speechMessage = current.question_text;
    setVoiceState(VoiceState.SPEAKING, 'JARVIS is speaking...');
  }

  // JARVIS speaks automatically -> finishes speaking -> microphone listens automatically!
  speakJarvis(speechMessage, () => {
    startVoiceListening();
  });
}

/**
 * Saves candidate answer for the current question via POST /api/interview/<id>/answer
 */
async function saveCurrentAnswer(silent = false, status = 'answered') {
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
        answer_text: answerText,
        status: status
      })
    });

    const result = await response.json();
    if (response.ok && result.status === 'success') {
      current.answer_text = answerText;
      current.status = status;
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
 * Advances to the next question manually
 */
async function handleNextQuestion() {
  submitAnswerAndContinue();
}

/**
 * Skips the current question
 */
async function handleSkipQuestion() {
  if (isEvaluating) return;
  isEvaluating = true;
  if (silenceTimer) clearTimeout(silenceTimer);
  stopVoiceListening(false);
  setVoiceState(VoiceState.THINKING, 'JARVIS is skipping question...');
  
  await saveCurrentAnswer(true, 'skipped');
  
  const total = activeInterview ? activeInterview.questions.length : 0;
  if (currentQuestionIndex < total - 1) {
    currentQuestionIndex++;
    isEvaluating = false;
    renderCurrentQuestion("JARVIS: Question skipped. Let's move to the next one.", "Question skipped. Let's move to the next one.");
  } else {
    isEvaluating = false;
    const finalFarewell = `Thank you ${candidateName}. You have completed all questions in your technical interview. JARVIS and NextHire are now generating your multi-dimensional evaluation scorecard.`;
    speakJarvis(finalFarewell, () => {
      completeInterviewSession();
    });
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
  stopVoiceListening(false);

  document.getElementById('chamber-section').style.display = 'none';
  const completedSection = document.getElementById('completed-section');
  if (completedSection) {
    let answered = 0;
    activeInterview.questions.forEach(q => {
      if (q.status !== 'skipped' && q.answer_text && q.answer_text.trim() !== '') {
        answered++;
      }
    });
    const total = activeInterview.questions.length;
    let pct = total > 0 ? Math.round((answered / total) * 100) : 0;
    
    document.getElementById('completed-total-q').textContent = `${answered} / ${total}`;
    document.getElementById('completed-role-name').textContent = activeInterview.role_name;
    const pctLabel = document.getElementById('completed-answers-percentage');
    if (pctLabel) pctLabel.textContent = `${pct}%`;
    
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

  // Floating Microphone toggle button
  const micBtn = document.getElementById('mic-toggle-btn');
  if (micBtn) {
    micBtn.addEventListener('click', toggleVoiceRecording);
  }

  // Done Speaking Button (Immediate submission without waiting for silence timer)
  const doneBtn = document.getElementById('done-speaking-btn');
  if (doneBtn) {
    doneBtn.addEventListener('click', () => {
      submitAnswerAndContinue();
    });
  }

  // Confirm Ready Button (Handshake)
  const confirmReadyBtn = document.getElementById('confirm-ready-btn');
  if (confirmReadyBtn) {
    confirmReadyBtn.addEventListener('click', () => {
      handleCandidateConfirmedReady();
    });
  }

  // Speak/Replay question button
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
        setVoiceState(VoiceState.IDLE, 'Ready when you are');
      }
    });
  }

  // Interactive AI Orb click also toggles voice recording intuitively
  const aiOrb = document.getElementById('ai-orb');
  if (aiOrb) {
    aiOrb.addEventListener('click', toggleVoiceRecording);
  }

  // Interactive Orb State Preview Switcher for testing all 4 JARVIS states
  const stateBtns = document.querySelectorAll('.orb-state-btn');
  stateBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const targetState = btn.dataset.state;
      if (targetState === 'idle') setVoiceState(VoiceState.IDLE, 'JARVIS is ready when you are');
      else if (targetState === 'speaking') setVoiceState(VoiceState.SPEAKING, 'JARVIS is speaking...');
      else if (targetState === 'listening') setVoiceState(VoiceState.LISTENING, 'JARVIS is listening...');
      else if (targetState === 'thinking' || targetState === 'analyzing') setVoiceState(VoiceState.THINKING, 'JARVIS is analyzing your answer...');
    });
  });

  // Save answer button
  const saveBtn = document.getElementById('submit-answer-btn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => saveCurrentAnswer(false));
  }

  // Skip question button
  const skipBtn = document.getElementById('skip-question-btn');
  if (skipBtn) {
    skipBtn.addEventListener('click', handleSkipQuestion);
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
        stopVoiceListening(false);
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
