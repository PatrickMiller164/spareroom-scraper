import unicodedata

def flush_print(i, list):
    print(f"\r{i}/{len(list)}. ", end="", flush=True)

def normalise(x: int, min: int, max: int) -> float:
    return 1 - ((x - min) / (max - min))

def clean_string(s):
    return unicodedata.normalize("NFKC", s).strip().lower()