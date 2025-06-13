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

    def interpret(self, text, tone="neutral", model="gemini-1.5-flash"):
        """
        Enhanced interpretation with contextual understanding and rephrasing capabilities

        Args:
            text (str): The text to interpret
            tone (str): The tone for interpretation (professional, simplified, academic, ai-prompts, neutral, formal, casual)
            model (str): The model to use (gemini-1.5-flash, gpt-3.5-turbo, etc.)

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
            # Default to Gemini
            return self._interpret_with_gemini(prompt, "gemini-1.5-flash")

    def _create_enhanced_prompt(self, text, tone):
        """Create an enhanced prompt with contextual understanding and rephrasing capabilities"""

        # Minimal base prompt
        base_prompt = f"Rephrase the following text while maintaining its context: {text}\n\n"

        return base_prompt



    def _create_prompt(self, text, tone):
        """Legacy method for backward compatibility - redirects to enhanced prompt"""
        return self._create_enhanced_prompt(text, tone)

    def _interpret_with_gemini(self, prompt, model_name):
        """Use Gemini model for enhanced interpretation with optimized parameters"""
        try:
            # Map model name to actual model ID if needed
            model_id = model_name
            if model_name == "gemini-2.0-flash-lite":
                model_id = "gemini-2.0-flash-lite"
            elif model_name == "gemini-2.5-flash-preview-04-17":
                # This is the exact model ID used in the UI for "Gemini 2.5 Flash Preview"
                model_id = "gemini-2.5-flash-preview-04-17"
            elif model_name == "gemini-2.5-flash":
                # Map to the correct Gemini 2.5 Flash Preview model
                model_id = "gemini-2.5-flash-preview-04-17"

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

            # Extract and return the text
            if response and response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini API")

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

    def analyze_context(self, text, model="gemini-1.5-flash"):
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
            return self._interpret_with_gemini(prompt, "gemini-1.5-flash")

    def rephrase_text(self, text, style="clear", model="gemini-1.5-flash"):
        """
        Rephrase text for better clarity and understanding

        Args:
            text (str): The text to rephrase
            style (str): The rephrasing style (clear, simple, formal, casual)
            model (str): The model to use for rephrasing

        Returns:
            str: Rephrased text
        """
        prompt = f"Rephrase this text by maintaining the context: {text}"

        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            return self._interpret_with_gemini(prompt, "gemini-1.5-flash")

    def detect_intent(self, text, model="gemini-1.5-flash"):
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
            return self._interpret_with_gemini(prompt, "gemini-1.5-flash")