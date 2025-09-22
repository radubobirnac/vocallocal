/**
 * Conversation Modal JavaScript
 * Handles the conversation room creation and joining functionality
 */

// Enhanced conversation modal functionality with debugging
function _openConversationModal(userInitiated = false) {
  console.log('🚀 OPENING CONVERSATION MODAL');
  console.log('User initiated:', userInitiated);
  console.log('Modal initialized:', conversationModalInitialized);

  // Additional safety check to prevent automatic opening (but allow user-initiated)
  if (!conversationModalInitialized && !userInitiated) {
    console.warn('⚠️ Conversation modal not initialized - preventing automatic opening');
    return;
  }

  const modal = document.getElementById('conversation-modal');
  if (modal) {
    console.log('✅ Modal element found');
    console.log('Current modal state:', {
      display: modal.style.display,
      visibility: modal.style.visibility,
      opacity: modal.style.opacity,
      classes: modal.className
    });

    // Clear any hidden states
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';
    modal.style.removeProperty('display'); // Remove any inline display style first

    // Show the modal
    modal.classList.add('show');
    modal.style.display = 'flex';
    modal.setAttribute('data-modal-state', 'visible');

    console.log('✅ CONVERSATION MODAL OPENED SUCCESSFULLY!');
    console.log('New modal state:', {
      display: modal.style.display,
      visibility: modal.style.visibility,
      opacity: modal.style.opacity,
      classes: modal.className
    });

    // Add a visual indicator that the modal is working
    modal.style.border = '3px solid #00ff00';

  } else {
    console.error('❌ CONVERSATION MODAL ELEMENT NOT FOUND!');

    // Debug: Check if any modal exists
    const allModals = document.querySelectorAll('[id*="modal"], .modal, .modal-overlay');
    console.log('All modal-like elements found:', allModals.length);
    allModals.forEach((modalEl, index) => {
      console.log(`Modal ${index + 1}:`, {
        id: modalEl.id,
        className: modalEl.className,
        tagName: modalEl.tagName
      });
    });
  }
}

function closeConversationModal() {
  const modal = document.getElementById('conversation-modal');
  if (modal) {
    // Remove show classes
    modal.classList.remove('show');
    modal.classList.remove('modal-show');
    modal.classList.remove('active');

    // Force hide with multiple methods
    modal.style.display = 'none';
    modal.style.visibility = 'hidden';
    modal.style.opacity = '0';
    modal.setAttribute('data-modal-state', 'hidden');

    console.log('Conversation modal closed and hidden');
  }
  resetConversationModal();
}

function resetConversationModal() {
  document.querySelector('.conversation-setup').style.display = 'block';
  document.getElementById('room-created').style.display = 'none';
  document.getElementById('room-code-input').value = '';
}

function copyRoomCode() {
  const roomCode = document.getElementById('generated-room-code').textContent;
  navigator.clipboard.writeText(roomCode).then(() => {
    showToast('Room code copied to clipboard!');
  }).catch(() => {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = roomCode;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast('Room code copied to clipboard!');
  });
}

function copyRoomLink() {
  const roomLink = document.getElementById('generated-room-link').value;
  navigator.clipboard.writeText(roomLink).then(() => {
    showToast('Room link copied to clipboard!');
  }).catch(() => {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = roomLink;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast('Room link copied to clipboard!');
  });
}

function showToast(message) {
  // Remove any existing toast
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }
  
  // Create new toast notification
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  // Auto remove after 3 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.remove();
    }
  }, 3000);
}

function validateRoomCode(code) {
  // Room code should be 6 alphanumeric characters
  const regex = /^[A-Z0-9]{6}$/;
  return regex.test(code);
}

// Prevent automatic conversation modal opening
let conversationModalInitialized = false;

