/**
 * Conversation Button Debug Script
 * 
 * Copy and paste this entire script into your browser console
 * when you have the VocalLocal application open at http://localhost:5001
 * 
 * This will diagnose why the conversation button is not responding
 */

console.log('🔧 Starting Conversation Button Debug Analysis...');
console.log('================================================');

// Helper function for colored console output
function debugLog(message, type = 'info') {
    const styles = {
        info: 'color: #2196F3; font-weight: bold;',
        success: 'color: #4CAF50; font-weight: bold;',
        error: 'color: #F44336; font-weight: bold;',
        warn: 'color: #FF9800; font-weight: bold;'
    };
    console.log(`%c${message}`, styles[type] || styles.info);
}

// Test 1: Check if button element exists
function testButtonExists() {
    debugLog('\n🔍 Test 1: Checking if conversation button exists...', 'info');
    
    const button = document.getElementById('conversation-button');
    if (button) {
        debugLog('✅ SUCCESS: Conversation button found!', 'success');
        console.log('Button element:', button);
        return button;
    } else {
        debugLog('❌ FAILED: Conversation button NOT found!', 'error');
        debugLog('Searching for similar elements...', 'warn');
        
        // Search for buttons with similar classes or text
        const allButtons = document.querySelectorAll('button');
        const chatButtons = Array.from(allButtons).filter(btn => 
            btn.textContent.toLowerCase().includes('chat') ||
            btn.textContent.toLowerCase().includes('conversation') ||
            btn.className.includes('conversation')
        );
        
        if (chatButtons.length > 0) {
            debugLog(`Found ${chatButtons.length} similar button(s):`, 'warn');
            chatButtons.forEach((btn, index) => {
                console.log(`Button ${index + 1}:`, btn);
            });
        } else {
            debugLog('No similar buttons found', 'error');
        }
        return null;
    }
}

// Test 2: Check button properties and styles
function testButtonProperties(button) {
    if (!button) return false;
    
    debugLog('\n🎨 Test 2: Checking button properties and styles...', 'info');
    
    const computedStyle = window.getComputedStyle(button);
    const rect = button.getBoundingClientRect();
    
    console.log('Button computed styles:', {
        display: computedStyle.display,
        visibility: computedStyle.visibility,
        pointerEvents: computedStyle.pointerEvents,
        zIndex: computedStyle.zIndex,
        position: computedStyle.position,
        opacity: computedStyle.opacity
    });
    
    console.log('Button position and size:', {
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        visible: rect.width > 0 && rect.height > 0
    });
    
    // Check if button is visible and clickable
    const isVisible = rect.width > 0 && rect.height > 0 && computedStyle.visibility !== 'hidden' && computedStyle.opacity !== '0';
    const isClickable = computedStyle.pointerEvents !== 'none';
    
    if (isVisible && isClickable) {
        debugLog('✅ SUCCESS: Button is visible and clickable!', 'success');
        return true;
    } else {
        debugLog(`❌ FAILED: Button visibility/clickability issues!`, 'error');
        debugLog(`Visible: ${isVisible}, Clickable: ${isClickable}`, 'error');
        return false;
    }
}

// Test 3: Check event listeners
function testEventListeners(button) {
    if (!button) return false;
    
    debugLog('\n👂 Test 3: Checking event listeners...', 'info');
    
    // Check if getEventListeners is available (Chrome DevTools)
    if (typeof getEventListeners === 'function') {
        const listeners = getEventListeners(button);
        console.log('Event listeners:', listeners);
        
        if (listeners.click && listeners.click.length > 0) {
            debugLog(`✅ SUCCESS: Found ${listeners.click.length} click listener(s)!`, 'success');
            return true;
        } else {
            debugLog('❌ FAILED: No click event listeners found!', 'error');
            return false;
        }
    } else {
        debugLog('⚠️ WARNING: getEventListeners not available (open Chrome DevTools)', 'warn');
        debugLog('Cannot check existing event listeners', 'warn');
        return null;
    }
}

// Test 4: Check if modal element exists
function testModalExists() {
    debugLog('\n🪟 Test 4: Checking if conversation modal exists...', 'info');
    
    const modal = document.getElementById('conversation-modal');
    if (modal) {
        debugLog('✅ SUCCESS: Conversation modal found!', 'success');
        console.log('Modal element:', modal);
        return modal;
    } else {
        debugLog('❌ FAILED: Conversation modal NOT found!', 'error');
        return null;
    }
}

// Test 5: Check JavaScript variables and functions
function testJavaScriptState() {
    debugLog('\n🔧 Test 5: Checking JavaScript state...', 'info');
    
    // Check if conversation modal functions exist
    const functions = ['openConversationModal', 'closeConversationModal', 'conversationModalInitialized'];
    const results = {};
    
    functions.forEach(funcName => {
        if (typeof window[funcName] !== 'undefined') {
            results[funcName] = typeof window[funcName];
            debugLog(`✅ ${funcName}: ${typeof window[funcName]}`, 'success');
        } else {
            results[funcName] = 'undefined';
            debugLog(`❌ ${funcName}: undefined`, 'error');
        }
    });
    
    // Check conversationModalInitialized value
    if (typeof conversationModalInitialized !== 'undefined') {
        debugLog(`conversationModalInitialized = ${conversationModalInitialized}`, 'info');
    }
    
    return results;
}

