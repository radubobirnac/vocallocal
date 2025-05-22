import logging
import os
import google.generativeai as genai
from openai import OpenAI

class InterpretationService:
    """Service for interpreting text using AI models"""
    
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
        Interpret text using the specified AI model
        
        Args:
            text (str): The text to interpret
            tone (str): The tone for interpretation (neutral, formal, casual)
            model (str): The model to use (gemini-1.5-flash, gpt-3.5-turbo, etc.)
            
        Returns:
            str: The interpretation result
        """
        self.logger.info(f"Interpreting text with {model}, tone: {tone}")
        
        # Create prompt based on tone
        prompt = self._create_prompt(text, tone)
        
        # Use appropriate model
        if "gemini" in model.lower():
            return self._interpret_with_gemini(prompt, model)
        elif "gpt" in model.lower():
            return self._interpret_with_openai(prompt, model)
        else:
            # Default to Gemini
            return self._interpret_with_gemini(prompt, "gemini-1.5-flash")
    
    def _create_prompt(self, text, tone):
        """Create a prompt based on the text and tone"""
        base_prompt = f"Please interpret the following text:\n\n{text}\n\n"
        
        if tone.lower() == "formal":
            base_prompt += "Provide a formal interpretation, using professional language."
        elif tone.lower() == "casual":
            base_prompt += "Provide a casual, conversational interpretation."
        else:
            base_prompt += "Provide a neutral, balanced interpretation."
            
        return base_prompt
    
    def _interpret_with_gemini(self, prompt, model_name):
        """Use Gemini model for interpretation"""
        try:
            # Map model name to actual model ID if needed
            model_id = model_name
            if model_name == "gemini":
                model_id = "gemini-1.5-flash"
                
            self.logger.info(f"Using Gemini model: {model_id}")
            
            # Generate content with Gemini
            model = genai.GenerativeModel(model_id)
            response = model.generate_content(prompt)
            
            # Extract and return the text
            if response and response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as e:
            self.logger.error(f"Gemini interpretation error: {str(e)}")
            raise
    
    def _interpret_with_openai(self, prompt, model_name):
        """Use OpenAI model for interpretation"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Check your API key.")
            
        try:
            self.logger.info(f"Using OpenAI model: {model_name}")
            
            # Generate content with OpenAI
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that interprets text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract and return the text
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("Empty response from OpenAI API")
                
        except Exception as e:
            self.logger.error(f"OpenAI interpretation error: {str(e)}")
            raise