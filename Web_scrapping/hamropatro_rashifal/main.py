# main.py
# This is the main entry point of the project. Running this file starts
# the entire scraping process. It calls the functions from scraper.py to
# fetch and parse the data, then calls the functions from utils.py to save
# the data and print it in the terminal. It also checks whether the content
# has changed since the last time the scraper was run.
#
# Usage:
#     python main.py

import logging
import sys
from datetime import datetime

from scraper import fetch_page, parse_rashifal
from utils import (
    save_to_csv,
    save_to_json,
    save_to_history,
    detect_changes,
    print_rashifal,
)

# Setting up logging so that all messages from this file and the other
# modules are printed to the terminal and also saved to a log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


# Running the full scraping pipeline from start to finish. It fetches
# the page, parses the rashifal data, checks for changes, saves the
# results to CSV and JSON, updates the history file, and prints
# everything to the terminal.
def main():
    start_time = datetime.now()
    logger.info("HamroPatro Rashifal Scraper started at " + start_time.strftime("%Y-%m-%d %H:%M:%S"))

    # Step 1: Fetching the HTML from the website
    html = fetch_page()

    if html is None:
        logger.error("Could not retrieve the page. Exiting.")
        sys.exit(1)

    # Step 2: Parsing the HTML to extract zodiac sign names and descriptions
    rashifal_data = parse_rashifal(html)

    if not rashifal_data:
        logger.error("No rashifal data was extracted. The page structure may have changed.")
        sys.exit(1)

    # Step 3: Checking if the content is different from the last scrape
    has_changed = detect_changes(rashifal_data)

    if has_changed:
        print("\n  Content has CHANGED since the last scrape.\n")
    else:
        print("\n  Content is the same as the last scrape.\n")

    # Step 4: Saving the data to CSV and JSON files
    save_to_csv(rashifal_data)
    save_to_json(rashifal_data)

    # Step 5: Appending this run to the history file
    save_to_history(rashifal_data)

    # Step 6: Printing the results in the terminal
    print_rashifal(rashifal_data)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("Scraping completed in " + str(round(elapsed, 2)) + " seconds.")
    logger.info("Records saved: " + str(len(rashifal_data)))
    logger.info("Output files: data/rashifal.csv and data/rashifal.json")
    logger.info("History file: data/history.json")
    logger.info("Log file: scraper.log")


if __name__ == "__main__":
    main()
