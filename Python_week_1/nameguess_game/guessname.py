import time

grid = [
    ['A','B','C','D','E'],
    ['F','G','H','I','J'],
    ['K','L','M','N','O'],
    ['P','Q','R','S','T'],
    ['U','V','W','X','Y']
]

def display(g, show_index=True):
    for i in range(len(g)):
        if show_index:
            print(i, "->", end=" ")
        else:
            print("   ", end=" ")
        
        for j in range(len(g[i])):
            print(g[i][j], end="  ")
        print()
    print()

def get_choices(n, max_row):
    choices = []
    for i in range(n):
        r = int(input(f"Row {i+1} (0-{max_row}): "))
        choices.append(r)
    return choices

def transform(g, choices):
    temp = []
    
    # Step 1: select rows
    for i in range(len(choices)):
        row_index = choices[i]
        temp.append(g[row_index])
    
    # Step 2: transpose
    rows = len(temp)
    cols = len(temp[0])
    
    new_grid = []
    
    for i in range(cols):
        new_row = []
        for j in range(rows):
            new_row.append(temp[j][i])
        new_grid.append(new_row)
    
    return new_grid

def get_diagonal(g):
    result = ""
    for i in range(len(g)):
        result = result + g[i][i]
    return result


# MAIN
print("Think of your name\n")
display(grid)

n = int(input("Number of letters: "))

c1 = get_choices(n, 4)
g1 = transform(grid, c1)

print("\nAfter Round 1:")
display(g1)

c2 = get_choices(n, len(g1)-1)
g2 = transform(g1, c2)

print("\nFinal Grid:")
display(g2, False)

print("AAABRA KA DABRAA.....")
time.sleep(1)

result = get_diagonal(g2)

print("Your name is:", result)