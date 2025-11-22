from bs4 import BeautifulSoup
import re
from src.logger_config import logger
from src.lists import jubilee_stations, elizabeth_line_stations
import unicodedata
from datetime import datetime

class RoomInfo:
    def __init__(self, url, page, domain):
        self.page = page
        self.url = domain + url
        self.id = url.split("=")[1].split("&")[0]
        self.get_room_soup()
        self.latitude, self.longitude = self.get_location()
        self.location = f"{self.latitude}, {self.longitude}"
        self.title = self.get_title()
        self.available_all_week = self.get_ul_feature_list()
        self.score = None
        self.average_price = None
        self.date_added = datetime.today().date()
        self.image_url = self.get_image_url()

        key_features = self.get_key_features()
        [setattr(self, k, v) for k, v in key_features.items()]

        features = self.get_feature_list()
        [setattr(self, k, v) for k, v in features.items()]

        setattr(self, "direct_line_to_office", self.check_station())

        self.reformat_keys()

    def get_room_soup(self):
        self.page.goto(self.url, timeout=10000)
        self.soup = BeautifulSoup(self.page.content(), "html.parser")

    def get_key_features(self):
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

    def get_feature_list(self):
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

    def get_location(self):
        pattern = r'location:\s*{[^}]*latitude:\s*"([^"]+)",\s*longitude:\s*"([^"]+)"'
        match = re.search(pattern, str(self.soup))

        if match:
            latitude = round(float(match.group(1)), 6)
            longitude = round(float(match.group(2)), 6)
            return latitude, longitude
        else:
            logger.warning("Location not found")
            return None, None

    def reformat_keys(self):
        dic = {}
        p = 1

        for attr, value in self.__dict__.items():
            if "£" in attr and "double" in value:
                dic[f"room_{p}_price_pcm"] = attr.replace("¬", "")
                dic[f"room_{p}_bed_size"] = value
                dic[attr] = value
                p += 1
            elif "deposit" in attr:
                match = re.search(r"Room\s*(\d+)", attr, re.IGNORECASE)
                room_num = match.group(1) if match else "1"
                dic[f"room_{room_num}_deposit"] = value
            elif "housemates" in attr:
                dic["#_flatmates"] = value

        for k, v in dic.items():
            setattr(self, k, v)

    def get_title(self):
        h1 = self.soup.find("h1", class_="ad_detail__heading")
        if h1:
            return h1.get_text(strip=True)
        else:
            return None

    def get_ul_feature_list(self):
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

    def check_station(self):
        def clean_string(s):
            return unicodedata.normalize("NFKC", s).strip().lower()

        x = getattr(self, "nearest_station")
        if x is not None:
            x = clean_string(x)

        list = jubilee_stations + elizabeth_line_stations
        list = [clean_string(i) for i in list]

        return x in list

    def get_image_url(self):
        img_tag = self.soup.find("img", class_="photo-gallery__main-image")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
        else:
            return None
