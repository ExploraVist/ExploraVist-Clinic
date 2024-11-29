#!/bin/bash

# File paths
PYTHON_SCRIPT="main.py"    # Replace with your Python script
TOP_LOG="data_log/top_log.txt"                    # Log file for top
PY_SPY_OUTPUT="data_log/py_spy_output.svg"        # Output file for py-spy flamegraph

# Run `top` in the background and save output to a file
echo "Starting top and logging to $TOP_LOG..."
top -b -d 1 > "$TOP_LOG" &
TOP_PID=$!  # Store the PID of the top command

# Run py-spy on the Python file
echo "Starting py-spy profiling on $PYTHON_SCRIPT..."
py-spy record --output "$PY_SPY_OUTPUT" -- python "$PYTHON_SCRIPT"

# Once py-spy finishes, kill the top process
echo "Stopping top process..."
kill $TOP_PID

echo "Monitoring and profiling completed."
echo "top log saved to: $TOP_LOG"
echo "py-spy flamegraph saved to: $PY_SPY_OUTPUT"
