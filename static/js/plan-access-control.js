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
                'tts': ['gemini-2.5-flash-tts'],
                'interpretation': ['gemini-2.0-flash-lite']
            },
            'basic': {
                'transcription': [
                    'gemini-2.0-flash-lite', 'gemini',
                    'gpt-4o-mini-transcribe',
                    'gemini-2.5-flash-preview-04-17'
                ],
                'translation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash',
                    'gpt-4.1-mini'
                ],
                'tts': [
                    'gemini-2.5-flash-tts',
                    'gpt4o-mini'
                ],
                'interpretation': [
                    'gemini-2.0-flash-lite',
                    'gemini-2.5-flash'
                ]
            },
            'professional': {
                'transcription': [
                    'gemini-2.0-flash-lite', 'gemini',
                    'gpt-4o-mini-transcribe',
                    'gpt-4o-transcribe',
                    'gemini-2.5-flash-preview-04-17'
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
            'gpt-4o-transcribe': { name: 'OpenAI GPT-4o', tier: 'professional' },
            'gemini-2.5-flash-preview-04-17': { name: 'Gemini 2.5 Flash Preview', tier: 'basic' },
            'gemini-2.5-flash': { name: 'Gemini 2.5 Flash Preview', tier: 'basic' },
            'gemini-2.5-flash-tts': { name: 'Gemini 2.5 Flash TTS', tier: 'free' },
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
                    this.userPlan = data.plan_type || 'free';
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
        const selectedOption = selector.options[selector.selectedIndex];

        // Check if this is a premium model selection by a normal user
        if (this.userRole === 'normal_user' && selectedOption && selectedOption.getAttribute('data-premium') === 'true') {
            // Show upgrade modal for normal users selecting premium models
            this.showUpgradeModal(model, serviceType);

            // Revert to first accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                this.isModelAccessible(option.value, serviceType)
            );
            if (accessibleOption) {
                selector.value = accessibleOption.value;
                console.log(`Reverted selection to accessible model: ${accessibleOption.value}`);
            }
        } else if (!this.isModelAccessible(model, serviceType)) {
            // Fallback for other cases (shouldn't happen with new logic)
            console.warn(`Unexpected inaccessible model selection: ${model} by ${this.userRole}`);

            // Revert to accessible model
            const accessibleOption = Array.from(selector.options).find(option =>
                this.isModelAccessible(option.value, serviceType)
            );
            if (accessibleOption) {
                selector.value = accessibleOption.value;
            }
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
        const planName = this.planNames[requiredPlan] || 'Higher Plan';

        // Create modal HTML
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
                ">
                    <div style="text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">🔒</div>
                        <h2 style="margin: 0 0 1rem 0; color: #333;">Premium Model Access Required</h2>
                        <p style="margin-bottom: 1.5rem; color: #666;">
                            <strong>${modelName}</strong> requires <strong>${planName}</strong> to access.
                        </p>
                        <p style="margin-bottom: 2rem; color: #666;">
                            Upgrade your subscription to unlock this premium AI model with enhanced accuracy and advanced features.
                        </p>
                        <div style="display: flex; gap: 1rem; justify-content: center;">
                            <button id="upgrade-btn" class="button button-primary" style="
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                border: none;
                                padding: 0.75rem 1.5rem;
                                border-radius: 10px;
                                font-weight: 600;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            ">
                                Upgrade to ${planName}
                            </button>
                            <button id="close-modal-btn" class="button button-outline" style="
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
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Setup event listeners
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.closeUpgradeModal();
        });

        document.getElementById('upgrade-btn').addEventListener('click', () => {
            this.redirectToUpgrade(requiredPlan);
        });

        // Close on overlay click
        document.getElementById('upgrade-modal').addEventListener('click', (e) => {
            if (e.target.id === 'upgrade-modal') {
                this.closeUpgradeModal();
            }
        });
    }

    closeUpgradeModal() {
        const modal = document.getElementById('upgrade-modal');
        if (modal) {
            modal.remove();
        }
    }

    redirectToUpgrade(plan) {
        // For now, redirect to dashboard with upgrade info
        // Later this will integrate with Stripe
        window.location.href = `/dashboard?upgrade=${plan}`;
    }

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

        return { allowed: true };
    }
}

// Initialize plan access control when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.planAccessControl = new PlanAccessControl();
});

// Export for use in other scripts
window.PlanAccessControl = PlanAccessControl;
