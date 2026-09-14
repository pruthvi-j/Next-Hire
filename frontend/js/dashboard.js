/**
 * NEXT HIRE - Candidate Dashboard Logic
 * MCA Academic Project - Phase 1 & 2
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Enforce authentication
  const user = await checkAuth(true);
  if (!user) return; // Will be redirected to login.html by checkAuth

  // Display user name in header and navbar
  const welcomeNameEl = document.getElementById('dashboard-welcome-name');
  if (welcomeNameEl) {
    welcomeNameEl.textContent = user.name;
  }
  const navUserEl = document.getElementById('nav-user-name');
  if (navUserEl) {
    navUserEl.textContent = user.name;
  }

  // Fetch dashboard metrics
  try {
    const response = await fetch(`${API_BASE}/api/dashboard`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (response.ok) {
      const result = await response.json();
      if (result.status === 'success' && result.data) {
        const data = result.data;
        
        // Update stats
        const statInterviews = document.getElementById('stat-interviews');
        if (statInterviews) statInterviews.textContent = data.stats.interviews_completed;

        const statResumes = document.getElementById('stat-resumes');
        if (statResumes) statResumes.textContent = data.stats.resumes_analyzed;

        const statScore = document.getElementById('stat-score');
        if (statScore) statScore.textContent = data.stats.readiness_score;

        const statRole = document.getElementById('stat-role');
        if (statRole) statRole.textContent = data.stats.target_role;

        // Render Recent Activity table rows
        const activityList = document.getElementById('recent-activity-tbody');
        if (activityList && data.recent_activity) {
          activityList.innerHTML = '';
          data.recent_activity.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td><strong>${item.title}</strong></td>
              <td><span class="badge badge-primary">${item.category}</span></td>
              <td>${item.date}</td>
              <td><span class="badge badge-success">${item.status}</span></td>
            `;
            activityList.appendChild(row);
          });
        }
      }
    }
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
  }
});
