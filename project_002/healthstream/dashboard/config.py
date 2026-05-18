# Dashboard settings loaded from environment variables.
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL     = os.getenv("API_BASE_URL",     "http://api:8000")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))
PAGE_TITLE       = "Healthstream Analytics"