// Initialize conversation modal functionality
document.addEventListener('DOMContentLoaded', function() {
  console.log('Conversation modal script loaded - setting up event listeners');

  // Ensure modal is hidden on page load with multiple safeguards
  const modal = document.getElementById('conversation-modal');
  if (modal) {
    // Remove any show classes
    modal.classList.remove('show');
    modal.classList.remove('modal-show');
    modal.classList.remove('active');

    // Force hide with inline style (highest priority)
    modal.style.display = 'none';
    modal.style.visibility = 'hidden';
    modal.style.opacity = '0';

    // Set data attribute to track state
    modal.setAttribute('data-modal-state', 'hidden');

    console.log('Conversation modal explicitly hidden on page load with multiple safeguards');

    // Additional check after a short delay to ensure it stays hidden
    setTimeout(() => {
      if (modal.style.display !== 'none') {
        console.warn('Modal display was changed, forcing it to stay hidden');
        modal.style.display = 'none';
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
      }
    }, 100);
  }

  // Enhanced conversation button setup with debugging
  function setupConversationButton() {
    console.log('🔍 Looking for conversation button...');
    const conversationButton = document.getElementById('conversation-button');

    if (conversationButton) {
      console.log('✅ Conversation button found!');
      console.log('Button element:', conversationButton);
      console.log('Button classes:', conversationButton.className);
      console.log('Button text:', conversationButton.textContent.trim());

      // Check if button is visible and clickable
      const rect = conversationButton.getBoundingClientRect();
      const computedStyle = window.getComputedStyle(conversationButton);

      console.log('Button dimensions:', {
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left
      });

      console.log('Button styles:', {
        display: computedStyle.display,
        visibility: computedStyle.visibility,
        pointerEvents: computedStyle.pointerEvents,
        zIndex: computedStyle.zIndex
      });

      // Remove any existing listeners to prevent duplicates
      const newButton = conversationButton.cloneNode(true);
      conversationButton.parentNode.replaceChild(newButton, conversationButton);

      // Add enhanced click listener
      newButton.addEventListener('click', function(event) {
        console.log('🎉 CONVERSATION BUTTON CLICKED!');
        console.log('Click event details:', {
          type: event.type,
          target: event.target.tagName,
          currentTarget: event.currentTarget.tagName,
          bubbles: event.bubbles,
          cancelable: event.cancelable
        });

        event.preventDefault();
        event.stopPropagation();

        // Force modal to open
        console.log('🚀 Opening conversation modal...');
        _openConversationModal(true);
      });

      // Add visual feedback for debugging
      newButton.style.border = '2px solid #00ff00';
      newButton.title = 'Conversation button - Click to test!';

      console.log('✅ Click listener added successfully');
      return true;
    } else {
      console.warn('❌ Conversation button not found on this page');

      // Debug: List all buttons on the page
      const allButtons = document.querySelectorAll('button');
      console.log('All buttons found on page:', allButtons.length);
      allButtons.forEach((btn, index) => {
        console.log(`Button ${index + 1}:`, {
          id: btn.id,
          className: btn.className,
          text: btn.textContent.trim().substring(0, 50)
        });
      });

      return false;
    }
  }

  // Try to set up the button with retries
  if (!setupConversationButton()) {
    console.log('🔄 Button not found immediately, setting up retry mechanism...');
    let retryCount = 0;
    const maxRetries = 10;

    const retryInterval = setInterval(() => {
      retryCount++;
      console.log(`🔄 Retry ${retryCount}/${maxRetries} - Looking for conversation button...`);

      if (setupConversationButton()) {
        console.log('✅ Button found and set up successfully!');
        clearInterval(retryInterval);
      } else if (retryCount >= maxRetries) {
        console.error('❌ Failed to find conversation button after all retries');
        clearInterval(retryInterval);
      }
    }, 500);
  }
  
  // Create room button
  const createRoomBtn = document.getElementById('create-room-btn');
  if (createRoomBtn) {
    createRoomBtn.addEventListener('click', async function() {
      // Disable button to prevent double clicks
      this.disabled = true;
      this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
      
      try {
        console.log('🚀 Creating room...');
        const response = await fetch('/conversation/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        console.log('📡 Response status:', response.status);
        const result = await response.json();
        console.log('📋 Response data:', result);
        
        if (result.success) {
          // Show room created section
          document.querySelector('.conversation-setup').style.display = 'none';
          document.getElementById('room-created').style.display = 'block';

          // Fill in room details
          document.getElementById('generated-room-code').textContent = result.room_code;
          document.getElementById('generated-room-link').value = window.location.origin + result.shareable_link;

          // Set up enter room button - use direct room URL if creator was auto-added
          const enterRoomBtn = document.getElementById('enter-room-btn');
          if (result.creator_auto_added && result.direct_room_url) {
            enterRoomBtn.textContent = 'Enter Room';
            enterRoomBtn.onclick = function() {
              window.location.href = result.direct_room_url;
            };
            console.log('Creator auto-added to room, using direct room access');
          } else {
            enterRoomBtn.textContent = 'Join Room';
            enterRoomBtn.onclick = function() {
              window.location.href = result.shareable_link;
            };
            console.log('Creator not auto-added, using join flow');
          }
        } else {
          console.error('❌ Room creation failed:', result.error);
          showToast('Error creating room: ' + result.error);
        }
      } catch (error) {
        console.error('❌ Create room error:', error);
        showToast('Failed to create room. Please try again.');
      } finally {
        // Re-enable button
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-plus"></i> Create Room';
      }
    });
  }
  
  // Join room button
  const joinRoomBtn = document.getElementById('join-room-btn');
  if (joinRoomBtn) {
    joinRoomBtn.addEventListener('click', function() {
      const roomCodeInput = document.getElementById('room-code-input');
      const roomCode = roomCodeInput.value.trim().toUpperCase();
      
      if (!validateRoomCode(roomCode)) {
        showToast('Please enter a valid 6-character room code.');
        roomCodeInput.focus();
        return;
      }
      
      // Disable button and show loading
      this.disabled = true;
      this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Joining...';
      
      // Navigate to join page
      window.location.href = `/conversation/join/${roomCode}`;
    });
  }
  
  // Enter key in room code input
  const roomCodeInput = document.getElementById('room-code-input');
  if (roomCodeInput) {
    roomCodeInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        document.getElementById('join-room-btn').click();
      }
    });
    
    // Auto-format room code input
    roomCodeInput.addEventListener('input', function(e) {
      let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      if (value.length > 6) {
        value = value.substring(0, 6);
      }
      e.target.value = value;
    });
  }
  
  // Close modal on overlay click
  const conversationModal = document.getElementById('conversation-modal');
  if (conversationModal) {
    conversationModal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeConversationModal();
      }
    });
  }
  
  // Close modal on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const modal = document.getElementById('conversation-modal');
      if (modal && (modal.classList.contains('show') || modal.style.display === 'flex')) {
        closeConversationModal();
      }
    }
  });

  // Mark as initialized after all event listeners are set up
  setTimeout(() => {
    conversationModalInitialized = true;
    console.log('Conversation modal fully initialized');
  }, 100);
});

// Export functions for global access with safeguards
window.openConversationModal = function(userInitiated = false) {
  if (!conversationModalInitialized && !userInitiated) {
    console.warn('Conversation modal not properly initialized - preventing automatic opening');
    return;
  }
  _openConversationModal(userInitiated);
};

window.closeConversationModal = closeConversationModal;
window.resetConversationModal = resetConversationModal;
window.copyRoomCode = copyRoomCode;
window.copyRoomLink = copyRoomLink;
