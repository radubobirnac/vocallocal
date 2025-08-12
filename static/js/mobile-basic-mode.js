/**
 * Mobile Basic Mode Enhancements
 * Provides mobile-specific functionality and UX improvements for basic mode
 */

class MobileBasicMode {
  constructor() {
    this.isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent.toLowerCase());
    this.isRecording = false;
    this.recordingStartTime = null;
    this.recordingTimer = null;
    
    if (this.isMobile) {
      this.init();
    }
  }

  init() {
    console.log('[MobileBasicMode] Initializing mobile basic mode enhancements');
    this.setupMobileOptimizations();
    this.setupTouchInteractions();
    this.setupVisualFeedback();
    this.setupAccessibility();
    this.setupPerformanceOptimizations();
  }

  /**
   * Setup mobile-specific optimizations
   */
  setupMobileOptimizations() {
    // Optimize viewport for mobile
    this.optimizeViewport();
    
    // Setup mobile-friendly interactions
    this.setupMobileFriendlyButtons();
    
    // Optimize text areas for mobile
    this.optimizeTextAreas();
    
    // Setup mobile keyboard handling
    this.setupMobileKeyboard();
  }

  optimizeViewport() {
    // Prevent zoom on input focus
    const viewportMeta = document.querySelector('meta[name="viewport"]');
    if (viewportMeta) {
      viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }
    
    // Handle orientation changes
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.adjustLayoutForOrientation();
      }, 100);
    });
  }

  adjustLayoutForOrientation() {
    const basicMode = document.getElementById('basic-mode');
    if (!basicMode) return;
    
    if (window.orientation === 90 || window.orientation === -90) {
      // Landscape mode
      basicMode.classList.add('landscape-mode');
      this.optimizeForLandscape();
    } else {
      // Portrait mode
      basicMode.classList.remove('landscape-mode');
      this.optimizeForPortrait();
    }
  }

  optimizeForLandscape() {
    const transcript = document.getElementById('basic-transcript');
    const interpretation = document.getElementById('basic-interpretation');
    
    if (transcript) {
      transcript.style.minHeight = '120px';
    }
    if (interpretation) {
      interpretation.style.minHeight = '100px';
    }
  }

  optimizeForPortrait() {
    const transcript = document.getElementById('basic-transcript');
    const interpretation = document.getElementById('basic-interpretation');
    
    if (transcript) {
      transcript.style.minHeight = '200px';
    }
    if (interpretation) {
      interpretation.style.minHeight = '150px';
    }
  }

  setupMobileFriendlyButtons() {
    // Make buttons more touch-friendly
    const buttons = document.querySelectorAll('#basic-mode .button, #basic-mode .button-icon');
    buttons.forEach(button => {
      // Ensure minimum touch target size
      const rect = button.getBoundingClientRect();
      if (rect.width < 44 || rect.height < 44) {
        button.style.minWidth = '44px';
        button.style.minHeight = '44px';
      }
      
      // Add touch feedback
      this.addTouchFeedback(button);
    });
    
    // Special handling for record button
    const recordBtn = document.getElementById('basic-record-btn');
    if (recordBtn) {
      this.setupRecordButtonEnhancements(recordBtn);
    }
  }

  addTouchFeedback(element) {
    element.addEventListener('touchstart', (e) => {
      element.classList.add('touch-active');
      
      // Haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate(10);
      }
    }, { passive: true });
    
    element.addEventListener('touchend', () => {
      setTimeout(() => {
        element.classList.remove('touch-active');
      }, 150);
    }, { passive: true });
  }

  setupRecordButtonEnhancements(recordBtn) {
    // Add visual recording state
    recordBtn.addEventListener('click', () => {
      if (!this.isRecording) {
        this.startRecordingVisuals(recordBtn);
      } else {
        this.stopRecordingVisuals(recordBtn);
      }
    });
    
    // Add long press for continuous recording
    let longPressTimer;
    
    recordBtn.addEventListener('touchstart', (e) => {
      longPressTimer = setTimeout(() => {
        if (!this.isRecording) {
          this.startContinuousRecording(recordBtn);
        }
      }, 500);
    }, { passive: true });
    
    recordBtn.addEventListener('touchend', () => {
      clearTimeout(longPressTimer);
    }, { passive: true });
  }

  startRecordingVisuals(recordBtn) {
    this.isRecording = true;
    this.recordingStartTime = Date.now();
    
    recordBtn.classList.add('recording');
    recordBtn.innerHTML = '<i class="fas fa-stop"></i>';
    
    // Start recording timer
    this.startRecordingTimer();
    
    // Show recording indicator
    this.showRecordingIndicator();
  }

  stopRecordingVisuals(recordBtn) {
    this.isRecording = false;
    this.recordingStartTime = null;
    
    recordBtn.classList.remove('recording');
    recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    
    // Stop recording timer
    this.stopRecordingTimer();
    
    // Hide recording indicator
    this.hideRecordingIndicator();
  }

  startRecordingTimer() {
    this.recordingTimer = setInterval(() => {
      if (this.recordingStartTime) {
        const elapsed = Date.now() - this.recordingStartTime;
        const seconds = Math.floor(elapsed / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        const timeString = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        this.updateRecordingTimer(timeString);
      }
    }, 1000);
  }

  stopRecordingTimer() {
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
      this.recordingTimer = null;
    }
    this.updateRecordingTimer('00:00');
  }

  updateRecordingTimer(timeString) {
    let timerElement = document.getElementById('mobile-recording-timer');
    if (!timerElement) {
      timerElement = this.createRecordingTimer();
    }
    timerElement.textContent = timeString;
  }

  createRecordingTimer() {
    const timer = document.createElement('div');
    timer.id = 'mobile-recording-timer';
    timer.className = 'mobile-recording-timer';
    timer.textContent = '00:00';
    
    const cardHeader = document.querySelector('#basic-mode .card-header');
    if (cardHeader) {
      cardHeader.appendChild(timer);
    }
    
    return timer;
  }

  showRecordingIndicator() {
    let indicator = document.getElementById('mobile-recording-indicator');
    if (!indicator) {
      indicator = this.createRecordingIndicator();
    }
    indicator.style.display = 'block';
  }

  hideRecordingIndicator() {
    const indicator = document.getElementById('mobile-recording-indicator');
    if (indicator) {
      indicator.style.display = 'none';
    }
  }

  createRecordingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'mobile-recording-indicator';
    indicator.className = 'mobile-recording-indicator';
    indicator.innerHTML = '<i class="fas fa-circle"></i> Recording...';
    
    const basicMode = document.getElementById('basic-mode');
    if (basicMode) {
      basicMode.insertBefore(indicator, basicMode.firstChild);
    }
    
    return indicator;
  }

  /**
   * Setup touch interactions
   */
  setupTouchInteractions() {
    // Prevent double-tap zoom on buttons
    const buttons = document.querySelectorAll('#basic-mode button');
    buttons.forEach(button => {
      button.addEventListener('touchend', (e) => {
        e.preventDefault();
        button.click();
      });
    });
    
    // Setup swipe gestures for text areas
    this.setupSwipeGestures();
  }

  setupSwipeGestures() {
    const transcript = document.getElementById('basic-transcript');
    const interpretation = document.getElementById('basic-interpretation');
    
    [transcript, interpretation].forEach(textarea => {
      if (textarea) {
        this.addSwipeToSelect(textarea);
      }
    });
  }

  addSwipeToSelect(element) {
    let startY = 0;
    let startX = 0;
    
    element.addEventListener('touchstart', (e) => {
      startY = e.touches[0].clientY;
      startX = e.touches[0].clientX;
    }, { passive: true });
    
    element.addEventListener('touchmove', (e) => {
      const currentY = e.touches[0].clientY;
      const currentX = e.touches[0].clientX;
      const diffY = Math.abs(currentY - startY);
      const diffX = Math.abs(currentX - startX);
      
      // If horizontal swipe is dominant, select all text
      if (diffX > diffY && diffX > 50) {
        element.select();
      }
    }, { passive: true });
  }

  /**
   * Setup visual feedback
   */
  setupVisualFeedback() {
    // Add loading states to buttons
    this.setupLoadingStates();
    
    // Add success/error feedback
    this.setupStatusFeedback();
  }

  setupLoadingStates() {
    const actionButtons = [
      'basic-interpret-btn',
      'basic-play-btn',
      'basic-upload-btn'
    ];
    
    actionButtons.forEach(buttonId => {
      const button = document.getElementById(buttonId);
      if (button) {
        button.addEventListener('click', () => {
          this.showButtonLoading(button);
        });
      }
    });
  }

  showButtonLoading(button) {
    button.classList.add('loading');
    const originalText = button.innerHTML;
    
    // Auto-remove loading state after 5 seconds
    setTimeout(() => {
      this.hideButtonLoading(button, originalText);
    }, 5000);
  }

  hideButtonLoading(button, originalText) {
    button.classList.remove('loading');
    if (originalText) {
      button.innerHTML = originalText;
    }
  }

  setupStatusFeedback() {
    // Enhanced status messages for mobile
    const status = document.getElementById('status');
    if (status) {
      // Make status messages more prominent on mobile
      status.style.position = 'sticky';
      status.style.top = '0';
      status.style.zIndex = '100';
    }
  }

  /**
   * Setup accessibility improvements
   */
  setupAccessibility() {
    // Add ARIA labels for mobile screen readers
    this.addAriaLabels();
    
    // Improve focus management
    this.improveFocusManagement();
  }

  addAriaLabels() {
    const recordBtn = document.getElementById('basic-record-btn');
    if (recordBtn) {
      recordBtn.setAttribute('aria-label', 'Start or stop voice recording');
    }
    
    const transcript = document.getElementById('basic-transcript');
    if (transcript) {
      transcript.setAttribute('aria-label', 'Transcribed text will appear here');
    }
    
    const interpretation = document.getElementById('basic-interpretation');
    if (interpretation) {
      interpretation.setAttribute('aria-label', 'AI interpretation will appear here');
    }
  }

  improveFocusManagement() {
    // Ensure proper tab order on mobile
    const focusableElements = document.querySelectorAll('#basic-mode button, #basic-mode select, #basic-mode textarea');
    focusableElements.forEach((element, index) => {
      element.setAttribute('tabindex', index + 1);
    });
  }

  /**
   * Setup performance optimizations
   */
  setupPerformanceOptimizations() {
    // Debounce text area updates
    this.setupTextAreaDebouncing();
    
    // Optimize scroll performance
    this.optimizeScrolling();
  }

  setupTextAreaDebouncing() {
    const textAreas = document.querySelectorAll('#basic-mode textarea');
    textAreas.forEach(textarea => {
      let timeout;
      textarea.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          // Trigger any necessary updates
          this.handleTextAreaUpdate(textarea);
        }, 300);
      });
    });
  }

  handleTextAreaUpdate(textarea) {
    // Save content to localStorage for recovery
    const key = `mobile-basic-${textarea.id}`;
    try {
      localStorage.setItem(key, textarea.value);
    } catch (e) {
      console.warn('Could not save textarea content to localStorage');
    }
  }

  optimizeScrolling() {
    const textAreas = document.querySelectorAll('#basic-mode textarea');
    textAreas.forEach(textarea => {
      textarea.style.webkitOverflowScrolling = 'touch';
    });
  }

  /**
   * Optimize text areas for mobile
   */
  optimizeTextAreas() {
    const textAreas = document.querySelectorAll('#basic-mode textarea');
    textAreas.forEach(textarea => {
      // Prevent zoom on focus
      textarea.style.fontSize = '16px';
      
      // Add mobile-friendly attributes
      textarea.setAttribute('autocomplete', 'off');
      textarea.setAttribute('autocorrect', 'off');
      textarea.setAttribute('autocapitalize', 'off');
      textarea.setAttribute('spellcheck', 'false');
    });
  }

  /**
   * Setup mobile keyboard handling
   */
  setupMobileKeyboard() {
    const textAreas = document.querySelectorAll('#basic-mode textarea');
    textAreas.forEach(textarea => {
      textarea.addEventListener('focus', () => {
        // Scroll element into view when keyboard appears
        setTimeout(() => {
          textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      });
    });
  }
}

// Initialize mobile basic mode enhancements
let mobileBasicMode;

function initializeMobileBasicMode() {
  if (!mobileBasicMode) {
    mobileBasicMode = new MobileBasicMode();
    window.mobileBasicMode = mobileBasicMode;
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeMobileBasicMode);
} else {
  initializeMobileBasicMode();
}

console.log('[MobileBasicMode] Mobile basic mode enhancements loaded');
