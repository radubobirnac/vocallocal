/**
 * Pay-As-You-Go Dashboard JavaScript
 * Handles overage display, pricing, and payment processing
 */

class PayAsYouGoDashboard {
    constructor() {
        this.overageStatus = null;
        this.pricing = null;
        this.init();
    }

    async init() {
        try {
            await this.loadOverageStatus();
            await this.loadPricing();
            this.setupEventListeners();
            this.updateUI();
        } catch (error) {
            console.error('Error initializing PAYG dashboard:', error);
        }
    }

    async loadOverageStatus() {
        try {
            const response = await fetch('/payg/status');
            const data = await response.json();
            
            if (data.success) {
                this.overageStatus = data.status;
                console.log('PAYG Status:', this.overageStatus);
            } else {
                console.error('Error loading overage status:', data.error);
            }
        } catch (error) {
            console.error('Error fetching overage status:', error);
        }
    }

    async loadPricing() {
        try {
            const response = await fetch('/payg/pricing');
            const data = await response.json();
            
            if (data.success) {
                this.pricing = data.pricing;
                console.log('PAYG Pricing:', this.pricing);
            } else {
                console.error('Error loading pricing:', data.error);
            }
        } catch (error) {
            console.error('Error fetching pricing:', error);
        }
    }

    setupEventListeners() {
        // Event listeners for PAYG dashboard functionality
        // Note: Pay outstanding charges, refresh status, and pricing buttons have been removed
        // This method is kept for future event listener additions if needed
    }

    updateUI() {
        if (!this.overageStatus) return;

        // Update eligibility status
        this.updateEligibilityStatus();

        // Update overage display
        this.updateOverageDisplay();

        // Update outstanding charges
        this.updateOutstandingCharges();

        // Update pricing display
        this.updatePricingDisplay();
    }

    updateEligibilityStatus() {
        const statusEl = document.getElementById('payg-eligibility-status');
        const paygSection = document.getElementById('payg-section');

        if (!statusEl) return;

        // Only show PAYG section if user has explicitly enabled it
        if (this.overageStatus.eligible && this.overageStatus.enabled) {
            if (paygSection) paygSection.style.display = 'block';

            statusEl.innerHTML = `
                <div class="payg-eligible">
                    <i class="fas fa-check-circle"></i>
                    <span>Pay-as-you-go enabled for ${this.overageStatus.plan_type} plan</span>
                </div>
            `;
        } else {
            // Hide PAYG section if not enabled
            if (paygSection) paygSection.style.display = 'none';
        }
    }

    updateOverageDisplay() {
        const overageEl = document.getElementById('payg-overage-details');
        if (!overageEl || !this.overageStatus.eligible) return;

        if (this.overageStatus.has_overages) {
            let overageHtml = '<div class="overage-breakdown">';
            
            for (const [service, details] of Object.entries(this.overageStatus.overages)) {
                overageHtml += `
                    <div class="overage-item">
                        <div class="overage-service">
                            <i class="fas fa-${this.getServiceIcon(service)}"></i>
                            <span>${this.getServiceName(service)}</span>
                        </div>
                        <div class="overage-details">
                            <span class="overage-amount">${details.amount.toFixed(1)} ${details.unit}</span>
                            <span class="overage-rate">@ $${details.rate.toFixed(3)}/${details.unit.slice(0, -1)}</span>
                            <span class="overage-cost">$${details.charge.toFixed(2)}</span>
                        </div>
                    </div>
                `;
            }
            
            overageHtml += '</div>';
            overageEl.innerHTML = overageHtml;
        } else {
            overageEl.innerHTML = `
                <div class="no-overages">
                    <i class="fas fa-check-circle"></i>
                    <span>No usage overages - you're within your plan limits!</span>
                </div>
            `;
        }
    }

    updateOutstandingCharges() {
        const chargesEl = document.getElementById('payg-outstanding-charges');

        if (!chargesEl || !this.overageStatus.eligible) return;

        const outstanding = this.overageStatus.combined_outstanding || 0;

        if (outstanding > 0) {
            chargesEl.innerHTML = `
                <div class="outstanding-charges">
                    <div class="charges-header">
                        <h3><i class="fas fa-credit-card"></i> Outstanding Charges</h3>
                        <span class="charges-amount">$${outstanding.toFixed(2)}</span>
                    </div>
                    <p class="charges-description">
                        Outstanding charges will be automatically billed at the end of your billing cycle.
                    </p>
                </div>
            `;
        } else {
            chargesEl.innerHTML = `
                <div class="no-charges">
                    <i class="fas fa-check-circle" style="color: #22c55e; font-size: 2rem; margin-bottom: 1rem;"></i>
                    <h3>No Outstanding Charges</h3>
                    <p>You're all caught up! No overage charges at this time.</p>
                </div>
            `;
        }
    }

    updatePricingDisplay() {
        const pricingEl = document.getElementById('payg-pricing-summary');
        if (!pricingEl || !this.pricing) return;

        let pricingHtml = '<div class="pricing-summary">';
        pricingHtml += '<h4><i class="fas fa-tag"></i> Pay-as-you-go Rates</h4>';
        pricingHtml += '<div class="pricing-grid">';

        for (const [service, details] of Object.entries(this.pricing)) {
            pricingHtml += `
                <div class="pricing-item">
                    <div class="pricing-service">
                        <i class="fas fa-${this.getServiceIcon(service)}"></i>
                        <span>${this.getServiceName(service)}</span>
                    </div>
                    <div class="pricing-rate">$${details.rate.toFixed(3)} ${details.unit}</div>
                </div>
            `;
        }

        pricingHtml += '</div></div>';
        pricingEl.innerHTML = pricingHtml;
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
    // Only initialize if we're on the dashboard page and user has a subscription
    if (window.location.pathname.includes('dashboard')) {
        window.paygDashboard = new PayAsYouGoDashboard();
    }
});

// Handle payment success/cancel from URL parameters
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const paygPayment = urlParams.get('payg_payment');
    
    if (paygPayment === 'success') {
        // Show success message and refresh status
        alert('Payment successful! Your outstanding charges have been cleared.');
        if (window.paygDashboard) {
            window.paygDashboard.refreshStatus();
        }
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (paygPayment === 'cancelled') {
        // Show cancelled message
        alert('Payment was cancelled. Your outstanding charges remain unpaid.');
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});
