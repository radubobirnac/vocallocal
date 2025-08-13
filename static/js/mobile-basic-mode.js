/**
 * Mobile Basic Mode Enhancements
 * Provides mobile-specific functionality and UX improvements for basic mode
 */

class MobileBasicMode {
  constructor() {
    // Improved mobile detection: check both user agent AND viewport width
    this.isMobile = this.detectMobile();
    this.isRecording = false;
    this.recordingStartTime = null;
    this.recordingTimer = null;

    if (this.isMobile) {
      this.init();
    }
  }

  detectMobile() {
    // Check user agent for actual mobile devices
    const userAgentMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent.toLowerCase());

    // Check viewport width for mobile emulation or small screens
    const viewportMobile = window.innerWidth <= 768;

    // Check for touch capability
    const touchCapable = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    const isMobile = userAgentMobile || (viewportMobile && touchCapable) || viewportMobile;

    console.log('[MobileBasicMode] Mobile detection:', {
      userAgent: userAgentMobile,
      viewport: viewportMobile,
      touch: touchCapable,
      final: isMobile,
      width: window.innerWidth
    });

    return isMobile;
  }

  init() {
    console.log('[MobileBasicMode] Initializing mobile basic mode enhancements');
    this.setupMobileOptimizations();
    this.setupTouchInteractions();
    this.setupVisualFeedback();
    this.setupAccessibility();
    this.setupPerformanceOptimizations();
    this.setupMobilePlaybackControls();
    this.setupResizeListener();
    this.runMobileInterfaceTests();
  }

  setupResizeListener() {
    // Re-check mobile status on window resize (for desktop browser mobile emulation)
    window.addEventListener('resize', () => {
      const wasMobile = this.isMobile;
      this.isMobile = this.detectMobile();

      if (this.isMobile && !wasMobile) {
        console.log('[MobileBasicMode] Switched to mobile view, re-initializing...');
        this.setupMobilePlaybackControls();
        this.runMobileInterfaceTests();
      } else if (!this.isMobile && wasMobile) {
        console.log('[MobileBasicMode] Switched to desktop view');
      }
    });
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
    // Ensure microphone button is always visible on mobile
    this.ensureMicrophoneButtonPersistence(recordBtn);

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
    // Keep microphone icon instead of changing to stop icon for mobile
    // This ensures the button always shows its purpose
    recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';

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

  ensureMicrophoneButtonPersistence(recordBtn) {
    // Force the button to always be visible and maintain its microphone icon
    const forceVisibility = () => {
      recordBtn.style.display = 'flex';
      recordBtn.style.visibility = 'visible';
      recordBtn.style.opacity = '1';

      // Ensure microphone icon is present
      const icon = recordBtn.querySelector('i');
      if (!icon || !icon.classList.contains('fa-microphone')) {
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      }
    };

    // Initial force
    forceVisibility();

    // Set up mutation observer to prevent the button from being hidden
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' || mutation.type === 'childList') {
          // Check if button visibility was changed
          const computedStyle = getComputedStyle(recordBtn);
          if (computedStyle.display === 'none' ||
              computedStyle.visibility === 'hidden' ||
              computedStyle.opacity === '0') {
            console.log('[MobileBasicMode] Microphone button visibility was changed, restoring...');
            forceVisibility();
          }
        }
      });
    });

    // Observe the button and its parent for changes
    observer.observe(recordBtn, {
      attributes: true,
      childList: true,
      subtree: true,
      attributeFilter: ['style', 'class']
    });

    // Also observe the parent container
    const parentContainer = recordBtn.closest('.flex');
    if (parentContainer) {
      observer.observe(parentContainer, {
        attributes: true,
        childList: true,
        subtree: true
      });
    }

    // Periodic check as backup
    setInterval(() => {
      const computedStyle = getComputedStyle(recordBtn);
      if (computedStyle.display === 'none' ||
          computedStyle.visibility === 'hidden' ||
          computedStyle.opacity === '0') {
        console.log('[MobileBasicMode] Periodic check: Microphone button was hidden, restoring...');
        forceVisibility();
      }
    }, 1000);
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

  /**
   * Setup mobile-specific playback controls
   * Combines play/pause/stop functionality into a single button
   */
  setupMobilePlaybackControls() {
    console.log('[MobileBasicMode] Setting up mobile playback controls');

    // Track current playback state
    this.playbackState = 'stopped'; // 'stopped', 'playing', 'paused'
    this.currentAudio = null;

    // Override the play button behavior for mobile
    const playBtn = document.getElementById('basic-play-btn');
    if (playBtn) {
      // Remove existing event listeners by cloning the button
      const newPlayBtn = playBtn.cloneNode(true);
      playBtn.parentNode.replaceChild(newPlayBtn, playBtn);

      // Add mobile-specific event listener
      newPlayBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.handleMobilePlaybackClick();
      });

      // Update button title for mobile
      newPlayBtn.setAttribute('title', 'Play/Pause/Stop audio');
      newPlayBtn.setAttribute('aria-label', 'Play, pause, or stop audio playback');
    }

    // Listen for TTS events to update button state
    document.addEventListener('tts-started', (e) => {
      if (e.detail.sourceId === 'basic-transcript') {
        this.updateMobilePlayButton('playing');
      }
    });

    document.addEventListener('tts-stopped', (e) => {
      if (e.detail.sourceId === 'basic-transcript') {
        this.updateMobilePlayButton('stopped');
      }
    });

    document.addEventListener('tts-ended', (e) => {
      if (e.detail.sourceId === 'basic-transcript') {
        this.updateMobilePlayButton('stopped');
      }
    });
  }

  handleMobilePlaybackClick() {
    console.log('[MobileBasicMode] Mobile playback button clicked, current state:', this.playbackState);

    const transcriptEl = document.getElementById('basic-transcript');
    if (!transcriptEl || !transcriptEl.value.trim()) {
      console.log('[MobileBasicMode] No transcript text to play');
      return;
    }

    switch (this.playbackState) {
      case 'stopped':
        // Start playing
        console.log('[MobileBasicMode] Starting playback');
        this.startMobilePlayback();
        break;
      case 'playing':
        // Stop playback (combining pause and stop functionality)
        console.log('[MobileBasicMode] Stopping playback');
        this.stopMobilePlayback();
        break;
      case 'paused':
        // Resume playing (not implemented yet, so restart)
        console.log('[MobileBasicMode] Resuming playback');
        this.startMobilePlayback();
        break;
    }
  }

  startMobilePlayback() {
    // Use the existing TTS function
    if (window.speakText) {
      window.speakText('basic-transcript');
      this.playbackState = 'playing';
      this.updateMobilePlayButton('playing');
    }
  }

  stopMobilePlayback() {
    // Use the existing stop function
    if (window.stopSpeakText) {
      window.stopSpeakText('basic-transcript');
      this.playbackState = 'stopped';
      this.updateMobilePlayButton('stopped');
    }
  }

  updateMobilePlayButton(state) {
    const playBtn = document.getElementById('basic-play-btn');
    if (!playBtn) return;

    const icon = playBtn.querySelector('i');
    if (!icon) return;

    this.playbackState = state;

    switch (state) {
      case 'playing':
        icon.className = 'fas fa-stop';
        playBtn.setAttribute('title', 'Stop audio');
        break;
      case 'paused':
        icon.className = 'fas fa-play';
        playBtn.setAttribute('title', 'Resume audio');
        break;
      case 'stopped':
      default:
        icon.className = 'fas fa-play';
        playBtn.setAttribute('title', 'Play audio');
        break;
    }

    console.log('[MobileBasicMode] Updated mobile play button to state:', state);
  }

  /**
   * Run tests to verify mobile interface functionality
   */
  runMobileInterfaceTests() {
    console.log('[MobileBasicMode] Running mobile interface tests...');

    setTimeout(() => {
      this.testStopButtonHidden();
      this.testMicrophoneButtonVisible();
      this.testPlayButtonEnhanced();
    }, 1000);
  }

  testStopButtonHidden() {
    const stopBtn = document.getElementById('basic-stop-btn');
    if (stopBtn) {
      const computedStyle = getComputedStyle(stopBtn);
      const isHidden = computedStyle.display === 'none';
      console.log('[MobileBasicMode] Stop button hidden test:', isHidden ? '✅ PASS' : '❌ FAIL');
      if (!isHidden) {
        console.warn('[MobileBasicMode] Stop button should be hidden on mobile');
      }
    } else {
      console.log('[MobileBasicMode] Stop button not found');
    }
  }

  testMicrophoneButtonVisible() {
    const recordBtn = document.getElementById('basic-record-btn');
    if (recordBtn) {
      const computedStyle = getComputedStyle(recordBtn);
      const isVisible = computedStyle.display !== 'none' &&
                       computedStyle.visibility !== 'hidden' &&
                       computedStyle.opacity !== '0';
      console.log('[MobileBasicMode] Microphone button visible test:', isVisible ? '✅ PASS' : '❌ FAIL');

      // Test icon presence
      const icon = recordBtn.querySelector('i.fa-microphone');
      const hasIcon = icon !== null;
      console.log('[MobileBasicMode] Microphone icon present test:', hasIcon ? '✅ PASS' : '❌ FAIL');

      if (!isVisible || !hasIcon) {
        console.warn('[MobileBasicMode] Microphone button should be visible with microphone icon');
      }
    } else {
      console.log('[MobileBasicMode] Microphone button not found');
    }
  }

  testPlayButtonEnhanced() {
    const playBtn = document.getElementById('basic-play-btn');
    if (playBtn) {
      const hasEnhancedTitle = playBtn.getAttribute('title').includes('Play/Pause/Stop') ||
                              playBtn.getAttribute('aria-label').includes('Play, pause, or stop');
      console.log('[MobileBasicMode] Play button enhanced test:', hasEnhancedTitle ? '✅ PASS' : '❌ FAIL');

      if (!hasEnhancedTitle) {
        console.warn('[MobileBasicMode] Play button should have enhanced functionality for mobile');
      }
    } else {
      console.log('[MobileBasicMode] Play button not found');
    }
  }
}

// Initialize mobile basic mode enhancements
let mobileBasicMode;

function initializeMobileBasicMode() {
  if (!mobileBasicMode) {
    mobileBasicMode = new MobileBasicMode();
    window.mobileBasicMode = mobileBasicMode;

    // Force initialization for testing purposes if viewport is mobile-sized
    if (!mobileBasicMode.isMobile && window.innerWidth <= 768) {
      console.log('[MobileBasicMode] Force initializing for mobile viewport testing');
      mobileBasicMode.isMobile = true;
      mobileBasicMode.init();
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeMobileBasicMode);
} else {
  initializeMobileBasicMode();
}

console.log('[MobileBasicMode] Mobile basic mode enhancements loaded');
