MAIN = {
    "use_with_database": True,
    "update_database": False,
    "headless": True,
    "number_of_pages": 1,
    "min_rent": "200",
    "max_rent": "900",
    "filename": "database.xlsx",
}

CREATE_MAP = {
    "show_saved_listings": True,
    "show_old_listings": False,
    "show_new_listings": True,
    "min_score": 15,
}

favourites = [
    "15488310",
    "17907139",
    "17904389",
    "17910459",
    "17046308",
    "17909831",
    "17907746",
    "17905276",
    "17915496",
    "16128927",
    "1377695252",
    "1377695252",
    "17921501",
    "11544880",
    "15955759",
    "1376839644",
    "1377526447",
]

SCORE_WEIGHTINGS = {
    "direct_line_to_office": 1,
    "commute_to_office": 5,
    "commute_to_central": 4,
    "minimum_term": 1,
    "bills_included?": 4,
    "broadband_included": 1,
    "garden/patio": 1,
    "living_room": 3,
    "balcony/rooftop_terrace": 1,
    "total_#_rooms": 2,
    "gender": 1,
    "average_price": 5,
}
