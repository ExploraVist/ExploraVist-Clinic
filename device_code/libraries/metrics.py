import time
import csv
import os
from functools import wraps

def ensure_directory_exists(filename):
    """Create directory for the file if it doesn't exist"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

def timed(func):
    """
    A decorator that logs function execution timing data to a CSV file.
    Each function call creates a new row with timing information.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        # Append timing data to CSV
        filename = 'data_log/timing_results.csv'
        ensure_directory_exists(filename)
        
        file_exists = os.path.exists(filename)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['function_name', 'start_time', 'end_time', 'duration'])
            writer.writerow([func.__name__, start_time, end_time, duration])
        
        print(f"{func.__name__} took {duration:.2f} seconds.")
        return result
    return wrapper