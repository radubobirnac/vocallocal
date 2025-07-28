/**
 * Edge Browser Compatibility Fixes for Pricing Page
 * Provides polyfills and fallbacks for modern JavaScript features
 */

(function() {
    'use strict';
    
    // Detect Edge browser
    function isEdge() {
        return /Edge\/\d+/.test(navigator.userAgent) || /Edg\/\d+/.test(navigator.userAgent);
    }
    
    // Add Edge class to body for CSS targeting
    if (isEdge()) {
        document.documentElement.classList.add('edge-browser');
    }
    
    // Polyfill for Array.includes (for older Edge versions)
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            'use strict';
            if (this == null) {
                throw new TypeError('Array.prototype.includes called on null or undefined');
            }
            
            var O = Object(this);
            var len = parseInt(O.length) || 0;
            if (len === 0) {
                return false;
            }
            var n = parseInt(fromIndex) || 0;
            var k;
            if (n >= 0) {
                k = n;
            } else {
                k = len + n;
                if (k < 0) {k = 0;}
            }
            
            function sameValueZero(x, y) {
                return x === y || (typeof x === 'number' && typeof y === 'number' && isNaN(x) && isNaN(y));
            }
            
            for (;k < len; k++) {
                if (sameValueZero(O[k], searchElement)) {
                    return true;
                }
            }
            return false;
        };
    }
    
    // Polyfill for String.includes (for older Edge versions)
    if (!String.prototype.includes) {
        String.prototype.includes = function(search, start) {
            'use strict';
            if (typeof start !== 'number') {
                start = 0;
            }
            
            if (start + search.length > this.length) {
                return false;
            } else {
                return this.indexOf(search, start) !== -1;
            }
        };
    }
    
    // Enhanced authentication detection for Edge
    function checkAuthenticationEdge() {
        // Multiple methods to detect authentication state
        var methods = [
            function() { return document.body.classList.contains('authenticated'); },
            function() { return document.querySelector('[data-user-authenticated]') !== null; },
            function() { return typeof window.currentUser !== 'undefined'; },
            function() { return document.body.hasAttribute('data-user-authenticated'); }
        ];
        
        for (var i = 0; i < methods.length; i++) {
            try {
                if (methods[i]()) {
                    return true;
                }
            } catch (e) {
                console.warn('Authentication check method failed:', e);
            }
        }
        return false;
    }
    
    // Enhanced event listener management for Edge
    function addEventListenerEdge(element, event, handler, options) {
        if (element.addEventListener) {
            element.addEventListener(event, handler, options || false);
        } else if (element.attachEvent) {
            // Fallback for very old Edge/IE
            element.attachEvent('on' + event, handler);
        }
    }
    
    // Enhanced DOM ready detection for Edge
    function domReadyEdge(callback) {
        if (document.readyState === 'loading') {
            addEventListenerEdge(document, 'DOMContentLoaded', callback);
        } else {
            callback();
        }
    }
    
    // Enhanced fetch polyfill for Edge (if needed)
    if (!window.fetch) {
        window.fetch = function(url, options) {
            return new Promise(function(resolve, reject) {
                var xhr = new XMLHttpRequest();
                options = options || {};
                
                xhr.open(options.method || 'GET', url);
                
                // Set headers
                if (options.headers) {
                    for (var key in options.headers) {
                        xhr.setRequestHeader(key, options.headers[key]);
                    }
                }
                
                xhr.onload = function() {
                    var response = {
                        ok: xhr.status >= 200 && xhr.status < 300,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        json: function() {
                            return Promise.resolve(JSON.parse(xhr.responseText));
                        },
                        text: function() {
                            return Promise.resolve(xhr.responseText);
                        }
                    };
                    resolve(response);
                };
                
                xhr.onerror = function() {
                    reject(new Error('Network error'));
                };
                
                xhr.send(options.body || null);
            });
        };
    }
    
    // Enhanced CSS Grid detection and fallback
    function setupGridFallback() {
        var testElement = document.createElement('div');
        testElement.style.display = 'grid';
        
        if (testElement.style.display !== 'grid') {
            // Grid not supported, add fallback class
            document.documentElement.classList.add('no-grid-support');
            
            // Apply flexbox fallback to pricing grid
            var pricingGrid = document.querySelector('.pricing-grid');
            if (pricingGrid) {
                pricingGrid.style.display = 'flex';
                pricingGrid.style.flexWrap = 'wrap';
                pricingGrid.style.justifyContent = 'center';
                pricingGrid.style.gap = '2rem';
                
                var cards = pricingGrid.querySelectorAll('.pricing-card');
                for (var i = 0; i < cards.length; i++) {
                    cards[i].style.flex = '1 1 300px';
                    cards[i].style.maxWidth = '350px';
                    cards[i].style.margin = '0 1rem 2rem 1rem';
                }
            }
        }
    }
    
    // Enhanced plan highlighting for Edge
    function highlightPlanEdge(planType) {
        var cards = document.querySelectorAll('.pricing-card');
        
        for (var i = 0; i < cards.length; i++) {
            var card = cards[i];
            var cardPlanType = null;
            
            // Determine plan type from card content
            if (card.textContent.indexOf('Basic Plan') !== -1) {
                cardPlanType = 'basic';
            } else if (card.textContent.indexOf('Professional Plan') !== -1) {
                cardPlanType = 'professional';
            } else if (card.textContent.indexOf('Pay-As-You-Go') !== -1) {
                cardPlanType = 'payg';
            }
            
            if (cardPlanType === planType) {
                card.classList.add('plan-highlighted');
                
                // Apply styles directly for Edge compatibility
                card.style.transform = 'scale(1.05)';
                card.style.boxShadow = '0 10px 30px rgba(102, 126, 234, 0.3)';
                card.style.border = '3px solid #667eea';
                card.style.transition = 'all 0.3s ease';
                
                // Add animation class
                card.style.animation = 'planGlow 2s ease-in-out';
            }
        }
    }
    
    // Enhanced notification system for Edge
    function showNotificationEdge(message, type) {
        type = type || 'success';
        
        var notification = document.createElement('div');
        notification.className = 'notification notification-' + type;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.backgroundColor = type === 'success' ? '#48bb78' : '#f56565';
        notification.style.color = '#ffffff';
        notification.style.padding = '1rem 1.5rem';
        notification.style.borderRadius = '0.5rem';
        notification.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        notification.style.zIndex = '1000';
        notification.style.maxWidth = '300px';
        notification.style.wordWrap = 'break-word';
        notification.textContent = message;
        
        // Add animation
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        notification.style.transition = 'all 0.3s ease-out';
        
        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(function() {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 10);
        
        // Auto-remove after 5 seconds
        setTimeout(function() {
            if (notification.parentNode) {
                notification.style.transform = 'translateX(100%)';
                notification.style.opacity = '0';
                setTimeout(function() {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    // Enhanced payment status handling for Edge
    function handlePaymentStatusEdge() {
        var urlParams = new URLSearchParams(window.location.search);
        var paymentStatus = urlParams.get('payment');
        var planType = urlParams.get('plan');
        
        if (paymentStatus === 'success' && planType) {
            showNotificationEdge('Payment successful! Welcome to your new plan.', 'success');
            highlightPlanEdge(planType);
            
            // Clean up URL
            if (window.history && window.history.replaceState) {
                var cleanUrl = window.location.pathname;
                window.history.replaceState({}, document.title, cleanUrl);
            }
        } else if (paymentStatus === 'cancelled') {
            showNotificationEdge('Payment was cancelled. You can try again anytime.', 'info');
        }
    }
    
    // Initialize Edge compatibility features
    domReadyEdge(function() {
        console.log('Edge compatibility features initialized');
        
        // Setup grid fallback
        setupGridFallback();
        
        // Handle payment status
        handlePaymentStatusEdge();
        
        // Enhance existing pricing functionality
        if (window.pricingPAYG && typeof window.pricingPAYG.checkAuthentication === 'function') {
            // Override authentication check with Edge-compatible version
            window.pricingPAYG.checkAuthentication = checkAuthenticationEdge;
        }
        
        // Add Edge-specific event listeners
        var enablePaygBtn = document.getElementById('enable-payg-static-btn');
        if (enablePaygBtn) {
            addEventListenerEdge(enablePaygBtn, 'click', function(e) {
                console.log('PAYG button clicked in Edge');
                // Let the original handler run
            });
        }
        
        // Ensure proper focus management for accessibility
        var buttons = document.querySelectorAll('.button');
        for (var i = 0; i < buttons.length; i++) {
            addEventListenerEdge(buttons[i], 'focus', function(e) {
                e.target.style.outline = '2px solid #667eea';
                e.target.style.outlineOffset = '2px';
            });
            
            addEventListenerEdge(buttons[i], 'blur', function(e) {
                e.target.style.outline = '';
                e.target.style.outlineOffset = '';
            });
        }
    });
    
    // Export functions for global use
    window.EdgeCompatibility = {
        isEdge: isEdge,
        checkAuthentication: checkAuthenticationEdge,
        showNotification: showNotificationEdge,
        highlightPlan: highlightPlanEdge,
        addEventListener: addEventListenerEdge
    };
    
})();
