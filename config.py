MAIN = {
    "use_database": True,
    "update_database": False,
    "headless": True,
    "number_of_pages": 10,
    "min_rent": "200",
    "max_rent": "1000",
    "filename": "database.xlsx",
}

CREATE_MAP = {
    "show_saved_listings": True,
    "show_old_listings": False,
    "show_new_listings": True,
    "min_score": 15,
}

FAVOURITES = []

SCORE_WEIGHTINGS = {
    "direct_line_to_office": 1,
    "commute_to_office": 5,
    "commute_to_central": 4,
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
