"""
Comprehensive debug script for Augment Agent issues
"""

import os
import sys
import time
import subprocess
import threading

def test_file_operations():
    """Test file creation, reading, and editing"""
    print("\n=== Testing File Operations ===")
    
    test_file_path = "augment_test_file.txt"
    
    # Create a test file
    try:
        with open(test_file_path, "w") as f:
            f.write("Line 1: This is a test file for Augment Agent debugging.\n")
            f.write("Line 2: This line will be edited.\n")
            f.write("Line 3: This line will remain unchanged.\n")
        
        print(f"✓ Created test file: {test_file_path}")
        
        # Read the test file
        with open(test_file_path, "r") as f:
            content = f.read()
        
        print(f"✓ Read test file content successfully")
        
        # Edit the test file
        with open(test_file_path, "r") as f:
            lines = f.readlines()
        
        lines[1] = "Line 2: This line has been edited successfully.\n"
        
        with open(test_file_path, "w") as f:
            f.writelines(lines)
        
        print(f"✓ Edited test file successfully")
        
        # Read the edited file
        with open(test_file_path, "r") as f:
            edited_content = f.read()
        
        print(f"✓ Read edited file content successfully")
        print(f"Edited content:\n{edited_content}")
        
        # Clean up
        os.remove(test_file_path)
        print(f"✓ Removed test file: {test_file_path}")
        
    except Exception as e:
        print(f"✗ Error in file operations: {str(e)}")
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def run_process(command, timeout=5):
    """Run a process and return its output"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        return {
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Process timed out"
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Error: {str(e)}"
        }

def test_process_handling():
    """Test process creation and handling"""
    print("\n=== Testing Process Handling ===")
    
    # Test a simple command
    print("Running a simple command (echo)...")
    result = run_process("echo Hello, Augment Agent!")
    
    if result["returncode"] == 0:
        print(f"✓ Command executed successfully")
        print(f"Output: {result['stdout'].strip()}")
    else:
        print(f"✗ Command failed with return code {result['returncode']}")
        print(f"Error: {result['stderr']}")
    
    # Test a Python command
    print("\nRunning a Python command...")
    result = run_process("python -c \"print('Hello from Python!')\"")
    
    if result["returncode"] == 0:
        print(f"✓ Python command executed successfully")
        print(f"Output: {result['stdout'].strip()}")
    else:
        print(f"✗ Python command failed with return code {result['returncode']}")
        print(f"Error: {result['stderr']}")

def main():
    """Main function to run all tests"""
    print("Starting Augment Agent comprehensive debug script...")
    
    # Test file operations
    test_file_operations()
    
    # Test process handling
    test_process_handling()
    
    print("\nAugment Agent comprehensive debug script completed.")

if __name__ == "__main__":
    main()
