"""
Test script for str_replace editor issues
"""

import os
import sys
import time

def create_test_file():
    """Create a test file for str_replace testing"""
    test_file_path = "test_str_replace.txt"
    
    with open(test_file_path, "w") as f:
        f.write("Line 1: This is a test file for str_replace testing.\n")
        f.write("Line 2: This line will be edited.\n")
        f.write("Line 3: This line will remain unchanged.\n")
    
    print(f"Created test file: {test_file_path}")
    return test_file_path

def read_file(file_path):
    """Read a file and return its content"""
    with open(file_path, "r") as f:
        content = f.read()
    return content

def main():
    """Main function to test str_replace functionality"""
    print("Starting str_replace test script...")
    
    # Create a test file
    test_file_path = create_test_file()
    
    # Read the test file
    content = read_file(test_file_path)
    print(f"Original content:\n{content}")
    
    # Print exact representation of line 2 for debugging
    with open(test_file_path, "r") as f:
        lines = f.readlines()
    
    line2 = lines[1]
    print(f"Line 2 (len={len(line2)}):")
    print(repr(line2))
    
    # Edit the test file manually
    with open(test_file_path, "r") as f:
        lines = f.readlines()
    
    lines[1] = "Line 2: This line has been edited manually.\n"
    
    with open(test_file_path, "w") as f:
        f.writelines(lines)
    
    print(f"Edited test file manually")
    
    # Read the edited file
    edited_content = read_file(test_file_path)
    print(f"Edited content:\n{edited_content}")
    
    # Clean up
    os.remove(test_file_path)
    print(f"Removed test file: {test_file_path}")
    
    print("str_replace test script completed.")

if __name__ == "__main__":
    main()
