document.addEventListener('DOMContentLoaded', function() {
  // Profile page specific JavaScript
  console.log('Profile page loaded');

  // We'll use a global function to initialize the history dropdown
  // This ensures it's only initialized once, regardless of which script does it
  if (typeof window.initializeHistoryDropdown === 'function') {
    window.initializeHistoryDropdown();
  } else {
    console.log('History dropdown initialization function not found');

    // Define the function if it doesn't exist yet
    window.initializeHistoryDropdown = function() {
      const historyButton = document.getElementById('history-button');
      const historyDropdown = document.getElementById('history-dropdown');

      if (historyButton && historyDropdown && !historyButton._initialized) {
        console.log('Initializing history dropdown from profile.js');
        // Mark as initialized to prevent duplicate event listeners
        historyButton._initialized = true;

        historyButton.addEventListener('click', (event) => {
          event.stopPropagation();
          const isExpanded = historyButton.getAttribute('aria-expanded') === 'true';

          historyButton.setAttribute('aria-expanded', !isExpanded);
          historyDropdown.classList.toggle('show');

          // Close user dropdown if open
          const avatarButton = document.getElementById('avatar-button');
          const userDropdown = document.getElementById('user-dropdown');
          if (avatarButton && userDropdown) {
            avatarButton.setAttribute('aria-expanded', 'false');
            userDropdown.classList.remove('show');
          }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
          historyButton.setAttribute('aria-expanded', 'false');
          historyDropdown.classList.remove('show');
        });

        // Prevent dropdown from closing when clicking inside it
        historyDropdown.addEventListener('click', (event) => {
          event.stopPropagation();
        });
      }
    };

    // Call the function to initialize the dropdown
    window.initializeHistoryDropdown();
  }
});