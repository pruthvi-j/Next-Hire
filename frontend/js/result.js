/**
 * NEXT HIRE - Candidate Assessment Scorecard Controller (Phase 8)
 * Liquid Glass UI & Dynamic Evaluation Rendering
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Verify session authentication
  const user = await checkAuth(true);
  if (!user) return;

  // Retrieve interview_id from URL query string if provided (?id=... or ?interview_id=...)
  const urlParams = new URLSearchParams(window.location.search);
  const interviewId = urlParams.get('id') || urlParams.get('interview_id');

  await loadInterviewResult(interviewId);
});

/**
 * Fetches and displays interview evaluation results
 */
async function loadInterviewResult(interviewId) {
  const loadingState = document.getElementById('result-loading-state');
  const errorState = document.getElementById('result-error-state');
  const contentArea = document.getElementById('result-content-area');

  if (loadingState) loadingState.style.display = 'block';
  if (errorState) errorState.style.display = 'none';
  if (contentArea) contentArea.style.display = 'none';

  try {
    const endpoint = interviewId 
      ? `${API_BASE}/api/interview/${interviewId}/result?t=${Date.now()}`
      : `${API_BASE}/api/interview/latest-result?t=${Date.now()}`;

    const response = await fetch(endpoint, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.message || `HTTP ${response.status}: Failed to load evaluation scorecard.`);
    }

    const payload = await response.json();
    const data = payload.data;

    if (!data) {
      throw new Error('No assessment results returned from database.');
    }

    renderScorecard(data);

    if (loadingState) loadingState.style.display = 'none';
    if (contentArea) contentArea.style.display = 'block';

  } catch (error) {
    console.error('[Scorecard Error]', error);
    if (loadingState) loadingState.style.display = 'none';
    if (errorState) {
      errorState.style.display = 'block';
      const msg = document.getElementById('error-message-text');
      if (msg) msg.textContent = error.message;
    }
  }
}

/**
 * Renders the full evaluation scorecard onto the Liquid Glass DOM
 */
