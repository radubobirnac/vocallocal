/**
 * Cache Manager for VocalLocal
 * Handles service worker registration and cache management
 */

class CacheManager {
  constructor() {
    this.swRegistration = null;
    this.updateAvailable = false;
    this.init();
  }

  async init() {
    if ('serviceWorker' in navigator) {
      try {
        await this.registerServiceWorker();
        this.setupUpdateListener();
        this.setupCacheControls();
      } catch (error) {
        console.error('Cache Manager: Failed to initialize:', error);
      }
    } else {
      console.log('Cache Manager: Service workers not supported');
    }
  }

  async registerServiceWorker() {
    try {
      this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
      console.log('Cache Manager: Service worker registered successfully');
      
      // Check for updates immediately
      this.swRegistration.addEventListener('updatefound', () => {
        console.log('Cache Manager: Update found');
        this.handleUpdate();
      });
      
      // Check for updates periodically
      setInterval(() => {
        this.swRegistration.update();
      }, 60000); // Check every minute
      
    } catch (error) {
      console.error('Cache Manager: Service worker registration failed:', error);
    }
  }

  handleUpdate() {
    const newWorker = this.swRegistration.installing;
    if (!newWorker) return;

    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        this.updateAvailable = true;
        this.showUpdateNotification();
      }
    });
  }

  showUpdateNotification() {
    // Create update notification
    const notification = document.createElement('div');
    notification.id = 'cache-update-notification';
    notification.className = 'cache-update-notification';
    notification.innerHTML = `
      <div class="cache-update-content">
        <span class="cache-update-message">
          <i class="fas fa-sync-alt"></i>
          A new version is available!
        </span>
        <button class="cache-update-button" onclick="cacheManager.applyUpdate()">
          Update Now
        </button>
        <button class="cache-update-dismiss" onclick="cacheManager.dismissUpdate()">
          Later
        </button>
      </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .cache-update-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: hsl(var(--primary));
        color: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
      }
      
      .cache-update-content {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .cache-update-message {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
      }
      
      .cache-update-button, .cache-update-dismiss {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.2s;
      }
      
      .cache-update-button {
        background: white;
        color: hsl(var(--primary));
      }
      
      .cache-update-button:hover {
        background: #f0f0f0;
      }
      
      .cache-update-dismiss {
        background: transparent;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
      }
      
      .cache-update-dismiss:hover {
        background: rgba(255, 255, 255, 0.1);
      }
      
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(notification);
  }

  async applyUpdate() {
    if (this.swRegistration && this.swRegistration.waiting) {
      // Tell the waiting service worker to skip waiting
      this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
      
      // Reload the page to get the new version
      window.location.reload();
    }
  }

  dismissUpdate() {
    const notification = document.getElementById('cache-update-notification');
    if (notification) {
      notification.remove();
    }
  }

  setupUpdateListener() {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('Cache Manager: New service worker took control');
      window.location.reload();
    });
  }

  setupCacheControls() {
    // Add cache control methods to window for debugging
    window.cacheControls = {
      clearCache: () => this.clearCache(),
      forceUpdate: () => this.forceUpdate(),
      checkCacheStatus: () => this.checkCacheStatus()
    };
  }

  async clearCache() {
    try {
      if (this.swRegistration) {
        const messageChannel = new MessageChannel();
        
        return new Promise((resolve, reject) => {
          messageChannel.port1.onmessage = (event) => {
            if (event.data.success) {
              console.log('Cache Manager: Cache cleared successfully');
              resolve();
            } else {
              console.error('Cache Manager: Failed to clear cache:', event.data.error);
              reject(new Error(event.data.error));
            }
          };
          
          this.swRegistration.active.postMessage(
            { type: 'CLEAR_CACHE' },
            [messageChannel.port2]
          );
        });
      }
    } catch (error) {
      console.error('Cache Manager: Error clearing cache:', error);
      throw error;
    }
  }

  async forceUpdate() {
    try {
      if (this.swRegistration) {
        await this.swRegistration.update();
        console.log('Cache Manager: Force update completed');
      }
    } catch (error) {
      console.error('Cache Manager: Error forcing update:', error);
    }
  }

  async checkCacheStatus() {
    try {
      const cacheNames = await caches.keys();
      console.log('Cache Manager: Available caches:', cacheNames);
      
      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        console.log(`Cache Manager: ${cacheName} contains ${keys.length} items`);
      }
    } catch (error) {
      console.error('Cache Manager: Error checking cache status:', error);
    }
  }
}

// Initialize cache manager
const cacheManager = new CacheManager();

// Make it globally available
window.cacheManager = cacheManager;
