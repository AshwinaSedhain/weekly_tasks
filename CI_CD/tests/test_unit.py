"""Unit tests for calculator operations."""
import pytest
from calculator import (
    add, subtract, multiply, divide,
    power, modulo, square_root, absolute,
)


# --- add ---
def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-4, -6) == -10


def test_add_zero():
    assert add(0, 0) == 0


def test_add_mixed():
    assert add(-1, 1) == 0


# --- subtract ---
def test_subtract_positive():
    assert subtract(10, 4) == 6


def test_subtract_negative():
    assert subtract(0, 5) == -5


def test_subtract_same():
    assert subtract(7, 7) == 0


# --- multiply ---
def test_multiply_positive():
    assert multiply(3, 4) == 12


def test_multiply_negative():
    assert multiply(-2, 5) == -10


def test_multiply_zero():
    assert multiply(0, 100) == 0


# --- divide ---
def test_divide_normal():
    assert divide(10, 2) == 5.0


def test_divide_float():
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0)


# --- power ---
def test_power_positive():
    assert power(2, 10) == 1024


def test_power_zero_exp():
    assert power(3, 0) == 1


def test_power_square():
    assert power(5, 2) == 25


# --- modulo ---
def test_modulo_normal():
    assert modulo(10, 3) == 1


def test_modulo_even():
    assert modulo(20, 4) == 0


def test_modulo_by_zero():
    with pytest.raises(ValueError):
        modulo(5, 0)


# --- square_root ---
def test_square_root_perfect():
    assert square_root(9) == 3.0


def test_square_root_zero():
    assert square_root(0) == 0.0


def test_square_root_negative():
    with pytest.raises(ValueError):
        square_root(-1)


# --- absolute ---
def test_absolute_negative():
    assert absolute(-7) == 7


def test_absolute_positive():
    assert absolute(5) == 5


def test_absolute_zero():
    assert absolute(0) == 0
