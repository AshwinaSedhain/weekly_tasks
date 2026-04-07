from multiprocessing import Process
import time
import os

def calculate_sum(n):
    total = sum(range(n))
    print(f"Process {os.getpid()}: Sum = {total}")

if __name__ == "__main__":
    import os
    processes = []
    start = time.time()
    
    for i in range(4):
        p = Process(target=calculate_sum, args=(10000000,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    print(f"Total time: {time.time() - start:.2f}s")
