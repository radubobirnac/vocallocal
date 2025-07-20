#!/usr/bin/env python3
"""
Diagnose TTS Stop Button Issues
Comprehensive diagnosis of stop button functionality and persistent audio problems
"""

import sys
import os
import time
import requests

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def test_tts_endpoint_with_session():
    """Test TTS endpoint with authenticated session to verify audio generation."""
    print("🔧 Testing TTS Endpoint with Authentication")
    print("=" * 60)
    
    try:
        # Create session for authentication
        session = requests.Session()
        
        # Login as super user
        print("🔑 Logging in as super user...")
        login_data = {
            'email': 'superuser@vocallocal.com',
            'password': 'superpassword123'
        }
        
        login_response = session.post('http://localhost:5001/auth/login',
                                    data=login_data,
                                    timeout=10)
        
        print(f"Login response: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            print("✅ Login successful")
            
            # Test TTS endpoint
            print("🎵 Testing TTS endpoint...")
            tts_payload = {
                'text': 'This is a test of the TTS stop button functionality. The audio should play and then be stoppable.',
                'language': 'en',
                'tts_model': 'gemini-2.5-flash-tts'
            }
            
            tts_response = session.post('http://localhost:5001/api/tts',
                                      json=tts_payload,
                                      timeout=30)
            
            print(f"TTS response: {tts_response.status_code}")
            print(f"Content-Type: {tts_response.headers.get('Content-Type', 'unknown')}")
            
            if tts_response.status_code == 200:
                content_type = tts_response.headers.get('Content-Type', '')
                if 'audio' in content_type:
                    audio_size = len(tts_response.content)
                    print(f"✅ TTS endpoint working! Audio size: {audio_size} bytes")
                    
                    # Save test audio file
                    with open('test_tts_audio.mp3', 'wb') as f:
                        f.write(tts_response.content)
                    print(f"📁 Test audio saved as: test_tts_audio.mp3")
                    
                    return True
                else:
                    print(f"❌ TTS returned non-audio content: {content_type}")
                    print(f"Response preview: {tts_response.text[:200]}...")
                    return False
            else:
                print(f"❌ TTS failed: {tts_response.status_code}")
                print(f"Response: {tts_response.text[:200]}...")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TTS endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_script_js_functions():
    """Check if the main script.js file has the required stop functions."""
    print("\n🔧 Checking script.js Stop Functions")
    print("=" * 60)
    
    try:
        script_path = 'static/script.js'
        if not os.path.exists(script_path):
            print(f"❌ script.js not found at: {script_path}")
            return False
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Check for required functions
        functions_to_check = [
            'function stopSpeakText',
            'function stopAllAudio',
            'addEventListener.*click.*stop',
            'ttsPlayers',
            'currentAudio'
        ]
        
        print("📋 Checking for required functions and variables:")
        all_found = True
        
        for func_pattern in functions_to_check:
            import re
            if re.search(func_pattern, script_content, re.IGNORECASE):
                print(f"   ✅ Found: {func_pattern}")
            else:
                print(f"   ❌ Missing: {func_pattern}")
                all_found = False
        
        # Check specific stop button event handlers
        stop_handlers = [
            'basic-stop-interpretation-btn',
            'stopSpeakText.*basic-interpretation',
            'addEventListener.*click.*stopSpeakText'
        ]
        
        print("\n📋 Checking stop button event handlers:")
        for handler in stop_handlers:
            if re.search(handler, script_content, re.IGNORECASE):
                print(f"   ✅ Found: {handler}")
            else:
                print(f"   ❌ Missing: {handler}")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error checking script.js: {str(e)}")
        return False

def test_audio_cleanup_logic():
    """Test the audio cleanup logic patterns."""
    print("\n🔧 Testing Audio Cleanup Logic")
    print("=" * 60)
    
    try:
        script_path = 'static/script.js'
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Check for proper cleanup patterns
        cleanup_patterns = [
            'audio\.pause\(\)',
            'audio\.currentTime = 0',
            'URL\.revokeObjectURL',
            'delete ttsPlayers',
            'currentAudio = null'
        ]
        
        print("📋 Checking audio cleanup patterns:")
        cleanup_score = 0
        
        for pattern in cleanup_patterns:
            import re
            matches = re.findall(pattern, script_content, re.IGNORECASE)
            if matches:
                print(f"   ✅ Found {len(matches)} instances: {pattern}")
                cleanup_score += 1
            else:
                print(f"   ❌ Missing: {pattern}")
        
        print(f"\n📊 Cleanup Score: {cleanup_score}/{len(cleanup_patterns)}")
        
        if cleanup_score >= len(cleanup_patterns) * 0.8:  # 80% threshold
            print("✅ Audio cleanup logic appears comprehensive")
            return True
        else:
            print("❌ Audio cleanup logic may be incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error testing cleanup logic: {str(e)}")
        return False

def check_persistent_audio_issues():
    """Check for potential causes of persistent audio playback."""
    print("\n🔧 Checking Persistent Audio Issues")
    print("=" * 60)
    
    potential_issues = [
        {
            'name': 'Multiple Audio Instances',
            'description': 'Check if multiple audio elements are created without cleanup',
            'check': 'Look for audio creation without proper tracking'
        },
        {
            'name': 'Service Worker Audio',
            'description': 'Check if service workers are caching or playing audio',
            'check': 'Look for service worker registration'
        },
        {
            'name': 'Web Audio API Context',
            'description': 'Check if Web Audio API contexts are not being closed',
            'check': 'Look for AudioContext usage'
        },
        {
            'name': 'Background Audio Processing',
            'description': 'Check for background audio processing scripts',
            'check': 'Look for background processing files'
        }
    ]
    
    print("📋 Potential Persistent Audio Issues:")
    
    for issue in potential_issues:
        print(f"\n🔍 {issue['name']}:")
        print(f"   Description: {issue['description']}")
        
        # Check for service worker
        if 'service worker' in issue['name'].lower():
            sw_files = ['static/sw.js', 'static/service-worker.js', 'templates/sw.js']
            sw_found = any(os.path.exists(f) for f in sw_files)
            if sw_found:
                print(f"   ⚠️ Service worker files found - may cause persistent audio")
            else:
                print(f"   ✅ No service worker files found")
        
        # Check for Web Audio API
        elif 'web audio' in issue['name'].lower():
            try:
                script_path = 'static/script.js'
                if os.path.exists(script_path):
                    with open(script_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'AudioContext' in content or 'webkitAudioContext' in content:
                        print(f"   ⚠️ Web Audio API usage found - check context cleanup")
                    else:
                        print(f"   ✅ No Web Audio API usage found")
                else:
                    print(f"   ❓ Cannot check - script.js not found")
            except Exception as e:
                print(f"   ❌ Error checking: {str(e)}")
        
        # Check for background processing
        elif 'background' in issue['name'].lower():
            bg_files = ['static/background-processing.js', 'static/worker.js']
            bg_found = any(os.path.exists(f) for f in bg_files)
            if bg_found:
                print(f"   ⚠️ Background processing files found")
                for f in bg_files:
                    if os.path.exists(f):
                        print(f"      - {f}")
            else:
                print(f"   ✅ No background processing files found")
        
        else:
            print(f"   ℹ️ Manual check required: {issue['check']}")

def generate_stop_button_fix_recommendations():
    """Generate recommendations for fixing stop button issues."""
    print("\n📋 Stop Button Fix Recommendations")
    print("=" * 60)
    
    recommendations = [
        {
            'issue': 'Stop Button Not Working',
            'fixes': [
                'Ensure script.js is loaded before test pages',
                'Verify stop button event handlers are attached',
                'Check that stopSpeakText() function exists and is callable',
                'Confirm sourceId matches between play and stop functions'
            ]
        },
        {
            'issue': 'Audio Continues After Stop',
            'fixes': [
                'Implement audio.pause() in stop functions',
                'Reset audio.currentTime = 0 to prevent resume',
                'Call URL.revokeObjectURL() to free memory',
                'Clear audio references from global variables',
                'Remove audio elements from DOM if created dynamically'
            ]
        },
        {
            'issue': 'Persistent Audio After Refresh',
            'fixes': [
                'Add beforeunload event listener to stop all audio',
                'Implement visibilitychange handler to pause on tab switch',
                'Check for service workers that might cache audio',
                'Ensure no background audio processing continues',
                'Clear any Web Audio API contexts'
            ]
        },
        {
            'issue': 'Button State Not Updating',
            'fixes': [
                'Call setTTSButtonState() after stopping audio',
                'Ensure button visibility is properly managed',
                'Update button states in all stop functions',
                'Check for CSS display/visibility conflicts'
            ]
        }
    ]
    
    for rec in recommendations:
        print(f"\n🔧 {rec['issue']}:")
        for i, fix in enumerate(rec['fixes'], 1):
            print(f"   {i}. {fix}")

def main():
    """Main diagnostic function."""
    print("🚨 TTS STOP BUTTON FUNCTIONALITY DIAGNOSIS")
    print("=" * 80)
    
    print("Diagnosing TTS stop button issues and persistent audio problems...")
    print("")
    
    # Run diagnostics
    tts_working = test_tts_endpoint_with_session()
    script_functions = check_script_js_functions()
    cleanup_logic = test_audio_cleanup_logic()
    
    # Check for persistent audio issues
    check_persistent_audio_issues()
    
    # Generate recommendations
    generate_stop_button_fix_recommendations()
    
    print(f"\n" + "="*80)
    print(f"🎯 DIAGNOSIS SUMMARY:")
    print(f"="*80)
    
    print(f"TTS Endpoint Working: {'✅' if tts_working else '❌'}")
    print(f"Script Functions Present: {'✅' if script_functions else '❌'}")
    print(f"Cleanup Logic Complete: {'✅' if cleanup_logic else '❌'}")
    
    if tts_working and script_functions and cleanup_logic:
        print(f"\n🎉 STOP BUTTON SHOULD BE WORKING")
        print(f"   If issues persist, check browser console for errors")
        print(f"   Test with: http://localhost:5001/test_tts_simple.html")
    else:
        print(f"\n❌ STOP BUTTON ISSUES IDENTIFIED")
        print(f"   Review the recommendations above to fix the issues")
    
    return tts_working and script_functions and cleanup_logic

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
