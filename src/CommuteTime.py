import requests
import json
from src.logger_config import logger
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
OFFICE_LAT = os.getenv("OFFICE_LOCATION_LAT")
OFFICE_LONG = os.getenv("OFFICE_LOCATION_LONG")

CENTRAL_LAT = os.getenv("CENTRAL_LAT")
CENTRAL_LONG =os.getenv("CENTRAL_LONG")

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


class CommuteTime:
    def __init__(self, location, id):
        self.API_KEY = API_KEY
        self.id = id
        self.commute_to_office = None
        self.commute_to_central = None

        location = tuple(map(float, location.split(",")))
        ROOM_LAT=location[0]
        ROOM_LONG=location[1]

        args = [
            ('commute_to_office', (ROOM_LAT, ROOM_LONG), (OFFICE_LAT, OFFICE_LONG)),
            ('commute_to_central', (ROOM_LAT, ROOM_LONG), (CENTRAL_LAT, CENTRAL_LONG))
        ]
        for (attr, room, destination) in args:
            response = self._get_response(room, destination)
            val = self._parse_response(response)
            setattr(self, attr, val)

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
            "arrivalTime": f"{self._last_tuesday_9am()}",
            "computeAlternativeRoutes": False,
            "languageCode": "en-US",
            "units": "METRIC",
        }

        return requests.post(URL, headers=headers, json=payload)

    def _parse_response(self, response: requests.models.Response) -> str:
        if response.status_code == 200:
            data = response.json()
            if "routes" not in data or not data["routes"]:
                logger.warning(f"Couldn't find 'routes' in response for {self.id}")
                return "N/A"
            duration = data["routes"][0]["duration"]
            minutes = int(duration.replace("s", "")) // 60
            return f"{minutes} mins"
        else:
            print(f"Request failed: {response.text}")

    @staticmethod
    def _last_tuesday_9am() -> str:
        ref_date = datetime.today()
        offset = (ref_date.weekday() - 1) % 7  # 1 = Tuesday
        last_tuesday_date = ref_date - timedelta(days=offset)
        tuesday_9am = datetime.combine(last_tuesday_date.date(), time(9, 0))
        return tuesday_9am.strftime("%Y-%m-%dT%H:%M:%SZ")
