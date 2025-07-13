/**
 * Pay-As-You-Go Pricing Page JavaScript
 * Handles PAYG controls, status display, and integration on pricing page
 */

class PricingPagePAYG {
    constructor() {
        this.paygStatus = null;
        this.serviceStatus = null;
        this.isAuthenticated = false;
        this.init();
    }

    async init() {
        try {
            // Check if user is authenticated
            this.isAuthenticated = this.checkAuthentication();

            if (this.isAuthenticated) {
                await this.loadPAYGStatus();
                await this.loadServiceStatus();
                await this.loadCurrentUsage();
            }

            this.setupEventListeners();
            this.updateUI();
        } catch (error) {
            console.error('Error initializing pricing PAYG:', error);
        }
    }

    checkAuthentication() {
        // Check if user is logged in (you can adjust this based on your auth system)
        return document.body.classList.contains('authenticated') || 
               document.querySelector('[data-user-authenticated]') !== null ||
               window.currentUser !== undefined;
    }

    async loadPAYGStatus() {
        try {
            const response = await fetch('/payg/service-status');
            const data = await response.json();
            
            if (data.success) {
                this.paygStatus = data.payg_status;
                this.serviceStatus = data.service_status;
                console.log('PAYG Status:', this.paygStatus);
                console.log('Service Status:', this.serviceStatus);
            } else {
                console.error('Error loading PAYG status:', data.error);
            }
        } catch (error) {
            console.error('Error fetching PAYG status:', error);
            // User might not be authenticated
            this.isAuthenticated = false;
        }
    }

    async loadServiceStatus() {
        try {
            const response = await fetch('/payg/pricing');
            const data = await response.json();

            if (data.success) {
                this.pricing = data.pricing;
            }
        } catch (error) {
            console.error('Error fetching pricing:', error);
        }
    }

    async loadCurrentUsage() {
        try {
            const response = await fetch('/payg/status');
            const data = await response.json();

            if (data.success) {
                this.currentUsage = data.status;
                console.log('Current usage loaded:', this.currentUsage);
            }
        } catch (error) {
            console.error('Error fetching current usage:', error);
        }
    }

