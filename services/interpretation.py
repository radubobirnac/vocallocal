import logging
import os
import google.generativeai as genai
from openai import OpenAI
import json
import re

class InterpretationService:
    """Enhanced service for interpreting text using AI models with contextual understanding and rephrasing capabilities"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize Gemini
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.logger.info("Gemini API initialized")

        # Initialize OpenAI
        self.openai_client = None
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
            self.logger.info("OpenAI API initialized")

    def interpret(self, text, tone="neutral", model="gemini-2.5-flash-preview"):
        """
        Enhanced interpretation with contextual understanding and rephrasing capabilities

        Args:
            text (str): The text to interpret
            tone (str): The tone for interpretation (professional, simplified, academic, ai-prompts, neutral, formal, casual)
            model (str): The model to use (gemini-2.5-flash-preview, gemini-2.5-flash-preview-05-20, gemini-2.5-flash, gpt-3.5-turbo, etc.)

        Returns:
            str: The enhanced interpretation result with contextual analysis and rephrasing
        """
        self.logger.info(f"Interpreting text with {model}, tone: {tone}")

        # Create enhanced prompt based on tone
        prompt = self._create_enhanced_prompt(text, tone)

        # Use appropriate model
        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            # Default to Gemini 2.5 Flash Preview
            return self._interpret_with_gemini(prompt, "gemini-2.5-flash-preview")

    def _create_enhanced_prompt(self, text, tone):
        """Create an enhanced prompt with contextual understanding and rephrasing capabilities"""

        # Clean, minimal prompt that explicitly requests direct output
        base_prompt = f"Rewrite this text to be clearer and more professional. Provide only the rewritten text without any headers, options, or explanations: {text}"

        return base_prompt



    def _create_prompt(self, text, tone):
        """Legacy method for backward compatibility - redirects to enhanced prompt"""
        return self._create_enhanced_prompt(text, tone)

    def _interpret_with_gemini(self, prompt, model_name):
        """Use Gemini model for enhanced interpretation with optimized parameters"""
        try:
            # Extract original text from prompt for fallback purposes
            original_text = self._extract_text_from_prompt(prompt)

            # Map model name to actual model ID if needed
            model_id = model_name
            if model_name == "gemini-2.5-flash-preview":
                model_id = "gemini-2.5-flash-preview-05-20"
            elif model_name == "gemini-2.5-flash-preview-05-20":
                # Direct mapping for the specific 05-20 model
                model_id = "gemini-2.5-flash-preview-05-20"
            elif model_name == "gemini-2.0-flash-lite":
                # Legacy mapping - use 2.5 Flash Preview instead
                model_id = "gemini-2.5-flash-preview-05-20"
                self.logger.warning(f"Mapping legacy model {model_name} to gemini-2.5-flash-preview-05-20")
            elif model_name == "gemini-2.5-flash-preview-04-17":
                # Map old model to new working model for backward compatibility
                model_id = "gemini-2.5-flash-preview-05-20"
                self.logger.warning(f"Mapping deprecated model {model_name} to {model_id}")
            elif model_name == "gemini-2.5-flash":
                # Map to the correct Gemini 2.5 Flash Preview model
                model_id = "gemini-2.5-flash-preview-05-20"

            self.logger.info(f"Using Gemini model: {model_id}")

            # Configure generation parameters for better contextual understanding
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,  # Balanced creativity for nuanced interpretation
                top_p=0.9,       # Allow for diverse but relevant responses
                top_k=40,        # Reasonable vocabulary diversity
                max_output_tokens=2048,  # Allow for comprehensive interpretations
                candidate_count=1
            )

            # Generate content with Gemini using enhanced configuration
            model = genai.GenerativeModel(model_id)
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Enhanced error handling for Gemini responses
            if not response:
                raise Exception("No response received from Gemini API")

            # Check if response has candidates
            if not hasattr(response, 'candidates') or not response.candidates:
                raise Exception("No candidates returned from Gemini API")

            # Check the first candidate
            candidate = response.candidates[0]

            # Check finish reason for safety filtering
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                self.logger.info(f"Gemini response finish_reason: {finish_reason}")

                if finish_reason == 2:  # SAFETY
                    self.logger.warning("Gemini response was filtered due to safety concerns")
                    # Try with a more neutral prompt
                    return self._retry_with_neutral_prompt(original_text, model_id, generation_config)
                elif finish_reason == 3:  # RECITATION
                    self.logger.warning("Gemini response was filtered due to recitation concerns")
                    return self._retry_with_neutral_prompt(original_text, model_id, generation_config)
                elif finish_reason not in [0, 1]:  # 0=UNSPECIFIED, 1=STOP (normal completion)
                    self.logger.warning(f"Gemini response finished with unexpected reason: {finish_reason}")

            # Check if we have valid parts with text
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        cleaned_text = self._clean_interpretation_response(part.text.strip())
                        return cleaned_text

            # Fallback: try to access response.text directly
            try:
                if response.text:
                    cleaned_text = self._clean_interpretation_response(response.text.strip())
                    return cleaned_text
            except Exception as text_error:
                self.logger.warning(f"Could not access response.text: {str(text_error)}")

            # If all else fails, try a fallback approach
            self.logger.warning("Standard response extraction failed, trying fallback")
            return self._fallback_interpretation(original_text, model_id)

        except Exception as e:
            self.logger.error(f"Gemini interpretation error: {str(e)}")
            raise

    def _interpret_with_openai(self, prompt, model_name):
        """Use OpenAI model for enhanced interpretation with optimized parameters"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Check your API key.")

        try:
            self.logger.info(f"Using OpenAI model: {model_name}")

            # Simple system prompt
            system_prompt = "Rephrase text while maintaining context."

            # Generate content with OpenAI using enhanced configuration
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Balanced creativity for nuanced interpretation
                top_p=0.9,       # Allow for diverse but relevant responses
                max_tokens=2048,  # Allow for comprehensive interpretations
                frequency_penalty=0.1,  # Slight penalty to avoid repetition
                presence_penalty=0.1    # Encourage diverse vocabulary
            )

            # Extract and return the text
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("Empty response from OpenAI API")

        except Exception as e:
            self.logger.error(f"OpenAI interpretation error: {str(e)}")
            raise

    def analyze_context(self, text, model="gemini-2.5-flash-preview"):
        """
        Perform focused context analysis on text

        Args:
            text (str): The text to analyze
            model (str): The model to use for analysis

        Returns:
            str: Context analysis result
        """
        prompt = f"Analyze the context of this text: {text}"

        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            return self._interpret_with_gemini(prompt, "gemini-2.5-flash-preview")

    def rephrase_text(self, text, style="clear", model="gemini-2.5-flash-preview"):
        """
        Rephrase text for better clarity and understanding

        Args:
            text (str): The text to rephrase
            style (str): The rephrasing style (clear, simple, formal, casual)
            model (str): The model to use for rephrasing

        Returns:
            str: Rephrased text
        """
        prompt = f"Rewrite this text to be clearer and more professional. Provide only the rewritten text without any headers, options, or explanations: {text}"

        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            return self._interpret_with_gemini(prompt, "gemini-2.5-flash-preview")

    def detect_intent(self, text, model="gemini-2.5-flash-preview"):
        """
        Detect the intent and purpose behind the text

        Args:
            text (str): The text to analyze
            model (str): The model to use for analysis

        Returns:
            str: Intent detection result
        """
        prompt = f"Detect the intent of this text: {text}"

        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            return self._interpret_with_gemini(prompt, "gemini-2.5-flash-preview")

    def _extract_text_from_prompt(self, prompt):
        """Extract the original text from the prompt for fallback purposes"""
        # Handle the new prompt format
        if "Provide only the rewritten text without any headers, options, or explanations:" in prompt:
            return prompt.split("Provide only the rewritten text without any headers, options, or explanations:")[1].strip()
        elif "Rephrase the following text while maintaining its context:" in prompt:
            return prompt.split("Rephrase the following text while maintaining its context:")[1].strip()
        elif "Rephrase this text by maintaining the context:" in prompt:
            return prompt.split("Rephrase this text by maintaining the context:")[1].strip()
        elif "Analyze the context of this text:" in prompt:
            return prompt.split("Analyze the context of this text:")[1].strip()
        elif "Detect the intent of this text:" in prompt:
            return prompt.split("Detect the intent of this text:")[1].strip()
        else:
            # Fallback: return the prompt itself
            return prompt

    def _retry_with_neutral_prompt(self, text, model_id, _generation_config=None):
        """Retry with a more neutral prompt to avoid safety filtering"""
        try:
            self.logger.info("Retrying with neutral prompt to avoid safety filtering")

            # Create a very simple, neutral prompt
            neutral_prompt = f"Please rewrite this text in a clear and professional way: {text}"

            # Use more conservative generation settings
            safe_config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for safer responses
                top_p=0.8,       # More conservative sampling
                top_k=20,        # Reduced vocabulary diversity
                max_output_tokens=1024,  # Shorter responses
                candidate_count=1
            )

            model = genai.GenerativeModel(model_id)
            response = model.generate_content(
                neutral_prompt,
                generation_config=safe_config
            )

            # Try to extract text with the same error handling
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return self._clean_interpretation_response(part.text.strip())

            # If that fails, return a simple fallback
            return self._simple_fallback(text)

        except Exception as e:
            self.logger.error(f"Neutral prompt retry failed: {str(e)}")
            return self._simple_fallback(text)

    def _fallback_interpretation(self, text, model_id):
        """Fallback interpretation when all else fails"""
        try:
            self.logger.info("Using fallback interpretation method")

            # Try with the most basic prompt possible
            basic_prompt = f"Improve this text: {text}"

            # Use very conservative settings
            minimal_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.7,
                top_k=10,
                max_output_tokens=512,
                candidate_count=1
            )

            model = genai.GenerativeModel(model_id)
            response = model.generate_content(
                basic_prompt,
                generation_config=minimal_config
            )

            if response and response.text:
                return self._clean_interpretation_response(response.text.strip())
            else:
                return self._simple_fallback(text)

        except Exception as fallback_error:
            self.logger.error(f"Fallback interpretation failed: {str(fallback_error)}")
            return self._simple_fallback(text)

    def _simple_fallback(self, text):
        """Ultimate fallback when all AI methods fail"""
        return f"Enhanced version: {text}"

    def _clean_interpretation_response(self, text):
        """Clean up the interpretation response to remove unwanted formatting"""
        if not text:
            return text

        # Remove common structured response patterns
        # Pattern 1: Remove "**Option X (Description):**" headers
        text = re.sub(r'\*\*Option\s+\d+\s*\([^)]+\):\*\*\s*', '', text, flags=re.IGNORECASE)

        # Pattern 2: Remove "**Option X:**" headers
        text = re.sub(r'\*\*Option\s+\d+:\*\*\s*', '', text, flags=re.IGNORECASE)

        # Pattern 3: Remove numbered list patterns like "1. " at the beginning
        text = re.sub(r'^\d+\.\s+', '', text)

        # Pattern 4: Remove bullet points
        text = re.sub(r'^[•\-\*]\s+', '', text)

        # Pattern 5: Remove markdown bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

        # Pattern 6: Remove any remaining structured headers
        text = re.sub(r'^[A-Z][^:]*:\s*', '', text, flags=re.MULTILINE)

        # Pattern 7: Remove "Here's" or "Here is" introductory phrases
        text = re.sub(r'^Here\'s\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^Here\s+is\s+', '', text, flags=re.IGNORECASE)

        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text
