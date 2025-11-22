"""
Gemini Model Manager

This module provides dynamic model discovery and fallback management for Gemini API.
It automatically queries available models and provides intelligent fallback when models
become deprecated or unavailable.
"""

import os
import json
import time
import requests
import logging
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta


class GeminiModelManager:
    """
    Centralized manager for Gemini model discovery and fallback handling.
    
    Features:
    - Dynamic model discovery via Gemini API
    - Intelligent fallback based on model capabilities
    - Two-tier caching (memory + persistent file)
    - Automatic model family detection
    """
    
    def __init__(self, api_key: str, logger: logging.Logger, cache_duration_hours: int = 24):
        """
        Initialize the Gemini Model Manager.

        Args:
            api_key: Gemini API key
            logger: Logger instance
            cache_duration_hours: How long to cache model data (default: 24 hours)
        """
        self.api_key = api_key
        self.logger = logger
        self.cache_duration = timedelta(hours=cache_duration_hours)

        # In-memory cache
        self._models_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None

        # Persistent cache file - use absolute path relative to this file's directory
        # This ensures it works in both development and deployment environments
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_file = os.path.join(current_dir, "gemini_models_cache.json")
        self.logger.debug(f"Gemini models cache file path: {self.cache_file}")
        
        # Model capability mappings
        self.capability_requirements = {
            'transcription': ['generateContent'],
            'translation': ['generateContent'],
            'tts': ['generateContent'],  # TTS models have special naming
            'interpretation': ['generateContent']
        }
        
        # Model family preferences (best to worst)
        self.model_family_preferences = [
            'gemini-2.5-flash',
            'gemini-2.5-pro', 
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash'
        ]
        
        self.logger.info("GeminiModelManager initialized with dynamic fallback support")
    
    def get_available_models(self, force_refresh: bool = False) -> Dict:
        """
        Get available Gemini models with caching.
        
        Args:
            force_refresh: Force refresh from API instead of using cache
            
        Returns:
            Dictionary containing model information
        """
        # Check if we can use cached data
        if not force_refresh and self._is_cache_valid():
            if self._models_cache:
                self.logger.debug("Using in-memory cached models")
                return self._models_cache
            
            # Try loading from persistent cache
            cached_data = self._load_persistent_cache()
            if cached_data:
                self.logger.debug("Using persistent cached models")
                self._models_cache = cached_data
                self._cache_timestamp = datetime.now()
                return cached_data
        
        # Fetch fresh data from API
        self.logger.info("Fetching fresh model data from Gemini API")
        try:
            models_data = self._fetch_models_from_api()
            
            # Update caches
            self._models_cache = models_data
            self._cache_timestamp = datetime.now()
            self._save_persistent_cache(models_data)
            
            return models_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch models from API: {e}")
            
            # Try to use stale cache as fallback
            cached_data = self._load_persistent_cache()
            if cached_data:
                self.logger.warning("Using stale cached data due to API failure")
                return cached_data
            
            # Return empty dict if all else fails
            self.logger.error("No cached data available, returning empty model list")
            return {"models": []}
    
    def get_best_model_for_capability(self, capability: str, preferred_model: Optional[str] = None) -> Tuple[str, bool, str]:
        """
        Get the best available model for a specific capability.
        
        Args:
            capability: Required capability ('transcription', 'translation', 'tts', 'interpretation')
            preferred_model: Preferred model name (optional)
            
        Returns:
            Tuple of (model_name, is_fallback, reason)
        """
        models_data = self.get_available_models()
        available_models = models_data.get("models", [])
        
        # If preferred model is specified and available, use it
        if preferred_model:
            for model in available_models:
                model_name = model.get("name", "").replace("models/", "")
                if model_name == preferred_model:
                    required_methods = self.capability_requirements.get(capability, [])
                    supported_methods = model.get("supportedGenerationMethods", [])
                    
                    if all(method in supported_methods for method in required_methods):
                        self.logger.debug(f"Preferred model {preferred_model} is available")
                        return preferred_model, False, "Preferred model available"
        
        # Find best fallback model
        return self._find_best_fallback(capability, available_models, preferred_model)

    def _find_best_fallback(self, capability: str, available_models: List[Dict], preferred_model: Optional[str]) -> Tuple[str, bool, str]:
        """Find the best fallback model for a capability."""
        required_methods = self.capability_requirements.get(capability, [])

        # Special handling for TTS models
        if capability == 'tts':
            tts_models = [m for m in available_models if 'tts' in m.get("name", "").lower()]
            if tts_models:
                best_tts = tts_models[0].get("name", "").replace("models/", "")
                reason = f"TTS fallback from {preferred_model}" if preferred_model else "Best TTS model"
                return best_tts, bool(preferred_model), reason

        # Find models that support required capabilities
        compatible_models = []
        for model in available_models:
            supported_methods = model.get("supportedGenerationMethods", [])
            if all(method in supported_methods for method in required_methods):
                model_name = model.get("name", "").replace("models/", "")
                compatible_models.append(model_name)

        if not compatible_models:
            # Emergency fallback - use first available model
            if available_models:
                fallback = available_models[0].get("name", "").replace("models/", "")
                return fallback, True, "Emergency fallback - no compatible models found"
            else:
                return "gemini-2.5-flash", True, "No models available - using hardcoded fallback"

        # Select best model based on family preferences
        for preferred_family in self.model_family_preferences:
            for model_name in compatible_models:
                if preferred_family in model_name:
                    reason = f"Fallback from {preferred_model}" if preferred_model else f"Best available for {capability}"
                    return model_name, bool(preferred_model), reason

        # Use first compatible model if no family preference matches
        fallback = compatible_models[0]
        reason = f"Fallback from {preferred_model}" if preferred_model else f"First compatible for {capability}"
        return fallback, bool(preferred_model), reason

    def _fetch_models_from_api(self) -> Dict:
        """Fetch model list from Gemini API."""
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Add metadata
        data["fetched_at"] = datetime.now().isoformat()
        data["total_models"] = len(data.get("models", []))

        self.logger.info(f"Fetched {data['total_models']} models from Gemini API")
        return data

    def _is_cache_valid(self) -> bool:
        """Check if in-memory cache is still valid."""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self.cache_duration

    def _load_persistent_cache(self) -> Optional[Dict]:
        """Load models from persistent cache file."""
        try:
            if not os.path.exists(self.cache_file):
                return None

            with open(self.cache_file, 'r') as f:
                data = json.load(f)

            # Check if cache is still valid
            fetched_at = datetime.fromisoformat(data.get("fetched_at", "1970-01-01"))
            if datetime.now() - fetched_at < self.cache_duration:
                return data
            else:
                self.logger.debug("Persistent cache expired")
                return None

        except Exception as e:
            self.logger.warning(f"Failed to load persistent cache: {e}")
            return None

    def _save_persistent_cache(self, data: Dict) -> None:
        """Save models to persistent cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved model cache to {self.cache_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save persistent cache: {e}")

    def register_fallback(self, original_model: str, fallback_model: str, reason: str) -> None:
        """Register a fallback mapping for future use."""
        self.logger.info(f"Fallback registered: {original_model} -> {fallback_model} ({reason})")
        # This could be extended to save fallback mappings to a file for persistence

    def clear_cache(self) -> None:
        """Clear both in-memory and persistent caches."""
        self._models_cache = None
        self._cache_timestamp = None

        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            self.logger.info("Model cache cleared")
        except Exception as e:
            self.logger.warning(f"Failed to clear persistent cache: {e}")

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get detailed information about a specific model."""
        models_data = self.get_available_models()
        available_models = models_data.get("models", [])

        for model in available_models:
            if model.get("name", "").replace("models/", "") == model_name:
                return model

        return None
