from dataclasses import dataclass
from datetime import date
from typing import Optional
from collections import namedtuple

coordinates = namedtuple('Location', ['latitude', 'longitude'], defaults=[None, None])

@dataclass
class Room:
    status: str = ""
    url: str = ""
    id: Optional[str] = ""
    date_added: date = date.today()
    
    type: Optional[str] = None
    area: Optional[str] = None
    nearest_station: Optional[str] = None
    available_all_week: Optional[bool] = None

    direct_line_to_office: Optional[bool] = None
    location: Optional[str] = None
    location_1: Optional[str] = None
    location_2: Optional[str] = None

    average_price: Optional[int] = None
    average_deposit: Optional[int] = None

    available: Optional[str] = None
    minimum_term: Optional[str] = None
    maximum_term: Optional[str] = None

    bills_included: Optional[bool] = None
    broadband_included: Optional[bool] = None
    furnishings: Optional[bool] = None
    garden_or_patio: Optional[bool] = None
    living_room: Optional[bool] = None
    balcony_or_roof_terrace: Optional[bool] = None
    
    number_of_flatmates: Optional[int] = None
    total_number_of_rooms: Optional[int] = None
    room_sizes: Optional[list] = None
    score: Optional[float] = None
    image_url: str = ""

    poster_type: str = ""
    collective_word_count: int = 0
    preferable_poster_type: bool = False


@dataclass()
class PipelineConfig:
    check_for_expired_rooms: bool
    headless: bool
    number_of_pages: int
    min_rent: int
    max_rent: int
    output_path: str
    database_path: str
    ignored_ids_path: str
    favourite_ids_path: str
    messaged_ids_path: str
    domain: str
    update_database_only: bool

    def __post_init__(self):
        if self.number_of_pages < 0:
            raise ValueError("number_of_pages must be >= 0")
        
        if self.min_rent > self.max_rent:
            raise ValueError("min_rent cannot exceed max_rent")
