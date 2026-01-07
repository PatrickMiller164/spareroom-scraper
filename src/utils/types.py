from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Room:
    status: str = ""
    url: str = ''
    id: Optional[str] = None
    date_added: date = date.today()
    title: Optional[str] = None
    type: Optional[str] = None
    available_all_week: Optional[bool] = None
    area: Optional[str] = None
    location: Optional[str] = None
    nearest_station: Optional[str] = None
    direct_line_to_office: Optional[bool] = None
    location_1: Optional[str] = None
    location_2: Optional[str] = None
    score: Optional[float] = None
    average_price: Optional[int] = None
    average_deposit: Optional[int] = None
    available: Optional[str] = None
    minimum_term: Optional[str] = None
    maximum_term: Optional[str] = None
    bills_included: Optional[str] = None
    broadband_included: Optional[str] = None
    furnishings: Optional[str] = None
    garden_or_patio: Optional[str] = None
    living_room: Optional[str] = None
    balcony_or_roof_terrace: Optional[str] = None
    number_of_flatmates: Optional[int] = None
    total_number_of_rooms: Optional[int] = None
    room_sizes: Optional[list] = None
    image_url: Optional[str] = None


@dataclass(frozen=True)
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
    domain: str

    def __post_init__(self):
        if self.number_of_pages < 1:
            raise ValueError("number_of_pages must be >= 1")
        
        if self.min_rent > self.max_rent:
            raise ValueError("min_rent cannot exceed max_rent")
