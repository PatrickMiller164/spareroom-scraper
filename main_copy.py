import polars as pl
import pandas as pd
from src.SpareRoom import SpareRoom
from src.RoomInfo import GetRoomInfo
from src.Room import Room
from src.lists import output_cols
from src.logger_config import logger
from src.calculate_score import get_score
from src.utils import flush_print
from src.create_map import CreateMap
from config import CONFIG
from dataclasses import asdict
from typing import Optional
import os
import pickle
import xlsxwriter

DOMAIN = "https://www.spareroom.co.uk"
FILE = "data/rooms.pkl"

class SpareRoomManager:
    def __init__(self, remove_expired_rooms: bool, headless: bool,
        number_of_pages: int, min_rent: str, max_rent: str, filename: str) -> None:
        self.remove_expired_rooms = remove_expired_rooms
        self.headless = headless
        self.number_of_pages = number_of_pages
        self.min_rent = min_rent
        self.max_rent = max_rent
        self.filename = f'output/{filename}'
        self.db_path = FILE

        self.rooms: list[Room] = []
        self.sr: Optional[SpareRoom] = None
        self.new_room_urls = []

        if self.number_of_pages < 1:
            raise ValueError("Number_of_pages must be greater than 0")

    def run(self) -> None:

        logger.info(
        f"""STARTING PROGRAM
                
        Update database:    {self.remove_expired_rooms},
        Number of pages:    {self.number_of_pages}, 
        Minimum rent:       {self.min_rent}, 
        Maximmum rent:      {self.max_rent},
        Filename:           {self.filename}
        """
        )

        self.rooms = self._read_file()
        self.sr = SpareRoom(DOMAIN, self.headless)

        if self.remove_expired_rooms:
            self._remove_expired_rooms_from_database()

        self._remove_unwanted_rooms_from_database()

        # Search Spareroom, process new rooms
        self.sr.search_spareroom(self.min_rent, self.max_rent)
        self.sr.iterate_through_pages(self.number_of_pages)
        self.new_room_urls = self._filter_new_rooms_only(self.sr.room_urls)
        if self.new_room_urls:
            logger.info(f"Processing {len(self.new_room_urls)} new rooms")
            self._process_new_rooms()

        self._write_file()
        self._create_and_export_dataframe()

    def _remove_unwanted_rooms_from_database(self) -> None:
        if not os.path.exists(self.filename):
            return
        
        # Remove rooms from database that have been removed from excel file
        old_df = pl.read_excel(self.filename).select(pl.col('id'))
        kept_ids = old_df['id'].to_list()
        self.rooms = [r for r in self.rooms if r.id in kept_ids]

    def _remove_expired_rooms_from_database(self) -> None:
        # Exclude listings that have been taken off Spareroom
        valid_rows = []

        print()
        for i, row in enumerate(self.rooms, start=1):
            flush_print(i, self.rooms, "Checking room still exists")

            self.sr.page.goto(row.url, timeout=10000)
            url = self.sr.page.url
            if row.url != url:
                logger.warning(f"room {i} no longer found")
                continue
            valid_rows.append(row)
        print()

        self.rooms = valid_rows

    def _filter_new_rooms_only(self, room_urls: list[str]) -> list[str]:
        existing_ids = [row.id for row in self.rooms]
        room_ids = [url.split("=")[1].split("&")[0] for url in room_urls]
        return [url for (url, id) in zip(room_urls, room_ids) if id not in existing_ids]

    def _process_new_rooms(self) -> None:
        print()
        for i, url in enumerate(self.new_room_urls, start=1):
            flush_print(i, self.new_room_urls, "Processing new rooms")

            room_obj = GetRoomInfo(url, self.sr.page, DOMAIN)
            room = room_obj.room
            room.score = get_score(room)

            if room.room_sizes is not None and room.location != ("None, None"):
                self.rooms.append(room)
        print()

    def _create_and_export_dataframe(self) -> None:
        dict_list = [asdict(room) for room in self.rooms]
        df = (
            pl.LazyFrame(dict_list, infer_schema_length=len(dict_list))
            .select(output_cols)
            .filter(pl.col("average_price") > int(self.min_rent))
            .sort("score", descending=True)
        ).collect()
        df = df.to_pandas()
        df["date_added"] = df["date_added"].dt.strftime("%d-%b")

        with pd.ExcelWriter(self.filename, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]

            # Define hyperlink format
            link_format = workbook.add_format({"font_color": "blue", "underline": 1}) # type: ignore[attr-defined]

            # Replace URLs in column A with 'link' text + hyperlink formatting
            for row_num, url in enumerate(
                df["url"], start=1
            ):  # row 1 = Excel row 2 (zero-based index)
                worksheet.write_url(row_num, 1, url, link_format, string="link")

            # Autofit columns (works in pandas >=2.2 with xlsxwriter)
            worksheet.autofit()

        logger.info(f"Saved database to {self.filename}.")

    def _read_file(self) -> list[Room]:
        try:
            with open(self.db_path, "rb") as f:
                rows = pickle.load(f)
        except FileNotFoundError:
            rows = []
        logger.info(f"Database currently has {len(rows)} listings")
        return rows

    def _write_file(self) -> None:
        with open(self.db_path, "wb") as f:
            pickle.dump(self.rooms, f)
        logger.info(f"File now has {len(self.rooms)} listings")

if __name__ == "__main__":
    spm = SpareRoomManager(
        remove_expired_rooms=CONFIG["remove_expired_rooms"],
        headless=CONFIG["headless"],
        number_of_pages=CONFIG["number_of_pages"],
        min_rent=CONFIG["min_rent"],
        max_rent=CONFIG["max_rent"],
        filename=CONFIG["filename"],
    )
    spm.run()
    CreateMap(spm.rooms)
    logger.info("STOPPING PROGRAM")