// Test 6: Try to manually trigger the modal
function testManualTrigger() {
    debugLog('\n🚀 Test 6: Attempting manual modal trigger...', 'info');
    
    try {
        if (typeof openConversationModal === 'function') {
            debugLog('Calling openConversationModal(true)...', 'info');
            openConversationModal(true);
            debugLog('✅ SUCCESS: Manual trigger executed!', 'success');
            return true;
        } else {
            debugLog('❌ FAILED: openConversationModal function not found!', 'error');
            return false;
        }
    } catch (error) {
        debugLog(`❌ FAILED: Error calling openConversationModal: ${error.message}`, 'error');
        console.error(error);
        return false;
    }
}

// Test 7: Add a manual click listener
function testManualClickListener(button) {
    if (!button) return false;
    
    debugLog('\n👆 Test 7: Adding manual click listener...', 'info');
    
    try {
        button.addEventListener('click', function(event) {
            debugLog('🎉 MANUAL CLICK DETECTED!', 'success');
            console.log('Click event:', event);
            
            // Try to open modal manually
            if (typeof openConversationModal === 'function') {
                debugLog('Opening modal via manual listener...', 'info');
                openConversationModal(true);
            } else {
                debugLog('openConversationModal function not available', 'warn');
                // Fallback: try to show modal directly
                const modal = document.getElementById('conversation-modal');
                if (modal) {
                    modal.style.display = 'flex';
                    debugLog('Modal shown via direct manipulation', 'success');
                }
            }
        });
        
        debugLog('✅ SUCCESS: Manual click listener added!', 'success');
        debugLog('Try clicking the button now!', 'info');
        return true;
    } catch (error) {
        debugLog(`❌ FAILED: Error adding click listener: ${error.message}`, 'error');
        console.error(error);
        return false;
    }
}

// Main diagnostic function
function runConversationButtonDiagnostic() {
    debugLog('🔬 Running comprehensive conversation button diagnostic...', 'info');
    
    const results = {
        buttonExists: false,
        buttonProperties: false,
        eventListeners: null,
        modalExists: false,
        javascriptState: {},
        manualTrigger: false,
        manualListener: false
    };
    
    // Run all tests
    const button = testButtonExists();
    results.buttonExists = !!button;
    
    if (button) {
        results.buttonProperties = testButtonProperties(button);
        results.eventListeners = testEventListeners(button);
        results.manualListener = testManualClickListener(button);
    }
    
    const modal = testModalExists();
    results.modalExists = !!modal;
    
    results.javascriptState = testJavaScriptState();
    results.manualTrigger = testManualTrigger();
    
    // Summary
    debugLog('\n📊 DIAGNOSTIC SUMMARY:', 'info');
    debugLog('==================', 'info');
    
    Object.entries(results).forEach(([test, result]) => {
        const status = result === true ? '✅ PASS' : result === false ? '❌ FAIL' : '⚠️ WARN';
        debugLog(`${test}: ${status}`, result === true ? 'success' : result === false ? 'error' : 'warn');
    });
    
    // Recommendations
    debugLog('\n💡 RECOMMENDATIONS:', 'info');
    debugLog('==================', 'info');
    
    if (!results.buttonExists) {
        debugLog('1. Check if you\'re on the correct page with the conversation button', 'error');
        debugLog('2. Verify the button HTML is properly rendered', 'error');
    } else if (!results.buttonProperties) {
        debugLog('1. Check CSS styles that might be hiding or disabling the button', 'warn');
        debugLog('2. Look for z-index issues or overlapping elements', 'warn');
    } else if (results.eventListeners === false) {
        debugLog('1. Check if conversation-modal.js is loading properly', 'error');
        debugLog('2. Look for JavaScript errors in console', 'error');
        debugLog('3. Manual click listener has been added - try clicking now!', 'success');
    } else if (!results.modalExists) {
        debugLog('1. Check if the modal HTML is present in the page', 'error');
        debugLog('2. Verify the modal template is being rendered', 'error');
    } else {
        debugLog('1. Try the manual trigger test above', 'info');
        debugLog('2. Check browser console for any JavaScript errors', 'info');
        debugLog('3. Manual click listener added - button should work now!', 'success');
    }
    
    return results;
}

// Auto-run the diagnostic
runConversationButtonDiagnostic();

// Provide helper functions for manual testing
debugLog('\n🛠️ HELPER FUNCTIONS AVAILABLE:', 'info');
debugLog('================================', 'info');
debugLog('runConversationButtonDiagnostic() - Run full diagnostic again', 'info');
debugLog('testButtonExists() - Check if button exists', 'info');
debugLog('testModalExists() - Check if modal exists', 'info');
debugLog('testManualTrigger() - Try to open modal manually', 'info');

console.log('\n🎯 If the button still doesn\'t work after this diagnostic,');
console.log('please share the diagnostic summary results!');
