/**
 * NEXT HIRE - Candidate Assessment History Controller (Phase 9)
 * Liquid Glass UI, Session Filtering, Detail Modal & PDF Access
 */

let allHistoryRecords = [];

document.addEventListener('DOMContentLoaded', async () => {
  const user = await checkAuth(true);
  if (!user) return;

  await loadHistoryRecords();
  bindHistoryEvents();
});

/**
 * Loads historical interview records for the current authenticated user
 */
async function loadHistoryRecords() {
  const tbody = document.getElementById('history-table-body');
  const cardsContainer = document.getElementById('history-cards-container');
  const emptyNotice = document.getElementById('history-empty-notice');

  try {
    const response = await fetch(`${API_BASE}/api/interviews/history`, {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: Failed to load interview history.`);
    }

    const resJson = await response.json();
    allHistoryRecords = resJson.data || [];

    renderHistory(allHistoryRecords);

  } catch (error) {
    console.error('[History Error]', error);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: #f87171; padding: 2rem;">
            Failed to load interview history: ${escapeHtml(error.message)}
          </td>
        </tr>
      `;
    }
  }
}

/**
 * Renders the history records into table and card formats
 */
function renderHistory(records) {
  const tbody = document.getElementById('history-table-body');
  const cardsContainer = document.getElementById('history-cards-container');
  const emptyNotice = document.getElementById('history-empty-notice');
  const countBadge = document.getElementById('total-records-count');

  if (countBadge) countBadge.textContent = records.length;

  if (!records || records.length === 0) {
    if (tbody) tbody.innerHTML = '';
    if (cardsContainer) cardsContainer.innerHTML = '';
    if (emptyNotice) emptyNotice.style.display = 'block';
    return;
  }

  if (emptyNotice) emptyNotice.style.display = 'none';

  // 1. Render Table Rows
  if (tbody) {
    tbody.innerHTML = '';
    records.forEach(item => {
      const isDone = item.status === 'completed';
      const scoreText = item.score_display || (item.overall_score ? `Score: ${(item.overall_score / 20).toFixed(1)} / 5` : 'In Progress');
      const row = document.createElement('tr');
      row.style.cursor = 'pointer';
      row.title = 'Click to inspect interview evaluation details';

      row.innerHTML = `
        <td><strong style="color: #c7d2fe;">${escapeHtml(item.session_code)}</strong></td>
        <td>
          <div style="font-weight: 600; color: #ffffff;">${escapeHtml(item.role_name)}</div>
          <span class="badge badge-glass" style="font-size: 0.7rem;">${escapeHtml(item.difficulty)}</span>
        </td>
        <td>${escapeHtml(item.date)}</td>
        <td>
          <span class="badge badge-glass" style="font-size: 0.8rem;">${item.answered_count} / ${item.total_questions} Questions</span>
        </td>
        <td>
          <strong style="color: ${isDone ? '#34d399' : '#fbbf24'}; font-size: 0.95rem;">
            ${escapeHtml(scoreText)}
          </strong>
        </td>
        <td>
          <span class="badge badge-${isDone ? 'success' : 'warning'}">
            ${isDone ? 'Completed' : 'In Progress'}
          </span>
        </td>
        <td style="text-align: right;" onclick="event.stopPropagation();">
          <div style="display: inline-flex; gap: 0.4rem;">
            <button type="button" class="btn btn-primary btn-sm" onclick="openInterviewModal(${item.id})">
              Details
            </button>
            ${isDone ? `
              <a href="${API_BASE}/api/interview/${item.id}/pdf" download="NextHire_Report_NH_${String(item.id).padStart(3, '0')}.pdf" class="btn btn-glass btn-sm" title="Download PDF Report">
                📄 PDF
              </a>
            ` : `
              <a href="interview.html" class="btn btn-glass btn-sm">Resume</a>
            `}
          </div>
        </td>
      `;

      row.addEventListener('click', () => openInterviewModal(item.id));
      tbody.appendChild(row);
    });
  }

  // 2. Render Responsive Cards Grid
  if (cardsContainer) {
    cardsContainer.innerHTML = '';
    records.forEach(item => {
      const isDone = item.status === 'completed';
      const scoreText = item.score_display || (item.overall_score ? `Score: ${(item.overall_score / 20).toFixed(1)} / 5` : 'In Progress');

      const card = document.createElement('div');
      card.className = 'glass-card history-session-card';
      card.style.padding = '1.5rem';
      card.style.display = 'flex';
      card.style.flexDirection = 'column';
      card.style.justifyContent = 'space-between';
      card.style.cursor = 'pointer';

      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <span class="badge badge-primary">${escapeHtml(item.session_code)}</span>
            <span class="badge badge-${isDone ? 'success' : 'warning'}">${isDone ? 'Completed' : 'In Progress'}</span>
          </div>
          <h3 style="font-size: 1.25rem; color: #ffffff; margin-bottom: 0.25rem;">${escapeHtml(item.role_name)}</h3>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
            📅 ${escapeHtml(item.date)} &bull; ${item.total_questions} Questions
          </div>
          <div style="padding: 0.75rem 1rem; background: rgba(255, 255, 255, 0.03); border-radius: var(--radius-sm); border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 1.25rem;">
            <span style="font-size: 0.75rem; color: var(--text-muted); display: block; text-transform: uppercase;">Assessment Score</span>
            <strong style="font-size: 1.35rem; color: ${isDone ? '#34d399' : '#fbbf24'};">
              ${escapeHtml(scoreText)}
            </strong>
          </div>
        </div>
        <div style="display: flex; gap: 0.5rem; justify-content: space-between; align-items: center;" onclick="event.stopPropagation();">
          <button type="button" class="btn btn-primary btn-sm" style="flex: 1;" onclick="openInterviewModal(${item.id})">
            View Details
          </button>
          <a href="result.html?id=${item.id}" class="btn btn-glass btn-sm" title="Open Scorecard Page">
            Full Scorecard &rarr;
          </a>
          ${isDone ? `
            <a href="${API_BASE}/api/interview/${item.id}/pdf" download="NextHire_Report_NH_${String(item.id).padStart(3, '0')}.pdf" class="btn btn-glass btn-sm" title="Download PDF Report">
              📄 PDF
            </a>
          ` : ''}
        </div>
      `;

      card.addEventListener('click', () => openInterviewModal(item.id));
      cardsContainer.appendChild(card);
    });
  }
}

/**
 * Opens detailed evaluation modal for a specific interview
 */
async function openInterviewModal(interviewId) {
  const modal = document.getElementById('history-detail-modal');
  const modalBody = document.getElementById('modal-detail-content');
  if (!modal || !modalBody) return;

  modal.style.display = 'flex';
  modalBody.innerHTML = `
    <div style="text-align: center; padding: 3rem 1rem;">
      <div style="font-size: 2rem; margin-bottom: 0.5rem; animation: orbDrift 2s infinite ease-in-out;">⏳</div>
      <h3>Loading Session Details...</h3>
      <p style="color: var(--text-muted);">Fetching questions, answers, and diagnostic scores from database.</p>
    </div>
  `;

  try {
    const response = await fetch(`${API_BASE}/api/interview/${interviewId}/result`, {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: Failed to fetch interview details.`);
    }

    const payload = await response.json();
    const data = payload.data;

    renderModalContent(data);

  } catch (err) {
    console.error('[Modal Error]', err);
    modalBody.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: #f87171;">
        <h3>Failed to Load Interview Details</h3>
        <p style="color: var(--text-secondary); margin: 0.5rem 0 1.5rem;">${escapeHtml(err.message)}</p>
        <button type="button" class="btn btn-glass" onclick="closeHistoryModal()">Close</button>
      </div>
    `;
  }
}

/**
 * Renders loaded interview results inside the modal
 */
function renderModalContent(data) {
  const modalBody = document.getElementById('modal-detail-content');
  if (!modalBody) return;

  const overall = Number(data.overall_score || 0).toFixed(1);
  const score5 = (overall / 20).toFixed(1);
  const pdfUrl = `${API_BASE}/api/interview/${data.interview_id}/pdf`;
  const pdfFileName = `NextHire_Report_NH_${String(data.interview_id).padStart(3, '0')}.pdf`;

  const scores = data.scores || {};
  const tech = scores.technical || {};
  const comm = scores.communication || {};
  const qual = scores.quality || {};
  const conf = scores.confidence || {};

  const strengthsList = (data.strengths || []).map(s => `<li style="margin-bottom: 0.4rem; color: #a7f3d0;">✓ ${escapeHtml(s.replace(/^[✓•\-\*→]\s*/, ''))}</li>`).join('') || '<li style="color: var(--text-muted);">None recorded</li>';
  const weaknessesList = (data.weaknesses || []).map(w => `<li style="margin-bottom: 0.4rem; color: #fde68a;">• ${escapeHtml(w.replace(/^[✓•\-\*→]\s*/, ''))}</li>`).join('') || '<li style="color: var(--text-muted);">None recorded</li>';
  const recsList = (data.recommendations || []).map(r => `<li style="margin-bottom: 0.4rem; color: #c7d2fe;">→ ${escapeHtml(r.replace(/^[✓•\-\*→]\s*/, ''))}</li>`).join('') || '<li style="color: var(--text-muted);">None recorded</li>';

  const questionsHtml = (data.questions_details || []).map(q => {
    const s = q.scores || {};
    return `
      <div class="glass-card" style="margin-bottom: 1.25rem; padding: 1.25rem; border: 1px solid rgba(255,255,255,0.08);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.65rem;">
          <div style="display: flex; gap: 0.4rem; align-items: center;">
            <span class="badge badge-primary">Q${q.order} &bull; ${escapeHtml(q.question_code)}</span>
            <span class="badge badge-glass">${escapeHtml(q.language)}</span>
            <span class="badge badge-glass">${escapeHtml(q.topic)}</span>
          </div>
          <div style="display: flex; gap: 0.35rem; font-size: 0.75rem;">
            <span class="score-pill">Tech: <strong>${s.technical || 1}/5</strong></span>
            <span class="score-pill">Comm: <strong>${s.communication || 1}/5</strong></span>
            <span class="score-pill">Qual: <strong>${s.quality || 1}/5</strong></span>
            <span class="score-pill">Conf: <strong>${s.confidence || 1}/5</strong></span>
          </div>
        </div>

        <div style="padding: 0.75rem 1rem; background: rgba(255,255,255,0.04); border-left: 3px solid #6366f1; border-radius: var(--radius-sm); margin-bottom: 0.75rem;">
          <strong style="color: #ffffff; font-size: 0.95rem;">${escapeHtml(q.question_text)}</strong>
        </div>

        <div style="font-size: 0.88rem; color: #cbd5e1; font-style: italic; background: rgba(0,0,0,0.25); padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); margin-bottom: 0.75rem;">
          "${escapeHtml(q.answer_text)}"
        </div>

        <div style="font-size: 0.82rem; color: #94a3b8;">
          <strong style="color: #c7d2fe;">Feedback:</strong> ${escapeHtml(q.feedback || 'Completed.')}
        </div>
      </div>
    `;
  }).join('');

  modalBody.innerHTML = `
    <!-- Modal Header Info -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
      <div>
        <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.35rem;">
          <span class="badge badge-primary">#NH-2026-${String(data.interview_id).padStart(3, '0')}</span>
          <span class="badge badge-success">Completed Assessment</span>
        </div>
        <h2 style="font-size: 1.6rem; color: #ffffff;">${escapeHtml(data.role_name)}</h2>
        <span style="font-size: 0.85rem; color: var(--text-muted);">${data.total_questions} Questions &bull; Difficulty: ${escapeHtml(data.difficulty)}</span>
      </div>

      <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
        <a href="${pdfUrl}" download="${pdfFileName}" class="btn btn-primary btn-sm" style="background: linear-gradient(135deg, #10b981, #059669); border-color: #059669; display: inline-flex; align-items: center; gap: 0.35rem;">
          <span>📄 Download PDF Report</span>
        </a>
        <a href="result.html?id=${data.interview_id}" class="btn btn-glass btn-sm">
          Full Scorecard &rarr;
        </a>
      </div>
    </div>

    <!-- Scores Summary Bar -->
    <div class="grid-4" style="gap: 1rem; margin-bottom: 1.5rem;">
      <div class="scorecard-metric-card" style="text-align: center;">
        <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Overall Score</span>
        <strong style="font-size: 1.6rem; color: #10b981;">${score5} <span style="font-size: 0.9rem; color: var(--text-muted);">/ 5</span></strong>
        <span style="display: block; font-size: 0.75rem; color: #a7f3d0;">(${overall}%)</span>
      </div>
      <div class="scorecard-metric-card" style="text-align: center;">
        <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Technical Skills</span>
        <strong style="font-size: 1.6rem; color: #60a5fa;">${Number(tech.score_5 || 1).toFixed(1)} <span style="font-size: 0.9rem; color: var(--text-muted);">/ 5</span></strong>
        <span style="display: block; font-size: 0.75rem; color: #bfdbfe;">(${Number(tech.percentage || 20).toFixed(0)}%)</span>
      </div>
      <div class="scorecard-metric-card" style="text-align: center;">
        <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Communication</span>
        <strong style="font-size: 1.6rem; color: #a78bfa;">${Number(comm.score_5 || 1).toFixed(1)} <span style="font-size: 0.9rem; color: var(--text-muted);">/ 5</span></strong>
        <span style="display: block; font-size: 0.75rem; color: #ddd6fe;">(${Number(comm.percentage || 20).toFixed(0)}%)</span>
      </div>
      <div class="scorecard-metric-card" style="text-align: center;">
        <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Confidence Est.*</span>
        <strong style="font-size: 1.6rem; color: #f59e0b;">${Number(conf.score_5 || 1).toFixed(1)} <span style="font-size: 0.9rem; color: var(--text-muted);">/ 5</span></strong>
        <span style="display: block; font-size: 0.75rem; color: #fde68a;">(${Number(conf.percentage || 20).toFixed(0)}%)</span>
      </div>
    </div>

    <!-- Diagnostic Insights 3 Columns -->
    <div class="grid-3" style="gap: 1rem; margin-bottom: 2rem;">
      <div class="feedback-card" style="border-top: 3px solid #10b981; padding: 1rem;">
        <h4 style="font-size: 0.95rem; color: #a7f3d0; margin-bottom: 0.5rem;">STRENGTHS</h4>
        <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.85rem;">${strengthsList}</ul>
      </div>
      <div class="feedback-card" style="border-top: 3px solid #f59e0b; padding: 1rem;">
        <h4 style="font-size: 0.95rem; color: #fde68a; margin-bottom: 0.5rem;">AREAS TO IMPROVE</h4>
        <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.85rem;">${weaknessesList}</ul>
      </div>
      <div class="feedback-card" style="border-top: 3px solid #6366f1; padding: 1rem;">
        <h4 style="font-size: 0.95rem; color: #c7d2fe; margin-bottom: 0.5rem;">RECOMMENDATIONS</h4>
        <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.85rem;">${recsList}</ul>
      </div>
    </div>

    <!-- Questions Audit Summary -->
    <h3 style="font-size: 1.25rem; margin-bottom: 1rem;">Question &amp; Answer Transcripts</h3>
    <div style="max-height: 450px; overflow-y: auto; padding-right: 0.5rem;">
      ${questionsHtml}
    </div>
  `;
}

/**
 * Closes modal
 */
function closeHistoryModal() {
  const modal = document.getElementById('history-detail-modal');
  if (modal) modal.style.display = 'none';
}

/**
 * Event bindings & search filter
 */
function bindHistoryEvents() {
  // Search input
  const searchInput = document.getElementById('search-history');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = allHistoryRecords.filter(item => {
        return (
          item.role_name.toLowerCase().includes(q) ||
          item.session_code.toLowerCase().includes(q) ||
          item.status.toLowerCase().includes(q) ||
          (item.date && item.date.toLowerCase().includes(q))
        );
      });
      renderHistory(filtered);
    });
  }

  // Close modal on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeHistoryModal();
  });
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
