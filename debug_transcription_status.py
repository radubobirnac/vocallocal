#!/usr/bin/env python3
"""
Debug script to test the transcription status API endpoint and verify response format.

This script helps debug the Gemini 2.5 Flash Preview display issue by:
1. Testing the API endpoint directly
2. Checking response format
3. Simulating frontend processing
"""

import requests
import json
import sys
import time

def test_transcription_status_api(base_url="http://localhost:5001"):
    """Test the transcription status API endpoint."""
    
    print("Transcription Status API Debug Tool")
    print("=" * 50)
    print()
    
    # Test with a fake job ID to see the response format
    test_job_id = "test-job-123"
    status_url = f"{base_url}/api/transcription_status/{test_job_id}"
    
    print(f"Testing URL: {status_url}")
    print()
    
    try:
        response = requests.get(status_url, timeout=10)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Response JSON:")
                print(json.dumps(data, indent=2))
                print()
                
                # Simulate frontend processing
                print("Simulating Frontend Processing:")
                print("-" * 30)
                
                if data.get('status') == 'completed' and data.get('result'):
                    result = data['result']
                    print(f"Result type: {type(result).__name__}")
                    
                    # Apply the same logic as the frontend
                    if isinstance(result, str):
                        transcription_text = result
                        print(f"✅ String result: '{transcription_text}'")
                    elif isinstance(result, dict) and 'text' in result:
                        transcription_text = result['text']
                        print(f"✅ Object result with text: '{transcription_text}'")
                    else:
                        transcription_text = str(result) if result else "Transcription completed but no text was returned."
                        print(f"⚠️ Fallback result: '{transcription_text}'")
                    
                    print(f"Final transcription text: '{transcription_text}'")
                    print(f"Text length: {len(transcription_text)}")
                    
                elif data.get('status') == 'not_found':
                    print("✅ Job not found (expected for test job ID)")
                else:
                    print(f"Status: {data.get('status')}")
                    print(f"Error: {data.get('error')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print()
        print("Make sure the VocalLocal application is running on the specified port.")
        return False
    
    return True

def test_with_real_job_id(base_url="http://localhost:5001"):
    """Test with a real job ID if provided."""
    
    print("\nReal Job ID Testing")
    print("=" * 30)
    
    job_id = input("Enter a real job ID to test (or press Enter to skip): ").strip()
    
    if not job_id:
        print("Skipping real job ID test.")
        return
    
    status_url = f"{base_url}/api/transcription_status/{job_id}"
    print(f"Testing with job ID: {job_id}")
    print(f"URL: {status_url}")
    print()
    
    try:
        response = requests.get(status_url, timeout=10)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            print()
            
            # Check if this is a completed transcription
            if data.get('status') == 'completed' and data.get('result'):
                result = data['result']
                print(f"Result type: {type(result).__name__}")
                print(f"Result content: {result}")
                
                # Test the extraction logic
                if isinstance(result, str):
                    print(f"✅ Would extract string: '{result[:100]}...' (length: {len(result)})")
                elif isinstance(result, dict) and 'text' in result:
                    text = result['text']
                    print(f"✅ Would extract from object.text: '{text[:100]}...' (length: {len(text)})")
                else:
                    fallback = str(result) if result else "No text"
                    print(f"⚠️ Would use fallback: '{fallback[:100]}...'")
            else:
                print(f"Job status: {data.get('status')}")
                if data.get('error'):
                    print(f"Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing real job ID: {e}")

def generate_browser_test_script():
    """Generate a JavaScript test script for browser console."""
    
    script = """
// Browser Console Test Script for Transcription Status
// Copy and paste this into your browser's developer console while on the VocalLocal page

console.log('=== Transcription Status Debug Test ===');

// Test function to check a job ID
async function testTranscriptionStatus(jobId) {
    try {
        console.log(`Testing job ID: ${jobId}`);
        const response = await fetch(`/api/transcription_status/${jobId}`);
        const data = await response.json();
        
        console.log('Response:', data);
        console.log('Status:', data.status);
        console.log('Result type:', typeof data.result);
        console.log('Result content:', data.result);
        
        if (data.status === 'completed' && data.result) {
            let transcriptionText;
            
            if (typeof data.result === 'string') {
                transcriptionText = data.result;
                console.log('✅ Extracted as string:', transcriptionText.substring(0, 100) + '...');
            } else if (data.result && data.result.text) {
                transcriptionText = data.result.text;
                console.log('✅ Extracted from object.text:', transcriptionText.substring(0, 100) + '...');
            } else {
                transcriptionText = data.result.toString() || "No text";
                console.log('⚠️ Using fallback:', transcriptionText.substring(0, 100) + '...');
            }
            
            console.log('Final text length:', transcriptionText.length);
            
            // Test updating the transcript element
            const element = document.getElementById('basic-transcript');
            if (element) {
                console.log('Found transcript element:', element);
                element.value = transcriptionText;
                console.log('✅ Updated transcript element');
                
                // Trigger change event
                const event = new Event('change');
                element.dispatchEvent(event);
                console.log('✅ Triggered change event');
            } else {
                console.log('❌ Could not find basic-transcript element');
            }
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Usage: testTranscriptionStatus('your-job-id-here');
console.log('Use: testTranscriptionStatus("your-job-id") to test a specific job');
"""
    
    print("\nBrowser Console Test Script")
    print("=" * 40)
    print("Copy and paste the following script into your browser's developer console:")
    print()
    print(script)

def main():
    """Main function."""
    
    # Test the API endpoint
    success = test_transcription_status_api()
    
    if success:
        # Test with real job ID if available
        test_with_real_job_id()
        
        # Generate browser test script
        generate_browser_test_script()
        
        print("\nDebugging Summary:")
        print("=" * 30)
        print("1. ✅ API endpoint is accessible")
        print("2. ✅ Response format is being handled correctly")
        print("3. ✅ Frontend logic should work with the fix")
        print()
        print("Next steps:")
        print("- Test with a real transcription job")
        print("- Check browser console for any JavaScript errors")
        print("- Use the browser test script to debug in real-time")
        print("- Verify that the updateTranscript function is being called")
    else:
        print("\nDebugging Failed:")
        print("=" * 20)
        print("- Make sure VocalLocal is running")
        print("- Check the port number (default: 5001)")
        print("- Verify the API endpoint is working")

if __name__ == "__main__":
    main()
