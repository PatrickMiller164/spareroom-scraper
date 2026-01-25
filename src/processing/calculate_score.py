from config import SCORE_WEIGHTINGS
import src.utils.utils as ut
from src.utils.logger_config import logger
from src.utils.types import Room

def get_score(room: Room) -> float:
    """Calculate a composite score for a room.

    Each room attribute is converted into a normalised score between 0 and 1.
    Boolean metrics are scored as 1.0 (True) or 0.0 (False).
    Range-based metrics are normalised using predefined minimum and maximum values.
    Any missing or unhandled metrics contribute a score of 0.

    The final room score is calculated as a weighted sum of all metric scores,
    using the relative preferences defined in SCORE_WEIGHTINGS (config.py).

    Args:
        room: A populated Room instance containing the attributes used for scoring.

    Returns:
        The final room score, rounded to one decimal place.
    """
    BOOL_METRICS = {
        "direct_line_to_office",
        "bills_included",       
        "broadband_included",
        "furnishings",
        "garden_or_patio",
        "living_room",
        "balcony_or_rooftop_terrace",
        "preferable_poster_type"
    }

    RANGE_METRICS = {
        "location_1": (20, 60),
        "location_2": (20, 60),
        "minimum_term": (0, 12),
        "total_number_of_rooms": (2, 6),
        "average_price": (700, 1000),
        "collective_word_count": (0, 7)
    }

    metric_scores: dict[str, float] = {}

    for metric, _ in SCORE_WEIGHTINGS.items():
        val = getattr(room, metric, None)

        # Missing value
        if val is None:
            metric_scores[metric] = 0
            continue

        # Boolean metric
        if metric in BOOL_METRICS:
            metric_scores[metric] = 1.0 if val is True else 0.0
            continue

        # Range-based metric
        if metric in RANGE_METRICS:
            if isinstance(val, str):
                val = ut.string_to_number(val)

            if val is None:
                metric_scores[metric] = 0
                continue

            # A lower value is better for all metrics apart from collective_word_count
            min_v, max_v = RANGE_METRICS[metric]
            invert = True if metric != 'collective_word_count' else False
            metric_scores[metric] = ut.normalise(val, min_v, max_v, invert=invert)  
            continue

        logger.warning(f"Unhandled metric: {metric}")
        metric_scores[metric] = 0

    # Use relative weightings to calculate composite
    return round(
        sum(metric_scores[m] * SCORE_WEIGHTINGS[m] for m in metric_scores),
        1
    )
