import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
COOKIES_FILE = os.getenv("COOKIES_FILE") or None
