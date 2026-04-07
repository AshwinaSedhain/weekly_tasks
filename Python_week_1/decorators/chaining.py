def add_prefix(func):
    def wrapper():
        return "Hello " + func()
    return wrapper


def add_suffix(func):
    def wrapper():
        return func() + " !!!"
    return wrapper


@add_prefix
@add_suffix
def name():
    return "Ashwini"


print(name())