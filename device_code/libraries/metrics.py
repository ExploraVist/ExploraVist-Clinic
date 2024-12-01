import time
from functools import wraps
from collections import defaultdict

# Store timing data as: {function_name: [(start_time, end_time, duration), ...]}
timing_data = defaultdict(list)

def timed(func):
    """
    A decorator that measures and stores execution timing data for functions.

    Records start time, end time, and duration for each function call.
    Data is stored in timing_data dictionary for later analysis.

    Parameters:
        func (callable): The function to be timed.

    Returns:
        callable: The wrapped function with added timing functionality.

    Usage:
        @timed
        def my_function():
            # Function logic here

        # After running functions, access timing data:
        print(timing_data)
        
        # Export to CSV:
        export_timing_data('timing_results.csv')
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        timing_data[func.__name__].append({
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        })
        
        print(f"{func.__name__} took {duration:.2f} seconds.")
        return result
    return wrapper

def export_timing_data(filename='data_log/timing_results.csv'):
    """
    Exports the timing data to a CSV file.

    Parameters:
        filename (str): Name of the output CSV file
    """
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['function_name', 'start_time', 'end_time', 'duration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for func_name, measurements in timing_data.items():
            for measurement in measurements:
                writer.writerow({
                    'function_name': func_name,
                    'start_time': measurement['start_time'],
                    'end_time': measurement['end_time'],
                    'duration': measurement['duration']
                })