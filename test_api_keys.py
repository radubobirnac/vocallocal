#!/usr/bin/env python3
"""
Quick test to check if API keys are properly loaded
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_keys():
    """Test if API keys are available"""
    print("🔑 Testing API Key Configuration")
    print("=" * 50)
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OpenAI API Key: {openai_key[:10]}...{openai_key[-4:]}")
    else:
        print("❌ OpenAI API Key: NOT FOUND")
    
    # Check Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✅ Gemini API Key: {gemini_key[:10]}...{gemini_key[-4:]}")
    else:
        print("❌ Gemini API Key: NOT FOUND")
    
    # Test OpenAI connection
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            
            # Test with a simple request
            response = openai.models.list()
            print("✅ OpenAI API: Connection successful")
            
            # Check if Whisper is available
            models = [model.id for model in response.data]
            if 'whisper-1' in models:
                print("✅ OpenAI Whisper: Available")
            else:
                print("⚠️ OpenAI Whisper: Not found in model list")
                
        except Exception as e:
            print(f"❌ OpenAI API: Connection failed - {str(e)}")
    
    # Test Gemini connection
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            
            # Test with a simple request
            models = genai.list_models()
            model_names = [model.name for model in models]
            print("✅ Gemini API: Connection successful")
            
            # Check for specific models
            if any('gemini-2.0-flash' in name for name in model_names):
                print("✅ Gemini 2.0 Flash: Available")
            else:
                print("⚠️ Gemini 2.0 Flash: Not found")
                
        except Exception as e:
            print(f"❌ Gemini API: Connection failed - {str(e)}")
    
    # Test FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version_line}")
        else:
            print("❌ FFmpeg: Not working properly")
    except FileNotFoundError:
        print("❌ FFmpeg: Not installed")
    except Exception as e:
        print(f"❌ FFmpeg: Error - {str(e)}")

if __name__ == "__main__":
    test_api_keys()
