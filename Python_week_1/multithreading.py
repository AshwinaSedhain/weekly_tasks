import threading
import time

def download_file(file_id):
    print(f"Starting download {file_id}")
    time.sleep(2)  # Simulate network delay (I/O)
    print(f"Finished download {file_id}")

start = time.time()
threads = []
for i in range(5):
    t = threading.Thread(target=download_file, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
print(f"Total time: {time.time() - start:.2f}s")
