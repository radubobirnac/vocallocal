# TTS Service Implementation Plan

## Background
We've successfully refactored the VocalLocal project by implementing:
1. A base service class with common functionality
2. A transcription service for audio-to-text
3. A translation service for text translation

The next phase is to implement a TTS (Text-to-Speech) service following the same pattern.

## Current TTS Implementation
The current TTS functionality is implemented in app.py with these functions:
- `text_to_speech()` - Main endpoint at `/api/tts`
- `tts_with_openai()` - Helper function for OpenAI TTS
- `tts_with_gpt4o_mini()` - Helper function for GPT-4o Mini TTS
- `tts_with_google()` - Helper function for Google TTS (currently a placeholder)

## TTS Service Implementation Plan

### 1. Create TTS Service Class
Create a new file `src/services/tts_service.py` with:
- `TTSService` class extending `BaseService`
- Support for multiple providers (OpenAI, Google)
- Automatic fallback between providers
- Proper error handling and metrics tracking

### 2. TTS Service Methods
- `synthesize(text, language, provider, model, voice)` - Main method to convert text to speech
- `_synthesize_with_openai(text, language, voice, model)` - Helper method for OpenAI TTS
- `_synthesize_with_gpt4o_mini(text, language)` - Helper method for GPT-4o Mini TTS
- `_synthesize_with_google(text, language)` - Helper method for Google TTS

### 3. Update Application Code
- Update the `/api/tts` endpoint to use the new TTS service
- Remove the old TTS helper functions
- Add proper error handling

### 4. Create Test Script
- Create a test script to verify the functionality of the TTS service
- Test different providers, languages, and voices

## Implementation Details

### TTSService Class Structure
```python
class TTSService(BaseService):
    def __init__(self):
        super().__init__("tts_service")
        # Initialize API keys and providers
        
    def synthesize(self, text, language="en", provider="auto", model=None, voice=None):
        """Convert text to speech using the specified provider"""
        # Determine provider order
        # Try each provider in order
        # Return audio data
        
    def _synthesize_with_openai(self, text, language, voice=None, model="tts-1"):
        """Convert text to speech using OpenAI"""
        # Implementation
        
    def _synthesize_with_gpt4o_mini(self, text, language):
        """Convert text to speech using GPT-4o Mini"""
        # Implementation
        
    def _synthesize_with_google(self, text, language):
        """Convert text to speech using Google"""
        # Implementation (placeholder for now)
```

### Voice Mapping
- OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
- Default voice: onyx for all languages

### File Handling
- Return audio data as bytes
- Let the application handle file saving and response generation

## Next Steps
1. Implement the TTS service class
2. Update the application code
3. Create a test script
4. Test with different providers and languages
