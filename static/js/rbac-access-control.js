/**
 * RBAC-based access control for VocalLocal frontend
 * Manages model restrictions and UI updates based on user roles and subscription plans
 */

class RBACAccessControl {
    constructor() {
        this.userRole = 'normal_user'; // Default to normal user
        this.userPlan = 'free'; // Default to free plan

        // Define model categories based on RBAC system
        this.freeModels = [
            'gemini-2.0-flash-lite'
        ];

        this.premiumModels = [
            // OpenAI Transcription Models
            'gpt-4o-mini-transcribe',
            'gpt-4o-transcribe',

            // OpenAI Translation Models
            'gpt-4.1-mini',

            // OpenAI TTS Models
            'gpt4o-mini',
            'openai',  // OpenAI TTS-1

            // Gemini Premium Models
            'gemini-2.5-flash-preview-04-17',
            'gemini-2.5-flash',
            'gemini-2.5-flash-tts'
        ];

        this.modelInfo = {
            'gemini-2.0-flash-lite': { name: 'Gemini 2.0 Flash Lite', tier: 'free' },
            'gpt-4o-mini-transcribe': { name: 'OpenAI GPT-4o Mini', tier: 'premium' },
            'gpt-4o-transcribe': { name: 'OpenAI GPT-4o', tier: 'premium' },
            'gpt4o-mini': { name: 'GPT-4o Mini TTS', tier: 'premium', service: 'tts' },
            'openai': { name: 'OpenAI TTS-1', tier: 'premium', service: 'tts' },
            'gemini-2.5-flash-preview-04-17': { name: 'Gemini 2.5 Flash Preview', tier: 'premium' },
            'gemini-2.5-flash': { name: 'Gemini 2.5 Flash Preview', tier: 'premium' },
            'gemini-2.5-flash-tts': { name: 'Gemini 2.5 Flash TTS', tier: 'premium', service: 'tts' }
        };

        this.init();
    }

    async init() {
        await this.loadUserInfo();
        this.setupModelSelectors();
        this.setupEventListeners();
    }

    async loadUserInfo() {
        try {
            // Try to get user info from the backend
            const response = await fetch('/api/user/role-info');
            if (response.ok) {
                const data = await response.json();
                this.userRole = data.role || 'normal_user';
                this.userPlan = data.plan_type || 'free';
                this.hasPremiumAccess = data.has_premium_access || false;
                this.hasAdminPrivileges = data.has_admin_privileges || false;
                console.log(`User role loaded: ${this.userRole}, plan: ${this.userPlan}, premium: ${this.hasPremiumAccess}`);

                // Log Super User status specifically
                if (this.userRole === 'super_user') {
                    console.log('Super User detected - unlimited model access enabled');
                }
            } else {
                // Fallback: check if user is authenticated
                const authResponse = await fetch('/api/user/info');
                if (authResponse.ok) {
                    const authData = await authResponse.json();
                    this.userRole = authData.role || 'normal_user';
                    this.userPlan = authData.plan_type || 'free';
                    this.hasPremiumAccess = false;
                    this.hasAdminPrivileges = false;
                } else {
                    // User not authenticated, use defaults
                    this.userRole = 'normal_user';
                    this.userPlan = 'free';
                    this.hasPremiumAccess = false;
                    this.hasAdminPrivileges = false;
                }
            }
        } catch (error) {
            console.warn('Could not load user info, using defaults:', error);
            this.userRole = 'normal_user';
            this.userPlan = 'free';
            this.hasPremiumAccess = false;
            this.hasAdminPrivileges = false;
        }
    }

