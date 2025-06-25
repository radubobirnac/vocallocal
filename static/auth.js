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

  // Use global functions to initialize dropdowns if they exist
  if (typeof window.initializeProfileDropdown === 'function') {
    console.log('Auth.js: Calling global profile dropdown initialization');
    window.initializeProfileDropdown();
  } else {
    console.log('Auth.js: Global profile dropdown function not found, defining locally');

    // Define the global profile dropdown initialization function
    window.initializeProfileDropdown = function() {
      const avatarButton = document.getElementById('avatar-button');
      const userDropdown = document.getElementById('user-dropdown');


      if (avatarButton && userDropdown && !avatarButton._initialized) {
        console.log('Initializing profile dropdown from auth.js');

        // Mark as initialized to prevent duplicate event listeners
        avatarButton._initialized = true;

        // Remove any existing event listeners by cloning and replacing the button
        const newAvatarButton = avatarButton.cloneNode(true);
        avatarButton.parentNode.replaceChild(newAvatarButton, avatarButton);

        // Add click event listener
        newAvatarButton.addEventListener('click', function(event) {
          console.log('Avatar button clicked from auth.js');
          event.preventDefault();
          event.stopPropagation();

          const isExpanded = newAvatarButton.getAttribute('aria-expanded') === 'true';

          // Toggle dropdown visibility
          newAvatarButton.setAttribute('aria-expanded', !isExpanded);
          userDropdown.classList.toggle('show');

          // Close history dropdown if open
          if (historyButton && historyDropdown) {
            historyButton.setAttribute('aria-expanded', 'false');
            historyDropdown.classList.remove('show');
          }
        });

        // Ensure dropdown is visible when shown
        userDropdown.style.zIndex = '1000';

        // Prevent dropdown from closing when clicking inside it
        userDropdown.addEventListener('click', function(event) {
          event.stopPropagation();
        });
      }
    };

    // Call the newly defined function
    window.initializeProfileDropdown();
  }

  // History is now consolidated under Profile dropdown, no separate History dropdown needed

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

