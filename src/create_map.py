import folium
from folium.features import CustomIcon
from datetime import datetime
from config import CREATE_MAP, favourites


class CreateMap:
    def __init__(self, rows):
        self.map_center = [51.5074, -0.1278]
        self.map = folium.Map(
            location=self.map_center, tiles="Cartodb Positron", zoom_start=12
        )
        self.rows = rows
        self.blue_icon = (
            "/Users/patrickmiller/Coding/VSCode/spareroom/assets/marker-icon-blue.png"
        )
        self.grey_icon = (
            "/Users/patrickmiller/Coding/VSCode/spareroom/assets/marker-icon-grey.png"
        )
        self.yellow_icon = (
            "/Users/patrickmiller/Coding/VSCode/spareroom/assets/marker-icon-yellow.png"
        )

        self.filter_listings()

        if CREATE_MAP["show_saved_listings"]:
            self.create_and_add_popup(self.favourites, self.blue_icon)
        if CREATE_MAP["show_old_listings"]:
            self.create_and_add_popup(self.old_good_listings, self.grey_icon)
        if CREATE_MAP["show_new_listings"]:
            self.create_and_add_popup(self.new_good_listings, self.yellow_icon)

        self.map.save("output/map.html")

    def filter_listings(self):
        self.today = datetime.today().date()
        self.favourites = [x for x in self.rows if x["id"] in favourites]
        self.old_good_listings = [
            x
            for x in self.rows
            if x["score"] > CREATE_MAP["min_score"]
            and x["date_added"] != self.today
            and x["id"] not in self.favourites
        ]
        self.new_good_listings = [
            x
            for x in self.rows
            if x["score"] > CREATE_MAP["min_score"]
            and x["date_added"] == self.today
            and x["id"] not in self.favourites
        ]

    def create_and_add_popup(self, list, icon_url):
        for listing in list:
            location = tuple(map(float, listing["location"].split(",")))
            score = listing["score"]
            price = listing["average_price"]
            url = listing["url"]
            id = listing["id"]
            date_added = listing["date_added"]
            try:
                image_url = listing["image_url"]
            except:
                image_url = None

            popup_html = f"""
            <b>ID:</b> {id}<br>
            <b>Date added:</b> {date_added}<br>
            <b>Score:</b> {score}<br>
            <b>Price:</b> {price}<br>
            <a href="{url} target="_blank">View listing</a>
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
