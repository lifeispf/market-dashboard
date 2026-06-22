import json
from pathlib import Path

from dotenv import load_dotenv

# Load .env once at import time so every entry point (FastAPI server, unittest,
# manual ingest scripts) sees FRED_API_KEY / KRX_* without each having to call it.
# config_loader is imported transitively by virtually everything that needs config.
load_dotenv(Path(__file__).parent / ".env")

CONFIG_PATH = Path(__file__).parent / "config.json"
SECTORS_PATH = Path(__file__).parent / "sectors.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_sectors():
    with open(SECTORS_PATH, encoding="utf-8") as f:
        return json.load(f)
