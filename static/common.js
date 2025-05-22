/**
 * Common JavaScript functionality shared across multiple pages
 */

// Initialize the profile dropdown functionality
window.initializeProfileDropdown = function() {
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');
  const historyButton = document.getElementById('history-button');
  const historyDropdown = document.getElementById('history-dropdown');

  if (avatarButton && userDropdown && !avatarButton._initialized) {
    console.log('Initializing profile dropdown from common.js');

    // Mark as initialized to prevent duplicate event listeners
    avatarButton._initialized = true;

    // Remove any existing event listeners by cloning and replacing the button
    const newAvatarButton = avatarButton.cloneNode(true);
    avatarButton.parentNode.replaceChild(newAvatarButton, avatarButton);

    // Add click event listener
    newAvatarButton.addEventListener('click', function(event) {
      console.log('Avatar button clicked from common.js');
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

// Initialize the history dropdown functionality
window.initializeHistoryDropdown = function() {
  const historyButton = document.getElementById('history-button');
  const historyDropdown = document.getElementById('history-dropdown');
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');

  if (historyButton && historyDropdown && !historyButton._initialized) {
    console.log('Initializing history dropdown from common.js');
    // Mark as initialized to prevent duplicate event listeners
    historyButton._initialized = true;

    // Remove any existing event listeners by cloning and replacing the button
    const newHistoryButton = historyButton.cloneNode(true);
    historyButton.parentNode.replaceChild(newHistoryButton, historyButton);

    newHistoryButton.addEventListener('click', (event) => {
      console.log('History button clicked from common.js');
      event.preventDefault();
      event.stopPropagation();

      const isExpanded = newHistoryButton.getAttribute('aria-expanded') === 'true';

      newHistoryButton.setAttribute('aria-expanded', !isExpanded);
      historyDropdown.classList.toggle('show');

      // Close user dropdown if open
      if (avatarButton && userDropdown) {
        avatarButton.setAttribute('aria-expanded', 'false');
        userDropdown.classList.remove('show');
      }
    });

    // Ensure dropdown is visible when shown
    historyDropdown.style.zIndex = '1000';

    // Prevent dropdown from closing when clicking inside it
    historyDropdown.addEventListener('click', (event) => {
      event.stopPropagation();
    });
  }
};

// Close all dropdowns when clicking outside
function setupOutsideClickHandler() {
  document.addEventListener('click', function(event) {
    const avatarButton = document.getElementById('avatar-button');
    const userDropdown = document.getElementById('user-dropdown');
    const historyButton = document.getElementById('history-button');
    const historyDropdown = document.getElementById('history-dropdown');

    // Close user dropdown if open
    if (avatarButton && userDropdown &&
        !avatarButton.contains(event.target) &&
        !userDropdown.contains(event.target)) {
      avatarButton.setAttribute('aria-expanded', 'false');
      userDropdown.classList.remove('show');
    }

    // Close history dropdown if open
    if (historyButton && historyDropdown &&
        !historyButton.contains(event.target) &&
        !historyDropdown.contains(event.target)) {
      historyButton.setAttribute('aria-expanded', 'false');
      historyDropdown.classList.remove('show');
    }
  });
}

// Initialize all dropdowns when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('Common.js loaded - initializing shared functionality');

  // Initialize the profile dropdown
  window.initializeProfileDropdown();

  // Initialize the history dropdown
  window.initializeHistoryDropdown();

  // Setup outside click handler
  setupOutsideClickHandler();
});
