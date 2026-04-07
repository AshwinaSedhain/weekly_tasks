def multiply_result(n):   # parameterized decorator
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result * n
        return wrapper
    return decorator


@multiply_result(3)
def get_number():
    return 5


print(get_number())