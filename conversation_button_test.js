/**
 * Conversation Button Test Script
 * Run this in the browser console to test the conversation button functionality
 */

console.log('🧪 Starting Conversation Button Test...');

// Test 1: Check if button exists
function testButtonExists() {
    console.log('\n1️⃣ Testing if conversation button exists...');
    const button = document.getElementById('conversation-button');
    if (button) {
        console.log('✅ Button found:', button);
        console.log('   - ID:', button.id);
        console.log('   - Classes:', button.className);
        console.log('   - Text:', button.textContent.trim());
        return true;
    } else {
        console.log('❌ Button NOT found');
        return false;
    }
}

// Test 2: Check button properties
function testButtonProperties() {
    console.log('\n2️⃣ Testing button properties...');
    const button = document.getElementById('conversation-button');
    if (!button) return false;
    
    const rect = button.getBoundingClientRect();
    const style = window.getComputedStyle(button);
    
    console.log('📏 Button dimensions:', {
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left
    });
    
    console.log('🎨 Button styles:', {
        display: style.display,
        visibility: style.visibility,
        pointerEvents: style.pointerEvents,
        zIndex: style.zIndex,
        position: style.position
    });
    
    const isVisible = rect.width > 0 && rect.height > 0;
    const isClickable = style.pointerEvents !== 'none';
    
    if (isVisible && isClickable) {
        console.log('✅ Button is visible and clickable');
        return true;
    } else {
        console.log('❌ Button has issues:', { visible: isVisible, clickable: isClickable });
        return false;
    }
}

// Test 3: Check if modal exists
function testModalExists() {
    console.log('\n3️⃣ Testing if conversation modal exists...');
    const modal = document.getElementById('conversation-modal');
    if (modal) {
        console.log('✅ Modal found:', modal);
        console.log('   - ID:', modal.id);
        console.log('   - Classes:', modal.className);
        console.log('   - Current display:', modal.style.display);
        return true;
    } else {
        console.log('❌ Modal NOT found');
        return false;
    }
}

// Test 4: Test button click
function testButtonClick() {
    console.log('\n4️⃣ Testing button click...');
    const button = document.getElementById('conversation-button');
    if (!button) return false;
    
    console.log('🖱️ Simulating button click...');
    
    // Add a temporary listener to detect the click
    let clickDetected = false;
    const testListener = function(e) {
        clickDetected = true;
        console.log('✅ Click event detected!', e);
    };
    
    button.addEventListener('click', testListener);
    
    // Trigger the click
    button.click();
    
    // Clean up
    button.removeEventListener('click', testListener);
    
    if (clickDetected) {
        console.log('✅ Button click works');
        return true;
    } else {
        console.log('❌ Button click failed');
        return false;
    }
}

// Test 5: Test modal opening function
function testModalFunction() {
    console.log('\n5️⃣ Testing modal opening function...');
    
    if (typeof openConversationModal === 'function') {
        console.log('✅ openConversationModal function exists');
        console.log('🚀 Attempting to open modal...');
        
        try {
            openConversationModal(true);
            console.log('✅ Modal function executed successfully');
            return true;
        } catch (error) {
            console.log('❌ Error calling modal function:', error);
            return false;
        }
    } else {
        console.log('❌ openConversationModal function NOT found');
        return false;
    }
}

// Run all tests
function runAllTests() {
    console.log('🧪 CONVERSATION BUTTON DIAGNOSTIC TEST');
    console.log('=====================================');
    
    const results = {
        buttonExists: testButtonExists(),
        buttonProperties: testButtonProperties(),
        modalExists: testModalExists(),
        buttonClick: testButtonClick(),
        modalFunction: testModalFunction()
    };
    
    console.log('\n📊 TEST RESULTS:');
    console.log('================');
    Object.entries(results).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASS' : 'FAIL'}`);
    });
    
    const passedCount = Object.values(results).filter(Boolean).length;
    const totalCount = Object.keys(results).length;
    
    console.log(`\n🏁 SUMMARY: ${passedCount}/${totalCount} tests passed`);
    
    if (passedCount === totalCount) {
        console.log('🎉 ALL TESTS PASSED! The conversation button should be working.');
    } else {
        console.log('⚠️ Some tests failed. Check the issues above.');
    }
    
    return results;
}

// Auto-run tests
runAllTests();

// Export for manual use
window.conversationButtonTest = {
    runAllTests,
    testButtonExists,
    testButtonProperties,
    testModalExists,
    testButtonClick,
    testModalFunction
};

console.log('\n💡 You can run individual tests by calling:');
console.log('   conversationButtonTest.testButtonExists()');
console.log('   conversationButtonTest.testButtonClick()');
console.log('   conversationButtonTest.runAllTests()');
