"""
Test script for terminal issues
"""

import os
import sys
import time
import subprocess
import threading

def run_background_process():
    """Run a background process that outputs periodically"""
    # Create a temporary Python script
    temp_script = "temp_background.py"
    with open(temp_script, "w") as f:
        f.write("""
import time
print('Starting background process...')
for i in range(10):
    print(f'Background process: {i}')
    time.sleep(1)
print('Background process completed.')
""")

    # Run the script
    process = subprocess.Popen(
        ["python", temp_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(f"Started background process with PID: {process.pid}")
    return process

def main():
    """Main function to test terminal functionality"""
    print("Starting terminal test script...")

    temp_script = "temp_background.py"

    try:
        # Run a background process
        process = run_background_process()

        # Wait for a bit
        print("Waiting for 3 seconds...")
        time.sleep(3)

        # Check if the process is still running
        if process.poll() is None:
            print("Process is still running")

            # Read some output
            output, _ = process.communicate()
            print(f"Process output:\n{output}")
        else:
            print(f"Process has completed with return code: {process.returncode}")
            output, error = process.communicate()
            print(f"Process output:\n{output}")
            if error:
                print(f"Process error:\n{error}")
    finally:
        # Clean up the temporary script
        if os.path.exists(temp_script):
            os.remove(temp_script)
            print(f"Removed temporary script: {temp_script}")

    print("Terminal test script completed.")

if __name__ == "__main__":
    main()
