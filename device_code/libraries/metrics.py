import time
import csv
from datetime import datetime

import time

class Metrics:
    def __init__(self):
        self.steps = []
        self.start_time = None

    def start(self):
        """Start tracking the total time."""
        self.start_time = time.time()

    def add_step(self, step_name, duration):
        """
        Add a step to the metrics.

        Parameters:
            step_name (str): Name of the step (function name).
            duration (float): Execution time of the step in seconds.
        """
        self.steps.append({"step": step_name, "time": duration})

    def get_total_time(self):
        """
        Calculate the total time from start to now.

        Returns:
            float: Total elapsed time in seconds.
        """
        return time.time() - self.start_time if self.start_time else None

    def clear(self):
        """Reset metrics for a new request."""
        self.steps = []
        self.start_time = None


def append_metrics_to_csv(metrics_file, timestamp, llm_model, steps, total_time):
    """
    Appends metrics data to a CSV file.
    
    Parameters:
        metrics_file (str): Path to the CSV file.
        timestamp (str): Timestamp of the request.
        llm_model (str): The LLM model used (e.g., GPT-4o-mini).
        steps (list of dict): List of steps with their timings.
        total_time (float): Total time for the entire request.
    """
    # Ensure the file exists or create it with headers
    with open(metrics_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow(["Timestamp", "LLM Model", "Step", "Timing (s)", "Total Time (s)"])
        
        # Write each step
        for step in steps:
            writer.writerow([
                timestamp, 
                llm_model, 
                step["name"], 
                step["time"], 
                total_time if step["is_last"] else ""
            ])


def timed(metrics):
    """
    Decorator to measure and log the execution time of a function.

    Parameters:
        metrics (Metrics): The Metrics object to log timings to.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.add_step(func.__name__, duration)
            print(f"{func.__name__} took {duration:.2f} seconds")
            return result
        return wrapper
    return decorator
