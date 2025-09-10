        # Handle model name formatting
        # Note: 04-17 model is deprecated, automatically mapping to working 05-20 model
        if model_name == 'gemini-2.5-flash-preview-04-17':
            # 04-17 model is deprecated - automatically use 05-20 instead
            model_name = "models/gemini-2.5-flash-preview-05-20"
        elif model_name == 'gemini-2.5-flash-preview' or model_name == 'gemini-2.5-flash-preview-05-20':
            # Direct mapping for both general and specific 05-20 model
            model_name = "models/gemini-2.5-flash-preview-05-20"
        elif 'gemini-2.5-flash' in model_name or model_name == 'gemini-2.5-flash':
            # Use working 05-20 model instead of deprecated 04-17
            model_name = "models/gemini-2.5-flash-preview-05-20"
        elif 'gemini-2.5-pro' in model_name:
            model_name = "models/gemini-2.5-pro-preview-03-25"