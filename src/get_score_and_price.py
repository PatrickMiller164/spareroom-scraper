import re
from config import SCORE_WEIGHTINGS

def normalise(x: int, min: int, max: int) -> float:
    return 1 - ((x - min) / (max - min))

def get_score_and_price(row):
    # Get metrics from row dictionary
    metrics = [
        "direct_line_to_office",
        "commute_to_office",
        "commute_to_central",
        "minimum_term",
        "bills_included?",
        "broadband_included",
        "furnishings",
        "garden/patio",
        "living_room",
        "balcony/rooftop_terrace",
        "total_#_rooms",
        "gender",
        "room_1_price_pcm",
        "room_2_price_pcm",
        "room_3_price_pcm",
        "room_4_price_pcm",
    ]
    dic = {}
    for metric in metrics:
        dic[metric] = row.get(metric, None)

    # Get number from string
    price_keys = [
        "room_1_price_pcm",
        "room_2_price_pcm",
        "room_3_price_pcm",
        "room_4_price_pcm",
        "commute_to_office",
        "commute_to_central",
        "minimum_term",
        "total_#_rooms",
    ]
    prices = []
    for i in price_keys:
        try:
            match = re.search(r"[\d,]+", dic[i])
            if match:
                number = int(match.group())
                if "price_pcm" in i:
                    if "pw" in dic[i]:
                        number = int(number * 52 / 12)
                    prices.append(number)
                else:
                    dic[i] = number
        except (KeyError, TypeError, ValueError):
            pass
        if "price_pcm" in i:
            dic.pop(i, None)

    # Get average_price
    average_price = sum(prices) // len(prices) if prices else None
    dic["average_price"] = average_price

    # Calculate binary scores
    score = {}
    for key in dic.keys():
        if key == "direct_line_to_office":
            score[key] = int(dic[key] is True)
        elif key == "bills_included?":
            if dic[key] == "Yes":
                score[key] = 1
            elif dic[key] == "Some":
                score[key] = 0.5
            else:
                score[key] = 0
        elif key == "broadband_included":
            score[key] = int(dic[key] == "Yes")
        elif key == "garden/patio":
            score[key] = int(dic[key] == "Yes")
        elif key == "living_room":
            score[key] = int(dic[key] == "shared" or dic[key] == "own")
        elif key == "balcony/rooftop_terrace":
            score[key] = int(dic[key] == "Yes")
        elif key == "gender":
            score[key] = int(dic[key] != "Females preferred")

    # Calculate range scores
    range_keys = {
        "commute_to_office": [20, 60],
        "commute_to_central": [20, 60],
        "minimum_term": [0, 12],
        "total_#_rooms": [2, 6],
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

    return score, average_price
