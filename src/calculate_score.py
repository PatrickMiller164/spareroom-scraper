import re
from config import SCORE_WEIGHTINGS
from src.utils import normalise, string_to_number

def get_score(row):

    # Get metrics from row dictionary
    metrics = [
        "direct_line_to_office",
        "commute_to_office",
        "commute_to_central",
        "minimum_term",
        "bills_included",
        "broadband_included",
        "furnishings",
        "garden_or_patio",
        "living_room",
        "balcony_or_rooftop_terrace",
        "total_number_of_rooms",
        "gender",
        "average_price"
    ]

    keys_to_parse = [
        "commute_to_office",
        "commute_to_central",
        "minimum_term",
        "total_number_of_rooms",
    ]

    dic = {}
    for metric in metrics:
        value = getattr(row, metric, None)

        if metric in keys_to_parse and value is not None:
            dic[metric] = string_to_number(value)
        else:
            dic[metric] = value

    # Calculate binary scores
    score = {}
    for key in dic.keys():
        if key == "direct_line_to_office":
            score[key] = int(dic[key] is True)
        elif key == "bills_included":
            if dic[key] == "Yes":
                score[key] = 1
            elif dic[key] == "Some":
                score[key] = 0.5
            else:
                score[key] = 0
        elif key == "broadband_included":
            score[key] = int(dic[key] == "Yes")
        elif key == "garden_or_patio":
            score[key] = int(dic[key] == "Yes")
        elif key == "living_room":
            score[key] = int(dic[key] == "shared" or dic[key] == "own")
        elif key == "balcony_or_rooftop_terrace":
            score[key] = int(dic[key] == "Yes")
        elif key == "gender":
            score[key] = int(dic[key] != "Females preferred")

    # Calculate range scores
    range_keys = {
        "commute_to_office": [20, 60],
        "commute_to_central": [20, 60],
        "minimum_term": [0, 12],
        "total_number_of_rooms": [2, 6],
        "average_price": [700, 1000],
    }
    for key in range_keys.keys():

        val = dic[key]
        min = range_keys[key][0]
        max = range_keys[key][1]

        if isinstance(val, int):
            score[key] = normalise(val, min, max)
        else:
            score[key] = 0

    # Use relative weightings to calculate composite
    for key in score.keys():
        score[key] = score[key] * SCORE_WEIGHTINGS[key]
    score = round(sum(score.values()), 1)

    return score
