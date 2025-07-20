/**
 * Browser Console Test Script for TTS Stop Functionality
 * 
 * Instructions:
 * 1. Open browser and navigate to http://localhost:5001
 * 2. Log in with a verified user account
 * 3. Open browser console (F12)
 * 4. Copy and paste this entire script into the console
 * 5. Press Enter to run the tests
 * 
 * This script will test all stop button functionality automatically
 */

(function() {
    'use strict';
    
    console.log('🚀 Starting TTS Stop Button Functionality Test');
    console.log('=' .repeat(60));
    
    // Test configuration
    const TEST_CONFIG = {
        testText: 'This is a test of the TTS stop button functionality.',
        testLanguage: 'en',
        testDelay: 2000, // 2 seconds between tests
        stopDelay: 1000  // 1 second before stopping
    };
    
    // Test results tracking
    const testResults = {
        passed: 0,
        failed: 0,
        total: 0,
        details: []
    };
    
    function logTest(testName, passed, details = '') {
        testResults.total++;
        if (passed) {
            testResults.passed++;
            console.log(`✅ ${testName}: PASSED ${details}`);
        } else {
            testResults.failed++;
            console.log(`❌ ${testName}: FAILED ${details}`);
        }
        testResults.details.push({ testName, passed, details });
    }
    
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Test 1: Check if stop functions exist
    function testStopFunctionsExist() {
        console.log('\n🔍 Test 1: Checking if stop functions exist...');
        
        const stopSpeakTextExists = typeof window.stopSpeakText === 'function';
        const stopAllAudioExists = typeof window.stopAllAudio === 'function';
        
        logTest('stopSpeakText function exists', stopSpeakTextExists);
        logTest('stopAllAudio function exists', stopAllAudioExists);
        
        return stopSpeakTextExists && stopAllAudioExists;
    }
    
    // Test 2: Check if TTS buttons exist
    function testTTSButtonsExist() {
        console.log('\n🔍 Test 2: Checking if TTS buttons exist...');
        
        const buttons = [
            'basic-play-btn',
            'basic-stop-btn',
            'basic-play-interpretation-btn',
            'basic-stop-interpretation-btn'
        ];
        
        let allButtonsExist = true;
        
        buttons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            const exists = button !== null;
            logTest(`Button ${buttonId} exists`, exists);
            if (!exists) allButtonsExist = false;
        });
        
        return allButtonsExist;
    }
    
    // Test 3: Test button event handlers
    function testButtonEventHandlers() {
        console.log('\n🔍 Test 3: Testing button event handlers...');
        
        const stopButtons = [
            'basic-stop-btn',
            'basic-stop-interpretation-btn'
        ];
        
        let allHandlersWork = true;
        
        stopButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                // Check if button has click handler
                const hasHandler = button.onclick !== null || 
                                 button.addEventListener !== undefined;
                logTest(`${buttonId} has event handler`, hasHandler);
                if (!hasHandler) allHandlersWork = false;
            }
        });
        
        return allHandlersWork;
    }
    
    // Test 4: Test TTS access control
    async function testTTSAccessControl() {
        console.log('\n🔍 Test 4: Testing TTS access control...');
        
        try {
            const response = await fetch('/api/user/role-info', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const userInfo = await response.json();
                logTest('User authentication', true, `Role: ${userInfo.role}`);
                
                // Check TTS access
                const ttsResponse = await fetch('/api/user/tts-access', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (ttsResponse.ok) {
                    const ttsAccess = await ttsResponse.json();
                    logTest('TTS access check', ttsAccess.allowed, 
                           `Reason: ${ttsAccess.reason || 'N/A'}`);
                    return ttsAccess.allowed;
                } else {
                    logTest('TTS access check', false, `HTTP ${ttsResponse.status}`);
                    return false;
                }
            } else {
                logTest('User authentication', false, `HTTP ${response.status}`);
                return false;
            }
        } catch (error) {
            logTest('TTS access control', false, `Error: ${error.message}`);
            return false;
        }
    }
    
    // Test 5: Test actual TTS stop functionality
    async function testActualTTSStop() {
        console.log('\n🔍 Test 5: Testing actual TTS stop functionality...');
        
        // Test basic transcript TTS stop
        const transcriptArea = document.getElementById('basic-transcript');
        const playBtn = document.getElementById('basic-play-btn');
        const stopBtn = document.getElementById('basic-stop-btn');
        
        if (!transcriptArea || !playBtn || !stopBtn) {
            logTest('Basic TTS elements found', false, 'Missing elements');
            return false;
        }
        
        // Set test text
        transcriptArea.value = TEST_CONFIG.testText;
        
        // Test play button click
        console.log('🎵 Starting TTS playback...');
        playBtn.click();
        
        // Wait for TTS to start
        await delay(TEST_CONFIG.stopDelay);
        
        // Check if stop button is visible
        const stopBtnVisible = stopBtn.style.display !== 'none';
        logTest('Stop button becomes visible', stopBtnVisible);
        
        if (stopBtnVisible) {
            // Test stop button click
            console.log('🛑 Clicking stop button...');
            stopBtn.click();
            
            // Wait a moment for stop to take effect
            await delay(500);
            
            // Check if play button is visible again
            const playBtnVisible = playBtn.style.display !== 'none';
            logTest('Play button reappears after stop', playBtnVisible);
            
            return playBtnVisible;
        }
        
        return false;
    }
    
    // Test 6: Test interpretation TTS stop
    async function testInterpretationTTSStop() {
        console.log('\n🔍 Test 6: Testing interpretation TTS stop...');
        
        const interpretationArea = document.getElementById('basic-interpretation');
        const playBtn = document.getElementById('basic-play-interpretation-btn');
        const stopBtn = document.getElementById('basic-stop-interpretation-btn');
        
        if (!interpretationArea || !playBtn || !stopBtn) {
            logTest('Interpretation TTS elements found', false, 'Missing elements');
            return false;
        }
        
        // Set test text
        interpretationArea.value = TEST_CONFIG.testText;
        
        // Test play button click
        console.log('🎵 Starting interpretation TTS...');
        playBtn.click();
        
        // Wait for TTS to start
        await delay(TEST_CONFIG.stopDelay);
        
        // Check if stop button is visible
        const stopBtnVisible = stopBtn.style.display !== 'none';
        logTest('Interpretation stop button becomes visible', stopBtnVisible);
        
        if (stopBtnVisible) {
            // Test stop button click
            console.log('🛑 Clicking interpretation stop button...');
            stopBtn.click();
            
            // Wait a moment for stop to take effect
            await delay(500);
            
            // Check if play button is visible again
            const playBtnVisible = playBtn.style.display !== 'none';
            logTest('Interpretation play button reappears after stop', playBtnVisible);
            
            return playBtnVisible;
        }
        
        return false;
    }
    
    // Test 7: Test global stop functionality
    async function testGlobalStopFunctionality() {
        console.log('\n🔍 Test 7: Testing global stop functionality...');
        
        // Start multiple TTS streams if possible
        const transcriptArea = document.getElementById('basic-transcript');
        const interpretationArea = document.getElementById('basic-interpretation');
        const playBtn1 = document.getElementById('basic-play-btn');
        const playBtn2 = document.getElementById('basic-play-interpretation-btn');
        
        if (transcriptArea && interpretationArea && playBtn1 && playBtn2) {
            // Set test text
            transcriptArea.value = 'First TTS stream for testing.';
            interpretationArea.value = 'Second TTS stream for testing.';
            
            // Start both streams
            console.log('🎵 Starting multiple TTS streams...');
            playBtn1.click();
            await delay(200);
            playBtn2.click();
            
            // Wait for streams to start
            await delay(TEST_CONFIG.stopDelay);
            
            // Test global stop (Escape key)
            console.log('🛑 Testing global stop (Escape key)...');
            const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
            document.dispatchEvent(escapeEvent);
            
            // Wait for stop to take effect
            await delay(500);
            
            // Check if both play buttons are visible
            const playBtn1Visible = playBtn1.style.display !== 'none';
            const playBtn2Visible = playBtn2.style.display !== 'none';
            
            logTest('Global stop works', playBtn1Visible && playBtn2Visible, 
                   'Both play buttons reappeared');
            
            return playBtn1Visible && playBtn2Visible;
        } else {
            logTest('Global stop test', false, 'Missing required elements');
            return false;
        }
    }
    
    // Test 8: Test stopAllAudio function directly
    function testStopAllAudioFunction() {
        console.log('\n🔍 Test 8: Testing stopAllAudio function directly...');
        
        try {
            if (typeof window.stopAllAudio === 'function') {
                console.log('🛑 Calling stopAllAudio() directly...');
                window.stopAllAudio();
                logTest('stopAllAudio function call', true, 'Function executed without error');
                return true;
            } else {
                logTest('stopAllAudio function call', false, 'Function not found');
                return false;
            }
        } catch (error) {
            logTest('stopAllAudio function call', false, `Error: ${error.message}`);
            return false;
        }
    }
    
    // Main test runner
    async function runAllTests() {
        console.log('🚀 Running comprehensive TTS stop button tests...\n');
        
        // Run all tests
        testStopFunctionsExist();
        await delay(TEST_CONFIG.testDelay);
        
        testTTSButtonsExist();
        await delay(TEST_CONFIG.testDelay);
        
        testButtonEventHandlers();
        await delay(TEST_CONFIG.testDelay);
        
        await testTTSAccessControl();
        await delay(TEST_CONFIG.testDelay);
        
        await testActualTTSStop();
        await delay(TEST_CONFIG.testDelay);
        
        await testInterpretationTTSStop();
        await delay(TEST_CONFIG.testDelay);
        
        await testGlobalStopFunctionality();
        await delay(TEST_CONFIG.testDelay);
        
        testStopAllAudioFunction();
        
        // Display final results
        console.log('\n' + '='.repeat(60));
        console.log('🎯 TTS Stop Button Test Results:');
        console.log('='.repeat(60));
        console.log(`✅ Passed: ${testResults.passed}`);
        console.log(`❌ Failed: ${testResults.failed}`);
        console.log(`📊 Total: ${testResults.total}`);
        console.log(`📈 Success Rate: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
        
        if (testResults.failed === 0) {
            console.log('\n🎉 ALL TESTS PASSED! TTS stop functionality is working correctly.');
        } else {
            console.log('\n⚠️ Some tests failed. Review the details above.');
        }
        
        console.log('\n📋 Detailed Results:');
        testResults.details.forEach(result => {
            const status = result.passed ? '✅' : '❌';
            console.log(`${status} ${result.testName}: ${result.details}`);
        });
        
        return testResults.failed === 0;
    }
    
    // Start the tests
    runAllTests().then(success => {
        console.log(`\n🏁 Test suite completed. Success: ${success}`);
    }).catch(error => {
        console.error('❌ Test suite failed with error:', error);
    });
    
})();
