/**
 * Usage Enforcement and Upgrade Prompts for VocalLocal
 *
 * This script handles usage limit enforcement on the client side and
 * displays appropriate upgrade prompts when limits are reached.
 */

class UsageEnforcement {
    constructor() {
        this.userRole = 'normal_user'; // Default role
        this.init();
    }

    async init() {
        // Load user role information
        await this.loadUserRole();

        // Only set up usage interceptors for normal users
        if (this.userRole === 'normal_user') {
            this.setupUsageInterceptors();
        } else {
            console.log(`Usage enforcement bypassed for ${this.userRole} role`);
        }

        // Set up upgrade modal (but only show for normal users)
        this.setupUpgradeModal();
    }

    async loadUserRole() {
        try {
            const response = await fetch('/api/user/role-info');
            if (response.ok) {
                const data = await response.json();
                this.userRole = data.role || 'normal_user';
                console.log(`User role loaded for usage enforcement: ${this.userRole}`);
            } else {
                console.warn('Could not load user role, defaulting to normal_user');
                this.userRole = 'normal_user';
            }
        } catch (error) {
            console.warn('Error loading user role for usage enforcement:', error);
            this.userRole = 'normal_user';
        }
    }

    // Check if user should be subject to usage limits
    shouldEnforceUsage() {
        // Skip usage enforcement for admin and super_user roles
        return !(this.userRole === 'admin' || this.userRole === 'super_user');
    }

    setupUsageInterceptors() {
        // Store original functions if they exist
        if (window.transcribeAudio) {
            this.originalTranscribeAudio = window.transcribeAudio;
            window.transcribeAudio = this.interceptTranscribeAudio.bind(this);
        }

        if (window.translateText) {
            this.originalTranslateText = window.translateText;
            window.translateText = this.interceptTranslateText.bind(this);
        }

        // Intercept form submissions for transcription
        this.interceptTranscriptionForms();
    }

