def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = ""
            for _ in range(n):
                result += func(*args, **kwargs) + "\n"
            return result
        return wrapper
    return decorator


def uppercase(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper



@repeat(3)
@uppercase

def message():
    return "hello ashwini"


print(message())