    isModelAccessible(model) {
        // Admin and Super Users have access to all models - no restrictions
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Model ${model} accessible for ${this.userRole} role`);
            return true;
        }

        // Use premium access flag as backup check
        if (this.hasPremiumAccess) {
            console.log(`Model ${model} accessible via premium access`);
            return true;
        }

        // Normal users are restricted to free models unless they have premium subscription
        if (this.userRole === 'normal_user') {
            // Check if this is a TTS model and user is on free plan
            const modelInfo = this.modelInfo[model];
            if (modelInfo && modelInfo.service === 'tts' && this.userPlan === 'free') {
                console.log(`Model ${model} access denied - TTS not available on free plan`);
                return false;
            }

            // Free models are always accessible
            if (this.freeModels.includes(model)) {
                return true;
            }

            // Premium models require subscription (future enhancement)
            // For now, normal users can't access premium models
            console.log(`Model ${model} restricted for normal user`);
            return false;
        }

        // Default to no access
        console.log(`Model ${model} access denied - unknown role: ${this.userRole}`);
        return false;
    }

    getAccessReason(model) {
        // Check access first
        if (this.isModelAccessible(model)) {
            if (this.userRole === 'admin') {
                return { allowed: true, reason: 'Admin access - unlimited models' };
            } else if (this.userRole === 'super_user') {
                return { allowed: true, reason: 'Super User access - unlimited models' };
            } else if (this.hasPremiumAccess) {
                return { allowed: true, reason: 'Premium access granted' };
            } else if (this.freeModels.includes(model)) {
                return { allowed: true, reason: 'Free model access' };
            } else {
                return { allowed: true, reason: 'Access granted' };
            }
        }

        // Access denied - provide reason
        if (this.userRole === 'normal_user') {
            // Check if this is a TTS model blocked for free users
            const modelInfo = this.modelInfo[model];
            if (modelInfo && modelInfo.service === 'tts' && this.userPlan === 'free') {
                return {
                    allowed: false,
                    reason: 'Text-to-Speech is not available on the Free Plan',
                    upgradeRequired: true,
                    ttsBlocked: true
                };
            }

            if (this.freeModels.includes(model)) {
                return { allowed: true, reason: 'Free model access' };
            } else {
                return {
                    allowed: false,
                    reason: 'Premium model requires subscription or role upgrade',
                    upgradeRequired: true
                };
            }
        }

        return {
            allowed: false,
            reason: 'Access denied',
            upgradeRequired: true
        };
    }

    setupModelSelectors() {
        // Setup all model selectors
        const selectors = [
            'global-transcription-model',
            'translation-model-select',
            'tts-model-select',
            'interpretation-model-select'
        ];

        selectors.forEach(selectorId => {
            this.setupSelector(selectorId);
        });
    }

    setupSelector(selectorId) {
        const selector = document.getElementById(selectorId);
        if (!selector) return;

        console.log(`Setting up selector ${selectorId} for role: ${this.userRole}`);

        // Process each option
        Array.from(selector.options).forEach(option => {
            const model = option.value;
            const accessInfo = this.getAccessReason(model);

            if (!accessInfo.allowed) {
                // Add lock icon for restricted models
                const modelName = this.modelInfo[model]?.name || model;
                const planText = accessInfo.ttsBlocked ? '(Upgrade Required)' : '(Higher Plan)';
                option.textContent = `🔒 ${modelName} ${planText}`;
                option.disabled = false; // Keep enabled so we can detect selection attempts
                option.style.color = '#999';
                option.title = accessInfo.reason;
                option.dataset.restricted = 'true'; // Mark as restricted for event handling
                console.log(`Model ${model} restricted in ${selectorId}: ${accessInfo.reason}`);
            } else {
                // Ensure accessible models are enabled and remove any lock icons
                option.disabled = false;
                option.style.color = '';
                option.dataset.restricted = 'false'; // Mark as accessible

                // Clean up the option text to remove any existing lock icons
                const modelName = this.modelInfo[model]?.name || model;
                option.textContent = modelName;
                option.title = accessInfo.reason;

                // For Super Users and Admins, add a subtle indicator
                if (this.userRole === 'super_user') {
                    option.title = `${modelName} - Super User Access`;
                } else if (this.userRole === 'admin') {
                    option.title = `${modelName} - Admin Access`;
                }

                console.log(`Model ${model} accessible in ${selectorId}`);
            }
        });

        // Ensure selected value is accessible
        if (!this.isModelAccessible(selector.value)) {
            // Select first accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                this.isModelAccessible(option.value)
            );
            if (accessibleOption) {
                selector.value = accessibleOption.value;
                console.log(`Switched to accessible model: ${accessibleOption.value} in ${selectorId}`);
            }
        }
    }

    setupEventListeners() {
        // Listen for model selection changes
        document.addEventListener('change', (event) => {
            if (this.isModelSelector(event.target)) {
                this.handleModelSelection(event.target);
            }
        });
    }

    isModelSelector(element) {
        const modelSelectors = [
            'global-transcription-model',
            'translation-model-select',
            'tts-model-select',
            'interpretation-model-select'
        ];
        return modelSelectors.includes(element.id);
    }

    handleModelSelection(selector) {
        const model = selector.value;
        const selectedOption = selector.options[selector.selectedIndex];

        // Check if the selected option is marked as restricted
        if (selectedOption && selectedOption.dataset.restricted === 'true') {
            // Show upgrade modal immediately
            this.showUpgradeModal(model);

            // Revert to the first accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                !option.dataset.restricted && option.value !== ''
            );

            if (accessibleOption) {
                selector.value = accessibleOption.value;
                console.log(`Reverted selection to accessible model: ${accessibleOption.value}`);
            } else {
                // Fallback to empty selection
                selector.value = '';
            }
        }
    }

    showUpgradeModal(model) {
        // Don't show upgrade modals for admin or super users
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Upgrade modal bypassed for ${this.userRole} role: ${model}`);
            return;
        }

        // Close any existing modal first
        this.closeUpgradeModal();

        const modelName = this.modelInfo[model]?.name || model;
        const accessInfo = this.getAccessReason(model);

        // Determine if this is a TTS-specific restriction
        const isTTSBlocked = accessInfo.ttsBlocked;
        const title = isTTSBlocked ? 'Text-to-Speech Not Available' : 'Premium Feature Required';
        const description = isTTSBlocked
            ? 'Text-to-Speech features are not included in the Free Plan.'
            : `<strong>${modelName}</strong> requires a premium subscription.`;

        // Create enhanced modal HTML with upgrade options using CSS classes
        const modalHtml = `
            <div id="rbac-upgrade-modal" class="modal-overlay">
                <div class="modal-content">
                    <button id="rbac-modal-close-x" class="modal-close-x">×</button>

                    <div style="text-align: center;">
                        <div class="modal-lock-icon">🔒</div>

                        <h2 class="modal-title">${title}</h2>

                        <p class="modal-description">${description}</p>

                        <p class="modal-subtitle">
                            Upgrade to unlock premium AI models, higher usage limits, and advanced features.
                        </p>

                        <div class="modal-upgrade-buttons">
                            <button id="rbac-upgrade-basic-btn" class="upgrade-btn upgrade-btn-basic" data-plan="basic">
                                <div class="plan-name">Basic Plan</div>
                                <div class="plan-price">$4.99/month</div>
                            </button>

                            <button id="rbac-upgrade-professional-btn" class="upgrade-btn upgrade-btn-professional" data-plan="professional">
                                <div class="plan-name">Professional Plan</div>
                                <div class="plan-price">$12.99/month</div>
                                <div class="popular-badge">POPULAR</div>
                            </button>
                        </div>

                        <button id="rbac-close-modal-btn" class="modal-close-btn">
                            Maybe Later
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Setup event listeners with proper error handling
        const setupEventListener = (id, handler) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('click', handler);
            } else {
                console.warn(`Element with id ${id} not found`);
            }
        };

        // Close button event listeners
        setupEventListener('rbac-close-modal-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.closeUpgradeModal();
        });

        setupEventListener('rbac-modal-close-x', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.closeUpgradeModal();
        });

        // Note: upgrade buttons with data-plan attributes are handled by payment.js automatically
        // The payment.js listens for clicks on elements with [data-plan] attribute

        // Close on overlay click (but not on modal content)
        const modal = document.getElementById('rbac-upgrade-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'rbac-upgrade-modal') {
                    this.closeUpgradeModal();
                }
            });
        }

        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeUpgradeModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // Prevent body scroll when modal is open
        document.body.classList.add('modal-open');
    }

    closeUpgradeModal() {
        const modal = document.getElementById('rbac-upgrade-modal');
        if (modal) {
            // Add fade out animation
            modal.style.opacity = '0';
            modal.style.transform = 'scale(0.9)';
            modal.style.transition = 'all 0.2s ease-out';

            setTimeout(() => {
                modal.remove();
            }, 200);
        }

        // Restore body scroll
        document.body.classList.remove('modal-open');

        // Remove any escape key listeners
        document.removeEventListener('keydown', this.handleEscape);
    }



    // Public method to validate model access before API calls
    validateModelAccess(model) {
        const accessInfo = this.getAccessReason(model);

        if (!accessInfo.allowed) {
            return {
                allowed: false,
                error: {
                    code: 'model_access_denied',
                    message: accessInfo.reason,
                    upgrade_required: accessInfo.upgradeRequired
                }
            };
        }

        return { allowed: true };
    }
}

// Initialize RBAC access control when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rbacAccessControl = new RBACAccessControl();
});

// Export for use in other scripts
window.RBACAccessControl = RBACAccessControl;
