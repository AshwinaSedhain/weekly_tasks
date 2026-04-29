import pyautogui
import time
import random

print("Starting in 5 seconds... Move mouse to top-left corner to stop.")
time.sleep(5)

intervals = [120, 180]  # 2 min, 3 min
i = 0

try:
    while True:
        wait_time = intervals[i % 2]
        print(f"Waiting {wait_time} seconds...")

        time.sleep(wait_time)

        # --- Human-like small random mouse movement ---
        current_x, current_y = pyautogui.position()

        # Move slightly (random offset)
        new_x = current_x + random.randint(-50, 50)
        new_y = current_y + random.randint(-50, 50)

        pyautogui.moveTo(new_x, new_y, duration=0.5)
        pyautogui.moveTo(current_x, current_y, duration=0.5)

        # --- Switch tab ---
        pyautogui.hotkey('ctrl', 'tab')

        print("Moved cursor + switched tab")

        i += 1

except KeyboardInterrupt:
    print("Stopped by user.")
