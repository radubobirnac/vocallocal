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
            'gpt4o-mini': { name: 'GPT-4o Mini TTS', tier: 'premium' },
            'openai': { name: 'OpenAI TTS-1', tier: 'premium' },
            'gemini-2.5-flash-preview-04-17': { name: 'Gemini 2.5 Flash Preview', tier: 'premium' },
            'gemini-2.5-flash': { name: 'Gemini 2.5 Flash Preview', tier: 'premium' },
            'gemini-2.5-flash-tts': { name: 'Gemini 2.5 Flash TTS', tier: 'premium' }
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
                // Add lock icon and disable option for restricted models
                const modelName = this.modelInfo[model]?.name || model;
                option.textContent = `🔒 ${modelName} (Higher Plan)`;
                option.disabled = true;
                option.style.color = '#999';
                option.title = accessInfo.reason;
                console.log(`Model ${model} restricted in ${selectorId}`);
            } else {
                // Ensure accessible models are enabled and remove any lock icons
                option.disabled = false;
                option.style.color = '';

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

        if (!this.isModelAccessible(model)) {
            // Prevent selection and show upgrade modal
            event.preventDefault();
            this.showUpgradeModal(model);

            // Revert to accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                this.isModelAccessible(option.value)
            );
            if (accessibleOption) {
                selector.value = accessibleOption.value;
            }
        }
    }

    showUpgradeModal(model) {
        // Don't show upgrade modals for admin or super users
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Upgrade modal bypassed for ${this.userRole} role: ${model}`);
            return;
        }

        const modelName = this.modelInfo[model]?.name || model;
        const accessInfo = this.getAccessReason(model);

        // Create modal HTML
        const modalHtml = `
            <div id="rbac-upgrade-modal" class="modal-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            ">
                <div class="modal-content" style="
                    background: white;
                    padding: 2rem;
                    border-radius: 15px;
                    max-width: 500px;
                    margin: 1rem;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                ">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                        <h2 style="margin: 0 0 1rem 0; color: #333;">Model Access Restricted</h2>
                        <p style="margin-bottom: 1.5rem; color: #666;">
                            <strong>${modelName}</strong> requires premium access.
                        </p>
                        <p style="margin-bottom: 2rem; color: #666;">
                            ${accessInfo.reason}
                        </p>
                        <div style="display: flex; gap: 1rem; justify-content: center;">
                            <button id="rbac-close-modal-btn" class="button button-outline" style="
                                background: transparent;
                                color: #667eea;
                                border: 2px solid #667eea;
                                padding: 0.75rem 1.5rem;
                                border-radius: 10px;
                                font-weight: 600;
                                cursor: pointer;
                            ">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Setup event listeners
        document.getElementById('rbac-close-modal-btn').addEventListener('click', () => {
            this.closeUpgradeModal();
        });

        // Close on overlay click
        document.getElementById('rbac-upgrade-modal').addEventListener('click', (e) => {
            if (e.target.id === 'rbac-upgrade-modal') {
                this.closeUpgradeModal();
            }
        });
    }

    closeUpgradeModal() {
        const modal = document.getElementById('rbac-upgrade-modal');
        if (modal) {
            modal.remove();
        }
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
