import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
SECTORS_PATH = Path(__file__).parent / "sectors.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_sectors():
    with open(SECTORS_PATH, encoding="utf-8") as f:
        return json.load(f)
