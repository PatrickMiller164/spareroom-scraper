import unicodedata
from src.Room import Room
import pickle
from src.logger_config import logger

def flush_print(i, list, msg):
    print(f"\r{msg}: {i}/{len(list)}.", end="", flush=True)

def normalise(x: int, min: int, max: int) -> float:
    return 1 - ((x - min) / (max - min))

def clean_string(s):
    return unicodedata.normalize("NFKC", s).strip().lower()

def read_file(file: str) -> list[Room]:
    try:
        with open(file, "rb") as f:
            rows = pickle.load(f)
    except FileNotFoundError:
        rows = []

    logger.info(f"Database currently has {len(rows)} listings")
    return rows

def write_file(file: str, rooms: Room) -> None:
    with open(file, "wb") as f:
        pickle.dump(rooms, f)

    logger.info(f"File now has {len(rooms)} listings")