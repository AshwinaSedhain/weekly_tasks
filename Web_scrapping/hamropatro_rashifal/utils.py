# utils.py
# This file contains all the helper functions that are used by main.py.
# It is handling saving data to CSV and JSON files, loading and saving
# the scraping history, detecting whether the content has changed since
# the last scrape, and printing the results in a readable format in the terminal.

import csv
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "rashifal.csv")
JSON_FILE = os.path.join(DATA_DIR, "rashifal.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


# Creating the data folder if it does not already exist. This is called
# before any file is written so we never get a missing directory error.
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# Taking the list of rashifal dictionaries and writing them into a CSV file.
# Each row in the file represents one zodiac sign with its description,
# date, and the time it was scraped.
def save_to_csv(rashifal_list, filepath=CSV_FILE):
    ensure_data_dir()

    fieldnames = ["zodiac_sign", "description", "date", "scraped_at"]

    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rashifal_list)

        logger.info("Data saved to CSV: " + filepath)

    except IOError as e:
        logger.error("Failed to write CSV file: " + str(e))
        raise


# Taking the list of rashifal dictionaries and writing them into a JSON file.
# The ensure_ascii=False option is important here because the descriptions
# are in Nepali (Unicode) and we want them stored as readable text, not
# as escaped character codes.
def save_to_json(rashifal_list, filepath=JSON_FILE):
    ensure_data_dir()

    try:
        with open(filepath, mode="w", encoding="utf-8") as json_file:
            json.dump(rashifal_list, json_file, ensure_ascii=False, indent=4)

        logger.info("Data saved to JSON: " + filepath)

    except IOError as e:
        logger.error("Failed to write JSON file: " + str(e))
        raise


# Reading the history file and returning all past scrape records as a list.
# If the file does not exist yet, returning an empty list so the rest of
# the program does not crash on the very first run.
def load_history(filepath=HISTORY_FILE):
    if not os.path.exists(filepath):
        logger.debug("No history file found. Starting fresh.")
        return []

    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            history = json.load(f)
        logger.info("Loaded " + str(len(history)) + " historical scrape(s).")
        return history

    except (IOError, json.JSONDecodeError) as e:
        logger.warning("Could not read history file: " + str(e))
        return []


# Appending the current scrape results to the history file so that every
# past run is preserved. Each entry in the history stores the timestamp
# of when the scrape happened along with all the records from that run.
def save_to_history(rashifal_list, filepath=HISTORY_FILE):
    ensure_data_dir()

    history = load_history(filepath)

    entry = {
        "scraped_at": datetime.now().isoformat(),
        "records": rashifal_list,
    }
    history.append(entry)

    try:
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        logger.info("History updated. Total scrapes saved: " + str(len(history)))

    except IOError as e:
        logger.error("Failed to write history file: " + str(e))
        raise


# Comparing the freshly scraped data against the most recent entry in the
# history file to check if anything has changed. The comparison is done
# on the zodiac sign name and description text so that small differences
# in timestamps do not trigger a false change alert. Returning True if
# the content is different and False if it is the same.
def detect_changes(new_data, filepath=HISTORY_FILE):
    history = load_history(filepath)

    if not history:
        logger.info("No previous scrape found. Treating current data as new.")
        return True

    last_records = history[-1].get("records", [])

    def to_set(records):
        return {(r["zodiac_sign"], r["description"]) for r in records}

    new_set = to_set(new_data)
    old_set = to_set(last_records)

    if new_set != old_set:
        logger.info("Content has changed since the last scrape.")
        return True

    logger.info("No content changes detected since last scrape.")
    return False


# Printing all the scraped rashifal entries to the terminal in a clean
# and readable format. Each entry shows the zodiac sign name, the date,
# the time it was scraped, and the full horoscope description.
def print_rashifal(rashifal_list):
    print("\nHamroPatro Rashifal - Daily Horoscope\n")

    if not rashifal_list:
        print("No rashifal data found.")
        return

    for entry in rashifal_list:
        sign = entry.get("zodiac_sign", "Unknown")
        desc = entry.get("description", "No description available.")
        date = entry.get("date", "N/A")
        scraped_at = entry.get("scraped_at", "N/A")

        print("Zodiac Sign : " + sign)
        print("Date        : " + date)
        print("Scraped At  : " + scraped_at)
        print("Description :")

        # Wrapping the description text so it fits neatly within the terminal width
        words = desc.split()
        line = "  "
        for word in words:
            if len(line) + len(word) + 1 > 65:
                print(line)
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

        print("")

    print("Total signs scraped: " + str(len(rashifal_list)) + "\n")
