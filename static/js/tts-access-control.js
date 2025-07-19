/**
 * TTS Access Control for VocalLocal
 * Handles Text-to-Speech access restrictions for free users
 */

class TTSAccessControl {
    constructor() {
        this.userRole = null;
        this.userPlan = null;
        this.hasLoadedUserInfo = false;
        this.init();
    }

    async init() {
        await this.loadUserInfo();
        this.setupTTSControls();
        this.setupEventListeners();
    }

    async loadUserInfo() {
        try {
            const response = await fetch('/api/user/role-info');
            const data = await response.json();
            
            this.userRole = data.role || 'normal_user';
            this.userPlan = data.plan_type || 'free';
            this.hasLoadedUserInfo = true;
            
            console.log('TTS Access Control loaded user info:', {
                role: this.userRole,
                plan: this.userPlan
            });
        } catch (error) {
            console.error('Error loading user info for TTS access control:', error);
            // Default to most restrictive settings
            this.userRole = 'normal_user';
            this.userPlan = 'free';
            this.hasLoadedUserInfo = true;
        }
    }

    // Check if user has access to TTS based on their plan
    hasAccessToTTS() {
        // Admin and Super Users always have access
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            return true;
        }
        
        // Basic and Professional plans have access to TTS
        if (this.userPlan === 'basic' || this.userPlan === 'professional') {
            return true;
        }
        
