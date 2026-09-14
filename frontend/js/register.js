/**
 * NEXT HIRE - Candidate Registration Logic
 * MCA Academic Project - Phase 1 & 2
 */

document.addEventListener('DOMContentLoaded', async () => {
  // If user is already authenticated, redirect to dashboard
  await checkAuth(false, true);

  const registerForm = document.getElementById('register-form');
  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm-password');
  const strengthBar = document.getElementById('password-strength');
  const submitBtn = document.getElementById('register-submit-btn');

  // Password strength visual indicator
  if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', () => {
      const val = passwordInput.value;
      let score = 0;
      if (val.length >= 6) score += 30;
      if (/[A-Z]/.test(val)) score += 25;
      if (/[0-9]/.test(val)) score += 25;
      if (/[^A-Za-z0-9]/.test(val)) score += 20;

      strengthBar.style.width = `${Math.min(score, 100)}%`;
      if (score < 40) {
        strengthBar.style.backgroundColor = '#f43f5e'; // Red
      } else if (score < 75) {
        strengthBar.style.backgroundColor = '#f59e0b'; // Amber
      } else {
        strengthBar.style.backgroundColor = '#10b981'; // Green
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert('register-alert');

      const name = nameInput.value.trim();
      const email = emailInput.value.trim();
      const password = passwordInput.value;
      const confirmPassword = confirmPasswordInput.value;

      // Validation
      if (!name || name.length < 2) {
        showAlert('register-alert', 'Please enter your full name (minimum 2 characters).', 'danger');
        return;
      }

      const emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/;
      if (!email || !emailRegex.test(email)) {
        showAlert('register-alert', 'Please enter a valid email address.', 'danger');
        return;
      }

      if (password.length < 6) {
        showAlert('register-alert', 'Password must be at least 6 characters long.', 'danger');
        return;
      }

      if (password !== confirmPassword) {
        showAlert('register-alert', 'Passwords do not match. Please verify.', 'danger');
        return;
      }

      // Submit state
      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<span>Creating Account...</span>';

      try {
        const response = await fetch(`${API_BASE}/api/register`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
          showToast('Account created successfully!', 'success');
          setTimeout(() => {
            window.location.href = 'login.html?registered=true';
          }, 800);
        } else {
          showAlert('register-alert', data.message || 'Registration failed. Please try again.', 'danger');
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      } catch (err) {
        console.error('Registration error:', err);
        showAlert('register-alert', 'Server connection error. Please ensure the backend is running.', 'danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
});
