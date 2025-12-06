import requests
from src.logger_config import logger
from src.utils import get_last_tuesday_9am
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

OFFICE_LAT = os.getenv("OFFICE_LOCATION_LAT")
OFFICE_LONG = os.getenv("OFFICE_LOCATION_LONG")

CENTRAL_LAT = os.getenv("CENTRAL_LAT")
CENTRAL_LONG =os.getenv("CENTRAL_LONG")

last_tuesday = get_last_tuesday_9am()

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

class CommuteService:
    def __init__(self) -> None:
        self.API_KEY = API_KEY
        self.last_tuesday = last_tuesday
        self.office_location = (OFFICE_LAT, OFFICE_LONG)
        self.central_location = (CENTRAL_LAT, CENTRAL_LONG)
        self.session = requests.Session()

    def get_commutes(self, id: str, start: tuple) -> str:
        r1 = self._get_response(start, self.office_location)
        r2 = self._get_response(start, self.central_location)

        office_commute = self._parse_response(id=id, response=r1)
        central_commute = self._parse_response(id=id, response=r2)
        return (office_commute, central_commute)

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
            print(f"Request failed: {response.text}")