        // Free plan users don't have access to TTS
        return false;
    }
    
    // Check if specific TTS model is accessible
    canAccessTTSModel(model) {
        // First check if user has any TTS access
        if (!this.hasAccessToTTS()) {
            return false;
        }
        
        // Then check if the specific model is accessible based on plan
        if (window.planAccessControl) {
            return window.planAccessControl.isModelAccessible(model, 'tts');
        }
        
        return false;
    }

    setupTTSControls() {
        if (!this.hasLoadedUserInfo) {
            console.log('User info not loaded yet, skipping TTS control setup');
            return;
        }

        // Find all TTS-related buttons and controls
        const ttsButtons = document.querySelectorAll('[data-tts-button], .tts-button, [onclick*="playTTS"], [onclick*="textToSpeech"]');

        if (!this.hasAccessToTTS()) {
            console.log('TTS access denied for user, disabling buttons');

            // Disable TTS buttons (but let RBAC handle model selectors)
            ttsButtons.forEach(button => {
                this.disableTTSButton(button);
            });

            // Intercept TTS functions to prevent errors
            this.interceptTTSFunctions();

            // Add restriction notices
            this.addTTSRestrictionNotices();
        } else {
            console.log('TTS access granted for user');

            // Ensure TTS controls are enabled
            ttsButtons.forEach(button => {
                this.enableTTSButton(button);
            });
        }
    }

    disableTTSButton(button) {
        // Don't disable the button visually, but intercept clicks
        button.style.cursor = 'pointer';
        button.title = 'Text-to-Speech requires upgrade - click to see options';

        // Store original onclick if it exists
        if (button.onclick) {
            button.dataset.originalOnclick = button.onclick.toString();
        }

        // Remove original onclick to prevent errors
        button.onclick = null;

        // Add our interceptor as the primary click handler
        button.addEventListener('click', (e) => {
            if (!this.hasAccessToTTS()) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                this.showTTSUpgradeModal();
                return false;
            }
        }, true); // Use capture phase to intercept early

        // Mark button as TTS restricted
        button.dataset.ttsRestricted = 'true';
    }

    enableTTSButton(button) {
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
        button.title = '';
        
        // Restore original onclick if it was stored
        if (button.dataset.originalOnclick) {
            button.onclick = new Function(button.dataset.originalOnclick);
            delete button.dataset.originalOnclick;
        }
    }

    disableTTSSelector(selector) {
        // Mark TTS model options but keep them selectable
        Array.from(selector.options).forEach(option => {
            if (option.value !== '') {  // Keep empty/default option enabled
                option.disabled = false; // Allow selection
                option.style.color = '#999';
                // Only add lock if not already present
                if (!option.textContent.includes('🔒')) {
                    option.textContent = `🔒 ${option.textContent} (Upgrade Required)`;
                }
            }
        });

        selector.title = 'Text-to-Speech models require upgrade - selection will show upgrade prompt';

        // Don't change the current selection - let user select but block usage
    }

    enableTTSSelector(selector) {
        // Enable all options
        Array.from(selector.options).forEach(option => {
            option.disabled = false;
            option.style.color = '';
            // Remove lock icons and upgrade text
            option.textContent = option.textContent
                .replace(/🔒\s*/, '')
                .replace(/\s*\(Upgrade Required\)/, '');
        });

        selector.title = '';
    }

    interceptTTSFunctions() {
        // Intercept common TTS functions to prevent errors
        const originalFunctions = {};

        // List of common TTS function names to intercept
        const ttsFunctionNames = [
            'playTTS',
            'textToSpeech',
            'playAudio',
            'startTTS',
            'generateTTS',
            'synthesizeText',
            'speakText',
            'playText'  // This is the main function causing errors
        ];

        ttsFunctionNames.forEach(funcName => {
            if (window[funcName] && typeof window[funcName] === 'function') {
                // Store original function
                originalFunctions[funcName] = window[funcName];

                // Replace with interceptor
                window[funcName] = (...args) => {
                    if (!this.hasAccessToTTS()) {
                        console.log(`[TTS Access Control] Intercepted ${funcName} call - showing upgrade modal`);
                        this.showTTSUpgradeModal();
                        return Promise.reject(new Error('TTS access denied - upgrade required'));
                    }

                    // Call original function if access is allowed
                    return originalFunctions[funcName].apply(window, args);
                };
            }
        });

        // Store original functions for potential restoration
        this.originalTTSFunctions = originalFunctions;

        // Intercept SyncTTS object methods if they exist
        if (window.syncTTS) {
            this.interceptSyncTTSMethods();
        }

        // Also intercept the global playText function specifically
        this.interceptPlayTextFunction();

        // Intercept TTS API calls at the fetch level
        this.interceptTTSAPIRequests();
    }

    interceptSyncTTSMethods() {
        // Intercept syncTTS object methods (not class prototype)
        const syncTTSObj = window.syncTTS;

        if (syncTTSObj && syncTTSObj.play) {
            const originalPlay = syncTTSObj.play;
            syncTTSObj.play = (...args) => {
                if (!this.hasAccessToTTS()) {
                    console.log('[TTS Access Control] Intercepted syncTTS.play - showing upgrade modal');
                    this.showTTSUpgradeModal();
                    return;
                }
                return originalPlay.apply(syncTTSObj, args);
            };
        }

        if (syncTTSObj && syncTTSObj.stop) {
            // Don't intercept stop - always allow stopping
        }
    }

    interceptPlayTextFunction() {
        // This is the main function that's causing the errors
        // It's defined in sync-tts.js and called by button clicks

        // Wait for the function to be defined, then intercept it
        const checkAndIntercept = () => {
            if (window.playText && typeof window.playText === 'function') {
                if (!window.playText._intercepted) {
                    const originalPlayText = window.playText;

                    window.playText = (elementId) => {
                        if (!window.ttsAccessControl.hasAccessToTTS()) {
                            console.log('[TTS Access Control] Intercepted playText call - showing upgrade modal');
                            window.ttsAccessControl.showTTSUpgradeModal();
                            return;
                        }
                        return originalPlayText.call(window, elementId);
                    };

                    // Mark as intercepted to avoid double interception
                    window.playText._intercepted = true;
                    console.log('[TTS Access Control] Successfully intercepted playText function');
                }
            } else {
                // Try again in 100ms if function not yet defined
                setTimeout(checkAndIntercept, 100);
            }
        };

        // Start checking immediately and also after a delay
        checkAndIntercept();
        setTimeout(checkAndIntercept, 500);
        setTimeout(checkAndIntercept, 1000);
        setTimeout(checkAndIntercept, 2000);
    }

    interceptTTSAPIRequests() {
        // Intercept fetch requests to TTS API endpoints
        try {
            // Use a safer approach to check if already intercepted
            if (this._ttsInterceptionApplied) {
                console.log('[TTS Access Control] Fetch already intercepted for TTS API requests');
                return;
            }

            // Store original fetch with proper binding - use the safe validator's original if available
            let originalFetch;
            try {
                if (window.fetchFixValidatorSafe && typeof window.fetchFixValidatorSafe.getOriginalFetch === 'function') {
                    originalFetch = window.fetchFixValidatorSafe.getOriginalFetch();
                    console.log('[TTS Access Control] Using fetch-fix-validator-safe original fetch');
                } else if (window.fetchFixValidator && typeof window.fetchFixValidator.getOriginalFetch === 'function') {
                    originalFetch = window.fetchFixValidator.getOriginalFetch();
                    console.log('[TTS Access Control] Using fetch-fix-validator original fetch');
                } else {
                    // Safely get current fetch without triggering property access issues
                    originalFetch = window.fetch.bind(window);
                    console.log('[TTS Access Control] Using current window.fetch');
                }
            } catch (fetchAccessError) {
                console.warn('[TTS Access Control] Could not safely access fetch, skipping interception:', fetchAccessError);
                return;
            }

            const ttsInterceptedFetch = async (url, options = {}) => {
                try {
                    // Check if this is a TTS API request
                    if (typeof url === 'string' && url.includes('/api/tts')) {
                        if (!this.hasAccessToTTS()) {
                            console.log('[TTS Access Control] Intercepted TTS API request - showing upgrade modal');
                            this.showTTSUpgradeModal();

                            // Return a rejected promise to prevent the request
                            return Promise.reject(new Error('TTS access denied - upgrade required'));
                        }
                    }

                    // Call original fetch for allowed requests - ensure proper context
                    return originalFetch(url, options);
                } catch (error) {
                    console.error('[TTS Access Control] Error in fetch override:', error);
                    // Fallback to original fetch if override fails
                    return originalFetch(url, options);
                }
            };

            // Mark as intercepted on the instance to avoid property access issues
            this._ttsInterceptionApplied = true;

            // Apply the override safely
            try {
                window.fetch = ttsInterceptedFetch;
                console.log('[TTS Access Control] Successfully intercepted fetch for TTS API requests');
            } catch (assignmentError) {
                console.error('[TTS Access Control] Could not assign fetch override:', assignmentError);
                this._ttsInterceptionApplied = false;
            }

        } catch (error) {
            console.error('[TTS Access Control] Error setting up fetch interception:', error);
            // Don't throw - just log the error and continue
        }
    }

    addTTSRestrictionNotices() {
        // Add notices near TTS controls
        const ttsContainers = document.querySelectorAll('.tts-container, .tts-section, [data-tts-container]');

        ttsContainers.forEach(container => {
            if (!container.querySelector('.tts-restriction-notice')) {
                const notice = document.createElement('div');
                notice.className = 'tts-restriction-notice alert alert-info';
                notice.style.cssText = `
                    background: #e3f2fd;
                    border: 1px solid #2196f3;
                    color: #1976d2;
                    padding: 0.75rem;
                    border-radius: 8px;
                    margin: 0.5rem 0;
                    font-size: 0.9rem;
                `;
                notice.innerHTML = `
                    <i class="fas fa-info-circle"></i>
                    <strong>Text-to-Speech Upgrade Required</strong><br>
                    TTS features are available with Basic and Professional plans.
                    <a href="#" onclick="ttsAccessControl.showTTSUpgradeModal()" style="color: #1976d2; text-decoration: underline;">Learn more</a>
                `;

                container.insertBefore(notice, container.firstChild);
            }
        });
    }

    setupEventListeners() {
        // Listen for TTS-related events
        document.addEventListener('click', (event) => {
            const target = event.target;

            // Check if this is a TTS-related action
            if (this.isTTSAction(target) && !this.hasAccessToTTS()) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                this.showTTSUpgradeModal();
                return false;
            }
        }, true); // Use capture phase to intercept early

        // Intercept audio play events that might be TTS-related
        document.addEventListener('play', (event) => {
            const audio = event.target;

            // Check if this audio element is TTS-related
            if (this.isTTSAudio(audio) && !this.hasAccessToTTS()) {
                event.preventDefault();
                event.stopPropagation();
                audio.pause();
                this.showTTSUpgradeModal();
                return false;
            }
        }, true);

        // Model selector changes are handled by RBAC access control
        // This ensures consistent behavior across all model types
    }

    isTTSAction(element) {
        // Check if element or its attributes indicate TTS functionality
        const ttsIndicators = [
            'data-tts-button',
            'tts-button',
            'playTTS',
            'textToSpeech',
            'text-to-speech'
        ];

        return ttsIndicators.some(indicator =>
            element.classList.contains(indicator) ||
            element.hasAttribute(indicator) ||
            (element.onclick && element.onclick.toString().includes(indicator)) ||
            element.id.includes('tts') ||
            element.className.includes('tts')
        );
    }

    isTTSAudio(audioElement) {
        // Check if audio element is TTS-related
        if (!audioElement || audioElement.tagName !== 'AUDIO') {
            return false;
        }

        // Check various indicators that this is TTS audio
        const ttsIndicators = [
            'tts',
            'text-to-speech',
            'synthesis',
            'generated'
        ];

        return ttsIndicators.some(indicator =>
            audioElement.id.toLowerCase().includes(indicator) ||
            audioElement.className.toLowerCase().includes(indicator) ||
            (audioElement.src && audioElement.src.toLowerCase().includes(indicator)) ||
            audioElement.dataset.type === 'tts' ||
            audioElement.dataset.source === 'tts'
        );
    }

    showTTSUpgradeModal() {
        // Don't show modal for admin or super users
        if (this.userRole === 'admin' || this.userRole === 'super_user') {
            return;
        }

        // Use the enhanced RBAC modal instead for consistency
        if (window.rbacAccessControl) {
            // Create a dummy TTS model to trigger the enhanced modal
            window.rbacAccessControl.showUpgradeModal('gemini-2.5-flash-tts');
        } else {
            // Fallback to simple modal if RBAC not available
            this.showSimpleTTSModal();
        }
    }

    showSimpleTTSModal() {
        const modalHtml = `
            <div id="tts-upgrade-modal" class="modal-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
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
                        <h2 style="margin: 0 0 1rem 0; color: #333;">Text-to-Speech Not Available</h2>
                        <p style="margin-bottom: 1.5rem; color: #666;">
                            Text-to-Speech features are not included in the <strong>Free Plan</strong>.
                        </p>
                        <p style="margin-bottom: 2rem; color: #666;">
                            Upgrade to <strong>Basic</strong> or <strong>Professional</strong> plan to access TTS features.
                        </p>
                        <div style="display: flex; gap: 1rem; justify-content: center;">
                            <button id="tts-close-modal-btn" style="
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

        // Remove existing modal if present
        this.closeTTSUpgradeModal();

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Setup event listeners
        const closeBtn = document.getElementById('tts-close-modal-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeTTSUpgradeModal();
            });
        }

        // Close on overlay click
        const modal = document.getElementById('tts-upgrade-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'tts-upgrade-modal') {
                    this.closeTTSUpgradeModal();
                }
            });
        }
    }

    closeTTSUpgradeModal() {
        const modal = document.getElementById('tts-upgrade-modal');
        if (modal) {
            modal.remove();
        }

        // Also try to close RBAC modal if it's open
        if (window.rbacAccessControl) {
            window.rbacAccessControl.closeUpgradeModal();
        }
    }

    // Public method to validate TTS access before API calls
    validateTTSAccess() {
        if (!this.hasAccessToTTS()) {
            return {
                allowed: false,
                error: {
                    code: 'tts_access_denied',
                    message: 'Text-to-Speech is not available on the Free Plan',
                    upgrade_required: true
                }
            };
        }

        return { allowed: true };
    }
}

// Initialize TTS access control as early as possible
(function() {
    // Create the TTS access control instance immediately
    window.ttsAccessControl = new TTSAccessControl();

    // Set up event listeners immediately
    window.ttsAccessControl.setupEventListeners();

    // Set up TTS controls when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ttsAccessControl.setupTTSControls();
        });
    } else {
        // DOM is already ready
        window.ttsAccessControl.setupTTSControls();
    }

    // Also set up controls after other scripts have loaded
    setTimeout(() => {
        window.ttsAccessControl.setupTTSControls();
    }, 500);

    setTimeout(() => {
        window.ttsAccessControl.setupTTSControls();
    }, 1500);
})();

// Export for use in other scripts
window.TTSAccessControl = TTSAccessControl;
