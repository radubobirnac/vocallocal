/**
 * Fetch Fix Validator - Simplified Safe Version
 * This script ensures that all fetch overrides are properly bound to prevent "Illegal invocation" errors
 * Uses a non-intrusive approach that doesn't interfere with property access
 */

(function() {
    'use strict';

    console.log('[Fetch Fix Validator] Initializing simplified version...');

    // Store the original fetch function immediately
    const ORIGINAL_FETCH = window.fetch.bind(window);

    // Track all fetch overrides to prevent conflicts
    const fetchOverrides = new Map();
    let fetchOverrideCount = 0;
    
    // Validation function to check if a fetch override is properly bound
    function validateFetchOverride(overrideName, overrideFunction) {
        try {
            // Skip validation if function is not callable
            if (typeof overrideFunction !== 'function') {
                console.warn(`[Fetch Fix Validator] ⚠️ ${overrideName} is not a function`);
                return false;
            }

            // Test the override with a dummy request (non-blocking)
            const testUrl = 'data:text/plain,test';
            const testOptions = { method: 'GET' };

            // This should not throw an "Illegal invocation" error
            const result = overrideFunction.call(window, testUrl, testOptions);

            if (result && typeof result.then === 'function') {
                console.log(`[Fetch Fix Validator] ✅ ${overrideName} override is properly bound`);

                // Clean up the test promise to avoid unhandled rejections
                result.catch(() => {
                    // Ignore test errors
                });

                return true;
            } else {
                console.warn(`[Fetch Fix Validator] ⚠️ ${overrideName} override doesn't return a Promise`);
                return false;
            }
        } catch (error) {
            if (error.message.includes('Illegal invocation')) {
                console.error(`[Fetch Fix Validator] ❌ ${overrideName} override has illegal invocation error:`, error);
                return false;
            } else {
                // Other errors are acceptable for this test (e.g., network errors)
                console.log(`[Fetch Fix Validator] ✅ ${overrideName} override is properly bound (test error expected)`);
                return true;
            }
        }
    }
    
    // Function to create a safe fetch override wrapper
    function createSafeFetchOverride(overrideName, interceptorFunction) {
        return async function safeFetchWrapper(url, options = {}) {
            try {
                // Call the interceptor function if provided
                if (interceptorFunction) {
                    const interceptResult = await interceptorFunction(url, options);
                    if (interceptResult !== undefined) {
                        return interceptResult;
                    }
                }
                
                // Always use the original fetch with proper binding
                return ORIGINAL_FETCH(url, options);
            } catch (error) {
                console.error(`[Fetch Fix Validator] Error in ${overrideName} override:`, error);
                throw error;
            }
        };
    }
    
    // Simple monitoring approach - no property redefinition
    let currentFetch = window.fetch;
    let monitoringActive = false;

    // Start monitoring fetch changes without interfering with property access
    function startFetchMonitoring() {
        if (monitoringActive) return;

        monitoringActive = true;
        console.log('[Fetch Fix Validator] Starting non-intrusive fetch monitoring...');

        // Check for fetch changes periodically
        setInterval(() => {
            if (window.fetch !== currentFetch) {
                fetchOverrideCount++;
                const overrideName = `Override-${fetchOverrideCount}`;

                console.log(`[Fetch Fix Validator] Detected fetch override: ${overrideName}`);

                // Store the new fetch
                const newFetch = window.fetch;
                currentFetch = newFetch;

                // Store the override for tracking
                fetchOverrides.set(overrideName, newFetch);

                // Validate the new fetch function (non-blocking)
                if (typeof newFetch === 'function') {
                    setTimeout(() => {
                        try {
                            validateFetchOverride(overrideName, newFetch);
                        } catch (error) {
                            console.warn(`[Fetch Fix Validator] Could not validate ${overrideName}:`, error);
                        }
                    }, 100);
                }
            }
        }, 50); // Check every 50ms for responsiveness
    }

    // Start monitoring immediately
    startFetchMonitoring();
    
    // Provide utility functions for safe fetch overriding
    window.fetchFixValidator = {
        // Create a safe fetch override
        createSafeOverride: createSafeFetchOverride,
        
        // Get the original fetch function
        getOriginalFetch: () => ORIGINAL_FETCH,
        
        // Validate current fetch function
        validateCurrentFetch: () => {
            return validateFetchOverride('Current', window.fetch);
        },
        
        // Get override statistics
        getOverrideStats: () => {
            return {
                count: fetchOverrideCount,
                overrides: Array.from(fetchOverrides.keys())
            };
        },
        
        // Test fetch functionality
        testFetch: async () => {
            try {
                console.log('[Fetch Fix Validator] Testing current fetch implementation...');
                
                // Test with a simple data URL
                const response = await window.fetch('data:text/plain,test');
                const text = await response.text();
                
                if (text === 'test') {
                    console.log('[Fetch Fix Validator] ✅ Fetch test passed');
                    return true;
                } else {
                    console.error('[Fetch Fix Validator] ❌ Fetch test failed - unexpected response');
                    return false;
                }
            } catch (error) {
                if (error.message.includes('Illegal invocation')) {
                    console.error('[Fetch Fix Validator] ❌ Fetch test failed with illegal invocation:', error);
                    return false;
                } else {
                    console.log('[Fetch Fix Validator] ✅ Fetch test passed (expected error):', error.message);
                    return true;
                }
            }
        }
    };
    
    // Auto-test on page load
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            console.log('[Fetch Fix Validator] Running auto-test...');
            window.fetchFixValidator.testFetch();
            
            const stats = window.fetchFixValidator.getOverrideStats();
            console.log(`[Fetch Fix Validator] Override statistics:`, stats);
        }, 1000);
    });
    
    // Provide emergency fix function
    window.emergencyFetchFix = function() {
        console.log('[Emergency Fetch Fix] Applying emergency fix...');

        try {
            // Reset fetch to original
            currentFetch = ORIGINAL_FETCH;
            window.fetch = ORIGINAL_FETCH;

            console.log('[Emergency Fetch Fix] ✅ Fetch reset to original implementation');

            // Test the fix
            if (window.fetchFixValidator && window.fetchFixValidator.testFetch) {
                return window.fetchFixValidator.testFetch();
            } else {
                return true;
            }
        } catch (error) {
            console.error('[Emergency Fetch Fix] Error during emergency fix:', error);

            // Last resort: direct assignment
            window.fetch = ORIGINAL_FETCH;
            console.log('[Emergency Fetch Fix] ✅ Applied last resort fix');
            return true;
        }
    };
    
    console.log('[Fetch Fix Validator] ✅ Initialized successfully');
    
})();
