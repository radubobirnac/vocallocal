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
        model = data.get('interpretation_model', 'gemini-1.5-flash')
        
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
        
        # Return error response
        return jsonify({
            'error': str(e),
            'errorType': type(e).__name__,
            'details': 'See server logs for more information'
        }), 500