    interceptTranscriptionForms() {
        // Intercept file upload forms
        const fileInputs = document.querySelectorAll('input[type="file"][accept*="audio"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.checkTranscriptionUsage(e.target.files[0]);
                }
            });
        });
    }

    async checkTranscriptionUsage(file) {
        // Skip usage check for admins and super users
        if (!this.shouldEnforceUsage()) {
            console.log(`Transcription usage check bypassed for ${this.userRole} role`);
            return true;
        }

        // Estimate audio duration based on file size
        const fileSizeMB = file.size / (1024 * 1024);
        const estimatedMinutes = Math.max(0.1, fileSizeMB * 0.8);

        try {
            const response = await fetch('/api/check-usage', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: 'transcription',
                    amount: estimatedMinutes
                })
            });

            const result = await response.json();

            if (!result.allowed) {
                this.showUsageLimitModal(result);
                return false;
            }

            return true;
        } catch (error) {
            console.error('Error checking usage:', error);
            // Allow operation to continue if check fails
            return true;
        }
    }

    async interceptTranscribeAudio(...args) {
        // Check usage before proceeding
        const allowed = await this.checkTranscriptionUsage({ size: 1024 * 1024 }); // Default 1MB estimate

        if (allowed && this.originalTranscribeAudio) {
            return this.originalTranscribeAudio.apply(this, args);
        }
    }

    async interceptTranslateText(text, ...args) {
        // Skip usage check for admins and super users
        if (!this.shouldEnforceUsage()) {
            console.log(`Translation usage check bypassed for ${this.userRole} role`);
            if (this.originalTranslateText) {
                return this.originalTranslateText.apply(this, [text, ...args]);
            }
            return;
        }

        const wordCount = text.split(' ').length;

        try {
            const response = await fetch('/api/check-usage', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: 'translation',
                    amount: wordCount
                })
            });

            const result = await response.json();

            if (!result.allowed) {
                this.showUsageLimitModal(result);
                return;
            }

            if (this.originalTranslateText) {
                return this.originalTranslateText.apply(this, [text, ...args]);
            }
        } catch (error) {
            console.error('Error checking translation usage:', error);
            // Allow operation to continue if check fails
            if (this.originalTranslateText) {
                return this.originalTranslateText.apply(this, [text, ...args]);
            }
        }
    }

    showUsageLimitModal(usageInfo) {
        // Don't show usage limit modals for admin or super users
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Usage limit modal bypassed for ${this.userRole} role`);
            return;
        }

        const modal = this.createUsageLimitModal(usageInfo);
        document.body.appendChild(modal);
        modal.style.display = 'flex';

        // Auto-remove modal after 30 seconds
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 30000);
    }

    createUsageLimitModal(usageInfo) {
        const modal = document.createElement('div');
        modal.className = 'usage-limit-modal';
        modal.style.cssText = `
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
        `;

        const serviceName = {
            'transcription': 'Transcription',
            'translation': 'Translation',
            'tts': 'Text-to-Speech',
            'ai': 'AI Credits'
        }[usageInfo.service] || usageInfo.service;

        const upgradeOptions = this.getUpgradeOptions(usageInfo.plan_type);

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 15px;
                padding: 2rem;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                text-align: center;
            ">
                <div style="color: #e53e3e; font-size: 3rem; margin-bottom: 1rem;">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>

                <h2 style="color: #2d3748; margin-bottom: 1rem; font-size: 1.5rem;">
                    ${serviceName} Limit Reached
                </h2>

                <p style="color: #718096; margin-bottom: 1.5rem; line-height: 1.6;">
                    ${usageInfo.message}
                </p>

                <div style="
                    background: #f7fafc;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1.5rem;
                    text-align: left;
                ">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #4a5568;">Used:</span>
                        <span style="font-weight: 600;">${usageInfo.used}${this.getUnitSuffix(usageInfo.service)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #4a5568;">Limit:</span>
                        <span style="font-weight: 600;">${usageInfo.limit}${this.getUnitSuffix(usageInfo.service)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #4a5568;">Plan:</span>
                        <span style="font-weight: 600; text-transform: capitalize;">${usageInfo.plan_type}</span>
                    </div>
                </div>

                ${upgradeOptions.length > 0 ? `
                    <div style="margin-bottom: 1.5rem;">
                        <h3 style="color: #4a5568; margin-bottom: 1rem;">Upgrade Options:</h3>
                        <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                            ${upgradeOptions.map(option => `
                                <button onclick="window.location.href='/dashboard'" style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    border: none;
                                    padding: 0.75rem 1.5rem;
                                    border-radius: 8px;
                                    font-weight: 600;
                                    cursor: pointer;
                                    transition: transform 0.2s;
                                " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                                    ${option.name} - $${option.price}/month
                                </button>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button onclick="window.location.href='/dashboard'" style="
                        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        View Dashboard
                    </button>

                    <button onclick="this.closest('.usage-limit-modal').remove()" style="
                        background: #e2e8f0;
                        color: #4a5568;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Close
                    </button>
                </div>
            </div>
        `;

        return modal;
    }

    getUpgradeOptions(currentPlan) {
        const plans = {
            'free': [
                { name: 'Basic', price: '4.99' },
                { name: 'Professional', price: '12.99' }
            ],
            'basic': [
                { name: 'Professional', price: '12.99' }
            ],
            'professional': []
        };

        return plans[currentPlan] || [];
    }

    getUnitSuffix(service) {
        const units = {
            'transcription': ' min',
            'translation': ' words',
            'tts': ' min',
            'ai': ' credits'
        };
        return units[service] || '';
    }

    setupUpgradeModal() {
        // Add global function for upgrade prompts
        window.showUpgradePrompt = (planType) => {
            // Don't show upgrade prompts for admin or super users
            if (this.userRole === 'admin' || this.userRole === 'super_user') {
                console.log(`Upgrade prompt bypassed for ${this.userRole} role`);
                return;
            }

            const modal = this.createUpgradeModal(planType);
            document.body.appendChild(modal);
            modal.style.display = 'flex';
        };
    }

    createUpgradeModal(planType) {
        const modal = document.createElement('div');
        modal.className = 'upgrade-modal';
        modal.style.cssText = `
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
        `;

        const planDetails = {
            'basic': {
                name: 'Basic Plan',
                price: '$4.99/month',
                features: [
                    '280 transcription minutes',
                    '50,000 translation words',
                    '60 TTS minutes',
                    '50 AI credits',
                    'Premium model access'
                ]
            },
            'professional': {
                name: 'Professional Plan',
                price: '$12.99/month',
                features: [
                    '800 transcription minutes',
                    '160,000 translation words',
                    '200 TTS minutes',
                    '150 AI credits',
                    'Premium model access',
                    'Priority support'
                ]
            }
        };

        const plan = planDetails[planType];

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 15px;
                padding: 2rem;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                text-align: center;
            ">
                <div style="color: #667eea; font-size: 3rem; margin-bottom: 1rem;">
                    <i class="fas fa-crown"></i>
                </div>

                <h2 style="color: #2d3748; margin-bottom: 0.5rem; font-size: 1.5rem;">
                    ${plan.name}
                </h2>

                <div style="color: #667eea; font-size: 2rem; font-weight: 700; margin-bottom: 1.5rem;">
                    ${plan.price}
                </div>

                <ul style="text-align: left; margin-bottom: 2rem; padding-left: 0; list-style: none;">
                    ${plan.features.map(feature => `
                        <li style="
                            display: flex;
                            align-items: center;
                            gap: 0.5rem;
                            margin-bottom: 0.5rem;
                            color: #4a5568;
                        ">
                            <i class="fas fa-check" style="color: #48bb78;"></i>
                            ${feature}
                        </li>
                    `).join('')}
                </ul>

                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button onclick="alert('Payment processing will be available soon!')" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Upgrade Now
                    </button>

                    <button onclick="this.closest('.upgrade-modal').remove()" style="
                        background: #e2e8f0;
                        color: #4a5568;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Maybe Later
                    </button>
                </div>
            </div>
        `;

        return modal;
    }
}

// Initialize usage enforcement when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.usageEnforcementInstance = new UsageEnforcement();
});

// Handle usage limit errors from server responses
document.addEventListener('DOMContentLoaded', () => {
    // Use a flag to track if we've already set up interception
    if (window._usageEnforcementInterceptionApplied) {
        console.log('[Usage Enforcement] Fetch already intercepted for usage limit detection');
        return;
    }

    try {
        // Store original fetch with proper binding - use the safe validator's original if available
        let originalFetch;
        try {
            if (window.fetchFixValidatorSafe && typeof window.fetchFixValidatorSafe.getOriginalFetch === 'function') {
                originalFetch = window.fetchFixValidatorSafe.getOriginalFetch();
                console.log('[Usage Enforcement] Using fetch-fix-validator-safe original fetch');
            } else if (window.fetchFixValidator && typeof window.fetchFixValidator.getOriginalFetch === 'function') {
                originalFetch = window.fetchFixValidator.getOriginalFetch();
                console.log('[Usage Enforcement] Using fetch-fix-validator original fetch');
            } else {
                // Safely get current fetch without triggering property access issues
                originalFetch = window.fetch.bind(window);
                console.log('[Usage Enforcement] Using current window.fetch');
            }
        } catch (fetchAccessError) {
            console.warn('[Usage Enforcement] Could not safely access fetch, skipping interception:', fetchAccessError);
            return;
        }

        const usageInterceptedFetch = async function(...args) {
            try {
                // Call original fetch with proper context
                const response = await originalFetch(...args);

                if (response.status === 429) { // Too Many Requests (usage limit)
                    try {
                        const errorData = await response.clone().json();
                        if (errorData.errorType === 'UsageLimitExceeded') {
                            // Only show usage limit modal for normal users
                            if (window.usageEnforcementInstance && window.usageEnforcementInstance.shouldEnforceUsage()) {
                                window.usageEnforcementInstance.showUsageLimitModal(errorData.details);
                            } else {
                                console.log('Usage limit error bypassed for privileged user');
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing usage limit response:', e);
                    }
                }

                return response;
            } catch (error) {
                console.error('[Usage Enforcement] Error in fetch override:', error);
                // Fallback to original fetch if override fails
                return originalFetch(...args);
            }
        };

        // Mark as intercepted globally to avoid property access issues
        window._usageEnforcementInterceptionApplied = true;

        // Apply the override safely
        try {
            window.fetch = usageInterceptedFetch;
            console.log('[Usage Enforcement] Successfully intercepted fetch for usage limit detection');
        } catch (assignmentError) {
            console.error('[Usage Enforcement] Could not assign fetch override:', assignmentError);
            window._usageEnforcementInterceptionApplied = false;
        }

    } catch (error) {
        console.error('[Usage Enforcement] Error setting up fetch interception:', error);
        // Don't throw - just log the error and continue
    }
});
