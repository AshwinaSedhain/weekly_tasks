# scraper.py
# This file is responsible for fetching the webpage and extracting
# the rashifal data from it. It uses the requests library to download
# the page and BeautifulSoup to read through the HTML and find the
# zodiac sign names and their horoscope descriptions.

import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TARGET_URL = "https://www.hamropatro.com/rashifal"

# Setting a User-Agent header makes the request look like it is coming
# from a real browser. Many websites block requests that do not have this.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ne;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 15


# Sending a GET request to the given URL and returning the HTML content
# as a string. If anything goes wrong, such as a connection error or
# a timeout, the function logs the error and returns None so the rest
# of the program can handle it gracefully.
def fetch_page(url=TARGET_URL):
    logger.info("Fetching page: " + url)

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)

        # raise_for_status raises an error if the server returned a 4xx or 5xx code
        response.raise_for_status()

        logger.info("Page fetched successfully. Status code: " + str(response.status_code))
        return response.text

    except requests.exceptions.ConnectionError:
        logger.error("Connection error. Please check your internet connection.")
    except requests.exceptions.Timeout:
        logger.error("Request timed out after " + str(REQUEST_TIMEOUT) + " seconds.")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: " + str(e))
    except requests.exceptions.RequestException as e:
        logger.error("Unexpected request error: " + str(e))

    return None


# Taking the raw HTML string and parsing it using BeautifulSoup to find
# all twelve zodiac sign entries. For each sign, it is extracting the
# sign name and the horoscope description text. It is also recording
# today's date and the exact time the scraping happened.
def parse_rashifal(html):
    logger.info("Parsing HTML content.")

    soup = BeautifulSoup(html, "lxml")

    now = datetime.now()
    scraped_at = now.strftime("%Y-%m-%d %H:%M:%S")
    today_date = now.strftime("%Y-%m-%d")

    rashifal_list = []

    # These are the twelve zodiac sign names as they appear on the website in Nepali
    zodiac_signs_nepali = [
        "मेष", "बृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
        "तुला", "बृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
    ]

    # Some signs appear with alternate spellings on the site so we are
    # mapping them back to the standard name we want to store
    sign_aliases = {
        "वृष": "बृष",
        "वृश्चिक": "बृश्चिक",
    }

    sign_set = set(zodiac_signs_nepali) | set(sign_aliases.keys())

    # Searching through every HTML tag and collecting the ones whose
    # text exactly matches a zodiac sign name
    sign_elements = []
    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)
        if text in sign_set and tag.name in ("h2", "h3", "h4", "b", "strong", "span", "div", "p"):
            sign_elements.append(tag)

    logger.debug("Found " + str(len(sign_elements)) + " sign heading elements.")

    if sign_elements:
        rashifal_list = extract_from_headings(sign_elements, sign_aliases, scraped_at, today_date)

    # If the first approach found nothing, trying a simpler fallback method
    # that scans all text blocks for lines starting with a sign name
    if not rashifal_list:
        logger.warning("First strategy found no data. Trying fallback.")
        rashifal_list = extract_from_text_blocks(
            soup, zodiac_signs_nepali, sign_aliases, scraped_at, today_date
        )

    logger.info("Extracted " + str(len(rashifal_list)) + " rashifal entries.")
    return rashifal_list


# Going through each heading element that contains a zodiac sign name
# and looking for the description text nearby in the HTML structure.
# It is checking the next sibling element first, then the parent container,
# and finally the grandparent if needed.
def extract_from_headings(sign_elements, sign_aliases, scraped_at, today_date):
    results = []
    seen_signs = set()

    for sign_el in sign_elements:
        raw_sign = sign_el.get_text(strip=True)
        sign_name = sign_aliases.get(raw_sign, raw_sign)

        if sign_name in seen_signs:
            continue
        seen_signs.add(sign_name)

        description = ""

        # Trying the next sibling element first as the description usually sits right after the heading
        sibling = sign_el.find_next_sibling()
        if sibling:
            description = sibling.get_text(separator=" ", strip=True)

        # If the sibling text is too short, using the parent container's full text instead
        if len(description) < 20:
            parent = sign_el.parent
            if parent:
                full_text = parent.get_text(separator=" ", strip=True)
                description = full_text.replace(raw_sign, "", 1).strip()

        # Going one level higher if still not enough text
        if len(description) < 20 and sign_el.parent:
            grandparent = sign_el.parent.parent
            if grandparent:
                full_text = grandparent.get_text(separator=" ", strip=True)
                description = full_text.replace(raw_sign, "", 1).strip()

        if description:
            results.append({
                "zodiac_sign": sign_name,
                "description": description,
                "date": today_date,
                "scraped_at": scraped_at,
            })

    return results


# Scanning every paragraph and div on the page looking for text that
# starts with a zodiac sign name. This is a simpler fallback approach
# used when the heading-based strategy does not find any results.
def extract_from_text_blocks(soup, zodiac_signs, sign_aliases, scraped_at, today_date):
    results = []
    seen_signs = set()

    all_signs = zodiac_signs + list(sign_aliases.keys())

    for tag in soup.find_all(["p", "div", "li", "span"]):
        text = tag.get_text(separator=" ", strip=True)

        for sign in all_signs:
            if text.startswith(sign) and len(text) > len(sign) + 10:
                canonical = sign_aliases.get(sign, sign)
                if canonical in seen_signs:
                    continue
                seen_signs.add(canonical)

                description = text[len(sign):].strip(" :-")

                results.append({
                    "zodiac_sign": canonical,
                    "description": description,
                    "date": today_date,
                    "scraped_at": scraped_at,
                })
                break

    return results
