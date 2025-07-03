// Authentication-related JavaScript

// Password toggle functionality removed - passwords now always remain hidden for security

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

  // Password toggle functionality removed - passwords now always remain hidden
  console.log('Password fields configured to always remain hidden for security');

  // Enhanced form handling with loading states
  initializeFormHandling();

  function initializeFormHandling() {
    // Handle all auth forms (login, register)
    const authForms = document.querySelectorAll('form[action*="login"], form[action*="register"]');

    authForms.forEach(form => {
      const submitButton = form.querySelector('button[type="submit"]');

      if (submitButton) {
        form.addEventListener('submit', function(event) {
          // Add loading state
          submitButton.classList.add('loading');
          submitButton.disabled = true;

          // Store original text
          if (!submitButton.dataset.originalText) {
            submitButton.dataset.originalText = submitButton.textContent;
          }
          submitButton.textContent = 'Please wait...';

          // Remove loading state after a delay if form submission fails
          setTimeout(() => {
            if (submitButton.classList.contains('loading')) {
              submitButton.classList.remove('loading');
              submitButton.disabled = false;
              submitButton.textContent = submitButton.dataset.originalText;
            }
          }, 10000); // 10 second timeout
        });
      }
    });
  }

  // Enhanced password validation for registration
  const registerForm = document.querySelector('form[action*="register"]');
  if (registerForm) {
    const password = registerForm.querySelector('input[name="password"]');
    const confirmPassword = registerForm.querySelector('input[name="confirm_password"]');
    const submitButton = registerForm.querySelector('button[type="submit"]');

    // Real-time password validation
    function validatePasswords() {
      const passwordValue = password.value;
      const confirmPasswordValue = confirmPassword.value;

      // Clear previous validation states
      password.classList.remove('error', 'success');
      confirmPassword.classList.remove('error', 'success');

      let isValid = true;

      // Password length validation
      if (passwordValue.length > 0 && passwordValue.length < 8) {
        password.classList.add('error');
        isValid = false;
      } else if (passwordValue.length >= 8) {
        password.classList.add('success');
      }

      // Password match validation
      if (confirmPasswordValue.length > 0) {
        if (passwordValue !== confirmPasswordValue) {
          confirmPassword.classList.add('error');
          isValid = false;
        } else if (passwordValue === confirmPasswordValue && passwordValue.length >= 8) {
          confirmPassword.classList.add('success');
        }
      }

      return isValid;
    }

    if (password && confirmPassword) {
      password.addEventListener('input', validatePasswords);
      confirmPassword.addEventListener('input', validatePasswords);
    }

    registerForm.addEventListener('submit', async (event) => {
      // Check password validation first
      if (password.value !== confirmPassword.value) {
        event.preventDefault();
        showFormError('Passwords do not match!');
        return false;
      }

      if (password.value.length < 8) {
        event.preventDefault();
        showFormError('Password must be at least 8 characters long!');
        return false;
      }

      // Check email validation if email validator is available
      const emailInput = registerForm.querySelector('input[type="email"]');
      if (emailInput && window.emailValidator) {
        // Only prevent submission if email is explicitly marked as invalid
        if (emailInput.classList.contains('invalid')) {
          event.preventDefault();
          showFormError('Please enter a valid email address.');
          return false;
        }

        // Basic format validation as fallback
        const email = emailInput.value.trim();
        if (email && !window.emailValidator.validateFormat(email)) {
          event.preventDefault();
          showFormError('Please enter a valid email format.');
          return false;
        }

        // If email is not validated yet but looks valid, allow submission
        // The backend will handle final validation and OTP verification
        console.log('Email validation passed, allowing form submission');
      }

      return true;
    });
  }

  function showFormError(message) {
    // Remove existing error alerts
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());

    // Create new error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.textContent = message;

    // Insert at the top of the form
    const form = document.querySelector('form[action*="register"], form[action*="login"]');
    if (form) {
      const cardContent = form.closest('.card-content');
      if (cardContent) {
        cardContent.insertBefore(alert, cardContent.firstChild);
      }
    }

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 5000);
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

