/**
 * Common JavaScript functionality shared across multiple pages
 */

// Centralized Z-Index Management
window.ZIndexManager = {
  // Base layers (0-999)
  BASE: 1,
  NAVBAR: 100,
  STICKY_ELEMENTS: 200,

  // Content layers (1000-4999)
  FLOATING_BUTTONS: 1000,
  TOOLTIPS: 2000,
  DROPDOWNS: 3000,

  // Overlay layers (5000-9999)
  OVERLAYS: 5000,
  MODALS: 8000,

  // Critical layers (10000+)
  NOTIFICATIONS: 10000,
  PROFILE_DROPDOWN: 10001,
  PROFILE_DROPDOWN_BILINGUAL: 10005,
  EMERGENCY: 99999,

  // Get appropriate z-index for profile dropdown
  getProfileDropdownZIndex: function(isBilingualMode = false) {
    return isBilingualMode ? this.PROFILE_DROPDOWN_BILINGUAL : this.PROFILE_DROPDOWN;
  },

  // Get appropriate z-index for avatar button
  getAvatarButtonZIndex: function(isBilingualMode = false) {
    return isBilingualMode ? (this.PROFILE_DROPDOWN_BILINGUAL - 1) : (this.PROFILE_DROPDOWN - 1);
  }
};

// Initialize the profile dropdown functionality
window.initializeProfileDropdown = function() {
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');

  if (avatarButton && userDropdown && !avatarButton._initialized) {
    console.log('Initializing profile dropdown from common.js');

    // Mark as initialized to prevent duplicate event listeners
    avatarButton._initialized = true;

    // Remove any existing event listeners by cloning and replacing the button
    const newAvatarButton = avatarButton.cloneNode(true);
    avatarButton.parentNode.replaceChild(newAvatarButton, avatarButton);

    // Add click event listener with improved interaction handling
    newAvatarButton.addEventListener('click', function(event) {
      console.log('Avatar button clicked from common.js');
      event.preventDefault();
      event.stopPropagation();

      // Prevent rapid clicking
      if (newAvatarButton.dataset.processing === 'true') {
        return;
      }

      newAvatarButton.dataset.processing = 'true';
      setTimeout(() => {
        newAvatarButton.dataset.processing = 'false';
      }, 300);

      const isExpanded = newAvatarButton.getAttribute('aria-expanded') === 'true';

      // Close dropdown if open, open if closed
      if (isExpanded) {
        window.closeProfileDropdown();
      } else {
        window.openProfileDropdown();
      }
    });

    // Ensure dropdown is visible when shown - Ultra high z-index for bilingual mode compatibility
    userDropdown.style.zIndex = '10001';

    // Prevent dropdown from closing when clicking inside it
    userDropdown.addEventListener('click', function(event) {
      event.stopPropagation();
    });

    // Add keyboard navigation support
    newAvatarButton.addEventListener('keydown', function(event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        newAvatarButton.click();
      } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        window.openProfileDropdown();
        // Focus first dropdown item
        setTimeout(() => {
          const firstItem = userDropdown.querySelector('.dropdown-item');
          if (firstItem) firstItem.focus();
        }, 100);
      }
    });

    // Add touch event handling for better mobile experience
    if ('ontouchstart' in window) {
      newAvatarButton.addEventListener('touchstart', function(event) {
        // Prevent double-tap zoom on mobile
        event.preventDefault();
      });
    }

    // Add dropdown item keyboard navigation
    userDropdown.addEventListener('keydown', function(event) {
      const items = userDropdown.querySelectorAll('.dropdown-item');
      const currentIndex = Array.from(items).indexOf(document.activeElement);

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          const nextIndex = (currentIndex + 1) % items.length;
          items[nextIndex].focus();
          break;
        case 'ArrowUp':
          event.preventDefault();
          const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
          items[prevIndex].focus();
          break;
        case 'Escape':
          event.preventDefault();
          window.closeProfileDropdown();
          newAvatarButton.focus();
          break;
        case 'Enter':
        case ' ':
          if (document.activeElement.classList.contains('dropdown-item')) {
            document.activeElement.click();
          }
          break;
      }
    });
  }
};



