# HamroPatro Rashifal Scraper

## About This Project

This is a Python web scraping project built as a learning exercise. The goal of this project is to automatically collect daily horoscope data (called Rashifal in Nepali) from the website hamropatro.com and save it in a structured format that can be used later. The project uses two popular Python libraries, requests and BeautifulSoup, to do all the work.

## What Website We Used

We scraped data from https://www.hamropatro.com/rashifal. HamroPatro is a popular Nepali calendar and astrology website. The rashifal page shows daily horoscope predictions for all twelve zodiac signs written in the Nepali language. Each zodiac sign has a short paragraph describing what the day looks like for people born under that sign.

## What We Have Done

We built a scraper that visits the rashifal page every time it is run and collects the horoscope text for all twelve zodiac signs. The scraped data is saved into two files, one in CSV format and one in JSON format, so it can be opened in Excel or used in other programs. We also built a history feature that keeps a record of every past scrape so you can look back at what the horoscopes said on previous days. On top of that, the program automatically detects whether the content on the website has changed since the last time it was run.

## How It Works

When you run the program, it starts in main.py which controls the whole process step by step. First it calls the fetch_page function in scraper.py which sends a request to the hamropatro website and downloads the HTML of the page. Then it calls the parse_rashifal function which uses BeautifulSoup to read through the HTML and find the zodiac sign names and their descriptions. After that, main.py calls functions from utils.py to save the data to CSV and JSON, update the history file, check for changes, and print everything neatly in the terminal.

## How We Scraped the Data

The website renders each zodiac sign inside an HTML container that has the sign name as a heading and the horoscope text as a paragraph next to it. We used BeautifulSoup to search through all the HTML tags and find the ones whose text matched one of the twelve Nepali zodiac sign names. Once we found a sign heading, we looked at the element right next to it to get the description text. If that did not work, we looked at the parent container. We also built a fallback method that scans every paragraph on the page for text that starts with a sign name, just in case the page layout changes in the future.

## Project Structure

The project is split into three Python files to keep things organized and easy to understand.

- main.py is the entry point. It runs the full pipeline from fetching to saving to printing.
- scraper.py handles fetching the webpage and parsing the HTML to extract the data.
- utils.py contains helper functions for saving to CSV, saving to JSON, managing history, detecting changes, and printing output.

## Setup Instructions

Make sure you have Python 3.10 or newer installed on your computer. You can check by running `python --version` in your terminal.

It is recommended to create a virtual environment before installing the dependencies. You can do that by running `python -m venv venv` and then activating it with `source venv/bin/activate` on Linux or Mac, or `venv\Scripts\activate` on Windows.

Once the virtual environment is active, install the required libraries by running this command inside the project folder:

```
pip install -r requirements.txt
```

After that, run the scraper with:

```
python main.py
```

## Output Files

After running the scraper, a folder called data will be created automatically with three files inside it. The file rashifal.csv contains the latest scrape in spreadsheet format. The file rashifal.json contains the same data in JSON format. The file history.json stores every past scrape so you can track changes over time. There is also a scraper.log file created in the project folder that records a detailed log of every run.

## Dependencies

The project uses three libraries listed in requirements.txt. The requests library is used to send HTTP requests to the website. The beautifulsoup4 library is used to parse the HTML and find the data we need. The lxml library is used as the HTML parser backend for BeautifulSoup because it is fast and reliable.
