import unicodedata
import re
from datetime import datetime, timedelta, time

def flush_print(i: int, list: list, msg: str) -> None:
    """Print a progress message on the same line, flushing output immediately.

    Args:
        i: Current index or iteration number.
        list: List being iterated over (used to get total length).
        msg: Message prefix to display before progress count.
    """
    print(f"\r{msg}: {i}/{len(list)}.", end="", flush=True)

def normalise(x: int, min: int, max: int) -> float:
    """Normalize a value to a 0–1 scale, inverted.

    Maps `x` from the range [`min`, `max`] to a float between 0 and 1,
    where `min` maps to 1.0 and `max` maps to 0.0.

    Args:
        x: Value to normalize.
        min: Minimum of the original range.
        max: Maximum of the original range.

    Returns:
        Normalized value between 0.0 and 1.0.
    """
    return 1 - ((x - min) / (max - min))

def clean_string(s: str) -> str:
    """Normalize and clean a string.

    Applies Unicode NFKC normalization, strips leading and trailing whitespace,
    and converts the string to lowercase.

    Args:
        s: Input string to clean.

    Returns:
        The normalized, lowercase, and stripped string.
    """
    return unicodedata.normalize("NFKC", s).strip().lower()

def string_to_number(string: str) -> int | None:
    """Convert a numeric string with optional commas to an integer.

    Extracts the first sequence of digits (allowing commas) from the input string,
    removes commas, and converts it to an integer. Returns `None` if no digits are found.

    Args:
        string: Input string potentially containing a number.

    Returns:
        The extracted integer, or `None` if no number is found.
    """
    match = re.search(r"[\d,]+", string)
    if not match:
        return None

    num_str = match.group().replace(",", "")
    return int(num_str)
    
def get_last_tuesday_9am() -> str:
    """Return the datetime of the most recent Tuesday at 9:00 AM in UTC format.

    Calculates the last Tuesday relative to today and returns the time set to
    9:00 AM. The result is formatted as an ISO 8601 UTC string.

    Returns:
        A string representing last Tuesday at 9:00 AM in the format "YYYY-MM-DDTHH:MM:SSZ".
    """
    ref_date = datetime.today()
    offset = (ref_date.weekday() - 1) % 7  # 1 = Tuesday
    last_tuesday_date = ref_date - timedelta(days=offset)
    tuesday_9am = datetime.combine(last_tuesday_date.date(), time(9, 0))
    return tuesday_9am.strftime("%Y-%m-%dT%H:%M:%SZ")