// Close all dropdowns when clicking outside
function setupOutsideClickHandler() {
  // Handle both click and touch events for better mobile support
  function handleOutsideInteraction(event) {
    const avatarButton = document.getElementById('avatar-button');
    const userDropdown = document.getElementById('user-dropdown');

    // Close user dropdown if open and click/touch is outside
    if (avatarButton && userDropdown &&
        userDropdown.classList.contains('show') &&
        !avatarButton.contains(event.target) &&
        !userDropdown.contains(event.target)) {

      // Use the dedicated close function for consistency
      window.closeProfileDropdown();
    }
  }

  // Add both click and touchstart listeners for comprehensive mobile support
  document.addEventListener('click', handleOutsideInteraction, { passive: true });

  // Add touchstart for mobile devices (but prevent duplicate events)
  if ('ontouchstart' in window) {
    document.addEventListener('touchstart', function(event) {
      // Only handle touchstart if it's not followed by a click
      setTimeout(() => {
        if (!event.defaultPrevented) {
          handleOutsideInteraction(event);
        }
      }, 10);
    }, { passive: true });
  }
}

// Function to ensure dropdown visibility and proper positioning
window.ensureDropdownVisibility = function() {
  const userDropdown = document.getElementById('user-dropdown');
  const avatarButton = document.getElementById('avatar-button');
  const bilingualModeContent = document.getElementById('bilingual-mode-content');

  if (userDropdown && avatarButton) {
    // Check if bilingual mode is active
    const isBilingualModeActive = bilingualModeContent &&
      bilingualModeContent.style.display === 'block';

    // Check screen size for responsive positioning
    const isMobile = window.innerWidth <= 768;

    // Use centralized z-index management
    const dropdownZIndex = window.ZIndexManager.getProfileDropdownZIndex(isBilingualModeActive);
    const buttonZIndex = window.ZIndexManager.getAvatarButtonZIndex(isBilingualModeActive);

    userDropdown.style.zIndex = dropdownZIndex.toString();
    avatarButton.style.zIndex = buttonZIndex.toString();

    console.log(`Dropdown z-index set to ${dropdownZIndex}, button z-index set to ${buttonZIndex}${isBilingualModeActive ? ' (bilingual mode)' : ''}`);

    // Ensure proper stacking context
    const userAvatarMenu = avatarButton.closest('.user-avatar-menu');
    if (userAvatarMenu) {
      userAvatarMenu.style.zIndex = buttonZIndex.toString();
    }

    // Apply responsive positioning based on screen size
    if (isMobile) {
      // Mobile: always use absolute positioning below avatar for consistent downward opening
      userDropdown.style.position = 'absolute';
      userDropdown.style.top = 'calc(100% + 8px)';
      userDropdown.style.bottom = 'auto';
      userDropdown.style.right = '0';
      userDropdown.style.left = 'auto';

      // Check if dropdown would go off-screen and adjust if needed
      window.checkDropdownPosition();
    } else {
      // Desktop: standard absolute positioning
      userDropdown.style.position = 'absolute';
      userDropdown.style.top = 'calc(100% + 8px)';
      userDropdown.style.bottom = 'auto';
      userDropdown.style.right = '0';
      userDropdown.style.left = 'auto';
    }

    console.log('Dropdown visibility and positioning ensured');
  }
};

