import folium
from folium.features import CustomIcon
from datetime import datetime
from config import CREATE_MAP, FAVOURITES
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

        self.all_favourites: list = []
        self.old_favourites: list = []
        self.new_favourites: list = []

        self._show_all_favourites: bool = CREATE_MAP["show_all_favourites"]
        self._show_old_favourites: bool = CREATE_MAP["show_old_favourites"]
        self._show_new_favourites: bool = CREATE_MAP["show_new_favourites"]


    def run(self):
        """Populate the map with room listings and markers.

        Filters the input room listings into favorites, old good listings, and
        new good listings. Creates and adds popups for each category based on
        configuration, then saves the map to "output/map.html".
        """
        self._filter_listings()

        if self._show_all_favourites:
            self._create_and_add_popup(self.all_favourites, BLUE_ICON)
        if self._show_old_favourites:
            self._create_and_add_popup(self.old_favourites, GREY_ICON)
        if self._show_new_favourites:
            self._create_and_add_popup(self.new_favourites, YELLOW_ICON)

        self.map.save("output/map.html")

    def _filter_listings(self) -> None:
        self.all_favourites = [
            x for x in self.rooms if 
            x.id in FAVOURITES
        ]

        today = datetime.today().date()
        self.old_favourites = [
            x for x in self.rooms if 
            x.score > CREATE_MAP["min_score"]
            and x.date_added != today
            and x.id not in self.all_favourites
        ]
        self.new_favourites = [
            x for x in self.rooms if 
            x.score > CREATE_MAP["min_score"]
            and x.date_added == today
            and x.id not in self.all_favourites
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
