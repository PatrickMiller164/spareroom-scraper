import unicodedata
from src.Room import Room
import pickle
from src.logger_config import logger
import re
from datetime import datetime, timedelta, time

def flush_print(i: int, list: list, msg: str) -> None:
    print(f"\r{msg}: {i}/{len(list)}.", end="", flush=True)

def normalise(x: int, min: int, max: int) -> float:
    return 1 - ((x - min) / (max - min))

def clean_string(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip().lower()

def read_file(file: str) -> list[Room]:
    try:
        with open(file, "rb") as f:
            rows = pickle.load(f)
    except FileNotFoundError:
        rows = []

    logger.info(f"Database currently has {len(rows)} listings")
    return rows

def write_file(file: str, rooms: list[Room]) -> None:
    with open(file, "wb") as f:
        pickle.dump(rooms, f)

    logger.info(f"File now has {len(rooms)} listings")

def string_to_number(string: str) -> int | None:
    match = re.search(r"[\d,]+", string)
    if not match:
        return None

    num_str = match.group().replace(",", "")
    return int(num_str)
    
def get_last_tuesday_9am() -> str:
    ref_date = datetime.today()
    offset = (ref_date.weekday() - 1) % 7  # 1 = Tuesday
    last_tuesday_date = ref_date - timedelta(days=offset)
    tuesday_9am = datetime.combine(last_tuesday_date.date(), time(9, 0))
    return tuesday_9am.strftime("%Y-%m-%dT%H:%M:%SZ")