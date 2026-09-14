/**
 * NEXT HIRE - Resume Ingestion (Phase 3) & Role Analyzer (Phase 4)
 * MCA Academic Project
 */

let selectedFile = null;
let currentResumeData = null;
let selectedRoleId = null;
let availableRoles = [];

document.addEventListener('DOMContentLoaded', async () => {
  // Enforce session authentication
  const user = await checkAuth(true);
  if (!user) return;

  const dropzone = document.getElementById('resume-dropzone');
  const fileInput = document.getElementById('resume-file-input');
  const chooseFileBtn = document.getElementById('choose-file-btn');
  const fileInfoBox = document.getElementById('selected-file-info');
  const fileNameDisplay = document.getElementById('selected-file-name');
  const fileSizeBadge = document.getElementById('file-size-badge');
  const uploadBtn = document.getElementById('upload-submit-btn');
  const reuploadBtn = document.getElementById('reupload-btn');
  const analyzeRoleBtn = document.getElementById('analyze-role-btn');

  // Load available roles & check for previously parsed resume
  await loadRoles();
  await loadExistingResume();

  // File picker triggers
  if (chooseFileBtn && fileInput) {
    chooseFileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileValidation(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileValidation(fileInput.files[0]);
      }
    });
  }

  // Re-upload button
  if (reuploadBtn) {
    reuploadBtn.addEventListener('click', () => {
      document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
      fileInput.value = '';
      selectedFile = null;
      uploadBtn.disabled = true;
      fileInfoBox.style.display = 'none';
      showToast('Select a new PDF or DOCX resume to upload.', 'info');
    });
  }

  // Upload & Parse Action
  if (uploadBtn) {
    uploadBtn.addEventListener('click', async () => {
      if (!selectedFile) {
        showAlert('upload-alert', 'Please select a resume file before uploading.', 'danger');
        return;
      }

      hideAlert('upload-alert');
      uploadBtn.disabled = true;
      const originalText = uploadBtn.innerHTML;
      uploadBtn.innerHTML = '<span>Parsing with PyMuPDF / python-docx...</span>';

      const formData = new FormData();
      formData.append('resume', selectedFile);

      try {
        const response = await fetch(`${API_BASE}/api/resume/upload`, {
          method: 'POST',
          credentials: 'include',
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
          showToast('Resume uploaded and parsed successfully!', 'success');
          currentResumeData = result.data;
          renderParsedResume(result.data);

          // If a role was already selected, trigger analysis
          if (selectedRoleId) {
            analyzeSelectedRole(selectedRoleId);
          } else {
            // Auto-select first role for convenience
            if (availableRoles.length > 0) {
              selectRoleCard(availableRoles[0].id);
            }
          }
        } else {
          showAlert('upload-alert', result.message || 'Failed to parse resume file.', 'danger');
        }
      } catch (err) {
        console.error('Resume upload error:', err);
        showAlert('upload-alert', 'Network error while uploading resume. Please ensure backend is reachable.', 'danger');
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = originalText;
      }
    });
  }

  // Analyze Role Action
  if (analyzeRoleBtn) {
    analyzeRoleBtn.addEventListener('click', () => {
      if (!selectedRoleId) {
        showAlert('upload-alert', 'Please select a target job role to analyze.', 'danger');
        return;
      }
      analyzeSelectedRole(selectedRoleId);
    });
  }
});

/**
 * Validates selected file format and size
 */
