from typing import List

# Function with type hints
def calculate_average(numbers: List[int]) -> float:
    total = sum(numbers)
    return total / len(numbers)


# Correct data
nums = [10, 20, 30]
print("Average:", calculate_average(nums))


#  Intentional mistake (string inside int list)
#wrong_nums = [10, 20, "30"]


#right one
wrong_nums = [10, 20, 30]    

print("Average:", calculate_average(wrong_nums))