// Function to check and adjust dropdown position to prevent overlaps and off-screen issues
window.checkDropdownPosition = function() {
  const userDropdown = document.getElementById('user-dropdown');
  const avatarButton = document.getElementById('avatar-button');
  const userAvatarMenu = avatarButton?.closest('.user-avatar-menu');

  if (!userDropdown || !avatarButton || !userAvatarMenu) return;

  // Get button position and viewport dimensions
  const buttonRect = avatarButton.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  const dropdownHeight = 200; // Estimated dropdown height
  const dropdownWidth = 220; // Estimated dropdown width

  // Check for potential overlaps with other UI elements
  const potentialOverlaps = window.detectUIOverlaps(buttonRect, dropdownHeight, dropdownWidth);

  // Determine best position based on available space and overlaps
  const spaceBelow = viewportHeight - buttonRect.bottom;
  const spaceAbove = buttonRect.top;
  const spaceRight = viewportWidth - buttonRect.right;
  const spaceLeft = buttonRect.left;

  // Reset positioning classes
  userAvatarMenu.classList.remove('dropdown-above', 'dropdown-left', 'dropdown-center');

  // Position vertically
  if (spaceBelow < dropdownHeight && spaceAbove > dropdownHeight && !potentialOverlaps.above) {
    userAvatarMenu.classList.add('dropdown-above');
  }

  // Position horizontally for mobile
  if (window.innerWidth <= 768) {
    if (spaceRight < dropdownWidth && spaceLeft > dropdownWidth) {
      userAvatarMenu.classList.add('dropdown-left');
    } else if (spaceRight < dropdownWidth && spaceLeft < dropdownWidth) {
      userAvatarMenu.classList.add('dropdown-center');
    }
  }

  console.log('Dropdown position checked and adjusted for overlaps');
};

// Function to detect potential UI overlaps
window.detectUIOverlaps = function(buttonRect, dropdownHeight, dropdownWidth) {
  const overlaps = {
    above: false,
    below: false,
    left: false,
    right: false
  };

  // Check for overlaps with common UI elements
  const elementsToCheck = [
    '.modal',
    '.notification',
    '.toast',
    '#bilingual-mode-content',
    '.navbar',
    '.bottom-nav',
    '.slide-panel'
  ];

  elementsToCheck.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
      if (element.offsetParent !== null) { // Element is visible
        const rect = element.getBoundingClientRect();

        // Check for potential overlaps in each direction
        if (rect.bottom > buttonRect.top - dropdownHeight && rect.top < buttonRect.top) {
          overlaps.above = true;
        }
        if (rect.top < buttonRect.bottom + dropdownHeight && rect.bottom > buttonRect.bottom) {
          overlaps.below = true;
        }
        if (rect.right > buttonRect.left - dropdownWidth && rect.left < buttonRect.left) {
          overlaps.left = true;
        }
        if (rect.left < buttonRect.right + dropdownWidth && rect.right > buttonRect.right) {
          overlaps.right = true;
        }
      }
    });
  });

  return overlaps;
};

// Dedicated function to open profile dropdown
window.openProfileDropdown = function() {
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');

  if (!avatarButton || !userDropdown) return;

  // Close any other open dropdowns first
  window.closeAllDropdowns();

  // Check position and overlaps before opening
  window.checkDropdownPosition();

  // Set ARIA state
  avatarButton.setAttribute('aria-expanded', 'true');

  // Add show class with slight delay for smooth animation
  requestAnimationFrame(() => {
    userDropdown.classList.add('show');

    // Focus management for accessibility
    userDropdown.setAttribute('tabindex', '-1');

    // Add escape key listener
    document.addEventListener('keydown', window.handleDropdownEscape);
  });

  console.log('Profile dropdown opened');
};

// Dedicated function to close profile dropdown
window.closeProfileDropdown = function() {
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');

  if (!avatarButton || !userDropdown) return;

  // Set ARIA state
  avatarButton.setAttribute('aria-expanded', 'false');

  // Remove show class
  userDropdown.classList.remove('show');

  // Clean up event listeners
  document.removeEventListener('keydown', window.handleDropdownEscape);

  console.log('Profile dropdown closed');
};

