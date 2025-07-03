/**
 * Email validation functionality for VocalLocal
 * Provides real-time email validation with visual feedback
 */

class EmailValidator {
    constructor() {
        this.emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        this.validationCache = new Map();
        this.validationTimeout = null;
        this.isValidating = false;
    }

    /**
     * Validate email format using regex
     * @param {string} email - Email to validate
     * @returns {boolean} - True if format is valid
     */
    validateFormat(email) {
        if (!email || typeof email !== 'string') {
            return false;
        }
        return this.emailRegex.test(email.trim().toLowerCase());
    }

    /**
     * Validate email with backend (includes DNS/MX record checking)
     * @param {string} email - Email to validate
     * @returns {Promise<Object>} - Validation result
     */
    async validateWithBackend(email) {
        try {
            // Check cache first
            const cacheKey = email.toLowerCase().trim();
            if (this.validationCache.has(cacheKey)) {
                return this.validationCache.get(cacheKey);
            }

            const response = await fetch('/api/validate-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email })
            });

            const result = await response.json();
            
            // Cache the result for 5 minutes
            this.validationCache.set(cacheKey, result);
            setTimeout(() => {
                this.validationCache.delete(cacheKey);
            }, 5 * 60 * 1000);

            return result;
        } catch (error) {
            console.error('Email validation error:', error);
            return {
                valid: false,
                errors: ['Unable to validate email. Please check your connection.']
            };
        }
    }

    /**
     * Show validation feedback in the UI
     * @param {HTMLElement} emailInput - Email input element
     * @param {Object} validation - Validation result
     */
    showValidationFeedback(emailInput, validation) {
        // Remove existing feedback
        this.clearValidationFeedback(emailInput);

        const container = emailInput.parentElement;
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'email-validation-feedback';

        if (validation.valid) {
            feedbackDiv.className += ' valid';

            // Show appropriate message based on validation level
            let message = '<i class="fas fa-check-circle"></i> Email format is valid';

            if (validation.validation_level === 'format_domain_and_smtp') {
                message = '<i class="fas fa-check-circle"></i> Email address verified';
            } else if (validation.validation_level === 'format_only') {
                message = '<i class="fas fa-check-circle"></i> Email format is valid';
            }

            // Add informational note about OTP verification
            if (validation.warnings && validation.warnings.length > 0) {
                const warning = validation.warnings[0];
                if (warning.includes('OTP')) {
                    message += ' <span class="validation-note">(verification via OTP)</span>';
                } else if (warning.includes('does not verify')) {
                    message += ' <span class="validation-note">(format only)</span>';
                }
            }

            feedbackDiv.innerHTML = message;
            emailInput.classList.remove('invalid');
            emailInput.classList.add('valid');
        } else {
            feedbackDiv.className += ' invalid';
            const errors = validation.errors || ['Invalid email address'];
            let errorMessage = errors[0];

            // Provide helpful suggestions for common errors
            if (errorMessage.includes('does not exist or cannot receive emails')) {
                errorMessage += ' <span class="validation-suggestion">Please check the domain name.</span>';
            } else if (errorMessage.includes('format')) {
                errorMessage += ' <span class="validation-suggestion">Example: user@domain.com</span>';
            }

            feedbackDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;
            emailInput.classList.remove('valid');
            emailInput.classList.add('invalid');
        }

        container.appendChild(feedbackDiv);
    }

    /**
     * Clear validation feedback from the UI
     * @param {HTMLElement} emailInput - Email input element
     */
    clearValidationFeedback(emailInput) {
        const container = emailInput.parentElement;
        const existingFeedback = container.querySelector('.email-validation-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        emailInput.classList.remove('valid', 'invalid');
    }

    /**
     * Show loading state during validation
     * @param {HTMLElement} emailInput - Email input element
     */
    showLoadingState(emailInput) {
        this.clearValidationFeedback(emailInput);
        
        const container = emailInput.parentElement;
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'email-validation-feedback loading';
        feedbackDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating email...';
        
        container.appendChild(feedbackDiv);
        emailInput.classList.remove('valid', 'invalid');
    }

    /**
     * Initialize email validation for an input field
     * @param {HTMLElement} emailInput - Email input element
     * @param {Object} options - Configuration options
     */
    initializeValidation(emailInput, options = {}) {
        const {
            validateOnBlur = true,
            validateOnInput = true,
            debounceDelay = 1000,
            skipBackendValidation = false
        } = options;

        // Input event handler with debouncing
        if (validateOnInput) {
            emailInput.addEventListener('input', (event) => {
                const email = event.target.value.trim();
                
                // Clear previous timeout
                if (this.validationTimeout) {
                    clearTimeout(this.validationTimeout);
                }

                // Clear feedback if email is empty
                if (!email) {
                    this.clearValidationFeedback(emailInput);
                    return;
                }

                // Basic format validation (immediate)
                if (!this.validateFormat(email)) {
                    this.showValidationFeedback(emailInput, {
                        valid: false,
                        errors: ['Please enter a valid email format']
                    });
                    return;
                }

                // Skip backend validation if disabled
                if (skipBackendValidation) {
                    this.showValidationFeedback(emailInput, { valid: true });
                    return;
                }

                // Debounced backend validation
                this.validationTimeout = setTimeout(async () => {
                    if (this.isValidating) return;
                    
                    this.isValidating = true;
                    this.showLoadingState(emailInput);
                    
                    try {
                        const validation = await this.validateWithBackend(email);
                        this.showValidationFeedback(emailInput, validation);
                    } catch (error) {
                        console.error('Validation error:', error);
                        this.showValidationFeedback(emailInput, {
                            valid: false,
                            errors: ['Unable to validate email']
                        });
                    } finally {
                        this.isValidating = false;
                    }
                }, debounceDelay);
            });
        }

        // Blur event handler
        if (validateOnBlur) {
            emailInput.addEventListener('blur', async (event) => {
                const email = event.target.value.trim();
                
                if (!email) {
                    this.clearValidationFeedback(emailInput);
                    return;
                }

                if (!this.validateFormat(email)) {
                    this.showValidationFeedback(emailInput, {
                        valid: false,
                        errors: ['Please enter a valid email format']
                    });
                    return;
                }

                if (skipBackendValidation) {
                    this.showValidationFeedback(emailInput, { valid: true });
                    return;
                }

                // Only validate if not already validating
                if (!this.isValidating && !emailInput.classList.contains('valid')) {
                    this.isValidating = true;
                    this.showLoadingState(emailInput);
                    
                    try {
                        const validation = await this.validateWithBackend(email);
                        this.showValidationFeedback(emailInput, validation);
                    } catch (error) {
                        console.error('Validation error:', error);
                        this.showValidationFeedback(emailInput, {
                            valid: false,
                            errors: ['Unable to validate email']
                        });
                    } finally {
                        this.isValidating = false;
                    }
                }
            });
        }
    }

    /**
     * Validate email and return result (for form submission)
     * @param {string} email - Email to validate
     * @returns {Promise<Object>} - Validation result
     */
    async validateEmail(email) {
        if (!email || !this.validateFormat(email)) {
            return {
                valid: false,
                errors: ['Please enter a valid email address']
            };
        }

        try {
            return await this.validateWithBackend(email);
        } catch (error) {
            console.error('Email validation error:', error);
            return {
                valid: false,
                errors: ['Unable to validate email. Please try again.']
            };
        }
    }
}

// Global email validator instance
const emailValidator = new EmailValidator();

// Auto-initialize email validation on page load
document.addEventListener('DOMContentLoaded', function() {
    // Find all email inputs and initialize validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    
    emailInputs.forEach(input => {
        // Skip validation for OAuth forms or if explicitly disabled
        if (input.closest('.oauth-container') || input.hasAttribute('data-skip-validation')) {
            return;
        }
        
        emailValidator.initializeValidation(input, {
            validateOnBlur: true,
            validateOnInput: true,
            debounceDelay: 1000
        });
    });
});

// Export for use in other scripts
window.emailValidator = emailValidator;
