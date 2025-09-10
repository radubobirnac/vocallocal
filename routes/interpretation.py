from flask import Blueprint, request, jsonify
import traceback
import logging
from services.interpretation import InterpretationService

# Create blueprint
bp = Blueprint('interpretation', __name__, url_prefix='/api')

# Set up logging
logger = logging.getLogger(__name__)

# Initialize service
interpretation_service = InterpretationService()

@bp.route('/interpret', methods=['POST'])
def interpret_text():
    """
    Interpret text using AI models
    """
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        text = data.get('text')
        tone = data.get('tone', 'neutral')
        model = data.get('interpretation_model', 'gemini-2.5-flash-preview')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Log the request
        logger.info(f"Interpretation request: {len(text)} chars, tone: {tone}, model: {model}")
        
        # Process the interpretation
        result = interpretation_service.interpret(text, tone, model)
        
        # Return the result
        return jsonify({
            'interpretation': result,
            'model': model
        })
            
    except Exception as e:
        # Log the error
        error_details = traceback.format_exc()
        logger.error(f"Interpretation error: {str(e)}\n{error_details}")

        # Check for specific error types and provide helpful messages
        error_message = str(e)
        if "finish_reason" in error_message.lower() or "safety" in error_message.lower():
            error_message = "The content was filtered for safety reasons. Please try rephrasing your text."
        elif "empty response" in error_message.lower():
            error_message = "The AI service returned an empty response. Please try again."
        elif "api key" in error_message.lower():
            error_message = "API configuration error. Please contact support."

        # Return error response
        return jsonify({
            'error': error_message,
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500
