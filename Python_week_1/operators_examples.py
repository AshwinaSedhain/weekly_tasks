# Student Data (Variables & Types)
name = "Ashwina"
marks_math = 85
marks_science = 78
marks_english = 92


#using  ARITHMETIC OPERATORS

total = marks_math + marks_science + marks_english   # +
average = total / 3                                  # /
difference = marks_math - marks_science              # -
product = marks_math * 2                             # *
remainder = marks_math % 2                           # %
power = marks_math ** 2                              # **

print("Total:", total)
print("Average:", average)


# using  COMPARISON OPERATORS

print("Math > Science:", marks_math > marks_science)   # >
print("Math == English:", marks_math == marks_english) # ==
print("Science != English:", marks_science != marks_english) # !=
print("Math >= 80:", marks_math >= 80) # >=
print("Science <= 80:", marks_science <= 80) # <=


#use of  LOGICAL OPERATORS

passed = (marks_math >= 40 and marks_science >= 40 and marks_english >= 40)
excellent = (average > 80 or marks_english > 90)
not_failed = not (marks_math < 40)

print("Passed:", passed)
print("Excellent:", excellent)
print("Not Failed:", not_failed)


# using ASSIGNMENT OPERATORS

bonus = 5
bonus += 2   # same as bonus = bonus + 2
bonus *= 2   # same as bonus = bonus * 2

print("Bonus marks:", bonus)


#  using BITWISE OPERATORS

a = 5   # 0101
b = 3   # 0011

print("AND:", a & b)   # 0001 -> 1
print("OR:", a | b)    # 0111 -> 7
print("XOR:", a ^ b)   # 0110 -> 6
print("NOT a:", ~a)    # -(a+1)
print("Left Shift:", a << 1)  # 1010 -> 10
print("Right Shift:", a >> 1) # 0010 -> 2

#  use of MEMBERSHIP OPERATORS

subjects = ["Math", "Science", "English"]

print("Math in subjects:", "Math" in subjects)
print("History not in subjects:", "History" not in subjects)


# use of  IDENTITY OPERATORS
x = [1, 2, 3]
y = x
z = [1, 2, 3]

print("x is y:", x is y)     # True (same memory)
print("x is z:", x is z)     # False (different objects)
print("x == z:", x == z)     # True (same values)

if passed:
    if average >= 80:
        print(f"{name} got Distinction ")
    elif average >= 60:
        print(f"{name} got First Division")
    else:
        print(f"{name} Passed")
else:
    print(f"{name} Failed")