function renderScorecard(data) {
  // 1. Header Metadata & PDF Download Buttons
  const sessionCode = `#NH-2026-${String(data.interview_id).padStart(3, '0')}`;
  safeSetText('session-code-badge', sessionCode);
  safeSetText('evaluated-role-badge', data.role_name || 'Software Engineer');
  safeSetText('evaluated-diff-badge', data.difficulty || 'Medium');
  safeSetText('questions-count-badge', `${data.answered_count} Answered • ${data.skipped_count || 0} Skipped • ${data.total_questions} Total`);

  const pdfUrl = `${API_BASE}/api/interview/${data.interview_id}/pdf`;
  const pdfFileName = `NextHire_Report_NH_${String(data.interview_id).padStart(3, '0')}.pdf`;
  const pdfBtn = document.getElementById('download-pdf-btn');
  if (pdfBtn) {
    pdfBtn.href = pdfUrl;
    pdfBtn.setAttribute('download', pdfFileName);
  }
  const pdfBtnBottom = document.getElementById('download-pdf-btn-bottom');
  if (pdfBtnBottom) {
    pdfBtnBottom.href = pdfUrl;
    pdfBtnBottom.setAttribute('download', pdfFileName);
  }

  // 2. Overall Score & Status Rating
  const overall = Number(data.overall_score || 0).toFixed(1);
  safeSetText('overall-score-display', overall);

  const statusBadge = document.getElementById('candidate-status-badge');
  if (statusBadge) {
    if (overall >= 85) {
      statusBadge.textContent = '● Candidate Status: Industry Ready (Optimal)';
      statusBadge.className = 'badge badge-success';
    } else if (overall >= 70) {
      statusBadge.textContent = '● Candidate Status: Proficient & Qualified';
      statusBadge.className = 'badge badge-primary';
    } else if (overall >= 50) {
      statusBadge.textContent = '● Candidate Status: Developing Foundation';
      statusBadge.className = 'badge badge-warning';
    } else {
      statusBadge.textContent = '● Candidate Status: Foundational Review Required';
      statusBadge.className = 'badge badge-danger';
    }
  }

  // 3. Four Core Dimensions (Technical, Quality, Communication, Confidence)
  const scores = data.scores || {};
  
  // Technical
  const tech = scores.technical || {};
  safeSetText('tech-score-raw', `${Number(tech.score_5 || 1).toFixed(1)} / 5.0`);
  safeSetText('tech-score-pct', `${Number(tech.percentage || 20).toFixed(0)}%`);
  setBarWidth('tech-progress-bar', tech.percentage || 20);

  // Answer Quality
  const qual = scores.quality || {};
  safeSetText('qual-score-raw', `${Number(qual.score_5 || 1).toFixed(1)} / 5.0`);
  safeSetText('qual-score-pct', `${Number(qual.percentage || 20).toFixed(0)}%`);
  setBarWidth('qual-progress-bar', qual.percentage || 20);

  // Communication
  const comm = scores.communication || {};
  safeSetText('comm-score-raw', `${Number(comm.score_5 || 1).toFixed(1)} / 5.0`);
  safeSetText('comm-score-pct', `${Number(comm.percentage || 20).toFixed(0)}%`);
  setBarWidth('comm-progress-bar', comm.percentage || 20);

  // Confidence Estimate
  const conf = scores.confidence || {};
  safeSetText('conf-score-raw', `${Number(conf.score_5 || 1).toFixed(1)} / 5.0`);
  safeSetText('conf-score-pct', `${Number(conf.percentage || 20).toFixed(0)}%`);
  setBarWidth('conf-progress-bar', conf.percentage || 20);

  // AI Engine Info
  if (data.ai_service_info && data.ai_service_info.engine) {
    safeSetText('ai-engine-source-label', data.ai_service_info.engine);
  }

  // 4. Personalized Feedback Lists (Strengths, Weaknesses, Recommendations)
  renderBulletList('strengths-list-container', data.strengths || [], '✓', 'color: #34d399;');
  renderBulletList('weaknesses-list-container', data.weaknesses || [], '•', 'color: #fbbf24;');
  renderBulletList('recommendations-list-container', data.recommendations || [], '→', 'color: #60a5fa;');

  // 5. Question-by-Question Detailed Audit Breakdown
  renderQuestionsDetail(data.questions_details || []);
}

/**
 * Populates a structured bullet point feedback card
 */
function renderBulletList(containerId, items, symbol, symbolStyle) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';

  if (!items || items.length === 0) {
    container.innerHTML = `<li style="color: var(--text-muted); font-size: 0.85rem;">None recorded for this session.</li>`;
    return;
  }

  items.forEach(item => {
    // Strip leading bullets/checkmarks if already formatted
    let cleanText = item.replace(/^[✓•\-\*→]\s*/, '').trim();
    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.alignItems = 'flex-start';
    li.style.gap = '0.65rem';
    li.style.marginBottom = '0.75rem';
    li.style.fontSize = '0.92rem';
    li.style.lineHeight = '1.5';
    li.style.color = '#e2e8f0';

    li.innerHTML = `
      <span style="font-weight: bold; ${symbolStyle}">${symbol}</span>
      <span>${escapeHtml(cleanText)}</span>
    `;
    container.appendChild(li);
  });
}

/**
 * Renders the question-by-question technical details breakdown
 */
