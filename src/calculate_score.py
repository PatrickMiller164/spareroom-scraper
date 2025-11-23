import re
from config import SCORE_WEIGHTINGS
from src.utils import normalise, string_to_number
from src.logger_config import logger

def get_score(room):

    # Get metrics from room dictionary
    metrics = [
        "direct_line_to_office",        # Yes/No
        "commute_to_office",            # Int
        "commute_to_central",           # Int
        "minimum_term",                 # Int   
        "bills_included",               # Yes/Some/No
        "broadband_included",           # Yes/No
        "furnishings",                  # Unfurnished/Furnished
        "garden_or_patio",              # Yes/No
        "living_room",                  # No/Shared
        "balcony_or_rooftop_terrace",   # No/Yes
        "total_number_of_rooms",        # Int    
        "average_price"                 # Int
    ]

    GOOD_VALS = ['Furnished', 'Yes', 'shared', 'Some']
    BAD_VALS = ['Unfurnished', 'No']

    # Calculate range scores
    range_keys = {
        "commute_to_office": (20, 60),
        "commute_to_central": (20, 60),
        "minimum_term": (0, 12),
        "total_number_of_rooms": (2, 6),
        "average_price": (700, 1000),
    }

    metric_scores = {}
    for m in metrics:

        val = getattr(room, m, None)
        if val is None:
            metric_scores[m] = 0
            continue

        if val in GOOD_VALS:
            #print(f"Giving {m},{val} a score of 1")
            metric_scores[m] = 1

        elif val in BAD_VALS:
            #print(f"Giving {m},{val} a score of 0")
            metric_scores[m] = 0

        else:
            #print(f"Attempting to parse val from {m}")
            if isinstance(val, str):
                val = string_to_number(val)
            if val:
                min = range_keys[m][0]
                max = range_keys[m][1]
                c_val = normalise(val, min, max)
                metric_scores[m] = c_val
            else:
                logger.warning(f"{m, val} couldn't be assigned a val")
                metric_scores[m] = 0

    # Use relative weightings to calculate composite
    score = {}
    for key, value in metric_scores.items():
        score[key] = value * SCORE_WEIGHTINGS[key]
    score = round(sum(score.values()), 1)

    return score
