"""Core calculator operations."""


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract(a, b):
    """Return the difference of a and b."""
    return a - b


def multiply(a, b):
    """Return the product of a and b."""
    return a * b


def divide(a, b):
    """Return the quotient of a divided by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def power(base, exp):
    """Raise base to the power of exp."""
    return base ** exp


def modulo(a, b):
    """Return remainder of a divided by b."""
    if b == 0:
        raise ValueError("Cannot modulo by zero")
    return a % b


def square_root(n):
    """Return the square root of n."""
    if n < 0:
        raise ValueError("Cannot take square root of a negative number")
    return n ** 0.5


def absolute(n):
    """Return the absolute value of n."""
    return abs(n)
