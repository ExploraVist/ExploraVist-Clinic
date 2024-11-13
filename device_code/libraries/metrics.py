import time

def timed(func):
    """
    A decorator that measures and prints the execution time of a function.

    This decorator wraps a function, recording the time before and after it executes.
    It then calculates and prints the elapsed time in seconds. This can be useful 
    for performance monitoring, especially for functions that make API calls or 
    perform other time-consuming tasks.

    Parameters:
        func (callable): The function to be timed.

    Returns:
        callable: The wrapped function with added timing functionality.

    Usage:
        Apply this decorator to any function you want to time. For example:
        
        @timed
        def my_function():
            # Function logic here

        When `my_function()` is called, it will execute normally, and the decorator
        will print the time taken for the execution.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print(f"{func.__name__} took {elapsed_time:.2f} seconds.")
        return result
    return wrapper