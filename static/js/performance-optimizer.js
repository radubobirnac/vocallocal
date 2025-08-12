/**
 * Performance Optimizer for VocalLocal
 * Implements lazy loading, code splitting, and mobile performance optimizations
 */

class PerformanceOptimizer {
  constructor() {
    this.loadedModules = new Set();
    this.loadingPromises = new Map();
    this.criticalResources = new Set();
    this.deferredResources = new Set();
    
    this.init();
  }

  init() {
    console.log('[Performance] Initializing performance optimizer');
    this.setupIntersectionObserver();
    this.setupResourceHints();
    this.optimizeImageLoading();
    this.setupLazyScriptLoading();
    this.optimizeForMobile();
  }

  /**
   * Setup Intersection Observer for lazy loading
   */
  setupIntersectionObserver() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadLazyResource(entry.target);
            this.observer.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: '50px 0px',
        threshold: 0.1
      });
    }
  }

  /**
   * Add resource hints for better loading performance
   */
  setupResourceHints() {
    // Preconnect to external domains
    this.addResourceHint('preconnect', 'https://fonts.googleapis.com');
    this.addResourceHint('preconnect', 'https://fonts.gstatic.com');
    this.addResourceHint('preconnect', 'https://cdnjs.cloudflare.com');
    
    // DNS prefetch for API endpoints
    this.addResourceHint('dns-prefetch', window.location.origin);
  }

  addResourceHint(rel, href) {
    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    if (rel === 'preconnect') {
      link.crossOrigin = 'anonymous';
    }
    document.head.appendChild(link);
  }

  /**
   * Optimize image loading with lazy loading
   */
  optimizeImageLoading() {
    // Use native lazy loading if supported
    if ('loading' in HTMLImageElement.prototype) {
      document.querySelectorAll('img[data-src]').forEach(img => {
        img.loading = 'lazy';
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      });
    } else {
      // Fallback to Intersection Observer
      document.querySelectorAll('img[data-src]').forEach(img => {
        if (this.observer) {
          this.observer.observe(img);
        }
      });
    }
  }

  /**
   * Load lazy resource when it becomes visible
   */
  loadLazyResource(element) {
    if (element.tagName === 'IMG' && element.dataset.src) {
      element.src = element.dataset.src;
      element.removeAttribute('data-src');
    } else if (element.dataset.script) {
      this.loadScript(element.dataset.script);
    }
  }

  /**
   * Setup lazy script loading for non-critical features
   */
  setupLazyScriptLoading() {
    // Define non-critical scripts that can be loaded later
    this.deferredScripts = [
      '/static/js/bilingual-conversation.js',
      '/static/js/usage-enforcement.js',
      '/static/js/plan-access-control.js',
      '/static/sync-tts.js',
      '/static/direct-tts.js'
    ];

    // Load deferred scripts after initial page load
    if (document.readyState === 'complete') {
      this.loadDeferredScripts();
    } else {
      window.addEventListener('load', () => {
        setTimeout(() => this.loadDeferredScripts(), 100);
      });
    }
  }

  /**
   * Load deferred scripts with priority
   */
  async loadDeferredScripts() {
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
    
    // Load scripts based on user interaction and device type
    if (isMobile) {
      // On mobile, load scripts more aggressively to improve UX
      this.loadScriptsInBatches(this.deferredScripts, 2);
    } else {
      // On desktop, load scripts more conservatively
      this.loadScriptsInBatches(this.deferredScripts, 1);
    }
  }

  /**
   * Load scripts in batches to avoid blocking
   */
  async loadScriptsInBatches(scripts, batchSize) {
    for (let i = 0; i < scripts.length; i += batchSize) {
      const batch = scripts.slice(i, i + batchSize);
      const promises = batch.map(script => this.loadScript(script));
      
      try {
        await Promise.all(promises);
        // Small delay between batches to prevent blocking
        await new Promise(resolve => setTimeout(resolve, 50));
      } catch (error) {
        console.warn('[Performance] Error loading script batch:', error);
      }
    }
  }

  /**
   * Load script with caching and error handling
   */
  loadScript(src) {
    if (this.loadedModules.has(src)) {
      return Promise.resolve();
    }

    if (this.loadingPromises.has(src)) {
      return this.loadingPromises.get(src);
    }

    const promise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      
      script.onload = () => {
        this.loadedModules.add(src);
        this.loadingPromises.delete(src);
        console.log(`[Performance] Loaded script: ${src}`);
        resolve();
      };
      
      script.onerror = () => {
        this.loadingPromises.delete(src);
        console.warn(`[Performance] Failed to load script: ${src}`);
        reject(new Error(`Failed to load script: ${src}`));
      };
      
      document.head.appendChild(script);
    });

    this.loadingPromises.set(src, promise);
    return promise;
  }

  /**
   * Mobile-specific optimizations
   */
  optimizeForMobile() {
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
    
    if (isMobile) {
      // Reduce animation complexity on mobile
      this.optimizeAnimationsForMobile();
      
      // Optimize touch interactions
      this.optimizeTouchInteractions();
      
      // Reduce memory usage
      this.optimizeMemoryUsage();
      
      // Optimize network requests
      this.optimizeNetworkRequests();
    }
  }

  /**
   * Optimize animations for mobile performance
   */
  optimizeAnimationsForMobile() {
    // Reduce motion if user prefers it
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.documentElement.style.setProperty('--animation-duration', '0.1s');
      document.documentElement.style.setProperty('--transition-duration', '0.1s');
    }
    
    // Use transform instead of changing layout properties
    const style = document.createElement('style');
    style.textContent = `
      @media (max-width: 768px) {
        * {
          will-change: auto !important;
        }
        .slide-panel {
          transform: translateZ(0);
        }
        .nav-tab {
          transform: translateZ(0);
        }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Optimize touch interactions
   */
  optimizeTouchInteractions() {
    // Add touch-action optimization
    const style = document.createElement('style');
    style.textContent = `
      .record-button, .nav-tab, .button {
        touch-action: manipulation;
      }
      .transcription-text, .translation-text {
        touch-action: pan-y;
      }
    `;
    document.head.appendChild(style);
    
    // Optimize scroll performance
    document.addEventListener('touchstart', () => {}, { passive: true });
    document.addEventListener('touchmove', () => {}, { passive: true });
  }

  /**
   * Optimize memory usage on mobile
   */
  optimizeMemoryUsage() {
    // Clean up unused audio objects
    setInterval(() => {
      if (window.gc && typeof window.gc === 'function') {
        window.gc();
      }
    }, 30000);
    
    // Limit concurrent audio processing
    if (window.AudioContext) {
      const originalAudioContext = window.AudioContext;
      let activeContexts = 0;
      const maxContexts = 2;
      
      window.AudioContext = function(...args) {
        if (activeContexts >= maxContexts) {
          throw new Error('Maximum audio contexts reached');
        }
        activeContexts++;
        const context = new originalAudioContext(...args);
        
        const originalClose = context.close.bind(context);
        context.close = function() {
          activeContexts--;
          return originalClose();
        };
        
        return context;
      };
    }
  }

  /**
   * Optimize network requests for mobile
   */
  optimizeNetworkRequests() {
    // Implement request debouncing
    this.setupRequestDebouncing();
    
    // Optimize fetch requests
    this.optimizeFetchRequests();
  }

  setupRequestDebouncing() {
    const debounceMap = new Map();
    
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
      // Debounce similar requests
      const key = `${url}-${JSON.stringify(options)}`;
      
      if (debounceMap.has(key)) {
        clearTimeout(debounceMap.get(key).timeout);
      }
      
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          debounceMap.delete(key);
          originalFetch(url, options).then(resolve).catch(reject);
        }, 50);
        
        debounceMap.set(key, { timeout, resolve, reject });
      });
    };
  }

  optimizeFetchRequests() {
    // Add compression headers for mobile
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
      if (!options.headers) {
        options.headers = {};
      }
      
      // Add compression headers
      options.headers['Accept-Encoding'] = 'gzip, deflate, br';
      
      // Add mobile-specific headers
      if (/android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent)) {
        options.headers['X-Mobile-Request'] = 'true';
      }
      
      return originalFetch(url, options);
    };
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    if ('performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0];
      const paint = performance.getEntriesByType('paint');
      
      return {
        loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
        domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
        loadedModules: this.loadedModules.size
      };
    }
    return null;
  }
}

// Initialize performance optimizer
const performanceOptimizer = new PerformanceOptimizer();
window.performanceOptimizer = performanceOptimizer;

console.log('[Performance] Performance optimizer loaded');
