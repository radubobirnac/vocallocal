/**
 * Plan-based access control for VocalLocal frontend
 * Manages model restrictions and UI updates based on user subscription plans
 */

class PlanAccessControl {
    constructor() {
        this.userPlan = 'free'; // Default to free plan
        this.userRole = 'normal_user'; // Default to normal user role
        this.planModelAccess = {
            'free': {
                'transcription': ['gemini-2.0-flash-lite', 'gemini'],
                'translation': ['gemini-2.0-flash-lite'],
                'tts': [], // No free TTS models - all require upgrade
                'interpretation': ['gemini-2.0-flash-lite']
            },
            'basic': {
                'transcription': [
                    'gemini-2.0-flash-lite', 'gemini',
                    'gpt-4o-mini-transcribe',
                    'gpt-4o-transcribe',                // Added GPT-4o access for Basic Plan
                    'gemini-2.5-flash-preview-04-17',  // UI compatibility (maps to 05-20)
                    'gemini-2.5-flash-preview-05-20'   // Working model
                ],
                'translation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash',
                    'gpt-4.1-mini'
                ],
                'tts': [
                    'gemini-2.5-flash-tts',
                    'gpt4o-mini',
                    'openai'
                ],
                'interpretation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash'
                ]
            },
            'professional': {
                'transcription': [
                    // Include all basic models
                    'gemini-2.0-flash-lite', 'gemini',
                    'gpt-4o-mini-transcribe',
                    'gemini-2.5-flash-preview-04-17',
                    // Professional-only models
                    'gpt-4o-transcribe'
                ],
                'translation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash',
                    'gpt-4.1-mini'
                ],
                'tts': [
                    'gemini-2.5-flash-tts',
                    'gpt4o-mini',
                    'openai'
                ],
                'interpretation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash'
                ]
            }
        };

        this.modelInfo = {
            'gemini-2.0-flash-lite': { name: 'Gemini 2.0 Flash Lite', tier: 'free' },
            'gpt-4o-mini-transcribe': { name: 'OpenAI GPT-4o Mini', tier: 'basic' },
            'gpt-4o-transcribe': { name: 'OpenAI GPT-4o', tier: 'basic' },
            'gemini-2.5-flash-preview-04-17': { name: 'Gemini 2.5 Flash Preview', tier: 'basic' },  // UI compatibility
            'gemini-2.5-flash-preview-05-20': { name: 'Gemini 2.5 Flash Preview 05-20', tier: 'basic' },  // Working model
            'gemini-2.5-flash': { name: 'Gemini 2.5 Flash Preview', tier: 'basic' },
            'gemini-2.5-flash-tts': { name: 'Gemini 2.5 Flash TTS', tier: 'basic' },
            'gpt4o-mini': { name: 'GPT-4o Mini TTS', tier: 'basic' },
            'openai': { name: 'OpenAI TTS-1', tier: 'professional' }
        };

        this.planNames = {
            'basic': 'Basic Plan ($4.99/month)',
            'professional': 'Professional Plan ($12.99/month)'
        };

        this.init();
    }

    async init() {
        await this.loadUserPlan();
        await this.loadUserRole();
        this.setupModelSelectors();
        this.setupEventListeners();
    }

    async loadUserPlan() {
        try {
            // Try to get user plan from dashboard data or API
            if (window.dashboardData && window.dashboardData.user) {
                this.userPlan = window.dashboardData.user.plan_type || 'free';
            } else {
                // Fallback: fetch from API
                const response = await fetch('/api/user/plan');
                if (response.ok) {
                    const data = await response.json();
                    this.userPlan = data.plan?.plan_type || 'free';
                }
            }
            console.log(`User plan loaded: ${this.userPlan}`);
        } catch (error) {
            console.warn('Could not load user plan, defaulting to free:', error);
            this.userPlan = 'free';
        }
    }

    async loadUserRole() {
        try {
            const response = await fetch('/api/user/role-info');
            if (response.ok) {
                const data = await response.json();
                this.userRole = data.role || 'normal_user';
                console.log(`User role loaded for plan access control: ${this.userRole}`);
            } else {
                console.warn('Could not load user role, defaulting to normal_user');
                this.userRole = 'normal_user';
            }
        } catch (error) {
            console.warn('Error loading user role for plan access control:', error);
            this.userRole = 'normal_user';
        }
    }

    isModelAccessible(model, serviceType) {
        // Admin and Super Users have access to all models
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Model ${model} accessible for ${this.userRole} role`);
            return true;
        }

        // Normal users are restricted by their subscription plan
        const accessibleModels = this.planModelAccess[this.userPlan]?.[serviceType] || [];
        return accessibleModels.includes(model);
    }

    getRequiredPlan(model, serviceType) {
        for (const [plan, services] of Object.entries(this.planModelAccess)) {
            if (services[serviceType]?.includes(model)) {
                return plan;
            }
        }
        return null;
    }

    setupModelSelectors() {
        // Setup transcription model selectors
        this.setupSelector('global-transcription-model', 'transcription');
        this.setupSelector('transcription-model-select', 'transcription');

        // Setup translation model selector
        this.setupSelector('translation-model-select', 'translation');

        // Setup TTS model selector
        this.setupSelector('tts-model-select', 'tts');

        // Setup interpretation model selector
        this.setupSelector('interpretation-model-select', 'interpretation');
    }

    setupSelector(selectorId, serviceType) {
        const selector = document.getElementById(selectorId);
        if (!selector) return;

        console.log(`Setting up selector ${selectorId} for role: ${this.userRole}, plan: ${this.userPlan}`);

        // Process each option
        Array.from(selector.options).forEach(option => {
            const model = option.value;
            const isAccessible = this.isModelAccessible(model, serviceType);

            // Clean up option text first to remove any existing lock icons
            let cleanText = option.textContent.replace(/🔒\s*/g, '').replace(/\s*\([^)]*\)\s*$/, '');
            const modelName = this.modelInfo[model]?.name || cleanText;

            if (!isAccessible && this.userRole === 'normal_user') {
                // For normal users: show lock icon but keep option enabled for upgrade prompt
                const requiredPlan = this.getRequiredPlan(model, serviceType);
                const planName = this.planNames[requiredPlan] || 'Higher Plan';

                option.textContent = `🔒 ${modelName}`;
                option.disabled = false; // Keep enabled so users can click to see upgrade prompt
                option.style.color = '#999';
                option.title = `Requires ${planName} to access this model`;
                option.setAttribute('data-premium', 'true');
                option.setAttribute('data-required-plan', requiredPlan);
                console.log(`Model ${model} marked as premium in ${selectorId} for ${this.userRole}`);
            } else {
                // For accessible models or privileged users: clean display
                option.textContent = modelName;
                option.disabled = false;
                option.style.color = '';
                option.removeAttribute('data-premium');
                option.removeAttribute('data-required-plan');

                // Add role-specific titles for privileged users
                if (this.userRole === 'super_user') {
                    option.title = `${modelName} - Super User Access`;
                } else if (this.userRole === 'admin') {
                    option.title = `${modelName} - Admin Access`;
                } else {
                    option.title = `${modelName} - Available`;
                }

                console.log(`Model ${model} accessible in ${selectorId} for ${this.userRole}`);
            }
        });

        // Ensure selected value is accessible
        if (!this.isModelAccessible(selector.value, serviceType)) {
            // Select first accessible model
            const accessibleModels = this.planModelAccess[this.userPlan][serviceType] || [];
            if (accessibleModels.length > 0) {
                selector.value = accessibleModels[0];
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
            'transcription-model-select',
            'translation-model-select',
            'tts-model-select',
            'interpretation-model-select'
        ];
        return modelSelectors.includes(element.id);
    }

    handleModelSelection(selector) {
        const model = selector.value;
        const serviceType = this.getServiceTypeFromSelector(selector.id);

        // Check if the selected model is accessible to the user based on their plan
        if (!this.isModelAccessible(model, serviceType)) {
            // Model is not accessible - show upgrade modal and revert selection
            console.log(`Model ${model} not accessible for ${this.userRole} with ${this.userPlan} plan`);
            this.showUpgradeModal(model, serviceType);

            // Revert to first accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                this.isModelAccessible(option.value, serviceType)
            );
            if (accessibleOption) {
                selector.value = accessibleOption.value;
                console.log(`Reverted selection to accessible model: ${accessibleOption.value}`);
            } else {
                // Fallback to empty selection if no accessible models found
                selector.value = '';
                console.warn(`No accessible models found for ${serviceType} service`);
            }
        } else {
            // Model is accessible - allow the selection
            console.log(`Model ${model} accessible for ${this.userRole} with ${this.userPlan} plan`);
        }
    }

    getServiceTypeFromSelector(selectorId) {
        const mapping = {
            'global-transcription-model': 'transcription',
            'transcription-model-select': 'transcription',
            'translation-model-select': 'translation',
            'tts-model-select': 'tts',
            'interpretation-model-select': 'interpretation'
        };
        return mapping[selectorId] || 'transcription';
    }

    showUpgradeModal(model, serviceType) {
        // Don't show upgrade modals for admin or super users
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            console.log(`Plan upgrade modal bypassed for ${this.userRole} role: ${model}`);
            return;
        }

        const requiredPlan = this.getRequiredPlan(model, serviceType);
        const modelName = this.modelInfo[model]?.name || model;

        console.log(`Model ${model} requires ${requiredPlan} plan`);

        // Determine which buttons to show based on required plan and current user plan
        const showBasicButton = requiredPlan === 'basic' || (requiredPlan === 'professional' && this.userPlan === 'free');
        const showProfessionalButton = requiredPlan === 'professional' || (requiredPlan === 'basic' && this.userPlan === 'free');

        // Create dual-plan modal HTML (consistent with RBAC modal)
        const modalHtml = `
            <div id="upgrade-modal" class="modal-overlay" style="
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
                    position: relative;
                ">
                    <button id="modal-close-x" style="
                        position: absolute;
                        top: 1rem;
                        right: 1rem;
                        background: none;
                        border: none;
                        font-size: 1.5rem;
                        cursor: pointer;
                        color: #999;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        transition: all 0.2s ease;
                    " onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">×</button>

                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                        <h2 style="margin: 0 0 1rem 0; color: #333;">Premium Model Access Required</h2>
                        <p style="margin-bottom: 1rem; color: #666;">
                            <strong>${modelName}</strong> requires ${requiredPlan === 'basic' ? 'Basic Plan' : 'Professional Plan'} or higher.
                        </p>
                        <p style="margin-bottom: 2rem; color: #666;">
                            ${requiredPlan === 'basic' ?
                                'Upgrade to Basic Plan to access this model and unlock premium AI features.' :
                                'This premium model requires Professional Plan for access to advanced AI capabilities.'
                            }
                        </p>

                        <div style="display: flex; gap: 1rem; justify-content: center; margin-bottom: 1.5rem;">
                            ${showBasicButton ? `
                            <button id="upgrade-basic-btn" data-plan="basic" style="
                                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                                color: white;
                                border: none;
                                padding: 1rem 1.5rem;
                                border-radius: 10px;
                                font-weight: 600;
                                cursor: pointer;
                                transition: all 0.2s ease;
                                text-align: center;
                                min-width: 140px;
                                ${!showProfessionalButton ? 'min-width: 200px;' : ''}
                            ">
                                <div style="font-size: 0.9rem; margin-bottom: 0.25rem;">Basic Plan</div>
                                <div style="font-size: 1.1rem; font-weight: 700;">$4.99/month</div>
                                ${requiredPlan === 'basic' ? '<div style="font-size: 0.8rem; margin-top: 0.25rem; opacity: 0.9;">Required for this model</div>' : ''}
                            </button>
                            ` : ''}

                            ${showProfessionalButton ? `
                            <button id="upgrade-professional-btn" data-plan="professional" style="
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                border: none;
                                padding: 1rem 1.5rem;
                                border-radius: 10px;
                                font-weight: 600;
                                cursor: pointer;
                                transition: all 0.2s ease;
                                text-align: center;
                                min-width: 140px;
                                position: relative;
                                ${!showBasicButton ? 'min-width: 200px;' : ''}
                            ">
                                ${requiredPlan === 'professional' || !showBasicButton ? `
                                <div style="
                                    position: absolute;
                                    top: -8px;
                                    right: -8px;
                                    background: #ff4757;
                                    color: white;
                                    padding: 0.2rem 0.5rem;
                                    border-radius: 8px;
                                    font-size: 0.7rem;
                                    font-weight: 700;
                                ">${requiredPlan === 'professional' ? 'REQUIRED' : 'POPULAR'}</div>
                                ` : ''}
                                <div style="font-size: 0.9rem; margin-bottom: 0.25rem;">Professional Plan</div>
                                <div style="font-size: 1.1rem; font-weight: 700;">$12.99/month</div>
                                ${requiredPlan === 'professional' ? '<div style="font-size: 0.8rem; margin-top: 0.25rem; opacity: 0.9;">Required for this model</div>' : ''}
                            </button>
                            ` : ''}
                        </div>

                        <button id="close-modal-btn" style="
                            background: transparent;
                            color: #667eea;
                            border: 2px solid #667eea;
                            padding: 0.75rem 1.5rem;
                            border-radius: 10px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.2s ease;
                        ">
                            Maybe Later
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Setup event listeners
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.closeUpgradeModal();
        });

        document.getElementById('modal-close-x').addEventListener('click', () => {
            this.closeUpgradeModal();
        });

        // Note: upgrade buttons with data-plan attributes are handled by payment.js automatically
        // The payment.js listens for clicks on elements with [data-plan] attribute

        // Close on overlay click
        document.getElementById('upgrade-modal').addEventListener('click', (e) => {
            if (e.target.id === 'upgrade-modal') {
                this.closeUpgradeModal();
            }
        });

        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeUpgradeModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }

    closeUpgradeModal() {
        const modal = document.getElementById('upgrade-modal');
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
        document.body.style.overflow = '';
    }

    // Note: Upgrade functionality is now handled by payment.js
    // The payment.js automatically handles Stripe checkout for buttons with data-plan attributes

    // Public method to validate model access before API calls
    validateModelAccess(model, serviceType) {
        // Admin and Super Users always have access
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            return {
                allowed: true,
                role: this.userRole,
                message: `Access granted for ${this.userRole} role`
            };
        }

        if (!this.isModelAccessible(model, serviceType)) {
            const requiredPlan = this.getRequiredPlan(model, serviceType);
            const modelName = this.modelInfo[model]?.name || model;
            const planName = this.planNames[requiredPlan] || 'Higher Plan';

            return {
                allowed: false,
                error: {
                    code: 'model_access_denied',
                    message: `${modelName} requires ${planName}`,
                    required_plan: requiredPlan,
                    upgrade_message: `Upgrade to ${planName} to access ${modelName}`
                }
            };
        }
        
        // Model is accessible to the user
        return {
            allowed: true,
            model: model,
            plan: this.userPlan
        };
    }
}

// Initialize plan access control when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.planAccessControl = new PlanAccessControl();
});

// Export for use in other scripts
window.PlanAccessControl = PlanAccessControl;
