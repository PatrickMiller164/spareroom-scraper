import os
import requests
from dotenv import load_dotenv
import src.utils.utils as ut
from src.utils.types import coordinates
from src.utils.logger_config import logger

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


class CommuteService:
    def __init__(self) -> None:
        """Initiliase the commute service"""
        load_dotenv()

        self.API_KEY = os.getenv("GOOGLE_API_KEY")
        self.L1 = coordinates(latitude=os.getenv("L1_LAT"), longitude=os.getenv("L1_LON"))
        self.L2 = coordinates(latitude=os.getenv("L2_LAT"), longitude=os.getenv("L2_LON"))

        if self.API_KEY is None:
            logger.warning("Skipping CommuteService: GOOGLE_API_KEY not found in .env")
        if not (self.L1.latitude and self.L1.longitude):
            logger.warning("Skipping commute service for location 1: L1_LAT or L1_LON missing in .env")
        if not (self.L2.latitude and self.L2.longitude):
            logger.warning("Skipping commute service for location 2: L2_LAT or L2_LON missing in .env")
        
        self._last_tuesday = ut.get_last_tuesday_9am()
        self._session = requests.Session()

    def get_commute(self, id: str, start: coordinates, end: coordinates) -> str:
        """Gets public transport commute time between start and end location.

        Start location is the room's location. End location is self.L1 or self.L2, which are 
        set by the user (e.g., user's workplace). The commute time is calculated using Google's 
        Routes API. To estimate a realistic commute time for the user, the calculated commute time 
        assumes public transport is used, and that he/she will arrive at the destination
        for 9 AM on a Tuesday.

        Args:
            id: The id number of the room (room.id)
            start: The start location coordinates in latitude/longitude
            end: The end location coordinates in latitude/longitude

        Returns:
            The commute time in minutes (e.g., "32 mins")
        """
        r = self._get_response(start, end)
        return self._parse_response(id=id, response=r)

    def _get_response(self, start: coordinates, end: coordinates) -> requests.models.Response:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
        }
        payload = {
            "origin": {
                "location": {"latLng": {"latitude": start.latitude, "longitude": start.longitude}}
            },
            "destination": {
                "location": {"latLng": {"latitude": end.latitude, "longitude": end.longitude}}
            },
            "travelMode": "TRANSIT",
            "transitPreferences": {"allowedTravelModes": "RAIL"},
            "arrivalTime": f"{self._last_tuesday}",
            "computeAlternativeRoutes": False,
            "languageCode": "en-US",
            "units": "METRIC",
        }
        return self._session.post(URL, headers=headers, json=payload)

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
            return "N/A"