    setupEventListeners() {
        // Enable PAYG button (dynamic)
        const enableButton = document.getElementById('enable-payg-btn');
        if (enableButton) {
            enableButton.addEventListener('click', () => this.handleEnablePAYG());
        }

        // Enable PAYG button (static)
        const staticEnableButton = document.getElementById('enable-payg-static-btn');
        if (staticEnableButton) {
            staticEnableButton.addEventListener('click', () => this.handleEnablePAYG());
        }

        // Disable PAYG button
        const disableButton = document.getElementById('disable-payg-btn');
        if (disableButton) {
            disableButton.addEventListener('click', () => this.handleDisablePAYG());
        }

        // View dashboard link
        const dashboardLink = document.getElementById('view-payg-dashboard');
        if (dashboardLink) {
            dashboardLink.addEventListener('click', () => {
                window.location.href = '/dashboard#payg-section';
            });
        }

        // Upgrade prompt for free users
        const upgradeButtons = document.querySelectorAll('.payg-upgrade-btn');
        upgradeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Scroll to pricing plans or show upgrade modal
                document.getElementById('pricing-plans')?.scrollIntoView({ behavior: 'smooth' });
            });
        });
    }

    updateUI() {
        this.updatePAYGCard();
    }

    updatePAYGCard() {
        const paygCardContent = document.getElementById('payg-card-content');
        if (!paygCardContent) return;

        if (!this.isAuthenticated) {
            // Show login prompt
            paygCardContent.innerHTML = this.getLoginPromptHTML();
            return;
        }

        if (!this.paygStatus) {
            paygCardContent.innerHTML = this.getLoadingHTML();
            return;
        }

        if (!this.paygStatus.eligible) {
            // Show upgrade prompt for free users
            paygCardContent.innerHTML = this.getUpgradePromptHTML();
            return;
        }

        if (this.paygStatus.enabled) {
            // Show enabled status and controls
            paygCardContent.innerHTML = this.getEnabledStatusHTML();
        } else {
            // Show enable option for eligible users
            paygCardContent.innerHTML = this.getEnableOptionHTML();
        }
    }



    async handleEnablePAYG() {
        try {
            // Handle both dynamic and static buttons
            const enableButton = document.getElementById('enable-payg-btn');
            const staticEnableButton = document.getElementById('enable-payg-static-btn');
            const activeButton = enableButton || staticEnableButton;

            if (activeButton) {
                activeButton.disabled = true;
                activeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enabling...';
            }

            const response = await fetch('/payg/enable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Reload status and update UI
                await this.loadPAYGStatus();
                await this.loadServiceStatus();
                await this.loadCurrentUsage();
                this.updateUI();

                // Show success message
                this.showMessage('Pay-As-You-Go has been enabled successfully! You can now use services beyond your plan limits.', 'success');

                // Update static button if it exists
                if (staticEnableButton) {
                    staticEnableButton.innerHTML = '<i class="fas fa-check"></i> Enabled';
                    staticEnableButton.style.background = '#22c55e';
                    setTimeout(() => {
                        // Redirect to dashboard to see usage tracking
                        window.location.href = '/dashboard#payg-section';
                    }, 2000);
                }
            } else {
                this.showMessage(`Error: ${data.error}`, 'error');
                if (activeButton) {
                    activeButton.disabled = false;
                    activeButton.innerHTML = '<i class="fas fa-toggle-on"></i> Enable Pay-As-You-Go';
                }
            }
        } catch (error) {
            console.error('Error enabling PAYG:', error);
            this.showMessage('Error enabling Pay-As-You-Go. Please try again.', 'error');

            // Reset button state
            const activeButton = document.getElementById('enable-payg-btn') || document.getElementById('enable-payg-static-btn');
            if (activeButton) {
                activeButton.disabled = false;
                activeButton.innerHTML = '<i class="fas fa-toggle-on"></i> Enable Pay-As-You-Go';
            }
        }
    }

    async handleDisablePAYG() {
        try {
            if (!confirm('Are you sure you want to disable Pay-As-You-Go? You must pay any outstanding charges first.')) {
                return;
            }

            const disableButton = document.getElementById('disable-payg-btn');
            if (disableButton) {
                disableButton.disabled = true;
                disableButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Disabling...';
            }

            const response = await fetch('/payg/disable', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Reload status and update UI
                await this.loadPAYGStatus();
                await this.loadServiceStatus();
                this.updateUI();
                
                // Show success message
                this.showMessage('Pay-As-You-Go has been disabled.', 'success');
            } else {
                this.showMessage(`Error: ${data.error}`, 'error');
                if (disableButton) {
                    disableButton.disabled = false;
                    disableButton.innerHTML = '<i class="fas fa-toggle-off"></i> Disable Pay-As-You-Go';
                }
            }
        } catch (error) {
            console.error('Error disabling PAYG:', error);
            this.showMessage('Error disabling Pay-As-You-Go. Please try again.', 'error');
        }
    }

    getLoginPromptHTML() {
        return `
            <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                <li style="padding: 0.5rem 0; display: flex; align-items: center; justify-content: center; text-align: center; color: hsl(var(--muted-foreground));">
                    <i class="fas fa-sign-in-alt" style="margin-right: 0.5rem; color: #f59e0b;"></i>
                    Sign in to access Pay-As-You-Go
                </li>
            </ul>
            <a href="/auth/login" class="button button-primary w-full" style="width: 100%; justify-content: center; background: #667eea;">
                Sign In to Enable
            </a>
        `;
    }

    getUpgradePromptHTML() {
        return `
            <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-lock" style="color: #f59e0b; margin-right: 0.5rem;"></i>
                    Requires Basic or Professional plan
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.10/min transcription overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.001/word translation overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.15/min TTS overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    Only pay for usage beyond limits
                </li>
            </ul>
            <button class="button button-primary w-full payg-upgrade-btn" style="width: 100%; justify-content: center; background: #667eea;">
                <i class="fas fa-arrow-up"></i> Upgrade Required
            </button>
        `;
    }

    getEnableOptionHTML() {
        const outstandingCharges = this.paygStatus.outstanding_charges || 0;

        return `
            <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.10/min transcription overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.001/word translation overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    $0.15/min TTS overage
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    Only pay for usage beyond limits
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    Transparent per-unit billing
                </li>
                ${outstandingCharges > 0 ? `
                <li style="padding: 0.5rem 0; display: flex; align-items: center; color: #f59e0b;">
                    <i class="fas fa-exclamation-triangle" style="color: #f59e0b; margin-right: 0.5rem;"></i>
                    Outstanding: $${outstandingCharges.toFixed(2)}
                </li>
                ` : ''}
            </ul>
            <button id="enable-payg-btn" class="button button-primary w-full" style="width: 100%; justify-content: center; background: #667eea;">
                <i class="fas fa-toggle-on"></i> Enable Pay-As-You-Go
            </button>
        `;
    }

    getEnabledStatusHTML() {
        const outstandingCharges = this.paygStatus.outstanding_charges || 0;

        return `
            <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check-circle" style="color: #22c55e; margin-right: 0.5rem;"></i>
                    Pay-As-You-Go Active
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-chart-line" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    Usage tracking enabled
                </li>
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-credit-card" style="color: #4CAF50; margin-right: 0.5rem;"></i>
                    Automatic overage billing
                </li>
                ${outstandingCharges > 0 ? `
                <li style="padding: 0.5rem 0; display: flex; align-items: center; color: #f59e0b;">
                    <i class="fas fa-exclamation-triangle" style="color: #f59e0b; margin-right: 0.5rem;"></i>
                    Outstanding: $${outstandingCharges.toFixed(2)}
                </li>
                ` : `
                <li style="padding: 0.5rem 0; display: flex; align-items: center;">
                    <i class="fas fa-check" style="color: #22c55e; margin-right: 0.5rem;"></i>
                    No outstanding charges
                </li>
                `}
            </ul>
            <div style="display: flex; gap: 0.5rem; flex-direction: column;">
                <a id="view-payg-dashboard" class="button button-primary w-full" style="width: 100%; justify-content: center; background: #667eea;">
                    <i class="fas fa-chart-line"></i> View Dashboard
                </a>
                <button id="disable-payg-btn" class="button button-outline w-full" style="width: 100%; justify-content: center; border-color: #667eea; color: #667eea;">
                    <i class="fas fa-toggle-off"></i> Disable
                </button>
            </div>
        `;
    }

    getLoadingHTML() {
        return `
            <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                <li style="padding: 1rem 0; display: flex; align-items: center; justify-content: center; color: hsl(var(--muted-foreground));">
                    <i class="fas fa-spinner fa-spin" style="margin-right: 0.5rem;"></i>
                    Loading status...
                </li>
            </ul>
        `;
    }

    showMessage(message, type) {
        // Create or update message display
        let messageEl = document.getElementById('payg-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'payg-message';
            document.getElementById('payg-pricing-card')?.prepend(messageEl);
        }

        messageEl.className = `payg-message ${type}`;
        messageEl.style.cssText = `
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            ${type === 'success' ? 'background: #dcfce7; border: 1px solid #22c55e; color: #166534;' : 'background: #fef2f2; border: 1px solid #ef4444; color: #991b1b;'}
        `;
        messageEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            <span>${message}</span>
        `;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (messageEl) messageEl.remove();
        }, 5000);
    }

    getServiceIcon(service) {
        const icons = {
            'transcription': 'microphone',
            'translation': 'language',
            'tts': 'volume-up',
            'interpretation': 'brain'
        };
        return icons[service] || 'cog';
    }

    getServiceName(service) {
        const names = {
            'transcription': 'Transcription',
            'translation': 'Translation',
            'tts': 'Text-to-Speech',
            'interpretation': 'AI Interpretation'
        };
        return names[service] || service;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the pricing page
    if (window.location.pathname.includes('pricing') || document.getElementById('payg-pricing-card')) {
        window.pricingPAYG = new PricingPagePAYG();
    }
});
