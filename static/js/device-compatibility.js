/**
 * Device Compatibility Testing and Optimization
 * Detects device capabilities and applies appropriate optimizations
 */

class DeviceCompatibility {
  constructor() {
    this.deviceInfo = this.detectDevice();
    this.browserInfo = this.detectBrowser();
    this.capabilities = this.detectCapabilities();
    
    this.init();
  }

  init() {
    console.log('[DeviceCompat] Initializing device compatibility system');
    console.log('[DeviceCompat] Device:', this.deviceInfo);
    console.log('[DeviceCompat] Browser:', this.browserInfo);
    console.log('[DeviceCompat] Capabilities:', this.capabilities);
    
    this.applyDeviceOptimizations();
    this.setupPerformanceMonitoring();
    this.setupCompatibilityFixes();
    this.reportCompatibilityStatus();
  }

  /**
   * Detect device type and characteristics
   */
  detectDevice() {
    const userAgent = navigator.userAgent.toLowerCase();
    const platform = navigator.platform.toLowerCase();
    
    const device = {
      type: 'desktop',
      os: 'unknown',
      model: 'unknown',
      isTouch: 'ontouchstart' in window,
      screenSize: {
        width: window.screen.width,
        height: window.screen.height,
        ratio: window.devicePixelRatio || 1
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    };

    // Detect mobile devices
    if (/android/i.test(userAgent)) {
      device.type = 'mobile';
      device.os = 'android';
      
      // Detect specific Android devices
      if (/samsung/i.test(userAgent)) device.model = 'samsung';
      else if (/huawei/i.test(userAgent)) device.model = 'huawei';
      else if (/xiaomi/i.test(userAgent)) device.model = 'xiaomi';
      else if (/oneplus/i.test(userAgent)) device.model = 'oneplus';
      
    } else if (/iphone|ipod/i.test(userAgent)) {
      device.type = 'mobile';
      device.os = 'ios';
      device.model = 'iphone';
      
    } else if (/ipad/i.test(userAgent)) {
      device.type = 'tablet';
      device.os = 'ios';
      device.model = 'ipad';
      
    } else if (/tablet|kindle/i.test(userAgent)) {
      device.type = 'tablet';
      
    } else if (device.isTouch && device.viewport.width <= 768) {
      device.type = 'mobile';
    }

    // Detect OS
    if (/windows/i.test(userAgent)) device.os = 'windows';
    else if (/mac/i.test(userAgent)) device.os = 'macos';
    else if (/linux/i.test(userAgent)) device.os = 'linux';

    return device;
  }

  /**
   * Detect browser type and version
   */
  detectBrowser() {
    const userAgent = navigator.userAgent.toLowerCase();
    
    const browser = {
      name: 'unknown',
      version: 'unknown',
      engine: 'unknown',
      isWebView: false
    };

    // Detect browser
    if (/chrome/i.test(userAgent) && !/edge/i.test(userAgent)) {
      browser.name = 'chrome';
      browser.engine = 'blink';
    } else if (/safari/i.test(userAgent) && !/chrome/i.test(userAgent)) {
      browser.name = 'safari';
      browser.engine = 'webkit';
    } else if (/firefox/i.test(userAgent)) {
      browser.name = 'firefox';
      browser.engine = 'gecko';
    } else if (/edge/i.test(userAgent)) {
      browser.name = 'edge';
      browser.engine = 'blink';
    } else if (/opera/i.test(userAgent)) {
      browser.name = 'opera';
      browser.engine = 'blink';
    }

    // Detect WebView
    if (/wv|webview/i.test(userAgent)) {
      browser.isWebView = true;
    }

    // Extract version
    const versionMatch = userAgent.match(new RegExp(browser.name + '/([0-9.]+)'));
    if (versionMatch) {
      browser.version = versionMatch[1];
    }

    return browser;
  }

  /**
   * Detect device capabilities
   */
  detectCapabilities() {
    const capabilities = {
      webAudio: !!(window.AudioContext || window.webkitAudioContext),
      mediaRecorder: !!window.MediaRecorder,
      getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      webGL: this.detectWebGL(),
      localStorage: this.detectLocalStorage(),
      serviceWorker: 'serviceWorker' in navigator,
      intersectionObserver: 'IntersectionObserver' in window,
      resizeObserver: 'ResizeObserver' in window,
      webAssembly: 'WebAssembly' in window,
      es6: this.detectES6Support(),
      css: {
        grid: this.detectCSSSupport('display', 'grid'),
        flexbox: this.detectCSSSupport('display', 'flex'),
        customProperties: this.detectCSSSupport('--test', 'test'),
        backdropFilter: this.detectCSSSupport('backdrop-filter', 'blur(1px)')
      },
      performance: {
        memory: !!(performance && performance.memory),
        navigation: !!(performance && performance.navigation),
        timing: !!(performance && performance.timing)
      }
    };

    return capabilities;
  }

  detectWebGL() {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
    } catch (e) {
      return false;
    }
  }