// Function to close all dropdowns
window.closeAllDropdowns = function() {
  const dropdowns = document.querySelectorAll('.user-dropdown.show');
  dropdowns.forEach(dropdown => {
    dropdown.classList.remove('show');
    const button = dropdown.previousElementSibling;
    if (button && button.hasAttribute('aria-expanded')) {
      button.setAttribute('aria-expanded', 'false');
    }
  });
};

// Handle escape key for dropdown
window.handleDropdownEscape = function(event) {
  if (event.key === 'Escape') {
    window.closeProfileDropdown();
    // Return focus to avatar button
    const avatarButton = document.getElementById('avatar-button');
    if (avatarButton) {
      avatarButton.focus();
    }
  }
};

// Initialize all dropdowns when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('Common.js loaded - initializing shared functionality');

  // Initialize the profile dropdown
  window.initializeProfileDropdown();

  // Setup outside click handler
  setupOutsideClickHandler();

  // Ensure dropdown visibility
  window.ensureDropdownVisibility();

  // Listen for bilingual mode toggle to reinitialize dropdown
  const bilingualToggle = document.getElementById('bilingual-mode');
  if (bilingualToggle) {
    bilingualToggle.addEventListener('change', function() {
      setTimeout(() => {
        window.ensureDropdownVisibility();
        window.initializeProfileDropdown();
      }, 100);
    });
  }

  // Listen for window resize to adjust dropdown positioning
  window.addEventListener('resize', function() {
    setTimeout(() => {
      window.ensureDropdownVisibility();
      // If dropdown is open on mobile, recheck position
      if (window.innerWidth <= 768) {
        const userDropdown = document.getElementById('user-dropdown');
        if (userDropdown && userDropdown.classList.contains('show')) {
          window.checkDropdownPosition();
        }
      }
    }, 100);
  });

  // Listen for orientation change on mobile devices
  window.addEventListener('orientationchange', function() {
    setTimeout(() => {
      window.ensureDropdownVisibility();
      // Recheck position after orientation change
      if (window.innerWidth <= 768) {
        const userDropdown = document.getElementById('user-dropdown');
        if (userDropdown && userDropdown.classList.contains('show')) {
          window.checkDropdownPosition();
        }
      }
    }, 200);
  });

  // Validate dropdown implementation
  setTimeout(() => {
    window.validateDropdownImplementation();
  }, 1000);

  console.log('Common.js initialization complete');
});

// Validation function to ensure dropdown is working correctly
window.validateDropdownImplementation = function() {
  const avatarButton = document.getElementById('avatar-button');
  const userDropdown = document.getElementById('user-dropdown');
  const userAvatarMenu = avatarButton?.closest('.user-avatar-menu');

  const issues = [];

  if (!avatarButton) {
    issues.push('Avatar button not found');
  } else {
    if (!avatarButton.hasAttribute('aria-expanded')) {
      issues.push('Avatar button missing aria-expanded attribute');
    }
    if (!avatarButton.style.zIndex) {
      issues.push('Avatar button missing z-index');
    }
  }

  if (!userDropdown) {
    issues.push('User dropdown not found');
  } else {
    if (!userDropdown.style.zIndex) {
      issues.push('User dropdown missing z-index');
    }
    const computedStyle = window.getComputedStyle(userDropdown);
    if (computedStyle.position !== 'absolute') {
      issues.push('User dropdown not using absolute positioning');
    }
  }

  if (!userAvatarMenu) {
    issues.push('User avatar menu container not found');
  }

  if (issues.length > 0) {
    console.warn('Dropdown implementation issues detected:', issues);
  } else {
    console.log('✓ Dropdown implementation validation passed');
  }

  // Test z-index hierarchy
  const dropdownZIndex = parseInt(userDropdown?.style.zIndex || '0');
  const buttonZIndex = parseInt(avatarButton?.style.zIndex || '0');

  if (dropdownZIndex <= buttonZIndex) {
    console.warn('Z-index hierarchy issue: dropdown should be above button');
  } else {
    console.log('✓ Z-index hierarchy correct');
  }
};
