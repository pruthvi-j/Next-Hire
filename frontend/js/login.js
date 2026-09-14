/**
 * NEXT HIRE - Login Logic
 * MCA Academic Project - Phase 1 & 2
 */

document.addEventListener('DOMContentLoaded', async () => {
  // If user is already authenticated, redirect straight to dashboard
  await checkAuth(false, true);

  const loginForm = document.getElementById('login-form');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const submitBtn = document.getElementById('login-submit-btn');

  // Check if URL has registration success query param
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('registered') === 'true') {
    showAlert('login-alert', 'Registration complete! Please log in with your credentials.', 'success');
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert('login-alert');

      const email = emailInput.value.trim();
      const password = passwordInput.value;

      if (!email || !password) {
        showAlert('login-alert', 'Please enter both your email address and password.', 'danger');
        return;
      }

      // Set button loading state
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<span>Verifying...</span>';

      try {
        const response = await fetch(`${API_BASE}/api/login`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
          showToast('Login successful! Redirecting...', 'success');
          setTimeout(() => {
            window.location.href = 'dashboard.html';
          }, 600);
        } else {
          showAlert('login-alert', data.message || 'Invalid email or password.', 'danger');
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      } catch (err) {
        console.error('Login error:', err);
        showAlert('login-alert', 'Unable to reach the server. Please check your backend connection.', 'danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
});
