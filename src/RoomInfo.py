from bs4 import BeautifulSoup
import re
from src.logger_config import logger
from src.lists import jubilee_stations, elizabeth_line_stations
from datetime import datetime
from dataclasses import dataclass, fields
from src.utils import clean_string
from pprint import pprint

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
    score: str = None
    average_price: str = None
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
    gender: str = None
    min_age: str = None
    max_age: str = None
    room_1_bed_size: str = None
    room_1_price_pcm: str = None
    room_1_deposit: str = None
    room_2_bed_size: str = None
    room_2_price_pcm: str = None
    room_2_deposit: str = None
    room_3_bed_size: str = None
    room_3_price_pcm: str = None
    room_3_deposit: str = None
    room_4_bed_size: str = None
    room_4_price_pcm: str = None
    room_4_deposit: str = None
    image_url: str = None

class GetRoomInfo:
    room: Room
    
    def __init__(self, url: str, page, domain: str):
        self.page = page
        self.url = domain + url
        self.id = url.split("=")[1].split("&")[0]
        self.get_room_soup()

        # Start building a dictionary of room properties
        room_data = {
            "url": self.url,
            "id": self.id,
            "title": self._get_title(),
            "available_all_week": self._get_ul_feature_list(),
            "image_url": self._get_image_url(),
            "location": self._get_location_string()
        }

        # Get key features
        room_data.update(self._get_key_features())

        # Get feature list
        room_data.update(self._get_feature_list())

        # Format keys
        room_data = self._reformat_keys(room_data)

        station = room_data['nearest_station']
        room_data['direct_line_to_office'] = self._check_station(station)

        # Keep only valid keys and create Room dataclass object
        valid_keys = {f.name for f in fields(Room)}
        filtered_room_data = {k:v for k, v in room_data.items() if k in valid_keys}
        self.room = Room(**filtered_room_data)

    def get_room_soup(self):
        self.page.goto(self.url, timeout=10000)
        self.soup = BeautifulSoup(self.page.content(), "html.parser")

    def _get_key_features(self):
        key_names = ["type", "area", "postcode", "nearest_station"]
        key_features = dict.fromkeys(key_names)

        feature_list = self.soup.find("ul", class_="key-features")
        if feature_list:
            for i, feature in enumerate(feature_list.find_all("li")):
                text = feature.get_text(strip=True)
                if i == 0:
                    text = " ".join(
                        line.strip() for line in text.splitlines() if line.strip()
                    )
                elif i == 1:
                    text = " ".join(
                        word
                        for word in text.split()
                        if not any(char.isdigit() for char in word)
                    )
                elif i == 2:
                    text = text.split("Area")[0]
                elif i == 3:
                    text = text.split("Station")[0]
                key_features[key_names[i]] = text

        return key_features

    def _get_feature_list(self):
        features = {}

        feature_list = self.soup.find_all("dl", class_="feature-list")
        for i, dl in enumerate(feature_list):
            for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
                key = dt.get_text(strip=True)
                key = " ".join(
                    line.strip() for line in key.splitlines() if line.strip()
                )
                key = key.lower().replace(" ", "_")
                value = dd.get_text(strip=True)

                features[key] = value

        return features

    def _get_location(self):
        pattern = r'location:\s*{[^}]*latitude:\s*"([^"]+)",\s*longitude:\s*"([^"]+)"'
        match = re.search(pattern, str(self.soup))

        if match:
            latitude = round(float(match.group(1)), 6)
            longitude = round(float(match.group(2)), 6)
            return latitude, longitude
        else:
            logger.warning("Location not found")
            return None, None

    def _get_location_string(self):
        lat, lon = self._get_location()
        if lat is None and lon is None:
            return None
        return f"{lat}, {lon}"

    def _reformat_keys(self, room_data):

        RENAMING = {
            '#_flatmates': 'number_of_flatmates',
            '#_housemates': 'number_of_flatmates',
            'bills_included?': 'bills_included',
            'total_#_rooms': 'total_number_of_rooms',
            'garden/patio': 'garden_or_patio',
            'balcony/roof_terrace': 'balcony_or_roof_terrace'
        }

        CASTS = {
            'number_of_flatmates': int,
            'total_number_of_rooms': int
        }

        # Rename room attributes
        new = {}
        p = 1
        for attr, value in room_data.items():
            if "£" in attr and "double" in value:
                new[f"room_{p}_price_pcm"] = attr.replace("¬", "")
                new[f"room_{p}_bed_size"] = value
                p += 1
            elif "deposit" in attr:
                match = re.search(r"Room\s*(\d+)", attr, re.IGNORECASE)
                room_num = match.group(1) if match else "1"
                new[f"room_{room_num}_deposit"] = value

        for key in room_data.keys():
            if key in RENAMING.keys():
                new[RENAMING[key]] = room_data[key]
        room_data.update(new)

        # Cast to int if needed
        for key, value in room_data.items():
            if key in CASTS.keys() and value is not None:
                try:
                    new = CASTS[key](room_data[key])
                    room_data[key] = new
                except ValueError:
                    pass

        return room_data

    def _get_title(self) -> str:
        h1 = self.soup.find("h1", class_="ad_detail__heading")
        return h1.get_text(strip=True) if h1 else ""

    def _get_ul_feature_list(self) -> bool:
        feature_list = self.soup.find("ul", class_="feature-list")
        if feature_list:
            for feature in feature_list.find_all("li"):
                text = feature.get_text(strip=True)
                if text in [
                    "Room available Monday to Friday only",
                    "Room available weekends only",
                ]:
                    return False
        return True

    def _check_station(self, station) -> bool:

        #station = getattr(self, "nearest_station", None)
        if station is None:
            return False
        
        station = clean_string(station)
        
        list = jubilee_stations + elizabeth_line_stations
        list = [clean_string(i) for i in list]

        return station in list

    def _get_image_url(self) -> str:
        img_tag = self.soup.find("img", class_="photo-gallery__main-image")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
