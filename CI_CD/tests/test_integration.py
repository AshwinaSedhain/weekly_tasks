"""
Integration tests — verify multiple calculator operations
working together to simulate real-world usage.
"""
from calculator import add, subtract, multiply, divide, power, square_root, absolute  # noqa: E501


def test_chain_add_multiply():
    # (10 + 5) * 2 = 30
    result = multiply(add(10, 5), 2)
    assert result == 30


def test_chain_subtract_divide():
    # (100 - 20) / 4 = 20
    result = divide(subtract(100, 20), 4)
    assert result == 20.0


def test_complex_expression():
    # ((3 + 7) * 5 - 10) / 4 = 10
    step1 = add(3, 7)
    step2 = multiply(step1, 5)
    step3 = subtract(step2, 10)
    result = divide(step3, 4)
    assert result == 10.0


def test_power_then_sqrt():
    # sqrt(2^4) = sqrt(16) = 4.0
    result = square_root(power(2, 4))
    assert result == 4.0


def test_absolute_after_subtract():
    # abs(3 - 10) = 7
    result = absolute(subtract(3, 10))
    assert result == 7