  detectLocalStorage() {
    try {
      const test = 'test';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (e) {
      return false;
    }
  }

  detectES6Support() {
    try {
      return typeof Symbol !== 'undefined' && 
             typeof Promise !== 'undefined' && 
             typeof Map !== 'undefined';
    } catch (e) {
      return false;
    }
  }

  detectCSSSupport(property, value) {
    const element = document.createElement('div');
    element.style[property] = value;
    return element.style[property] === value;
  }

  /**
   * Apply device-specific optimizations
   */
  applyDeviceOptimizations() {
    // Apply mobile optimizations
    if (this.deviceInfo.type === 'mobile') {
      this.applyMobileOptimizations();
    }
    
    // Apply iOS-specific fixes
    if (this.deviceInfo.os === 'ios') {
      this.applyIOSFixes();
    }
    
    // Apply Android-specific fixes
    if (this.deviceInfo.os === 'android') {
      this.applyAndroidFixes();
    }
    
    // Apply browser-specific fixes
    this.applyBrowserFixes();
    
    // Apply performance optimizations based on capabilities
    this.applyPerformanceOptimizations();
  }

  applyMobileOptimizations() {
    // Disable hover effects on mobile
    const style = document.createElement('style');
    style.textContent = `
      @media (hover: none) {
        .button:hover,
        .nav-tab:hover,
        .card:hover {
          transform: none !important;
          box-shadow: inherit !important;
        }
      }
    `;
    document.head.appendChild(style);
    
    // Optimize touch targets
    document.body.classList.add('mobile-device');
    
    // Prevent zoom on input focus
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
        input.style.fontSize = '16px';
      }
    });
  }

  applyIOSFixes() {
    document.body.classList.add('ios-device');
    
    // Fix iOS Safari viewport issues
    const fixIOSViewport = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    
    fixIOSViewport();
    window.addEventListener('resize', fixIOSViewport);
    window.addEventListener('orientationchange', () => {
      setTimeout(fixIOSViewport, 100);
    });
    
    // Fix iOS audio context issues
    if (this.capabilities.webAudio) {
      this.fixIOSAudioContext();
    }
  }

  fixIOSAudioContext() {
    // iOS requires user interaction to start audio context
    const startAudioContext = () => {
      if (window.audioContext && window.audioContext.state === 'suspended') {
        window.audioContext.resume();
      }
    };
    
    document.addEventListener('touchstart', startAudioContext, { once: true });
    document.addEventListener('click', startAudioContext, { once: true });
  }

  applyAndroidFixes() {
    document.body.classList.add('android-device');
    
    // Fix Android Chrome address bar height issues
    const fixAndroidViewport = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    
    fixAndroidViewport();
    window.addEventListener('resize', fixAndroidViewport);
  }

  applyBrowserFixes() {
    document.body.classList.add(`browser-${this.browserInfo.name}`);
    
    // Safari-specific fixes
    if (this.browserInfo.name === 'safari') {
      this.applySafariFixes();
    }
    
    // Chrome-specific fixes
    if (this.browserInfo.name === 'chrome') {
      this.applyChromeFixes();
    }
    
    // Firefox-specific fixes
    if (this.browserInfo.name === 'firefox') {
      this.applyFirefoxFixes();
    }
  }

  applySafariFixes() {
    // Fix Safari flexbox issues
    const style = document.createElement('style');
    style.textContent = `
      .flex {
        display: -webkit-flex;
        display: flex;
      }
      .flex-col {
        -webkit-flex-direction: column;
        flex-direction: column;
      }
    `;
    document.head.appendChild(style);
  }

  applyChromeFixes() {
    // Chrome-specific optimizations
    if (this.deviceInfo.type === 'mobile') {
      // Optimize for Chrome mobile
      document.body.style.webkitTapHighlightColor = 'transparent';
    }
  }

  applyFirefoxFixes() {
    // Firefox-specific fixes
    const style = document.createElement('style');
    style.textContent = `
      input, textarea, select {
        -moz-appearance: none;
      }
    `;
    document.head.appendChild(style);
  }

  applyPerformanceOptimizations() {
    // Reduce animations on low-end devices
    if (this.isLowEndDevice()) {
      this.reducedMotionMode();
    }
    
    // Optimize based on memory constraints
    if (this.capabilities.performance.memory && performance.memory.usedJSHeapSize > 50000000) {
      this.memoryOptimizationMode();
    }
  }

  isLowEndDevice() {
    // Heuristics to detect low-end devices
    const lowEndIndicators = [
      this.deviceInfo.screenSize.width < 720,
      this.deviceInfo.screenSize.ratio < 2,
      !this.capabilities.webGL,
      !this.capabilities.webAssembly
    ];
    
    return lowEndIndicators.filter(Boolean).length >= 2;
  }

  reducedMotionMode() {
    const style = document.createElement('style');
    style.textContent = `
      *, *::before, *::after {
        animation-duration: 0.1s !important;
        transition-duration: 0.1s !important;
      }
    `;
    document.head.appendChild(style);
    document.body.classList.add('reduced-motion');
  }

  memoryOptimizationMode() {
    // Reduce memory usage
    document.body.classList.add('memory-optimized');
    
    // Disable non-essential features
    if (window.performanceOptimizer) {
      window.performanceOptimizer.enableMemoryOptimization();
    }
  }

  /**
   * Setup performance monitoring
   */
  setupPerformanceMonitoring() {
    if (this.capabilities.performance.timing) {
      this.monitorPageLoad();
    }
    
    if (this.capabilities.performance.memory) {
      this.monitorMemoryUsage();
    }
  }

  monitorPageLoad() {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
        
        console.log(`[DeviceCompat] Page load time: ${loadTime}ms`);
        console.log(`[DeviceCompat] DOM ready time: ${domReady}ms`);
        
        // Report slow loading
        if (loadTime > 5000) {
          console.warn('[DeviceCompat] Slow page load detected');
          this.handleSlowPerformance();
        }
      }, 100);
    });
  }

  monitorMemoryUsage() {
    setInterval(() => {
      if (performance.memory) {
        const used = performance.memory.usedJSHeapSize;
        const limit = performance.memory.jsHeapSizeLimit;
        const percentage = (used / limit) * 100;
        
        if (percentage > 80) {
          console.warn('[DeviceCompat] High memory usage detected:', percentage.toFixed(1) + '%');
          this.handleHighMemoryUsage();
        }
      }
    }, 30000);
  }

  handleSlowPerformance() {
    // Enable performance mode
    document.body.classList.add('performance-mode');
    
    // Notify user
    if (window.showStatus) {
      window.showStatus('Optimizing for your device...', 'info');
    }
  }

  handleHighMemoryUsage() {
    // Trigger garbage collection if available
    if (window.gc && typeof window.gc === 'function') {
      window.gc();
    }
    
    // Enable memory optimization
    this.memoryOptimizationMode();
  }

  /**
   * Setup compatibility fixes
   */
  setupCompatibilityFixes() {
    // Polyfills for missing features
    this.loadPolyfills();
    
    // Fallbacks for unsupported features
    this.setupFallbacks();
  }

  loadPolyfills() {
    const polyfillsNeeded = [];
    
    if (!this.capabilities.intersectionObserver) {
      polyfillsNeeded.push('intersection-observer');
    }
    
    if (!this.capabilities.resizeObserver) {
      polyfillsNeeded.push('resize-observer');
    }
    
    if (!this.capabilities.es6) {
      polyfillsNeeded.push('es6-polyfill');
    }
    
    // Load polyfills if needed
    polyfillsNeeded.forEach(polyfill => {
      console.log(`[DeviceCompat] Loading polyfill: ${polyfill}`);
      // In a real implementation, you would load the actual polyfill scripts
    });
  }

  setupFallbacks() {
    // Fallback for getUserMedia
    if (!this.capabilities.getUserMedia) {
      console.warn('[DeviceCompat] getUserMedia not supported, disabling recording features');
      this.disableRecordingFeatures();
    }
    
    // Fallback for Web Audio API
    if (!this.capabilities.webAudio) {
      console.warn('[DeviceCompat] Web Audio API not supported, using fallback audio');
      this.setupAudioFallback();
    }
  }

  disableRecordingFeatures() {
    const recordButtons = document.querySelectorAll('[id*="record"]');
    recordButtons.forEach(button => {
      button.disabled = true;
      button.title = 'Recording not supported on this device';
    });
  }

  setupAudioFallback() {
    // Use HTML5 audio as fallback
    window.audioFallbackMode = true;
  }

  /**
   * Report compatibility status
   */
  reportCompatibilityStatus() {
    const compatibility = {
      device: this.deviceInfo,
      browser: this.browserInfo,
      capabilities: this.capabilities,
      optimizations: this.getAppliedOptimizations(),
      timestamp: new Date().toISOString()
    };
    
    // Store compatibility info globally
    window.deviceCompatibility = compatibility;
    
    // Log summary
    console.log('[DeviceCompat] Compatibility report:', compatibility);
    
    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', 'device_compatibility', {
        device_type: this.deviceInfo.type,
        device_os: this.deviceInfo.os,
        browser_name: this.browserInfo.name,
        has_web_audio: this.capabilities.webAudio,
        has_media_recorder: this.capabilities.mediaRecorder
      });
    }
  }

  getAppliedOptimizations() {
    const optimizations = [];
    
    if (document.body.classList.contains('mobile-device')) {
      optimizations.push('mobile');
    }
    if (document.body.classList.contains('reduced-motion')) {
      optimizations.push('reduced-motion');
    }
    if (document.body.classList.contains('memory-optimized')) {
      optimizations.push('memory-optimized');
    }
    if (document.body.classList.contains('performance-mode')) {
      optimizations.push('performance-mode');
    }
    
    return optimizations;
  }

  /**
   * Get device compatibility score
   */
  getCompatibilityScore() {
    let score = 0;
    const maxScore = 10;
    
    // Basic functionality
    if (this.capabilities.localStorage) score += 1;
    if (this.capabilities.es6) score += 1;
    
    // Audio capabilities
    if (this.capabilities.webAudio) score += 2;
    if (this.capabilities.mediaRecorder) score += 2;
    if (this.capabilities.getUserMedia) score += 2;
    
    // Modern features
    if (this.capabilities.serviceWorker) score += 1;
    if (this.capabilities.intersectionObserver) score += 1;
    
    return Math.round((score / maxScore) * 100);
  }
}

// Initialize device compatibility
const deviceCompatibility = new DeviceCompatibility();
window.deviceCompatibility = deviceCompatibility;

console.log('[DeviceCompat] Device compatibility system loaded');
