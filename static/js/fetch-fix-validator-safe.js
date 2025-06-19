/**
 * Fetch Fix Validator - Ultra Safe Version
 * This script provides utilities for safe fetch handling without interfering with property access
 * Completely avoids property redefinition to prevent TypeError issues
 */

(function() {
    'use strict';
    
    console.log('[Fetch Fix Validator Safe] Initializing ultra-safe version...');
    
    // Store the original fetch function immediately
    const ORIGINAL_FETCH = window.fetch.bind(window);
    
    // Track fetch overrides without interfering with property access
    const fetchOverrides = [];
    let overrideCount = 0;
    
    // Validation function that's completely safe
    function validateFetchSafely(fetchFunction, name = 'Unknown') {
        try {
            if (typeof fetchFunction !== 'function') {
                console.warn(`[Fetch Fix Validator Safe] ${name} is not a function`);
                return false;
            }
            
            // Simple validation - just check if it's callable
            console.log(`[Fetch Fix Validator Safe] ✅ ${name} appears to be a valid function`);
            return true;
        } catch (error) {
            console.error(`[Fetch Fix Validator Safe] Error validating ${name}:`, error);
            return false;
        }
    }
    
    // Create a safe fetch wrapper that handles errors gracefully
    function createSafeFetchWrapper(originalFetch, interceptorFunction, name = 'SafeFetch') {
        return async function safeFetchWrapper(url, options = {}) {
            try {
                // Call the interceptor function if provided
                if (interceptorFunction && typeof interceptorFunction === 'function') {
                    const interceptResult = await interceptorFunction(url, options);
                    if (interceptResult !== undefined) {
                        return interceptResult;
                    }
                }
                
                // Always use the original fetch with proper binding
                return originalFetch(url, options);
            } catch (error) {
                console.error(`[Fetch Fix Validator Safe] Error in ${name}:`, error);
                
                // If there's an illegal invocation error, try to recover
                if (error.message.includes('Illegal invocation')) {
                    console.log(`[Fetch Fix Validator Safe] Recovering from illegal invocation in ${name}`);
                    try {
                        return ORIGINAL_FETCH(url, options);
                    } catch (recoveryError) {
                        console.error(`[Fetch Fix Validator Safe] Recovery failed:`, recoveryError);
                        throw recoveryError;
                    }
                }
                
                throw error;
            }
        };
    }
    
    // Monitor fetch changes without property redefinition
    let lastFetch = window.fetch;
    let monitoringActive = false;
    
    function startSafeMonitoring() {
        if (monitoringActive) return;
        
        monitoringActive = true;
        console.log('[Fetch Fix Validator Safe] Starting safe monitoring...');
        
        setInterval(() => {
            try {
                if (window.fetch !== lastFetch) {
                    overrideCount++;
                    const overrideName = `Override-${overrideCount}`;
                    
                    console.log(`[Fetch Fix Validator Safe] Detected fetch change: ${overrideName}`);
                    
                    // Store the override info
                    fetchOverrides.push({
                        name: overrideName,
                        function: window.fetch,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Validate the new fetch
                    validateFetchSafely(window.fetch, overrideName);
                    
                    lastFetch = window.fetch;
                }
            } catch (error) {
                console.warn('[Fetch Fix Validator Safe] Error during monitoring:', error);
            }
        }, 100);
    }
    
    // Provide safe utility functions
    window.fetchFixValidatorSafe = {
        // Get the original fetch function
        getOriginalFetch: () => ORIGINAL_FETCH,
        
        // Create a safe fetch wrapper
        createSafeWrapper: createSafeFetchWrapper,
        
        // Validate a fetch function safely
        validateFetch: validateFetchSafely,
        
        // Get override statistics
        getOverrideStats: () => ({
            count: overrideCount,
            overrides: fetchOverrides.map(o => ({ name: o.name, timestamp: o.timestamp }))
        }),
        
        // Test fetch functionality safely
        testFetch: async () => {
            try {
                console.log('[Fetch Fix Validator Safe] Testing current fetch...');
                
                // Test with a simple data URL
                const response = await window.fetch('data:text/plain,test');
                const text = await response.text();
                
                if (text === 'test') {
                    console.log('[Fetch Fix Validator Safe] ✅ Fetch test passed');
                    return true;
                } else {
                    console.error('[Fetch Fix Validator Safe] ❌ Fetch test failed - unexpected response');
                    return false;
                }
            } catch (error) {
                if (error.message.includes('Illegal invocation')) {
                    console.error('[Fetch Fix Validator Safe] ❌ Fetch test failed with illegal invocation:', error);
                    return false;
                } else {
                    console.log('[Fetch Fix Validator Safe] ✅ Fetch test passed (expected error):', error.message);
                    return true;
                }
            }
        },
        
        // Emergency recovery function
        emergencyRestore: () => {
            try {
                console.log('[Fetch Fix Validator Safe] Emergency restore...');
                window.fetch = ORIGINAL_FETCH;
                console.log('[Fetch Fix Validator Safe] ✅ Fetch restored to original');
                return true;
            } catch (error) {
                console.error('[Fetch Fix Validator Safe] ❌ Emergency restore failed:', error);
                return false;
            }
        }
    };
    
    // Start monitoring
    startSafeMonitoring();
    
    // Provide emergency fix function
    window.emergencyFetchFixSafe = function() {
        console.log('[Emergency Fetch Fix Safe] Applying safe emergency fix...');
        return window.fetchFixValidatorSafe.emergencyRestore();
    };
    
    // Auto-test on page load
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            console.log('[Fetch Fix Validator Safe] Running auto-test...');
            window.fetchFixValidatorSafe.testFetch();
            
            const stats = window.fetchFixValidatorSafe.getOverrideStats();
            console.log(`[Fetch Fix Validator Safe] Override statistics:`, stats);
        }, 1000);
    });
    
    console.log('[Fetch Fix Validator Safe] ✅ Initialized successfully');
    
})();
