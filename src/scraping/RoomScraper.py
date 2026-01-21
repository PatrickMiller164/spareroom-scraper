import re
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from typing import Optional, Dict, Any
from bs4.element import Tag, PageElement

import src.utils.utils as ut
from src.utils.logger_config import logger
from src.services.CommuteService import coordinates


class RoomScraper:
    def __init__(self, page: Page, url: str):
        self.page = page
        self.url = url
        self.soup: BeautifulSoup = self._get_room_soup()
        #print(self.soup)

    def scrape_data(self) -> Dict[str, Any]:
        """Initialise room_data dictionary and scrape info from HTML"""
        room_data: Dict[str, Any] = {
            "url": self.url,
            "id": ut.get_id_from_url(url=self.url),
            "available_all_week": self._letting_available_all_week(),
            "image_url": self._get_image_url()
        }

        # Get key features and feature list
        room_data.update(self._get_key_features())
        room_data.update(self._get_feature_list())

        # Get room coordinates and location
        room_data['coordinates'] = self._get_location()

        # Get poster type
        room_data['poster_type'] = self._get_poster_type()

        # Get We Count
        room_data['collective_word_count'] = self._get_collective_word_count()

        return room_data

    def _get_room_soup(self) -> BeautifulSoup:
        self.page.goto(self.url, timeout=10000)
        html: str = self.page.content()
        return BeautifulSoup(html, "html.parser")

    def _get_text(self, page_element: Optional[PageElement], default: str = "") -> str:
        return page_element.get_text(strip=True) if page_element else default
    
    def _get_image_url(self) -> str:
        img_tag: Optional[Tag] = self.soup.select_one("img.photo-gallery__main-image")
        src = img_tag.get("src") if img_tag else None
        return str(src) if src else ""
    
    def _letting_available_all_week(self) -> bool:
        """Extract bool for whether room is available 24/7"""
        feature_list: Optional[Tag] = self.soup.select_one("ul.feature-list")
        if feature_list:
            for li in feature_list.find_all("li"):
                text = self._get_text(li)
                if text in ["Room available Monday to Friday only", "Room available weekends only"]:
                    return False
        return True

    def _get_key_features(self) -> Dict[str, str]:
        """Extract key features: type, area, postcode, nearest_station"""
        key_names = ["type", "area", "postcode", "nearest_station"]
        features: Dict[str, str] = dict.fromkeys(key_names, "")

        ul: Optional[Tag] = self.soup.select_one("ul.key-features")
        if not ul:
            return features

        for i, li in enumerate(ul.find_all("li")):
            text = self._get_text(li)
            if i == 0:
                text = " ".join(line.strip() for line in text.splitlines() if line.strip())
            elif i == 1:
                text = " ".join(word for word in text.split() if not any(c.isdigit() for c in word))
            elif i == 2:
                text = text.split("Area")[0]
            elif i == 3:
                text = text.split("Station")[0]

            if i < len(key_names):
                features[key_names[i]] = text
        return features

    def _get_feature_list(self) -> Dict[str, str]:
        """Get detailed dictionary of room features"""
        features: Dict[str, str] = {}
        for dl in self.soup.select("dl.feature-list"):
            dt_tags = dl.find_all("dt")
            dd_tags = dl.find_all("dd")
            for dt, dd in zip(dt_tags, dd_tags):
                key = "_".join(dt.get_text(strip=True).lower().split())
                value = dd.get_text(strip=True)
                features[key] = value
        return features
    
    def _get_location(self) -> coordinates:
        pattern = r'location:\s*{[^}]*latitude:\s*"([^"]+)",\s*longitude:\s*"([^"]+)"'
        match = re.search(pattern, str(self.soup))
        if match:
            try:
                latitude = round(float(match.group(1)), 6)
                longitude = round(float(match.group(2)), 6)
                return coordinates(latitude, longitude)
            except ValueError:
                logger.warning("Failed to parse location coordinates")
        else:
            logger.warning("Location not found")
        return coordinates()
        
    def _get_poster_type(self) -> str:
        poster_type_el = self.soup.select_one(".advertiser-info em")
        return self._get_text(poster_type_el)

    def _get_collective_word_count(self) -> int:
        element = self.soup.select_one("p.detaildesc")
        text = self._get_text(element)

        words = text.split(" ")

        COLLECTIVE_WORDS = {
            "we", "us", "our", "ours",
            "together", "household", "home",
            "shared", "sharing"
        }
        collective_words = [w for w in words if w in COLLECTIVE_WORDS]
        return len(collective_words)
