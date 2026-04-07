import time

print(" Hi I am SYNCHRONOUS ")
def task(name, seconds):
    print(f"{name} START ({seconds}s)")
    time.sleep(seconds)       # BLOCKS - waits one by one
    print(f"{name} DONE")
    return seconds

# Run one by one
start = time.time()
task("Email", 2)
task("DB", 1) 
task("File", 3)
print(f"TOTAL: {time.time() - start:.2f}s (2+1+3=6s)")