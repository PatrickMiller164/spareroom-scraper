from config import SCORE_WEIGHTINGS
from src.utils import normalise, string_to_number
from src.logger_config import logger
from src.Room import Room

def get_score(room: Room) -> float:
    """Calculate the room's score

    Discrete metrics are normalised according to the defined GOOD_VALS and BAD_VALS.
    Continuous metrics are normalised according to the min and max values in range_keys.
    Once we have value between 0 and 1 for each metric, a composite is calculated
    according to the user's relative preferences (SCORE_WEIGHTINGS in config.py)

    Args:
        room: A populated Room object containing all properties to score the room.

    Returns:
        The room score (rounded to 1 DP)
    """

    # Get metrics from room dictionary
    metrics = [
        "direct_line_to_office",        # Yes/No
        "location_1",                   # Int
        "location_2",                   # Int
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
        "location_1": (20, 60),
        "location_2": (20, 60),
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
            logger.debug(f"Giving {m},{val} a score of 1")
            metric_scores[m] = 1

        elif val in BAD_VALS:
            logger.debug(f"Giving {m},{val} a score of 0")
            metric_scores[m] = 0

        else:
            logger.debug(f"Attempting to parse val from {m}")
            if isinstance(val, str):
                val = string_to_number(val)
            if val:
                min = range_keys[m][0]
                max = range_keys[m][1]
                c_val = normalise(val, min, max)
                metric_scores[m] = c_val
            else:
                logger.debug(f"When calculating score, {m}={val} couldn't be assigned a value")
                metric_scores[m] = 0

    # Use relative weightings to calculate composite
    return round(sum(v * SCORE_WEIGHTINGS[k] for k, v in metric_scores.items()), 1)
