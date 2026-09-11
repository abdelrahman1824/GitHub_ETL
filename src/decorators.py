from time import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        end_time = time()

        print(f"{func.__name__} executed in {end_time - start_time} seconds")

        return result

    return wrapper