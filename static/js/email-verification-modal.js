/**
 * Email Verification Modal for VocalLocal
 * Provides popup interface for entering verification codes
 */

class EmailVerificationModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.email = '';
        this.username = '';
        this.onVerificationSuccess = null;
        this.onVerificationCancel = null;
        this.resendCooldown = 0;
        this.resendTimer = null;
    }

    /**
     * Show the email verification modal
     * @param {Object} options - Configuration options
     */
    show(options = {}) {
        const {
            email = '',
            username = '',
            onSuccess = null,
            onCancel = null,
            message = 'Please check your email and enter the 6-digit verification code.'
        } = options;

        this.email = email;
        this.username = username;
        this.onVerificationSuccess = onSuccess;
        this.onVerificationCancel = onCancel;

        this.createModal(message);
        this.bindEvents();
        this.showModal();
    }

    /**
     * Create the modal HTML structure
     * @param {string} message - Message to display
     */
    createModal(message) {
        // Remove existing modal if present
        this.destroy();

        const modalHTML = `
            <div class="verification-modal-overlay" id="verificationModalOverlay">
                <div class="verification-modal" id="verificationModal">
                    <div class="verification-modal-header">
                        <button class="verification-modal-close" id="verificationModalClose" aria-label="Close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="verification-modal-content">
                        <div class="verification-icon">
                            <i class="fas fa-envelope-open-text"></i>
                        </div>
                        
                        <h2 class="verification-title">Verify Your Email</h2>
                        
                        <p class="verification-message">${message}</p>
                        
                        <div class="verification-email-display">
                            <i class="fas fa-envelope"></i>
                            <span>${this.email}</span>
                        </div>
                        
                        <div class="verification-code-container">
                            <label for="verificationCodeInput" class="verification-label">
                                Enter 6-digit verification code
                            </label>
                            <div class="verification-input-group">
                                <input 
                                    type="text" 
                                    id="verificationCodeInput" 
                                    class="verification-code-input"
                                    placeholder="000000"
                                    maxlength="6"
                                    autocomplete="off"
                                    inputmode="numeric"
                                    pattern="[0-9]*"
                                >
                                <button class="verification-paste-btn" id="verificationPasteBtn" title="Paste code">
                                    <i class="fas fa-paste"></i>
                                </button>
                            </div>
                            <div class="verification-feedback" id="verificationFeedback"></div>
                        </div>
                        
                        <div class="verification-actions">
                            <button class="verification-btn verification-btn-primary" id="verifyCodeBtn">
                                <i class="fas fa-check"></i>
                                Verify Email
                            </button>
                            
                            <button class="verification-btn verification-btn-secondary" id="resendCodeBtn">
                                <i class="fas fa-paper-plane"></i>
                                <span id="resendBtnText">Resend Code</span>
                            </button>
                        </div>
                        
                        <div class="verification-help">
                            <p>Didn't receive the email?</p>
                            <ul>
                                <li>Check your spam/junk folder</li>
                                <li>Make sure ${this.email} is correct</li>
                                <li>Wait a few minutes and try resending</li>
                            </ul>
                            
                            <button class="verification-change-email" id="changeEmailBtn">
                                <i class="fas fa-edit"></i>
                                Change Email Address
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('verificationModal');
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Close modal events
        document.getElementById('verificationModalClose').addEventListener('click', () => this.hide());
        document.getElementById('verificationModalOverlay').addEventListener('click', (e) => {
            if (e.target.id === 'verificationModalOverlay') {
                this.hide();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.hide();
            }
        });

        // Code input handling
        const codeInput = document.getElementById('verificationCodeInput');
        codeInput.addEventListener('input', (e) => this.handleCodeInput(e));
        codeInput.addEventListener('paste', (e) => this.handleCodePaste(e));

        // Paste button
        document.getElementById('verificationPasteBtn').addEventListener('click', () => this.pasteCode());

        // Verify button
        document.getElementById('verifyCodeBtn').addEventListener('click', () => this.verifyCode());

        // Resend button
        document.getElementById('resendCodeBtn').addEventListener('click', () => this.resendCode());

        // Change email button
        document.getElementById('changeEmailBtn').addEventListener('click', () => this.changeEmail());

        // Auto-focus on code input
        setTimeout(() => {
            codeInput.focus();
        }, 100);
    }

    /**
     * Handle code input formatting
     * @param {Event} e - Input event
     */
    handleCodeInput(e) {
        let value = e.target.value.replace(/\D/g, ''); // Only digits
        
        if (value.length > 6) {
            value = value.substring(0, 6);
        }
        
        e.target.value = value;
        
        // Auto-verify when 6 digits entered
        if (value.length === 6) {
            setTimeout(() => this.verifyCode(), 500);
        }
        
        // Clear any previous feedback
        this.clearFeedback();
    }

    /**
     * Handle code paste
     * @param {Event} e - Paste event
     */
    handleCodePaste(e) {
        e.preventDefault();
        const paste = (e.clipboardData || window.clipboardData).getData('text');
        const code = paste.replace(/\D/g, '').substring(0, 6);
        
        document.getElementById('verificationCodeInput').value = code;
        
        if (code.length === 6) {
            setTimeout(() => this.verifyCode(), 500);
        }
    }

    /**
     * Paste code from clipboard
     */
    async pasteCode() {
        try {
            const text = await navigator.clipboard.readText();
            const code = text.replace(/\D/g, '').substring(0, 6);
            document.getElementById('verificationCodeInput').value = code;
            
            if (code.length === 6) {
                setTimeout(() => this.verifyCode(), 500);
            }
        } catch (err) {
            console.log('Clipboard access denied');
        }
    }

    /**
     * Verify the entered code
     */
    async verifyCode() {
        const code = document.getElementById('verificationCodeInput').value.trim();
        
        if (code.length !== 6) {
            this.showFeedback('Please enter a 6-digit code', 'error');
            return;
        }

        this.setLoading(true);
        this.showFeedback('Verifying code...', 'loading');

        try {
            const response = await fetch('/api/verify-email-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.email,
                    code: code
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showFeedback('✓ Email verified successfully!', 'success');
                
                setTimeout(() => {
                    this.hide();
                    if (this.onVerificationSuccess) {
                        this.onVerificationSuccess(result);
                    }
                }, 1500);
            } else {
                this.showFeedback(result.message || 'Verification failed', 'error');
                
                if (result.error_type === 'expired' || result.error_type === 'too_many_attempts') {
                    this.enableResendButton();
                }
            }
        } catch (error) {
            console.error('Verification error:', error);
            this.showFeedback('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Resend verification code
     */
    async resendCode() {
        if (this.resendCooldown > 0) {
            return;
        }

        this.setResendLoading(true);

        try {
            const response = await fetch('/api/send-verification-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.email,
                    username: this.username
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showFeedback('New verification code sent!', 'success');
                this.startResendCooldown(60); // 60 seconds cooldown
                document.getElementById('verificationCodeInput').value = '';
                document.getElementById('verificationCodeInput').focus();
            } else {
                this.showFeedback(result.message || 'Failed to resend code', 'error');
            }
        } catch (error) {
            console.error('Resend error:', error);
            this.showFeedback('Network error. Please try again.', 'error');
        } finally {
            this.setResendLoading(false);
        }
    }

    /**
     * Change email address
     */
    changeEmail() {
        this.hide();
        if (this.onVerificationCancel) {
            this.onVerificationCancel('change_email');
        }
    }

    /**
     * Show feedback message
     * @param {string} message - Message to show
     * @param {string} type - Type: success, error, loading
     */
    showFeedback(message, type) {
        const feedback = document.getElementById('verificationFeedback');
        feedback.textContent = message;
        feedback.className = `verification-feedback ${type}`;
        feedback.style.display = 'block';
    }

    /**
     * Clear feedback message
     */
    clearFeedback() {
        const feedback = document.getElementById('verificationFeedback');
        feedback.style.display = 'none';
    }

    /**
     * Set loading state for verify button
     * @param {boolean} loading - Loading state
     */
    setLoading(loading) {
        const btn = document.getElementById('verifyCodeBtn');
        const input = document.getElementById('verificationCodeInput');
        
        if (loading) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
            input.disabled = true;
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check"></i> Verify Email';
            input.disabled = false;
        }
    }

    /**
     * Set loading state for resend button
     * @param {boolean} loading - Loading state
     */
    setResendLoading(loading) {
        const btn = document.getElementById('resendCodeBtn');
        
        if (loading) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Sending...</span>';
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> <span id="resendBtnText">Resend Code</span>';
        }
    }

    /**
     * Start resend cooldown timer
     * @param {number} seconds - Cooldown duration in seconds
     */
    startResendCooldown(seconds) {
        this.resendCooldown = seconds;
        const btn = document.getElementById('resendCodeBtn');
        const textSpan = document.getElementById('resendBtnText');
        
        btn.disabled = true;
        
        this.resendTimer = setInterval(() => {
            this.resendCooldown--;
            textSpan.textContent = `Resend Code (${this.resendCooldown}s)`;
            
            if (this.resendCooldown <= 0) {
                this.enableResendButton();
            }
        }, 1000);
    }

    /**
     * Enable resend button
     */
    enableResendButton() {
        if (this.resendTimer) {
            clearInterval(this.resendTimer);
            this.resendTimer = null;
        }
        
        this.resendCooldown = 0;
        const btn = document.getElementById('resendCodeBtn');
        const textSpan = document.getElementById('resendBtnText');
        
        btn.disabled = false;
        textSpan.textContent = 'Resend Code';
    }

    /**
     * Show the modal
     */
    showModal() {
        const overlay = document.getElementById('verificationModalOverlay');
        overlay.style.display = 'flex';
        
        // Trigger animation
        setTimeout(() => {
            overlay.classList.add('show');
            this.modal.classList.add('show');
        }, 10);
        
        this.isOpen = true;
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide the modal
     */
    hide() {
        const overlay = document.getElementById('verificationModalOverlay');
        
        if (overlay) {
            overlay.classList.remove('show');
            this.modal.classList.remove('show');
            
            setTimeout(() => {
                this.destroy();
            }, 300);
        }
        
        this.isOpen = false;
        document.body.style.overflow = '';
        
        if (this.onVerificationCancel) {
            this.onVerificationCancel('user_cancelled');
        }
    }

    /**
     * Destroy the modal
     */
    destroy() {
        const overlay = document.getElementById('verificationModalOverlay');
        if (overlay) {
            overlay.remove();
        }
        
        if (this.resendTimer) {
            clearInterval(this.resendTimer);
            this.resendTimer = null;
        }
        
        this.modal = null;
        this.isOpen = false;
    }
}

// Global instance
window.emailVerificationModal = new EmailVerificationModal();
