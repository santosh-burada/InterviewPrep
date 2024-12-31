import sys
import subprocess

# Debugging: Print the arguments
print("Arguments received:", sys.argv)

if len(sys.argv) != 2:
    print("Usage: python run.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

# Debugging: Indicate file execution
print(f"Running file: {filename}")

try:
    # Run the file and capture its output
    result = subprocess.run(
        ["python", filename],
        text=True,  # Ensure output is a string (not bytes)
        capture_output=True,  # Capture stdout and stderr
        check=True  # Raise an exception if the command fails
    )

    # Print the captured output
    print("Output of the executed file:")
    print(result.stdout)

    # Print errors, if any
    if result.stderr:
        print("Errors during execution:")
        print(result.stderr)

except subprocess.CalledProcessError as e:
    print(f"Execution failed with return code {e.returncode}")
    print("Error output:")
    print(e.stderr)


