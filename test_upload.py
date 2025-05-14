"""
Simple test script to test file uploads with different sizes.
"""

import os
import sys
import requests
import argparse
from tqdm import tqdm
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_upload(file_path, endpoint_url, model=None):
    """
    Test uploading a file to the specified endpoint.

    Args:
        file_path: Path to the file to upload
        endpoint_url: URL of the endpoint to test
        model: Optional model name to use for transcription
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return

    file_size = os.path.getsize(file_path)
    print(f"Testing upload of {file_path}")
    print(f"File size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")

    # Prepare the form data
    files = {'file': open(file_path, 'rb')}
    data = {}

    if model:
        data['model'] = model
        print(f"Using model: {model}")

    # Add language if it's a transcription endpoint
    if 'transcribe' in endpoint_url:
        data['language'] = 'ja'  # Japanese for the Yamato file

    # Upload the file with progress bar
    try:
        print(f"Uploading to {endpoint_url}...")

        # Use a session to handle cookies
        session = requests.Session()

        # First, make a request to get any necessary cookies
        session.get(endpoint_url.split('/api/')[0], verify=False)

        # Now upload the file
        response = session.post(
            endpoint_url,
            files=files,
            data=data,
            verify=False  # Disable SSL verification for self-signed certificates
        )

        # Check the response
        if response.status_code == 200:
            print("Upload successful!")
            print("Response:")
            print(response.json())
        else:
            print(f"Upload failed with status code {response.status_code}")
            print("Response:")
            print(response.text)

    except Exception as e:
        print(f"Error during upload: {str(e)}")

    finally:
        # Close the file
        files['file'].close()

def main():
    parser = argparse.ArgumentParser(description='Test file uploads')
    parser.add_argument('file_path', help='Path to the file to upload')
    parser.add_argument('--endpoint', default='https://localhost:5001/api/test-upload',
                        help='Endpoint URL (default: https://localhost:5001/api/test-upload)')
    parser.add_argument('--model', help='Model to use for transcription (e.g., gemini, gemini-2.5-flash)')
    parser.add_argument('--transcribe', action='store_true', help='Use the transcribe endpoint instead of test-upload')

    args = parser.parse_args()

    endpoint = args.endpoint
    if args.transcribe:
        # Use the transcribe endpoint instead
        endpoint = endpoint.replace('/test-upload', '/transcribe')
        print(f"Using transcribe endpoint: {endpoint}")

    test_upload(args.file_path, endpoint, args.model)

if __name__ == '__main__':
    main()
