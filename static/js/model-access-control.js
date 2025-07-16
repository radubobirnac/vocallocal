/**
 * Model Access Control for VocalLocal
 * Handles role-based model access restrictions on the frontend
 */

class ModelAccessControl {
    constructor() {
        this.userRole = null;
        this.hasLoadedUserRole = false;
        this.modelRestrictions = {
            free_models: [
                'gemini-2.0-flash-lite'
            ],
            premium_models: [
                // Transcription models
                'gpt-4o-mini-transcribe',
                'gpt-4o-transcribe',
                'gemini-2.5-flash-preview-04-17',  // UI compatibility (maps to 05-20)
                'gemini-2.5-flash-preview-05-20',  // Working model

                // Translation models
                'gpt-4.1-mini',

                // TTS models
                'gemini-2.5-flash-tts',
                'gpt4o-mini',
                'openai',

                // Interpretation models
                'gemini-2.5-flash'
            ]
        };
    }

    /**
     * Initialize the model access control system
     */
    async init() {
        try {
            await this.loadUserRole();
            this.applyModelRestrictions();
            console.log('Model Access Control initialized for role:', this.userRole);
        } catch (error) {
            console.error('Failed to initialize Model Access Control:', error);
            // Default to most restrictive access
            this.userRole = 'normal_user';
            this.applyModelRestrictions();
        }
    }

    /**
     * Load the current user's role from the server
     */
    async loadUserRole() {
        try {
            // Try to get user role from a global variable first (if set by server)
            if (window.currentUserRole) {
                this.userRole = window.currentUserRole;
                this.hasLoadedUserRole = true;
                return;
            }

            // If not available, try to determine from user context
            if (window.currentUser && window.currentUser.role) {
                this.userRole = window.currentUser.role;
                this.hasLoadedUserRole = true;
                return;
            }

            // Default to normal user if we can't determine the role
            this.userRole = 'normal_user';
            this.hasLoadedUserRole = true;

        } catch (error) {
            console.error('Error loading user role:', error);
            this.userRole = 'normal_user';
            this.hasLoadedUserRole = true;
        }
    }

    /**
     * Check if the current user can access a specific model
     */
    canAccessModel(modelName) {
        if (!this.hasLoadedUserRole) {
            console.warn('User role not loaded yet, defaulting to restricted access');
            return false;
        }

        // Admin and Super Users have access to all models
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            return true;
        }

        // Normal users can only access free models (unless they have premium subscription)
        if (this.userRole === 'normal_user') {
            // Check if it's a free model
            if (this.modelRestrictions.free_models.includes(modelName)) {
                return true;
            }

            // For premium models, we would need to check subscription status
            // For now, restrict access to premium models for normal users
            return false;
        }

        // Default to no access
        return false;
    }

    /**
     * Apply model restrictions to all model selection dropdowns
     */
    applyModelRestrictions() {
        const modelSelectors = [
            'global-transcription-model',
            'transcription-model-select',
            'translation-model-select',
            'tts-model-select',
            'interpretation-model-select'
        ];

        modelSelectors.forEach(selectorId => {
            const select = document.getElementById(selectorId);
            if (select) {
                this.restrictModelSelect(select);
            }
        });

        // Also apply to any model selects with class 'model-select'
        const classBasedSelects = document.querySelectorAll('.model-select');
        classBasedSelects.forEach(select => {
            this.restrictModelSelect(select);
        });
    }

    /**
     * Restrict a specific model selection dropdown
     */
    restrictModelSelect(selectElement) {
        if (!selectElement) return;

        const options = selectElement.querySelectorAll('option');
        let hasValidSelection = false;
        let firstValidOption = null;

        options.forEach(option => {
            const modelValue = option.value;
            const canAccess = this.canAccessModel(modelValue);

            if (canAccess) {
                // Enable the option
                option.disabled = false;
                option.classList.remove('premium-disabled');
                if (!firstValidOption) {
                    firstValidOption = option;
                }
                if (option.selected) {
                    hasValidSelection = true;
                }
            } else {
                // For normal users: keep enabled but mark as premium (plan-access-control will handle the UI)
                // For other cases: disable the option
                if (this.userRole === 'normal_user') {
                    option.disabled = false; // Let plan-access-control handle the interaction
                    option.classList.add('premium-disabled');
                } else {
                    option.disabled = true;
                    option.classList.add('premium-disabled');
                }

                // Don't add lock icon here - let plan-access-control handle the visual indicators
                // to avoid duplicate lock symbols
            }
        });

        // If current selection is invalid, switch to first valid option
        if (!hasValidSelection && firstValidOption) {
            selectElement.value = firstValidOption.value;

            // Trigger change event to update any dependent UI
            const changeEvent = new Event('change', { bubbles: true });
            selectElement.dispatchEvent(changeEvent);
        }
    }

    /**
     * Get available models for the current user
     */
    getAvailableModels() {
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            return [...this.modelRestrictions.free_models, ...this.modelRestrictions.premium_models];
        } else {
            return [...this.modelRestrictions.free_models];
        }
    }

    /**
     * Show upgrade prompt for restricted models
     */
    showUpgradePrompt(modelName) {
        // Only show upgrade prompts for normal users
        if (this.userRole === 'normal_user') {
            const message = `The ${modelName} model requires a premium subscription or Super User access. Please upgrade your plan or contact an administrator.`;

            // Try to use the app's showStatus function if available
            if (window.showStatus) {
                window.showStatus(message, 'warning');
            } else {
                alert(message);
            }
        } else {
            // For admin/super users, log that access should be granted
            console.log(`Model access should be granted for ${this.userRole} role: ${modelName}`);
        }
    }

    /**
     * Validate model selection before making API calls
     */
    validateModelSelection(modelName) {
        if (!this.canAccessModel(modelName)) {
            this.showUpgradePrompt(modelName);
            return false;
        }
        return true;
    }

    /**
     * Get user role information
     */
    getUserRoleInfo() {
        return {
            role: this.userRole,
            hasLoadedRole: this.hasLoadedUserRole,
            hasPremiumAccess: this.userRole === 'admin' || this.userRole === 'super_user',
            hasAdminPrivileges: this.userRole === 'admin'
        };
    }

    /**
     * Update user role (called when role changes)
     */
    updateUserRole(newRole) {
        this.userRole = newRole;
        this.hasLoadedUserRole = true;
        this.applyModelRestrictions();
        console.log('User role updated to:', newRole);
    }
}

// Create global instance
window.modelAccessControl = new ModelAccessControl();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.modelAccessControl.init();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModelAccessControl;
}
