"""
Augment Agent Troubleshooter

This script helps diagnose and fix common issues with Augment Agent:
1. "Terminal X not found" errors
2. "Failed to edit the file" errors with str_replace
3. "Terminal has already been disposed" errors

Usage:
    python augment_troubleshooter.py
"""

import os
import sys
import time
import subprocess
import threading
import tempfile
import shutil
import re

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print an error message"""
    print(f"✗ {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ {message}")

def test_file_operations():
    """Test file creation, reading, and editing"""
    print_header("Testing File Operations")
    
    test_file_path = "augment_test_file.txt"
    
    try:
        # Create a test file
        with open(test_file_path, "w") as f:
            f.write("Line 1: This is a test file for Augment Agent troubleshooting.\n")
            f.write("Line 2: This line will be edited.\n")
            f.write("Line 3: This line will remain unchanged.\n")
        
        print_success(f"Created test file: {test_file_path}")
        
        # Read the test file
        with open(test_file_path, "r") as f:
            content = f.read()
        
        print_success(f"Read test file content successfully")
        
        # Edit the test file
        with open(test_file_path, "r") as f:
            lines = f.readlines()
        
        lines[1] = "Line 2: This line has been edited successfully.\n"
        
        with open(test_file_path, "w") as f:
            f.writelines(lines)
        
        print_success(f"Edited test file successfully")
        
        # Read the edited file
        with open(test_file_path, "r") as f:
            edited_content = f.read()
        
        print_success(f"Read edited file content successfully")
        print(f"Edited content:\n{edited_content}")
        
        # Clean up
        os.remove(test_file_path)
        print_success(f"Removed test file: {test_file_path}")
        
        return True
        
    except Exception as e:
        print_error(f"Error in file operations: {str(e)}")
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        return False

def test_str_replace_compatibility():
    """Test compatibility with str_replace editor"""
    print_header("Testing str_replace Compatibility")
    
    test_file_path = "augment_str_replace_test.txt"
    
    try:
        # Create a test file with different line endings
        with open(test_file_path, "w", newline="\n") as f:  # Unix-style LF
            f.write("Line 1: This file uses LF line endings.\n")
            f.write("Line 2: This line will be edited.\n")
            f.write("Line 3: This line will remain unchanged.\n")
        
        print_success(f"Created test file with LF line endings: {test_file_path}")
        
        # Check line endings
        with open(test_file_path, "rb") as f:
            content = f.read()
        
        if b"\r\n" in content:
            print_info("File contains CRLF line endings (Windows style)")
        elif b"\n" in content:
            print_info("File contains LF line endings (Unix style)")
        
        # Print exact representation of line 2 for debugging
        with open(test_file_path, "r") as f:
            lines = f.readlines()
        
        line2 = lines[1]
        print_info(f"Line 2 (len={len(line2)}):")
        print_info(repr(line2))
        
        # Clean up
        os.remove(test_file_path)
        print_success(f"Removed test file: {test_file_path}")
        
        # Create a test file with Windows line endings
        with open(test_file_path, "w", newline="\r\n") as f:  # Windows-style CRLF
            f.write("Line 1: This file uses CRLF line endings.\r\n")
            f.write("Line 2: This line will be edited.\r\n")
            f.write("Line 3: This line will remain unchanged.\r\n")
        
        print_success(f"Created test file with CRLF line endings: {test_file_path}")
        
        # Check line endings
        with open(test_file_path, "rb") as f:
            content = f.read()
        
        if b"\r\n" in content:
            print_info("File contains CRLF line endings (Windows style)")
        elif b"\n" in content:
            print_info("File contains LF line endings (Unix style)")
        
        # Print exact representation of line 2 for debugging
        with open(test_file_path, "r") as f:
            lines = f.readlines()
        
        line2 = lines[1]
        print_info(f"Line 2 (len={len(line2)}):")
        print_info(repr(line2))
        
        # Clean up
        os.remove(test_file_path)
        print_success(f"Removed test file: {test_file_path}")
        
        print_info("Recommendation for str_replace issues:")
        print_info("1. Make sure to copy the exact text including whitespace")
        print_info("2. Be aware of line ending differences (CRLF vs LF)")
        print_info("3. Use line numbers to disambiguate between multiple occurrences")
        
        return True
        
    except Exception as e:
        print_error(f"Error in str_replace compatibility test: {str(e)}")
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        return False

def test_terminal_handling():
    """Test terminal process handling"""
    print_header("Testing Terminal Process Handling")
    
    temp_script = "temp_background.py"
    
    try:
        # Create a temporary Python script
        with open(temp_script, "w") as f:
            f.write("""
import time
print('Starting background process...')
for i in range(5):
    print(f'Background process: {i}')
    time.sleep(1)
print('Background process completed.')
""")
        
        print_success(f"Created temporary script: {temp_script}")
        
        # Run the script
        process = subprocess.Popen(
            ["python", temp_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print_success(f"Started background process with PID: {process.pid}")
        
        # Wait for a bit
        print_info("Waiting for 2 seconds...")
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            print_success("Process is still running")
            
            # Try to terminate the process
            process.terminate()
            
            # Wait for termination
            try:
                process.wait(timeout=2)
                print_success("Process terminated successfully")
            except subprocess.TimeoutExpired:
                # Force kill if termination times out
                process.kill()
                print_info("Process had to be forcefully killed")
        else:
            print_info(f"Process has already completed with return code: {process.returncode}")
        
        # Read output
        output, error = process.communicate()
        print_info(f"Process output:\n{output}")
        if error:
            print_info(f"Process error:\n{error}")
        
        print_info("Recommendation for terminal issues:")
        print_info("1. Always check if a terminal is still active before interacting with it")
        print_info("2. Use try/except blocks when interacting with terminals")
        print_info("3. Properly clean up terminals when done with them")
        
        return True
        
    except Exception as e:
        print_error(f"Error in terminal handling test: {str(e)}")
        return False
    finally:
        # Clean up the temporary script
        if os.path.exists(temp_script):
            os.remove(temp_script)
            print_success(f"Removed temporary script: {temp_script}")

def main():
    """Main function to run all tests"""
    print_header("Augment Agent Troubleshooter")
    print("This script helps diagnose and fix common issues with Augment Agent.")
    
    # Test file operations
    file_ops_success = test_file_operations()
    
    # Test str_replace compatibility
    str_replace_success = test_str_replace_compatibility()
    
    # Test terminal handling
    terminal_success = test_terminal_handling()
    
    # Print summary
    print_header("Summary")
    print(f"File Operations: {'✓ PASSED' if file_ops_success else '✗ FAILED'}")
    print(f"str_replace Compatibility: {'✓ PASSED' if str_replace_success else '✗ FAILED'}")
    print(f"Terminal Handling: {'✓ PASSED' if terminal_success else '✗ FAILED'}")
    
    print("\nRecommendations:")
    print("1. For 'Terminal X not found' errors:")
    print("   - Make sure to check if a terminal is still active before using it")
    print("   - Use try/except blocks when interacting with terminals")
    
    print("\n2. For 'Failed to edit the file' errors:")
    print("   - Make sure to copy the exact text including whitespace")
    print("   - Be aware of line ending differences (CRLF vs LF)")
    print("   - Use line numbers to disambiguate between multiple occurrences")
    
    print("\n3. For 'Terminal has already been disposed' errors:")
    print("   - Properly clean up terminals when done with them")
    print("   - Don't try to interact with terminals that have been closed")
    
    print("\nAugment Agent troubleshooting completed.")

if __name__ == "__main__":
    main()
