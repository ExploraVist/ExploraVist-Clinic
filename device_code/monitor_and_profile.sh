#!/bin/bash

# File paths
MPSTAT_LOG="data_log/cpu_usage.txt"       # Log file for mpstat
CSV_OUTPUT="data_log/cpu_usage.csv"       # Converted CSV file
PYTHON_SCRIPT="main.py"                   # Python script to profile
PY_SPY_OUTPUT="data_log/py_spy_output.svg"  # Output file for py-spy flamegraph
PYTHON_CSV_CONVERTER="convert_mpstat_to_csv.py"  # Python script for CSV conversion

# Function to clean up on Ctrl+C or script exit
cleanup() {
    echo "Stopping mpstat process..."
    kill $MPSTAT_PID 2>/dev/null  # Kill the mpstat process if it's running

    echo "Running Python CSV conversion script..."
    python3 "$PYTHON_CSV_CONVERTER" "$MPSTAT_LOG" "$CSV_OUTPUT"  # Run Python script to convert log to CSV

    echo "Stopping py-spy profiling..."
    kill $PY_SPY_PID 2>/dev/null  # Kill the py-spy process if still running

    echo "Monitoring and profiling completed."
    echo "CSV file created: $CSV_OUTPUT"
    echo "Py-spy flamegraph saved to: $PY_SPY_OUTPUT"
    exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup function
trap cleanup SIGINT

# Run `mpstat` in the background and save output to a file
echo "Starting mpstat and logging to $MPSTAT_LOG..."
mpstat -P ALL 1 > "$MPSTAT_LOG" &
MPSTAT_PID=$!  # Store the PID of the mpstat command

# Run py-spy on the Python script in the background
echo "Starting py-spy profiling on $PYTHON_SCRIPT..."
py-spy record --output "$PY_SPY_OUTPUT" -- python3 "$PYTHON_SCRIPT" &
PY_SPY_PID=$!  # Store the PID of the py-spy command

# Wait for the py-spy process to finish (if it ends naturally)
wait $PY_SPY_PID

# Perform cleanup
cleanup
