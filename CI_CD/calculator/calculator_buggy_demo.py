# Bug fixed: divide now returns correct quotient
def divide_buggy(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b   # FIXED
