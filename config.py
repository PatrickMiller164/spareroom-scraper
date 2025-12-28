CONFIG = {
    "check_for_expired_rooms": False,
    "headless": True,
    "number_of_pages": 1,
    "min_rent": "200",
    "max_rent": "1000",
    "filename": "database.xlsx",
}

MAP_SETTINGS = {
    "show_favourites": True,
    "show_new_listings": True,
    "min_score": 15,
}

SCORE_WEIGHTINGS = {
    "direct_line_to_office": 1,
    "location_1": 5,
    "location_2": 4,
    "minimum_term": 1,
    "bills_included": 4,
    "broadband_included": 1,
    "garden_or_patio": 1,
    "living_room": 3,
    "balcony_or_rooftop_terrace": 1,
    "total_number_of_rooms": 2,
    "gender": 1,
    "average_price": 5,
    "furnishings": 2
}
