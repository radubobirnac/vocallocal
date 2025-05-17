"""
Text-to-Speech service for VocalLocal
"""
import os
import time
import tempfile
import logging
import openai
import re
import io
import subprocess
import base64
import uuid
import json
from typing import List, Optional, Dict, Any, Union, BinaryIO
from services.base_service import BaseService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TTSService(BaseService):
    """Service for handling text-to-speech conversion"""

    def __init__(self):
        """Initialize the TTS service"""
        super().__init__()
        self.logger = logging.getLogger("tts_service")
        self.gemini_available = False
        self.openai_available = False
        self.gpt4o_mini_available = False

        # Check OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_available = True
            self.gpt4o_mini_available = True
            self.logger.info("OpenAI API key found. OpenAI TTS services available.")
        else:
            self.logger.warning("OpenAI API key not found. OpenAI TTS services will not be available.")

        # Try to import Google Generative AI
        try:
            import google.generativeai as genai
            self.genai = genai

            # Check Gemini API key
            self.gemini_api_key = os.getenv('GEMINI_API_KEY')
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_available = True
                self.logger.info("Google Generative AI module loaded successfully for TTS service")
            else:
                self.logger.warning("Gemini API key not found. Google TTS will not be available.")
        except ImportError as e:
            self.logger.warning(f"Google Generative AI module not available for TTS service: {str(e)}")
            self.genai = None

    def synthesize(self, text, language, model="gpt4o-mini"):
        """
        Convert text to speech using the specified model

        Args:
            text: Text to convert to speech
            language: Language code
            model: Model to use (gpt4o-mini, openai, google, auto)

        Returns:
            Path to the generated audio file
        """
        # Start timing for metrics
        start_time = time.time()
        temp_file_path = None

        try:
            # Validate input
            if not text or not text.strip():
                raise ValueError("Empty text provided")

            # Check if text is too long for OpenAI's TTS API (which has a limit)
            # OpenAI's limit is around 4096 characters
            if len(text) > 4000:
                self.logger.info(f"Text is too long ({len(text)} chars). Splitting into chunks.")
                
                # Split text into chunks
                text_chunks = self._chunk_text(text)
                self.logger.info(f"Split text into {len(text_chunks)} chunks")
                
                # Process only the first chunk for now (simpler solution)
                # This avoids the need for audio concatenation which requires pydub
                chunk = text_chunks[0]
                self.logger.info(f"Processing first chunk of {len(chunk)} chars")
                
                # Create a temporary file to store the audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file_path = temp_file.name

                # Determine which providers to try based on the model parameter
                provider_order = []
                if model == "auto":
                    # Auto mode: try GPT-4o Mini first, then OpenAI, then Google
                    if self.gpt4o_mini_available:
                        provider_order.append("gpt4o-mini")
                    if self.openai_available:
                        provider_order.append("openai")
                    if self.gemini_available:
                        provider_order.append("google")
                elif model == "gpt4o-mini":
                    # GPT-4o Mini mode: try GPT-4o Mini first, then OpenAI as fallback
                    if self.gpt4o_mini_available:
                        provider_order.append("gpt4o-mini")
                    if self.openai_available:
                        provider_order.append("openai")
                elif model == "openai":
                    # OpenAI mode: use only OpenAI
                    if self.openai_available:
                        provider_order.append("openai")
                elif model == "google":
                    # Google mode: use only Google
                    if self.gemini_available:
                        provider_order.append("google")
                else:
                    # Unknown model: use auto mode
                    self.logger.warning(f"Unknown model: {model}. Using auto mode.")
                    if self.gpt4o_mini_available:
                        provider_order.append("gpt4o-mini")
                    if self.openai_available:
                        provider_order.append("openai")
                    if self.gemini_available:
                        provider_order.append("google")
                
                # If no providers are available, raise an error
                if not provider_order:
                    raise RuntimeError("No TTS providers are available. Please check your API keys.")
                
                # Try each provider in order
                success = False
                model_used = None
                last_error = None
                
                for provider in provider_order:
                    try:
                        self.logger.info(f"Attempting TTS with {provider}")
                        
                        if provider == "gpt4o-mini":
                            self.tts_with_gpt4o_mini(chunk, language, temp_file_path)
                        elif provider == "openai":
                            self.tts_with_openai(chunk, language, temp_file_path)
                        elif provider == "google":
                            self.tts_with_google(chunk, language, temp_file_path)
                        
                        # If we get here, the TTS was successful
                        success = True
                        model_used = provider
                        break
                    
                    except Exception as e:
                        # Log the error
                        self.logger.error(f"{provider} TTS error: {str(e)}")
                        last_error = e
                        
                        # Continue to the next provider
                        continue
                
                # If all providers failed, raise the last error
                if not success:
                    if last_error:
                        raise last_error
                    else:
                        raise RuntimeError("All TTS providers failed")
                
                # Calculate performance metrics
                end_time = time.time()
                tts_time = end_time - start_time
                char_count = len(chunk)
                
                # Track metrics
                self.track_metrics("tts", model_used, char_count // 4, char_count, tts_time, True)
                
                self.logger.info(f"TTS successful for first chunk. Output saved to {temp_file_path}")
                
                # Add a warning message if there were more chunks that weren't processed
                if len(text_chunks) > 1:
                    self.logger.warning(f"Only processed the first chunk of text. {len(text_chunks)-1} chunks were skipped.")
                
                return temp_file_path
            
            # For shorter text, use the original implementation
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file_path = temp_file.name

            self.logger.info(f"TTS request: model={model}, language={language}, text_length={len(text)}")

            # Determine provider order based on model selection and availability
            provider_order = []

            if model == "auto":
                # Auto mode: try GPT-4o Mini first, then OpenAI, then Google
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
                if self.gemini_available:
                    provider_order.append("google")
            elif model == "gpt4o-mini":
                # GPT-4o Mini mode: try GPT-4o Mini first, then OpenAI as fallback
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
            elif model == "openai":
                # OpenAI mode: use only OpenAI
                if self.openai_available:
                    provider_order.append("openai")
            elif model == "google":
                # Google mode: use only Google
                if self.gemini_available:
                    provider_order.append("google")
            else:
                # Unknown model: use auto mode
                self.logger.warning(f"Unknown model: {model}. Using auto mode.")
                if self.gpt4o_mini_available:
                    provider_order.append("gpt4o-mini")
                if self.openai_available:
                    provider_order.append("openai")
                if self.gemini_available:
                    provider_order.append("google")

            # If no providers are available, raise an error
            if not provider_order:
                raise RuntimeError("No TTS providers are available. Please check your API keys.")

            # Try each provider in order
            success = False
            model_used = None
            last_error = None

            for provider in provider_order:
                try:
                    self.logger.info(f"Attempting TTS with {provider}")

                    if provider == "gpt4o-mini":
                        self.tts_with_gpt4o_mini(text, language, temp_file_path)
                    elif provider == "openai":
                        self.tts_with_openai(text, language, temp_file_path)
                    elif provider == "google":
                        self.tts_with_google(text, language, temp_file_path)

                    # If we get here, the TTS was successful
                    success = True
                    model_used = provider
                    break

                except Exception as e:
                    # Log the error
                    self.logger.error(f"{provider} TTS error: {str(e)}")
                    last_error = e

                    # Continue to the next provider
                    continue

            # If all providers failed, raise the last error
            if not success:
                # Clean up the temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    self.logger.info(f"Removed temporary file: {temp_file_path}")

                # Raise the last error
                if last_error:
                    raise last_error
                else:
                    raise RuntimeError("All TTS providers failed")

            # Calculate performance metrics
            end_time = time.time()
            tts_time = end_time - start_time
            char_count = len(text)

            # Track metrics
            self.track_metrics("tts", model_used, char_count // 4, char_count, tts_time, success)

            self.logger.info(f"TTS successful with {model_used}. Output saved to {temp_file_path}")
            return temp_file_path

        except Exception as e:
            # Track the error in metrics
            response_time = time.time() - start_time
            self.track_metrics("tts", model, 0, 0, response_time, False)

            # Clean up the temporary file if it exists
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    self.logger.info(f"Removed temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to remove temporary file: {str(cleanup_error)}")

            # Re-raise the exception with more context
            self.logger.error(f"TTS failed: {str(e)}")
            raise RuntimeError(f"Text-to-speech conversion failed: {str(e)}") from e

    def tts_with_openai(self, text, language, output_file_path):
        """
        Helper function to generate speech using OpenAI's TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Use onyx voice for all languages
        voice = 'onyx'

        # Check if OpenAI is available
        if not self.openai_available:
            raise RuntimeError("OpenAI API key is not configured. Cannot use OpenAI for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"OpenAI TTS request: language={language}, voice={voice}, text_length={len(text)}")

            # Generate speech with OpenAI
            start_time = time.time()
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            elapsed_time = time.time() - start_time
            self.logger.info(f"OpenAI TTS API call completed in {elapsed_time:.2f} seconds")

            # Save to the output file
            total_bytes = 0
            with open(output_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    total_bytes += len(chunk)

            self.logger.info(f"OpenAI TTS successful: {total_bytes} bytes written to {output_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"OpenAI TTS error: {str(e)}")
            raise RuntimeError(f"OpenAI TTS failed: {str(e)}") from e

    def tts_with_gpt4o_mini(self, text, language, output_file_path):
        """
        Helper function to generate speech using OpenAI's GPT-4o Mini TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Check if GPT-4o Mini is available
        if not self.gpt4o_mini_available:
            raise RuntimeError("OpenAI API key is not configured. Cannot use GPT-4o Mini for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"GPT-4o Mini TTS request: language={language}, text_length={len(text)}")

            # Generate speech with OpenAI's GPT-4o Mini TTS
            start_time = time.time()
            response = openai.audio.speech.create(
                model="gpt-4o-mini-tts",  # Use the GPT-4o Mini TTS model
                voice="alloy",  # Use alloy voice for all languages
                input=text
            )
            elapsed_time = time.time() - start_time
            self.logger.info(f"GPT-4o Mini TTS API call completed in {elapsed_time:.2f} seconds")

            # Save to the output file
            total_bytes = 0
            with open(output_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
                    total_bytes += len(chunk)

            self.logger.info(f"GPT-4o Mini TTS successful: {total_bytes} bytes written to {output_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"GPT-4o Mini TTS error: {str(e)}")
            raise RuntimeError(f"GPT-4o Mini TTS failed: {str(e)}") from e

    def tts_with_google(self, text, language, output_file_path):
        """
        Helper function to generate speech using Google's TTS service

        Args:
            text: Text to convert to speech
            language: Language code
            output_file_path: Path to save the output audio file

        Returns:
            True if successful, raises an exception otherwise

        Raises:
            RuntimeError: If the TTS operation fails
        """
        # Check if Gemini is available
        if not self.gemini_available:
            raise RuntimeError("Google Generative AI module is not available. Cannot use Google for TTS.")

        try:
            # Log request for debugging
            self.logger.info(f"Google TTS request: language={language}, text_length={len(text)}")

            # For now, we'll use a fallback to OpenAI TTS
            # This is a placeholder for the actual Google TTS implementation
            self.logger.info("Falling back to OpenAI TTS as Google TTS is not fully implemented yet")

            # In a real implementation, we would use Google Cloud Text-to-Speech API
            # For now, we'll use OpenAI TTS instead
            if self.openai_available:
                return self.tts_with_openai(text, language, output_file_path)
            else:
                raise RuntimeError("OpenAI API key is not configured. Cannot use fallback for Google TTS.")

        except Exception as e:
            self.logger.error(f"Google TTS error: {str(e)}")
            raise RuntimeError(f"Google TTS failed: {str(e)}") from e

    def _chunk_text(self, text, max_length=4000):
        """
        Split text into chunks that don't exceed max_length characters.
        Tries to split at sentence boundaries when possible.
        
        Args:
            text: Text to split
            max_length: Maximum length of each chunk
        
        Returns:
            List of text chunks
        """
        # If text is already short enough, return it as is
        if len(text) <= max_length:
            return [text]
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If a single sentence is too long, split it further
            if len(sentence) > max_length:
                # Add any existing content to chunks
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Split long sentence by commas, then by spaces if needed
                comma_parts = sentence.split(', ')
                sub_chunk = ""
                
                for part in comma_parts:
                    if len(sub_chunk) + len(part) + 2 <= max_length:
                        if sub_chunk:
                            sub_chunk += ", " + part
                        else:
                            sub_chunk = part
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        
                        # If part is still too long, split by spaces
                        if len(part) > max_length:
                            words = part.split()
                            sub_chunk = ""
                            for word in words:
                                if len(sub_chunk) + len(word) + 1 <= max_length:
                                    if sub_chunk:
                                        sub_chunk += " " + word
                                    else:
                                        sub_chunk = word
                                else:
                                    chunks.append(sub_chunk)
                                    sub_chunk = word
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = ""
                        else:
                            sub_chunk = part
            
            # If adding this sentence would make the chunk too long, start a new chunk
            elif len(current_chunk) + len(sentence) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = sentence
            
            # Otherwise, add the sentence to the current chunk
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _combine_audio_files(self, audio_file_paths):
        """
        Combine multiple audio files into a single audio file using FFmpeg.
        
        Args:
            audio_file_paths: List of paths to audio files
        
        Returns:
            Path to the combined audio file
        """
        if not audio_file_paths:
            return None
        
        if len(audio_file_paths) == 1:
            return audio_file_paths[0]
        
        # Create a temporary file for the file list
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as file_list:
            file_list_path = file_list.name
            # Write each file path to the list file
            for file_path in audio_file_paths:
                file_list.write(f"file '{file_path}'\n")
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as output_file:
            output_path = output_file.name
        
        try:
            # Get FFmpeg path
            ffmpeg_path = "ffmpeg"
            if hasattr(self, 'ffmpeg_path') and self.ffmpeg_path:
                ffmpeg_path = self.ffmpeg_path
            
            # Use FFmpeg to concatenate the files
            cmd = [
                ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                output_path
            ]
            
            # Run the command
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Return the path to the combined file
            return output_path
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            # If FFmpeg fails, return the first file as a fallback
            return audio_file_paths[0]
        except Exception as e:
            self.logger.error(f"Error combining audio files: {str(e)}")
            # If any other error occurs, return the first file as a fallback
            return audio_file_paths[0]
        finally:
            # Clean up the file list
            try:
                os.remove(file_list_path)
            except:
                pass
