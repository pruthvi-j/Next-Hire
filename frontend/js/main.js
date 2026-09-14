/**
 * NEXT HIRE - Core Utilities & Session Guard
 * MCA Academic Project - Phase 1 & 2
 */

// Determine API base URL dynamically
const API_BASE = window.location.port === '5000' || window.location.protocol === 'file:' 
  ? '' 
  : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
      ? 'http://127.0.0.1:5000' 
      : '');

/**
 * Display a floating toast notification
 */
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/**
 * Display an inline alert message inside an alert box
 */
function showAlert(elementId, message, type = 'danger') {
  const alertBox = document.getElementById(elementId);
  if (!alertBox) return;

  alertBox.className = `alert alert-${type}`;
  alertBox.textContent = message;
  alertBox.style.display = 'flex';
}

/**
 * Clear an inline alert message
 */
function hideAlert(elementId) {
  const alertBox = document.getElementById(elementId);
  if (alertBox) {
    alertBox.style.display = 'none';
  }
}

/**
 * Check current authentication state via GET /api/user
 * @param {boolean} requiresAuth - If true, unauthenticated users are redirected to login.html
 * @param {boolean} redirectIfAuth - If true (e.g. on login/register), authenticated users are redirected to dashboard.html
 */
async function checkAuth(requiresAuth = false, redirectIfAuth = false) {
  try {
    const response = await fetch(`${API_BASE}/api/user`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json'
      }
    });

    const data = await response.json();

    if (data.authenticated && data.user) {
      // User is logged in
      if (redirectIfAuth) {
        window.location.href = 'dashboard.html';
        return data.user;
      }

      // Update user info in navbar if elements exist
      const userNameEl = document.getElementById('nav-user-name');
      if (userNameEl) {
        userNameEl.textContent = data.user.name;
      }
      return data.user;
    } else {
      // User is not logged in
      if (requiresAuth) {
        window.location.href = 'login.html';
        return null;
      }
    }
  } catch (error) {
    console.warn('[NextHire Auth Check] Could not verify session:', error);
    if (requiresAuth) {
      window.location.href = 'login.html';
    }
  }
  return null;
}

/**
 * Perform user logout via POST /api/logout
 */
async function handleLogout() {
  try {
    const response = await fetch(`${API_BASE}/api/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();
    showToast(data.message || 'Logged out successfully', 'success');
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    window.location.href = 'login.html';
  }
}

/**
 * Initialize password toggle eye icons
 */
function initPasswordToggles() {
  const toggleButtons = document.querySelectorAll('.password-toggle');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          btn.innerHTML = '👁️';
          btn.setAttribute('title', 'Hide password');
        } else {
          input.type = 'password';
          btn.innerHTML = '🙈';
          btn.setAttribute('title', 'Show password');
        }
      }
    });
  });
}

// Global initialization on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();

  // Attach logout handler if button exists
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      handleLogout();
    });
  }
});
