#!/usr/bin/env python3
"""
Comprehensive TTS Button Debug Script

This script helps debug why the interpretation TTS button is not working
by testing various aspects of the implementation.
"""

import os
import re

def check_html_elements():
    """Check if the HTML elements exist with correct IDs."""
    print("🔍 Checking HTML template for button elements...")
    
    html_file = "templates/index.html"
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return False
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required elements
    elements_to_check = [
        ('basic-play-interpretation-btn', 'Interpretation Play Button'),
        ('basic-stop-interpretation-btn', 'Interpretation Stop Button'),
        ('basic-interpretation', 'Interpretation Textarea'),
        ('basic-play-btn', 'Transcription Play Button (working)'),
        ('basic-stop-btn', 'Transcription Stop Button (working)'),
        ('basic-transcript', 'Transcription Textarea (working)'),
        ('basic-language', 'Language Select')
    ]
    
    results = {}
    for element_id, description in elements_to_check:
        pattern = f'id="{element_id}"'
        found = pattern in content
        results[element_id] = found
        status = "✅ FOUND" if found else "❌ NOT FOUND"
        print(f"  {description}: {status}")
    
    return all(results.values())

def check_javascript_structure():
    """Check the JavaScript file structure."""
    print("\n🔍 Checking JavaScript file structure...")
    
    js_file = "static/script.js"
    if not os.path.exists(js_file):
        print(f"❌ JavaScript file not found: {js_file}")
        return False
    
    with open(js_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check for key components
    checks = {
        'DOMContentLoaded': False,
        'speakText_function': False,
        'isMobileDevice_function': False,
        'basic_play_btn_handler': False,
        'basic_play_interpretation_btn_handler': False,
        'minimal_test': False,
        'dom_verification': False
    }
    
    for i, line in enumerate(lines, 1):
        if "document.addEventListener('DOMContentLoaded'" in line:
            checks['DOMContentLoaded'] = True
            print(f"  ✅ DOMContentLoaded found at line {i}")
        
        if "function speakText(" in line:
            checks['speakText_function'] = True
            print(f"  ✅ speakText function found at line {i}")
        
        if "function isMobileDevice(" in line:
            checks['isMobileDevice_function'] = True
            print(f"  ✅ isMobileDevice function found at line {i}")
        
        if "getElementById('basic-play-btn')" in line:
            checks['basic_play_btn_handler'] = True
            print(f"  ✅ Transcription TTS handler found at line {i}")
        
        if "getElementById('basic-play-interpretation-btn')" in line:
            checks['basic_play_interpretation_btn_handler'] = True
            print(f"  ✅ Interpretation TTS handler found at line {i}")
        
        if "MINIMAL TEST" in line:
            checks['minimal_test'] = True
            print(f"  ✅ Minimal test found at line {i}")
        
        if "DOM VERIFICATION" in line:
            checks['dom_verification'] = True
            print(f"  ✅ DOM verification found at line {i}")
    
    missing = [key for key, found in checks.items() if not found]
    if missing:
        print(f"  ❌ Missing components: {', '.join(missing)}")
        return False
    
    return True

def check_domcontentloaded_structure():
    """Check if the interpretation TTS code is inside DOMContentLoaded."""
    print("\n🔍 Checking DOMContentLoaded block structure...")
    
    js_file = "static/script.js"
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find DOMContentLoaded block
    dom_start = content.find("document.addEventListener('DOMContentLoaded'")
    if dom_start == -1:
        print("❌ DOMContentLoaded block not found")
        return False
    
    # Find the matching closing bracket
    # This is a simplified check - count opening and closing brackets
    bracket_count = 0
    dom_end = -1
    
    for i, char in enumerate(content[dom_start:], dom_start):
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
            if bracket_count == 0:
                dom_end = i
                break
    
    if dom_end == -1:
        print("❌ Could not find end of DOMContentLoaded block")
        return False
    
    dom_block = content[dom_start:dom_end]
    
    # Check if interpretation TTS code is inside
    interpretation_inside = "basic-play-interpretation-btn" in dom_block
    minimal_test_inside = "MINIMAL TEST" in dom_block
    
    print(f"  DOMContentLoaded block: {dom_start} to {dom_end}")
    print(f"  Interpretation TTS inside: {'✅ YES' if interpretation_inside else '❌ NO'}")
    print(f"  Minimal test inside: {'✅ YES' if minimal_test_inside else '❌ NO'}")
    
    return interpretation_inside

def generate_test_html():
    """Generate a simple test HTML file."""
    print("\n🔧 Generating test HTML file...")
    
    test_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TTS Button Debug Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        .result { background: #f0f0f0; padding: 10px; margin: 10px 0; font-family: monospace; }
        textarea { width: 100%; height: 100px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>TTS Button Debug Test</h1>
    
    <div>
        <h3>Test Elements (matching main page structure)</h3>
        <button id="basic-play-interpretation-btn" class="button">▶️ Play Interpretation</button>
        <button id="basic-stop-interpretation-btn" class="button">⏹️ Stop Interpretation</button>
        <br>
        <textarea id="basic-interpretation" placeholder="Interpretation text...">This is test interpretation text for TTS debugging.</textarea>
        <br>
        <select id="basic-language">
            <option value="en">English</option>
        </select>
    </div>
    
    <div>
        <h3>Test Results</h3>
        <div id="test-results" class="result">Test results will appear here...</div>
    </div>
    
    <script>
        // Simple test functions
        function isMobileDevice() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        }
        
        function speakText(sourceId, text, lang) {
            console.log('🎵 speakText called:', { sourceId, text: text.substring(0, 30) + '...', lang });
            document.getElementById('test-results').innerHTML += 
                `<div>✅ speakText called: ${sourceId}, ${text.length} chars, ${lang}</div>`;
        }
        
        // Test the button
        document.addEventListener('DOMContentLoaded', () => {
            console.log('🧪 Test page loaded');
            
            const playBtn = document.getElementById('basic-play-interpretation-btn');
            const textarea = document.getElementById('basic-interpretation');
            const langSelect = document.getElementById('basic-language');
            
            document.getElementById('test-results').innerHTML = 
                `<div>Button found: ${!!playBtn}</div>
                 <div>Textarea found: ${!!textarea}</div>
                 <div>Language select found: ${!!langSelect}</div>`;
            
            if (playBtn) {
                playBtn.addEventListener('click', () => {
                    console.log('🎵 Button clicked!');
                    
                    const text = textarea.value;
                    const lang = langSelect.value;
                    
                    document.getElementById('test-results').innerHTML += 
                        `<div>🎵 Button clicked! Text: ${text.length} chars</div>`;
                    
                    if (isMobileDevice()) {
                        setTimeout(() => {
                            speakText('basic-interpretation', textarea.value, lang);
                        }, 50);
                    } else {
                        speakText('basic-interpretation', text, lang);
                    }
                });
            }
        });
    </script>
</body>
</html>"""
    
    with open("test_tts_simple.html", 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("  ✅ Test HTML file created: test_tts_simple.html")

def main():
    """Run all debug checks."""
    print("🚀 TTS Button Comprehensive Debug")
    print("=" * 50)
    
    # We're already in the correct directory
    
    html_ok = check_html_elements()
    js_ok = check_javascript_structure()
    dom_ok = check_domcontentloaded_structure()
    
    generate_test_html()
    
    print("\n📊 Debug Summary")
    print("=" * 50)
    print(f"HTML Elements: {'✅ PASS' if html_ok else '❌ FAIL'}")
    print(f"JavaScript Structure: {'✅ PASS' if js_ok else '❌ FAIL'}")
    print(f"DOMContentLoaded Structure: {'✅ PASS' if dom_ok else '❌ FAIL'}")
    
    if all([html_ok, js_ok, dom_ok]):
        print("\n🎉 All checks passed! The issue might be elsewhere.")
        print("💡 Try opening test_tts_simple.html to test button functionality.")
    else:
        print("\n⚠️ Some checks failed. Review the issues above.")

if __name__ == "__main__":
    main()
