import requests
import json
from src.logger_config import logger
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
office_location_lat = os.getenv("OFFICE_LOCATION_LAT")
office_location_long = os.getenv("OFFICE_LOCATION_LONG")


class get_commute_time:
    def __init__(self, location, id):
        self.API_KEY = api_key
        self.office_location = (office_location_lat, office_location_long)
        self.central = (51.5074, -0.1278)
        self.room_location = tuple(map(float, location.split(",")))
        self.url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        self.id = id
        self.commute_to_office = None
        self.commute_to_central = None
        self.get_times()

    def get_times(self):
        # If dict exists, load dict else create dict
        try:
            with open("data/commutes_dic.json", "r") as f:
                dic = json.load(f)
        except:
            dic = {}

        # If ID in dict, retrieve commute time from dict, else send reqeuest to Routes API
        if self.id not in dic.keys():
            dic[self.id] = [None, None]

        # Getting commute_to_office
        try:
            self.commute_to_office = dic[self.id][0] or self.get_directions(
                self.room_location, self.office_location
            )
            dic[self.id][0] = self.commute_to_office
        except Exception as e:
            logger.warning(e)

        # Getting commute_to_central
        try:
            self.commute_to_central = dic[self.id][1] or self.get_directions(
                self.room_location, self.central
            )
            dic[self.id][1] = self.commute_to_central
        except Exception as e:
            logger.warning(e)

        with open("data/commutes_dic.json", "w") as f:
            json.dump(dic, f, indent=4)

    def get_directions(self, start, end):
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
            "arrivalTime": f"{self.last_tuesday_9am()}",
            "computeAlternativeRoutes": False,
            "languageCode": "en-US",
            "units": "METRIC",
        }

        response = requests.post(self.url, headers=headers, json=payload)

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
    def last_tuesday_9am():
        ref_date = datetime.today()
        offset = (ref_date.weekday() - 1) % 7  # 1 = Tuesday
        last_tuesday_date = ref_date - timedelta(days=offset)
        tuesday_9am = datetime.combine(last_tuesday_date.date(), time(9, 0))
        return tuesday_9am.strftime("%Y-%m-%dT%H:%M:%SZ")