function handleFileValidation(file) {
  hideAlert('upload-alert');
  if (!file) return;

  const validExts = ['.pdf', '.docx'];
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

  if (!validExts.includes(ext)) {
    showAlert('upload-alert', `Unsupported file type "${ext}". Please upload a PDF (.pdf) or Word (.docx) document.`, 'danger');
    selectedFile = null;
    document.getElementById('upload-submit-btn').disabled = true;
    document.getElementById('selected-file-info').style.display = 'none';
    return;
  }

  // 10MB limit
  if (file.size > 10 * 1024 * 1024) {
    showAlert('upload-alert', 'File size exceeds 10MB limit. Please choose a smaller document.', 'danger');
    selectedFile = null;
    document.getElementById('upload-submit-btn').disabled = true;
    document.getElementById('selected-file-info').style.display = 'none';
    return;
  }

  selectedFile = file;

  // Display file info
  const fileInfoBox = document.getElementById('selected-file-info');
  const fileNameDisplay = document.getElementById('selected-file-name');
  const fileSizeBadge = document.getElementById('file-size-badge');
  const uploadBtn = document.getElementById('upload-submit-btn');

  fileNameDisplay.textContent = file.name;
  fileSizeBadge.textContent = `${(file.size / 1024).toFixed(1)} KB &bull; ${ext.toUpperCase().replace('.', '')}`;
  fileSizeBadge.innerHTML = `${(file.size / 1024).toFixed(1)} KB &bull; ${ext.toUpperCase().replace('.', '')}`;
  fileInfoBox.style.display = 'block';
  uploadBtn.disabled = false;

  showToast(`Attached: ${file.name}`, 'info');
}

/**
 * Checks for previously parsed resume on page load
 */
async function loadExistingResume() {
  try {
    const response = await fetch(`${API_BASE}/api/resume`, {
      method: 'GET',
      credentials: 'include'
    });

    if (response.ok) {
      const result = await response.json();
      if (result.has_resume && result.data) {
        currentResumeData = result.data;
        renderParsedResume(result.data);

        // Load existing role analysis if present
        loadExistingRoleAnalysis();
      }
    }
  } catch (err) {
    console.warn('Could not load existing resume profile:', err);
  }
}

/**
 * Loads all benchmark roles from GET /api/roles
 */
