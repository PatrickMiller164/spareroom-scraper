from dataclasses import dataclass
from datetime import datetime

@dataclass
class Room:
    url: str = None
    id: str = None
    date_added: datetime = datetime.today().date()
    title: str = None
    type: str = None
    available_all_week: bool = None
    area: str = None
    postcode: str = None
    location: str = None
    nearest_station: str = None
    direct_line_to_office: bool = None
    commute_to_office: str = None
    commute_to_central: str = None
    score: int = None
    average_price: int = None
    average_deposit: int = None
    available: str = None
    minimum_term: str = None
    maximum_term: str = None
    bills_included: str = None
    broadband_included: str = None
    furnishings: str = None
    garden_or_patio: str = None
    living_room: str = None
    balcony_or_roof_terrace: str = None
    number_of_flatmates: int = None
    total_number_of_rooms: int = None
    occupation: str = None
    min_age: str = None
    max_age: str = None
    room_sizes: list = None
    image_url: str = None