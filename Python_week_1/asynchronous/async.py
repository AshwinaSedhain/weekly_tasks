import asyncio
import time

print(" yo guys! I am ASYNCHRONOUS ")
async def task(name, seconds):
    print(f"{name} START ({seconds}s)")
    await asyncio.sleep(seconds)  # Non-blocking wait
    print(f"{name} DONE")
    return seconds

async def main():
    # ALL tasks TOGETHER
    results = await asyncio.gather(
        task("Email", 2),
        task("DB", 1),
        task("File", 3)
    )
    return results

start = time.time()
results = asyncio.run(main())
print(f"TOTAL: {time.time() - start:.2f}s (MAX=3s)")
print(f"Results: {results}")