/**
 * Payment Management for VocalLocal
 * Handles Stripe checkout and subscription management
 */

class PaymentManager {
    constructor() {
        // Initialize Stripe (will be set when publishable key is available)
        this.stripe = null;
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        // Initialize Stripe when publishable key is available
        if (window.stripePublishableKey) {
            this.stripe = Stripe(window.stripePublishableKey);
            console.log('Stripe initialized successfully');
        } else {
            console.warn('Stripe publishable key not found');
        }

        // Set up event listeners
        this.setupEventListeners();

        // Check for payment status in URL
        this.checkPaymentStatus();

        // Handle page visibility changes (detect return from Stripe)
        this.setupVisibilityHandlers();
    }
    
    setupEventListeners() {
        // Handle upgrade button clicks
        document.addEventListener('click', (e) => {
            // Check if the clicked element or its parent has data-plan attribute
            const planButton = e.target.closest('[data-plan]');
            if (planButton) {
                e.preventDefault();
                e.stopPropagation();
                const planType = planButton.getAttribute('data-plan');
                console.log(`Payment button clicked: ${planType}`);
                this.handleUpgradeClick(planType);
                return;
            }

            // Handle customer portal button
            if (e.target.matches('.customer-portal-btn')) {
                e.preventDefault();
                this.openCustomerPortal();
            }
        });
    }

    setupVisibilityHandlers() {
        // Handle page visibility changes to detect return from external sites
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.handlePageVisible();
            }
        });

        // Handle beforeunload to track processing state
        window.addEventListener('beforeunload', () => {
            if (this.isProcessing) {
                sessionStorage.setItem('paymentProcessing', 'true');
            }
        });
    }

    handlePageVisible() {
        // Clear processing state when user returns to page
        const wasProcessing = sessionStorage.getItem('paymentProcessing');
        if (wasProcessing || this.isProcessing) {
            console.log('User returned to page, clearing payment processing state');
            this.isProcessing = false;
            this.hideLoading();
            sessionStorage.removeItem('paymentProcessing');
        }
    }

    async handleUpgradeClick(planType) {
        console.log(`🚀 handleUpgradeClick called with plan: ${planType}`);

        if (this.isProcessing) {
            console.log('Payment already in progress');
            return;
        }

        if (!this.stripe) {
            console.error('❌ Stripe not initialized');
            this.showError('Payment system not initialized. Please refresh the page.');
            return;
        }

        console.log('✅ Starting payment process for plan:', planType);

        try {
            this.isProcessing = true;
            sessionStorage.setItem('paymentProcessing', 'true');
            this.showLoading(`Preparing ${planType} plan checkout...`);

            // Create checkout session
            const response = await fetch('/payment/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plan_type: planType
                })
            });

            // Check if user needs to login first
            if (response.status === 401 || response.status === 403) {
                console.log('User not authenticated, redirecting to login');
                window.location.href = `/auth/login?next=${encodeURIComponent('/pricing?plan=' + planType)}`;
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                console.error('Payment API error:', response.status, data);
                throw new Error(data.error || `Failed to create checkout session (${response.status})`);
            }
            
            if (!data.success) {
                throw new Error(data.error || 'Checkout session creation failed');
            }
            
            console.log('Checkout session created:', data.session_id);
            
            // Redirect to Stripe Checkout
            const result = await this.stripe.redirectToCheckout({
                sessionId: data.session_id
            });
            
            if (result.error) {
                throw new Error(result.error.message);
            }
            
        } catch (error) {
            console.error('Payment error:', error);
            this.showError(`Payment failed: ${error.message}`);
        } finally {
            this.isProcessing = false;
            this.hideLoading();
            // Clear any processing state from session storage
            sessionStorage.removeItem('paymentProcessing');
        }
    }
    
    async openCustomerPortal() {
        try {
            this.showLoading('Opening subscription management...');
            
            const response = await fetch('/payment/customer-portal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to open customer portal');
            }
            
            if (data.success && data.portal_url) {
                // Redirect to customer portal
                window.location.href = data.portal_url;
            } else {
                throw new Error('Invalid portal response');
            }
            
        } catch (error) {
            console.error('Customer portal error:', error);
            this.showError(`Failed to open subscription management: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    checkPaymentStatus() {
        // Check URL parameters for payment status
        const urlParams = new URLSearchParams(window.location.search);
        const paymentStatus = urlParams.get('payment');
        const planType = urlParams.get('plan');
        
        if (paymentStatus === 'success' && planType) {
            this.showSuccess(`Successfully upgraded to ${planType} plan! Your new features are now available.`);
            
            // Clean up URL
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
            
            // Refresh page data
            setTimeout(() => {
                window.location.reload();
            }, 3000);
            
        } else if (paymentStatus === 'cancelled') {
            this.showInfo('Payment was cancelled. You can try again anytime.');
            
            // Clean up URL
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }
    
    showLoading(message) {
        // Remove existing loading indicators
        this.hideLoading();
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.id = 'payment-loading';
        overlay.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            ">
                <div style="
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    text-align: center;
                    max-width: 300px;
                ">
                    <div style="
                        width: 40px;
                        height: 40px;
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #667eea;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 1rem;
                    "></div>
                    <p style="margin: 0; font-weight: 600;">${message}</p>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        
        document.body.appendChild(overlay);
    }
    
    hideLoading() {
        const loading = document.getElementById('payment-loading');
        if (loading) {
            loading.remove();
        }
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelectorAll('.payment-notification');
        existing.forEach(el => el.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'payment-notification';
        
        const colors = {
            error: { bg: '#fee', border: '#fcc', text: '#c33' },
            success: { bg: '#efe', border: '#cfc', text: '#3c3' },
            info: { bg: '#eef', border: '#ccf', text: '#33c' }
        };
        
        const color = colors[type] || colors.info;
        
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${color.bg};
                border: 2px solid ${color.border};
                color: ${color.text};
                padding: 1rem;
                border-radius: 8px;
                max-width: 400px;
                z-index: 10001;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <p style="margin: 0; font-weight: 600;">${message}</p>
                    <button onclick="this.closest('.payment-notification').remove()" style="
                        background: none;
                        border: none;
                        font-size: 1.2rem;
                        cursor: pointer;
                        color: ${color.text};
                        margin-left: 1rem;
                    ">&times;</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Utility method to check subscription status
    async getSubscriptionStatus() {
        try {
            const response = await fetch('/payment/subscription-status');
            const data = await response.json();
            
            if (response.ok && data.success) {
                return data;
            } else {
                throw new Error(data.error || 'Failed to get subscription status');
            }
        } catch (error) {
            console.error('Error getting subscription status:', error);
            return null;
        }
    }
}

// Initialize payment manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.paymentManager = new PaymentManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PaymentManager;
}
