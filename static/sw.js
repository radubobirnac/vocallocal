/**
 * Service Worker for VocalLocal
 * Handles caching strategies and ensures users get the latest version of assets
 */

const CACHE_NAME = 'vocallocal-v1';
const STATIC_CACHE_NAME = 'vocallocal-static-v1';
const DYNAMIC_CACHE_NAME = 'vocallocal-dynamic-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/static/styles.css',
  '/static/auth.css',
  '/static/home.css',
  '/static/history.css',
  '/static/script.js',
  '/static/auth.js',
  '/static/common.js',
  '/static/home.js',
  '/static/history.js',
  '/static/favicon.ico'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Error caching static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip external requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Handle static assets with version parameter (cache first)
  if (url.pathname.startsWith('/static/') && url.searchParams.has('v')) {
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            console.log('Service Worker: Serving versioned asset from cache:', url.pathname);
            return response;
          }
          
          return fetch(request)
            .then(fetchResponse => {
              if (fetchResponse.ok) {
                const responseClone = fetchResponse.clone();
                caches.open(STATIC_CACHE_NAME)
                  .then(cache => {
                    cache.put(request, responseClone);
                  });
              }
              return fetchResponse;
            });
        })
    );
    return;
  }
  
  // Handle static assets without version (network first, fallback to cache)
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(DYNAMIC_CACHE_NAME)
              .then(cache => {
                cache.put(request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          console.log('Service Worker: Network failed, serving static asset from cache:', url.pathname);
          return caches.match(request);
        })
    );
    return;
  }
  
  // Handle HTML pages (network first)
  if (request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(DYNAMIC_CACHE_NAME)
              .then(cache => {
                cache.put(request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          console.log('Service Worker: Network failed, serving HTML from cache:', url.pathname);
          return caches.match(request);
        })
    );
    return;
  }
  
  // Handle API requests (network only)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request));
    return;
  }
});

// Message event - handle cache updates
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys()
        .then(cacheNames => {
          return Promise.all(
            cacheNames.map(cacheName => {
              console.log('Service Worker: Clearing cache:', cacheName);
              return caches.delete(cacheName);
            })
          );
        })
        .then(() => {
          console.log('Service Worker: All caches cleared');
          event.ports[0].postMessage({ success: true });
        })
        .catch(error => {
          console.error('Service Worker: Error clearing caches:', error);
          event.ports[0].postMessage({ success: false, error: error.message });
        })
    );
  }
});

// Handle updates
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    // Force update check
    self.registration.update();
  }
});
