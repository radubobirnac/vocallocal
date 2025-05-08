// Authentication-related JavaScript

// Function to toggle password visibility
function togglePasswordVisibility(button) {
  try {
    // Find the password input that is a sibling of this button
    const passwordInput = button.parentElement.querySelector('input');
    const icon = button.querySelector('i');

    if (!passwordInput || !icon) {
      console.error('Password input or icon not found');
      return;
    }

    // Toggle password visibility
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      passwordInput.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  } catch (error) {
    console.error('Error toggling password visibility:', error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('Auth.js loaded - DOM Content Loaded');

  // Avatar dropdown toggle
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');

  if (avatarButton && userDropdown) {
    avatarButton.addEventListener('click', (event) => {
      event.stopPropagation();
      const isExpanded = avatarButton.getAttribute('aria-expanded') === 'true';

      avatarButton.setAttribute('aria-expanded', !isExpanded);
      userDropdown.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
      avatarButton.setAttribute('aria-expanded', 'false');
      userDropdown.classList.remove('show');
    });

    // Prevent dropdown from closing when clicking inside it
    userDropdown.addEventListener('click', (event) => {
      event.stopPropagation();
    });
  }

  // Password visibility toggle - add event listeners
  const passwordToggleBtns = document.querySelectorAll('.password-toggle-btn');

  if (passwordToggleBtns.length > 0) {
    // Remove any inline onclick attributes to prevent conflicts
    passwordToggleBtns.forEach(btn => {
      // Remove the inline onclick attribute if it exists
      if (btn.hasAttribute('onclick')) {
        btn.removeAttribute('onclick');
      }

      // Add the event listener
      btn.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent form submission if inside a form
        e.stopPropagation(); // Stop event from bubbling up
        togglePasswordVisibility(this);
      });
    });
  } else {
    console.warn('No password toggle buttons found on this page');
  }

  // Password validation for registration
  const registerForm = document.querySelector('form[action*="register"]');
  if (registerForm) {
    const password = registerForm.querySelector('input[name="password"]');
    const confirmPassword = registerForm.querySelector('input[name="confirm_password"]');

    registerForm.addEventListener('submit', (event) => {
      if (password.value !== confirmPassword.value) {
        event.preventDefault();
        alert('Passwords do not match!');
        return false;
      }

      if (password.value.length < 8) {
        event.preventDefault();
        alert('Password must be at least 8 characters long!');
        return false;
      }

      return true;
    });
  }

  // Password validation for change password form
  const changePasswordForm = document.querySelector('form[action*="change-password"]');
  if (changePasswordForm) {
    const newPassword = changePasswordForm.querySelector('input[name="new_password"]');
    const confirmPassword = changePasswordForm.querySelector('input[name="confirm_password"]');

    changePasswordForm.addEventListener('submit', (event) => {
      if (newPassword.value !== confirmPassword.value) {
        event.preventDefault();
        alert('New passwords do not match!');
        return false;
      }

      if (newPassword.value.length < 8) {
        event.preventDefault();
        alert('New password must be at least 8 characters long!');
        return false;
      }

      return true;
    });
  }
});

