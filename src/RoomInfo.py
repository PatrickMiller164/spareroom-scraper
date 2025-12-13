from bs4 import BeautifulSoup
import re
from src.logger_config import logger
from src.lists import jubilee_stations, elizabeth_line_stations
from dataclasses import fields
from src.utils import clean_string, string_to_number
from src.CommuteService import CommuteService, Location
from src.Room import Room

cs = CommuteService()
if cs.API_KEY is None:
    logger.warning("Skipping CommuteService as GOOGLE_API_KEY cannot be found in .env file")

if cs.L1.latitude is None or cs.L1.longitude is None:
    logger.warning("Skipping commute service for location 1 as at least one coordinate missing.")
    logger.warning("Ensure both L1_LAT and L1_LON are defined in the .env file")

if cs.L2.latitude is None or cs.L2.longitude is None:
    logger.warning("Skipping commute service for location 2 as at least one coordinate missing.")
    logger.warning("Ensure both L2_LAT and L2_LON are defined in the .env file")


class GetRoomInfo:
    room: Room
    
    def __init__(self, url: str, page, domain: str) -> None:
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
            "image_url": self._get_image_url()
        }

        # Get key features
        room_data.update(self._get_key_features())

        # Get feature list
        room_data.update(self._get_feature_list())

        station = room_data['nearest_station']
        room_data['direct_line_to_office'] = self._check_station(station)

        # Get listing location, run commute service if API KEY and location coordinates exist
        room_location = self._get_location()
        if room_location != (None, None):
            room_data['location'] = f"{room_location.latitude}, {room_location.longitude}"
            if cs.API_KEY:
                if cs.L1.latitude and cs.L1.longitude:
                    room_data['location_1'] = cs.get_commute(id=self.id, start=room_location, end=cs.L1)
                if cs.L2.latitude and cs.L2.longitude:
                    room_data['location_2'] = cs.get_commute(id=self.id, start=room_location, end=cs.L2)

        # Format, rename, and cast room_data dict
        room_data = self._reformat_keys(room_data)
        room_data = self._rename_keys(room_data)
        room_data = self._cast_keys(room_data)

        # Keep only valid keys and create Room dataclass object
        valid_keys = {f.name for f in fields(Room)}
        filtered_room_data = {k:v for k, v in room_data.items() if k in valid_keys}
        self.room = Room(**filtered_room_data)

    def get_room_soup(self) -> None:
        self.page.goto(self.url, timeout=10000)
        self.soup = BeautifulSoup(self.page.content(), "html.parser")

    def _get_key_features(self) -> dict:
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

    def _get_feature_list(self) -> dict:
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

    def _get_location(self) -> Location:
        pattern = r'location:\s*{[^}]*latitude:\s*"([^"]+)",\s*longitude:\s*"([^"]+)"'
        match = re.search(pattern, str(self.soup))

        if match:
            latitude = round(float(match.group(1)), 6)
            longitude = round(float(match.group(2)), 6)
            return Location(latitude, longitude)
        else:
            logger.warning("Location not found")
            return Location()

    def _reformat_keys(self, room_data: dict) -> dict:

        # Rename room attributes
        prices = []
        room_sizes = []
        deposits = []
        for key, value in room_data.items():

            if "£" in key and "double" in value:
                price = string_to_number(key)
                if 'pw' in key:
                    price = price * 52 / 12

                prices.append(price)
                room_sizes.append("double")

            elif "deposit" in key:
                deposit = string_to_number(value)
                deposits.append(deposit)

        if len(prices) > 0:
            room_data['average_price'] = int(sum(prices) / len(prices))

        if len(room_sizes) > 0:
            room_data['room_sizes'] = room_sizes

        if len(deposits) > 0:
            room_data['average_deposit'] = sum(deposits) / len(deposits)

        return room_data

    def _rename_keys(self, room_data: dict) -> dict:

        RENAMING = {
            '#_flatmates': 'number_of_flatmates',
            '#_housemates': 'number_of_flatmates',
            'bills_included?': 'bills_included',
            'total_#_rooms': 'total_number_of_rooms',
            'garden/patio': 'garden_or_patio',
            'balcony/roof_terrace': 'balcony_or_roof_terrace'
        }

        new = {RENAMING[k]: room_data[k] for k in room_data if k in RENAMING}

        room_data.update(new)
        return room_data

    def _cast_keys(self, room_data: dict) -> dict:

        CASTS = {
            'number_of_flatmates': int,
            'total_number_of_rooms': int
        }

        # Cast to int if needed
        for key, value in room_data.items():
            if key in CASTS.keys() and value is not None:
                try:
                    room_data[key] = CASTS[key](value)
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

    def _check_station(self, station: str) -> str:
        if station is None:
            return 'No'
        station = clean_string(station)
        list = jubilee_stations + elizabeth_line_stations
        list = [clean_string(i) for i in list]
        return 'Yes' if station in list else 'No'

    def _get_image_url(self) -> str:
        img_tag = self.soup.find("img", class_="photo-gallery__main-image")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
        