function renderQuestionsDetail(questions) {
  const container = document.getElementById('interview-details-container');
  if (!container) return;

  container.innerHTML = '';

  if (!questions || questions.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 1.5rem;">No detailed question transcripts available.</p>`;
    return;
  }

  questions.forEach(q => {
    const card = document.createElement('div');
    card.className = 'glass-card question-audit-card';
    card.style.marginBottom = '1.5rem';
    card.style.border = '1px solid rgba(255, 255, 255, 0.08)';

    const s = q.scores || {};
    const techScore = s.technical || 1;
    const commScore = s.communication || 1;
    const qualScore = s.quality || 1;
    const confScore = s.confidence || 1;

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.85rem;">
        <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
          <span class="badge badge-primary">Q${q.order} &bull; ${escapeHtml(q.question_code)}</span>
          <span class="badge badge-glass">${escapeHtml(q.language)}</span>
          <span class="badge badge-glass">${escapeHtml(q.topic)}</span>
          <span class="badge badge-warning" style="font-size: 0.72rem;">${escapeHtml(q.difficulty)}</span>
        </div>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <span class="score-pill" title="Technical Knowledge">Tech: <strong>${techScore}/5</strong></span>
          <span class="score-pill" title="Communication Clarity">Comm: <strong>${commScore}/5</strong></span>
          <span class="score-pill" title="Answer Quality">Quality: <strong>${qualScore}/5</strong></span>
          <span class="score-pill" title="Confidence Estimate (Observable Indicators)">Conf: <strong>${confScore}/5</strong></span>
        </div>
      </div>

      <!-- Question Text -->
      <div style="padding: 1rem; background: rgba(255, 255, 255, 0.03); border-left: 3px solid #6366f1; border-radius: var(--radius-sm); margin-bottom: 1rem;">
        <strong style="color: #ffffff; font-size: 1.05rem; line-height: 1.4;">${escapeHtml(q.question_text)}</strong>
      </div>

      <!-- Candidate Answer Transcript -->
      <div style="margin-bottom: 1rem;">
        <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 0.25rem;">
          Candidate Response Transcript (Speech/Typed):
          ${q.status === 'skipped' ? '<span class="badge badge-danger" style="margin-left: 0.5rem;">SKIPPED</span>' : ''}
        </span>
        <div style="padding: 0.85rem 1rem; background: rgba(0, 0, 0, 0.25); border-radius: var(--radius-sm); font-size: 0.9rem; color: #cbd5e1; font-style: italic; line-height: 1.5;">
          "${escapeHtml(q.answer_text)}"
        </div>
      </div>

      <!-- AI Evaluation & Feedback -->
      <div class="grid-2" style="gap: 1rem; margin-top: 0.75rem;">
        <div style="padding: 0.75rem; background: rgba(16, 185, 129, 0.08); border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
          <strong style="font-size: 0.8rem; color: #34d399; text-transform: uppercase; display: block; margin-bottom: 0.2rem;">Observed Strength</strong>
          <span style="font-size: 0.85rem; color: #e2e8f0;">${escapeHtml(q.strength || 'Good technical effort.')}</span>
        </div>
        <div style="padding: 0.75rem; background: rgba(245, 158, 11, 0.08); border-radius: var(--radius-sm); border: 1px solid rgba(245, 158, 11, 0.2);">
          <strong style="font-size: 0.8rem; color: #fbbf24; text-transform: uppercase; display: block; margin-bottom: 0.2rem;">Area for Improvement</strong>
          <span style="font-size: 0.85rem; color: #e2e8f0;">${escapeHtml(q.improvement || 'Review conceptual fundamentals.')}</span>
        </div>
      </div>

      <div style="margin-top: 0.75rem; font-size: 0.85rem; color: #94a3b8; line-height: 1.4;">
        <strong style="color: #c7d2fe;">Evaluator Feedback:</strong> ${escapeHtml(q.feedback || 'Completed.')}
      </div>
    `;

    container.appendChild(card);
  });
}

/**
 * Toggles the detailed question breakdown accordion
 */
function toggleInterviewDetails() {
  const container = document.getElementById('details-accordion-wrapper');
  const btn = document.getElementById('toggle-details-btn');
  if (!container) return;

  const isHidden = container.style.display === 'none' || container.style.display === '';
  if (isHidden) {
    container.style.display = 'block';
    if (btn) btn.innerHTML = '▲ Hide Detailed Answers';
    container.scrollIntoView({ behavior: 'smooth' });
  } else {
    container.style.display = 'none';
    if (btn) btn.innerHTML = '▼ [ View Interview Details ]';
  }
}

// Utility Helpers
function safeSetText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setBarWidth(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = `${Math.max(0, Math.min(100, pct))}%`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
