"""
Debug script for Augment Agent issues
"""

import os
import sys
import time

def main():
    """
    Main function to test Augment Agent functionality
    """
    print("Starting Augment Agent debug script...")
    
    # Test file editing
    test_file_path = "test_augment.txt"
    
    # Create a test file
    with open(test_file_path, "w") as f:
        f.write("This is a test file for Augment Agent debugging.\n")
        f.write("Line 2 of the test file.\n")
        f.write("Line 3 of the test file.\n")
    
    print(f"Created test file: {test_file_path}")
    
    # Read the test file
    with open(test_file_path, "r") as f:
        content = f.read()
    
    print(f"Test file content:\n{content}")
    
    # Clean up
    os.remove(test_file_path)
    print(f"Removed test file: {test_file_path}")
    
    print("Augment Agent debug script completed successfully.")

if __name__ == "__main__":
    main()
