#!/bin/bash

# File paths
MPSTAT_LOG="data_log/cpu_usage.txt"       # Log file for mpstat
CSV_OUTPUT="data_log/cpu_usage.csv"       # Converted CSV file
PYTHON_SCRIPT="main.py"                   # Python script to run
PYTHON_CSV_CONVERTER="libraries/convert_mpstat_to_csv.py"  # Python script for CSV conversion

# Function to clean up on Ctrl+C or script exit
cleanup() {
    echo "Stopping mpstat process..."
    kill $MPSTAT_PID 2>/dev/null  # Kill the mpstat process if it's running

    echo "Running Python CSV conversion script..."
    python3 "$PYTHON_CSV_CONVERTER" "$MPSTAT_LOG" "$CSV_OUTPUT"  # Run Python script to convert log to CSV

    echo "Monitoring and profiling completed."
    echo "CSV file created: $CSV_OUTPUT"
    exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup function
trap cleanup SIGINT

# Run `mpstat` in the background and save output to a file
echo "Starting mpstat and logging to $MPSTAT_LOG..."
mpstat -P ALL 1 > "$MPSTAT_LOG" &
MPSTAT_PID=$!  # Store the PID of the mpstat command

# Run the main Python script
echo "Running Python script: $PYTHON_SCRIPT..."
python3 "$PYTHON_SCRIPT"
MAIN_PYTHON_EXIT_CODE=$?  # Capture the exit code of the Python script

# After the Python script finishes, stop mpstat and generate the CSV
cleanup
