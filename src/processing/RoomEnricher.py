import src.utils.utils as ut
from src.utils.types import coordinates

jubilee_stations = [
    "Stanmore", "Canons Park", "Queensbury", "Kingsbury", "Wembley Park", "Neasden", "Dollis Hill",
    "Willesden Green", "Kilburn", "West Hampstead", "Finchley Road", "Swiss Cottage", "St. John's Wood",
    "Baker Street", "Bond Street", "Green Park", "Westminster", "Waterloo", "Southwark", "London Bridge", 
    "Bermondsey", "Canada Water", "Canary Wharf", "North Greenwich", "Canning Town", "West Ham", "Stratford",
]

elizabeth_line_stations = [
    "Reading", "Twyford", "Maidenhead", "Taplow", "Burnham", "Slough", "Langley", "Iver", "West Drayton",
    "Hayes & Harlington", "Southall", "Hanwell", "West Ealing", "Ealing Broadway", "Acton Main Line",
    "Paddington", "Bond Street", "Tottenham Court Road", "Farringdon", "Liverpool Street", "Whitechapel",
    "Canary Wharf", "Custom House", "Woolwich", "Abbey Wood", "Stratford","Maryland", "Forest Gate",
    "Manor Park", "Ilford", "Seven Kings", "Goodmayes", "Chadwell Heath", "Romford", "Gidea Park",
    "Harold Wood", "Brentwood", "Shenfield",
]


class RoomEnricher:
    def __init__(self, commute_service):
        self.cs = commute_service
        self.direct_stations = [ut.clean_string(i) for i in jubilee_stations + elizabeth_line_stations]

    def enrich(self, room_data: dict):
        room_data['direct_line_to_office'] = self._check_station(room_data['nearest_station'])

        # Get listing location, run commute service if API KEY and location coordinates exist
        coords: coordinates = room_data['coordinates']
        if not coords or coords.latitude is None or coords.longitude is None:
            return room_data
        
        room_data['location'] = f"{coords.latitude}, {coords.longitude}"

        if not self.cs.API_KEY:
            return room_data
        
        if self.cs.L1.latitude and self.cs.L1.longitude:
            room_data['location_1'] = self.cs.get_commute(id=room_data['id'], start=coords, end=self.cs.L1)
        if self.cs.L2.latitude and self.cs.L2.longitude:
            room_data['location_2'] = self.cs.get_commute(id=room_data['id'], start=coords, end=self.cs.L2)

        return room_data

    def _check_station(self, station: str) -> bool:
        if not station:
            return False
        return True if ut.clean_string(station) in self.direct_stations else False
