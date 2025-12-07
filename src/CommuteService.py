import requests
from src.logger_config import logger
from src.utils import get_last_tuesday_9am
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

L1_LAT = os.getenv("L1_LAT")
L1_LON = os.getenv("L1_LON")

L2_LAT = os.getenv("L2_LAT")
L2_LON =os.getenv("L2_LON")

last_tuesday = get_last_tuesday_9am()

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

class CommuteService:
    def __init__(self) -> None:
        self.API_KEY = API_KEY
        self.last_tuesday = last_tuesday
        self.L1 = (L1_LAT, L1_LON)
        self.L2 = (L2_LAT, L2_LON)
        self.session = requests.Session()

    def get_commute(self, id: str, start: tuple, end: tuple) -> str:
        r = self._get_response(start, end)
        return self._parse_response(id=id, response=r)

    def _get_response(self, start: tuple, end: tuple) -> requests.models.Response:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
        }
        payload = {
            "origin": {
                "location": {"latLng": {"latitude": start[0], "longitude": start[1]}}
            },
            "destination": {
                "location": {"latLng": {"latitude": end[0], "longitude": end[1]}}
            },
            "travelMode": "TRANSIT",
            "transitPreferences": {"allowedTravelModes": "RAIL"},
            "arrivalTime": f"{self.last_tuesday}",
            "computeAlternativeRoutes": False,
            "languageCode": "en-US",
            "units": "METRIC",
        }
        return self.session.post(URL, headers=headers, json=payload)

    def _parse_response(self, id: str, response: requests.models.Response) -> str:
        if response.status_code == 200:
            data = response.json()
            if "routes" not in data or not data["routes"]:
                logger.warning(f"Couldn't find 'routes' in response for {id}")
                return "N/A"
            duration = data["routes"][0]["duration"]
            minutes = int(duration.replace("s", "")) // 60
            return f"{minutes} mins"
        else:
            logger.warning(f"Request failed: {response.text}")
