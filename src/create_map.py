import folium
from folium.features import CustomIcon
from datetime import date
from config import MAP_SETTINGS
from src.Room import Room

MAP_CENTER = (51.5074, -0.1278)

BLUE_ICON = "assets/marker-icon-blue.png"
GREY_ICON = "assets/marker-icon-grey.png"
YELLOW_ICON = "assets/marker-icon-yellow.png"


class CreateMap:
    def __init__(self, rooms: list[Room]) -> None:
        """Initialize the map, setting the center point as central London.

        Args:
            rooms: List of Room objects to display on the map.
        """
        self.map = folium.Map(location=MAP_CENTER, tiles="Cartodb Positron", zoom_start=12)
        self.rooms: list[Room] = rooms

        self.favourites: list = []
        self.new_listings: list = []

        self._show_favourites: bool = MAP_SETTINGS["show_favourites"]
        self._show_new_listings: bool = MAP_SETTINGS["show_new_listings"]

    def run(self):
        """Populate the map with room listings and markers.

        Filters the input room listings into favorites, old good listings, and
        new good listings. Creates and adds popups for each category based on
        configuration, then saves the map to "output/map.html".
        """
        self._filter_listings()

        if self._show_favourites and self.favourites:
            self._create_and_add_popup(self.favourites, YELLOW_ICON)
        if self._show_new_listings and self.new_listings:
            self._create_and_add_popup(self.new_listings, BLUE_ICON)

        self.map.save("output/map.html")

    def _filter_listings(self) -> None:
        self.favourites = [
            r for r in self.rooms
            if r.status.lower()=='favourite'
        ]
        self.new_listings = [
            r for r in self.rooms 
            if r.score > MAP_SETTINGS["min_score"]
            and r.date_added == date.today()
            and r not in self.favourites
        ]

    def _create_and_add_popup(self, rooms: list[Room], icon_url: str) -> None:
        for room in rooms:
            location = tuple(map(float, room.location.split(",")))
            score = room.score
            price = room.average_price
            url = room.url
            id = room.id
            date_added = room.date_added
            image_url = room.image_url

            popup_html = f"""
            <b>ID:</b> {id}<br>
            <b>Date added:</b> {date_added}<br>
            <b>Score:</b> {score}<br>
            <b>Price:</b> {price}<br>
            <a href="{url} target="_blank">View room</a>
            """

            if image_url:
                popup_html += f'<br><img src="{image_url}" width="100">'

            icon = CustomIcon(icon_image=icon_url, icon_size=(18, 27))

            folium.Marker(
                location=location,
                radius=5,
                popup=folium.Popup(popup_html, max_width=150),
                icon=icon,
            ).add_to(self.map)
