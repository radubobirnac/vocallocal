#!/usr/bin/env python3
"""
Test the /api/test_transcribe_chunk endpoint to see the exact response format
"""

import requests
import tempfile
import subprocess
import os
import json
import urllib3

# Disable SSL warnings for localhost testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_endpoint():
    # Create a test audio file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.webm')
    temp_file.close()

    try:
        # Create test audio with FFmpeg
        cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', '-c:a', 'libopus', '-y', temp_file.name]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg failed: {result.stderr}")
            return

        with open(temp_file.name, 'rb') as f:
            audio_data = f.read()
        
        print(f'✅ Created test audio: {len(audio_data)} bytes')
        
        # Send to test endpoint
        files = {'audio': ('test.webm', audio_data, 'audio/webm')}
        data = {
            'language': 'en', 
            'model': 'gemini-2.0-flash-lite', 
            'chunk_number': '999', 
            'element_id': 'test'
        }
        
        print(f'📡 Sending request to https://localhost:5001/api/test_transcribe_chunk')
        print(f'📋 Data: {data}')
        
        response = requests.post(
            'https://localhost:5001/api/test_transcribe_chunk', 
            files=files, 
            data=data, 
            verify=False,
            timeout=30
        )
        
        print(f'📊 Status Code: {response.status_code}')
        print(f'📋 Response Headers: {dict(response.headers)}')
        print(f'📄 Raw Response Text: {response.text}')
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f'✅ JSON Response:')
                print(json.dumps(json_response, indent=2))
                
                # Check specific fields
                if 'text' in json_response:
                    print(f'📝 Transcription Text: "{json_response["text"]}"')
                if 'chunk_number' in json_response:
                    print(f'🔢 Chunk Number: {json_response["chunk_number"]}')
                if 'status' in json_response:
                    print(f'📊 Status: {json_response["status"]}')
                    
            except json.JSONDecodeError as e:
                print(f'❌ Failed to parse JSON: {e}')
        else:
            print(f'❌ Request failed with status {response.status_code}')
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Network error: {e}')
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
    finally:
        # Clean up
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

if __name__ == '__main__':
    test_endpoint()