async function loadRoles() {
  const container = document.getElementById('roles-cards-container');
  if (!container) return;

  try {
    const response = await fetch(`${API_BASE}/api/roles`);
    if (response.ok) {
      const result = await response.json();
      availableRoles = result.data || [];

      container.innerHTML = '';
      availableRoles.forEach(role => {
        const card = document.createElement('div');
        card.className = 'role-option-card';
        card.setAttribute('data-role-id', role.id);
        card.id = `role-card-${role.id}`;

        const skillsPreview = role.skills.slice(0, 4).join(', ');
        card.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <h4 style="color: #ffffff;">${role.role_name}</h4>
            <span class="badge badge-primary" style="font-size: 0.7rem;">${role.skills.length} Skills</span>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem; line-height: 1.4;">
            ${role.description}
          </p>
          <div style="font-size: 0.75rem; color: #a5b4fc;">
            <strong>Prerequisites:</strong> ${skillsPreview}...
          </div>
        `;

        card.addEventListener('click', () => {
          selectRoleCard(role.id);
        });

        container.appendChild(card);
      });
    }
  } catch (err) {
    console.error('Failed to fetch benchmark roles:', err);
  }
}

/**
 * Handles selecting a role card and triggers analysis if resume exists
 */
function selectRoleCard(roleId) {
  selectedRoleId = roleId;
  const cards = document.querySelectorAll('.role-option-card');
  cards.forEach(c => c.classList.remove('active'));

  const activeCard = document.getElementById(`role-card-${roleId}`);
  if (activeCard) {
    activeCard.classList.add('active');
  }

  const role = availableRoles.find(r => r.id === roleId);
  const promptText = document.getElementById('role-select-prompt');
  const analyzeBtn = document.getElementById('analyze-role-btn');

  if (role) {
    if (promptText) {
      promptText.innerHTML = `Selected: <strong style="color: #67e8f9;">${role.role_name}</strong>`;
    }
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
    }

    // If resume is parsed, auto-run analysis
    if (currentResumeData) {
      analyzeSelectedRole(roleId);
    }
  }
}

/**
 * Calls POST /api/roles/analyze and renders matching scorecard
 */
async function analyzeSelectedRole(roleId) {
  const resultsContainer = document.getElementById('role-analysis-results');
  const analyzeBtn = document.getElementById('analyze-role-btn');

  if (analyzeBtn) {
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Comparing Skills...';
  }

  try {
    const response = await fetch(`${API_BASE}/api/roles/analyze`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        role_id: roleId,
        resume_id: currentResumeData ? currentResumeData.resume_id : null
      })
    });

    const result = await response.json();

    if (response.ok && result.status === 'success') {
      renderRoleAnalysis(result.data);
      if (resultsContainer) {
        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
      }
      showToast(`Skill comparison complete for ${result.data.role_name}!`, 'success');
    } else {
      showAlert('upload-alert', result.message || 'Could not complete role analysis.', 'danger');
    }
  } catch (err) {
    console.error('Role analysis error:', err);
    showAlert('upload-alert', 'Network error during role analysis.', 'danger');
  } finally {
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = 'Re-Analyze Match &rarr;';
    }
  }
}

/**
 * Loads existing role analysis if user previously selected one
 */
async function loadExistingRoleAnalysis() {
  try {
    const response = await fetch(`${API_BASE}/api/roles/current`, {
      method: 'GET',
      credentials: 'include'
    });

    if (response.ok) {
      const result = await response.json();
      if (result.has_selection && result.data) {
        selectedRoleId = result.data.role_id;
        const card = document.getElementById(`role-card-${selectedRoleId}`);
        if (card) card.classList.add('active');
        renderRoleAnalysis(result.data);
        const resultsContainer = document.getElementById('role-analysis-results');
        if (resultsContainer) resultsContainer.style.display = 'block';
      }
    }
  } catch (err) {
    console.warn('Could not load current role selection:', err);
  }
}

/**
 * Renders parsed resume content into the Liquid Glass UI
 */
function renderParsedResume(data) {
  const container = document.getElementById('parsed-results-container');
  if (!container) return;

  document.getElementById('parsed-filename').textContent = data.filename || 'Document';
  document.getElementById('parsed-name').textContent = data.candidate_name || 'Not Detected';
  document.getElementById('parsed-email').textContent = data.email || 'Not Provided';
  document.getElementById('parsed-phone').textContent = data.phone || 'Not Provided';
  document.getElementById('parsed-education').textContent = data.education || 'Academic Degree';
  document.getElementById('parsed-experience').textContent = data.experience || 'Coursework & Projects';

  // Render Categorized Skills
  const skillsContainer = document.getElementById('categorized-skills-container');
  skillsContainer.innerHTML = '';

  if (data.categorized_skills && Object.keys(data.categorized_skills).length > 0) {
    for (const [category, skills] of Object.entries(data.categorized_skills)) {
      const catBox = document.createElement('div');
      catBox.innerHTML = `
        <div style="font-size: 0.85rem; font-weight: 600; color: #a5b4fc; margin-bottom: 0.35rem;">
          ${category} (${skills.length})
        </div>
        <div style="display: flex; flex-wrap: wrap;">
          ${skills.map(s => `<span class="skill-pill skill-pill-default">${s}</span>`).join('')}
        </div>
      `;
      skillsContainer.appendChild(catBox);
    }
  } else if (data.all_skills && data.all_skills.length > 0) {
    skillsContainer.innerHTML = `
      <div style="display: flex; flex-wrap: wrap;">
        ${data.all_skills.map(s => `<span class="skill-pill skill-pill-default">${s}</span>`).join('')}
      </div>
    `;
  } else {
    skillsContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">No technical keywords identified. Consider adding clear skill sections.</span>';
  }

  // Render Projects
  const projectsList = document.getElementById('parsed-projects-list');
  projectsList.innerHTML = '';
  if (data.projects && data.projects.length > 0) {
    data.projects.forEach(p => {
      const item = document.createElement('div');
      item.style.padding = '0.5rem 0.75rem';
      item.style.background = 'rgba(255, 255, 255, 0.02)';
      item.style.borderRadius = 'var(--radius-sm)';
      item.innerHTML = `
        <strong style="color: #ffffff; display: block; font-size: 0.9rem;">📌 ${p.title}</strong>
        <span style="color: var(--text-secondary); font-size: 0.85rem;">${p.description}</span>
      `;
      projectsList.appendChild(item);
    });
  } else {
    projectsList.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">No explicit projects section detected.</span>';
  }

  // Render Certifications
  const certsList = document.getElementById('parsed-certs-list');
  certsList.innerHTML = '';
  if (data.certifications && data.certifications.length > 0) {
    data.certifications.forEach(c => {
      const li = document.createElement('li');
      li.style.marginBottom = '0.4rem';
      li.innerHTML = `✔ ${c}`;
      certsList.appendChild(li);
    });
  } else {
    certsList.innerHTML = '<li style="color: var(--text-muted); font-size: 0.85rem;">No certifications detected.</li>';
  }

  container.style.display = 'block';
}

/**
 * Renders role matching analysis output
 */
function renderRoleAnalysis(analysis) {
  document.getElementById('match-role-title').textContent = analysis.role_name;
  document.getElementById('match-role-desc').textContent = analysis.description || '';
  document.getElementById('match-percentage-display').textContent = `${analysis.match_percentage}%`;

  // Color coordinate match percentage
  const pctDisplay = document.getElementById('match-percentage-display');
  const progressBar = document.getElementById('match-progress-bar');
  progressBar.style.width = `${analysis.match_percentage}%`;

  const badgeDisplay = document.getElementById('readiness-badge-display');
  badgeDisplay.className = `badge badge-${analysis.readiness_badge || 'primary'}`;
  badgeDisplay.innerHTML = analysis.readiness_rating;

  if (analysis.match_percentage >= 80) {
    pctDisplay.style.color = '#34d399';
    progressBar.style.background = 'linear-gradient(90deg, #10b981, #06b6d4)';
  } else if (analysis.match_percentage >= 50) {
    pctDisplay.style.color = '#fbbf24';
    progressBar.style.background = 'linear-gradient(90deg, #f59e0b, #6366f1)';
  } else {
    pctDisplay.style.color = '#f87171';
    progressBar.style.background = 'linear-gradient(90deg, #ef4444, #f59e0b)';
  }

  document.getElementById('match-ratio-text').textContent = 
    `${analysis.matched_count} of ${analysis.total_skills} Skills Matched`;
  document.getElementById('matched-count-badge').textContent = `${analysis.matched_count} Matched`;
  document.getElementById('missing-count-badge').textContent = `${analysis.missing_count} Recommended`;

  // Matched skills pills
  const matchedContainer = document.getElementById('matched-skills-container');
  matchedContainer.innerHTML = '';
  if (analysis.matched_skills && analysis.matched_skills.length > 0) {
    analysis.matched_skills.forEach(s => {
      const pill = document.createElement('span');
      pill.className = 'skill-pill skill-pill-matched';
      pill.innerHTML = `✓ ${s}`;
      matchedContainer.appendChild(pill);
    });
  } else {
    matchedContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">None of the core role prerequisites were found in the current resume.</span>';
  }

  // Missing / Recommended skills pills
  const missingContainer = document.getElementById('missing-skills-container');
  missingContainer.innerHTML = '';
  if (analysis.missing_skills && analysis.missing_skills.length > 0) {
    analysis.missing_skills.forEach(s => {
      const pill = document.createElement('span');
      pill.className = 'skill-pill skill-pill-missing';
      pill.innerHTML = `• ${s}`;
      missingContainer.appendChild(pill);
    });
  } else {
    missingContainer.innerHTML = '<span style="color: #34d399; font-size: 0.85rem;">Outstanding! All required skills are satisfied by your resume profile.</span>';
  }
}
