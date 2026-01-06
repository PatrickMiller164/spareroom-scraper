import polars as pl
import pandas as pd

from src.PlaywrightSessionManager import PlaywrightSession
from src.SpareRoomSearcher import SpareRoomSearcher
from src.SpareRoomScraper import SpareRoomScraper

from src.RoomInfo import GetRoomInfo
from src.Room import Room
from src.lists import output_cols
from src.logger_config import logger
from src.calculate_score import get_score
from src.utils import flush_print
from dataclasses import asdict
import os
import pickle
import json

class SpareRoomManager:
    def __init__(
        self, 
        check_for_expired_rooms: bool, 
        headless: bool,
        number_of_pages: int, 
        min_rent: str, 
        max_rent: str, 
        filename: str,
        db_path: str,
        domain: str
    ) -> None:
        """Initialise the SpareRoom scraper

        Args:
            check_for_expired_rooms: Whether to check and remove expired rooms from database
            headless: Whether to scrape SpareRoom showing the Chrome browser or not
            number_of_pages: Number of result pages to scrape (must be >= 1)
            min_rent: Minimum rent filter (as a string, e.g., "500")
            max_rent: Maximum rent filter (as a string, e.g., "1000")
            filename: Name of the output excel file (saved under the output/ directory)

        Raises:
            ValueError: If number of pages is less than 1
        """
        self.check_for_expired_rooms = check_for_expired_rooms
        self.headless = headless
        self.number_of_pages = number_of_pages
        self.min_rent = min_rent
        self.max_rent = max_rent
        self.filename = f'output/{filename}'
        self.db_path = db_path
        self.domain = domain

        self.ignored = []
        self.rooms: list[Room] = []
        self.new_room_urls = []

        if self.number_of_pages < 1:
            raise ValueError("Number_of_pages must be greater than 0")

    def run(self) -> None:
        """Run the full room scraping and processing workflow.

        Reads existing rooms from disk, optionally checks for expired rooms and removes
        them from database, removes unwanted rooms, searches for new listings, processes 
        any new rooms found, and writes the updated results to disk.
        """
        self.rooms = SpareRoomManager._read_pickle_file(path=self.db_path)
        self.ignored = []
        self.favourites = []

        if self.check_for_expired_rooms:
            self._check_for_expired_rooms_from_database()

        if os.path.exists(self.filename):
            self._process_ignore_and_favourite_requests()

        # Search Spareroom, process new rooms
        with PlaywrightSession(headless=self.headless) as session:
            search = SpareRoomSearcher(page=session.page, domain=self.domain)
            search.run(min_rent=self.min_rent, max_rent=self.max_rent)

            scraper = SpareRoomScraper(page=session.page, domain=self.domain)
            room_urls = scraper.collect_room_urls(pages=5)

        self.new_room_urls = self._filter_new_rooms_only(room_urls)
        logger.info(f"Processing {len(self.new_room_urls)} new rooms")
        if self.new_room_urls:
            self._process_new_rooms()

        self._write_pickle_file(path=self.db_path, ls=self.rooms)
        self._create_and_export_dataframe()

    def _check_for_expired_rooms_from_database(self) -> None:
        # Exclude listings that have been taken off Spareroom
        valid_rows = []

        with PlaywrightSession(self.headless) as session:
            page = session.page
            if not page:
                return

            print()
            for i, row in enumerate(self.rooms, start=1):
                flush_print(i, self.rooms, "Checking room still exists")

                try:
                    page.goto(row.url, timeout=10000)
                except Exception as e:
                    logger.warning(f"Failed to load {row.url}: {e}")
                    continue

                current_url = page.url
                if row.url != current_url:
                    logger.debug(f"room {i} no longer found")
                    continue

                valid_rows.append(row)
            print()

        self.rooms = valid_rows

    def _process_ignore_and_favourite_requests(self) -> None:
        df = pl.read_excel(self.filename)
        tuples = list(df.select(['id', 'status']).iter_rows())

        # Validate statuses
        for id, status in tuples:
            if status and status.lower() not in ['favourite', 'ignore']:
                logger.warning(f"room with id: {id} has invalid status: {status}")

        configs = [
            ('ignored', 'data/ignored_ids.json', 'ignore', 'Ignoring'),
            ('favourites', 'data/favourite_ids.json', 'favourite', 'Adding to favourites')
        ]

        for attr, path, keyword, msg in configs:
            ls = self._read_json_file(path=path)

            new_ids = [
                id for id, status in tuples 
                if status and status.lower()==keyword and id not in ls
            ]
            
            if new_ids:
                logger.info(f"{msg}: {new_ids}")
                ls.extend(new_ids)
                self._write_json_file(path=path, ls=ls)    

            setattr(self, attr, ls)

        # Remove ignored rooms from database and update status of favourited rooms
        self.rooms = [r for r in self.rooms if r.id not in self.ignored]
        for r in self.rooms:
            if r.id in self.favourites:
                r.status = 'FAVOURITE'

    def _filter_new_rooms_only(self, room_urls: list[str]) -> list[str]:
        existing_ids = [row.id for row in self.rooms]
        room_ids = [url.split("=")[1].split("&")[0] for url in room_urls]
        return [url for (url, id) in zip(room_urls, room_ids) if (id not in existing_ids) and (id not in self.ignored)]

    def _process_new_rooms(self) -> None:
        with PlaywrightSession(headless=self.headless) as session:
            page = session.page
            if not page:
                return
            
            print()
            for i, url in enumerate(self.new_room_urls, start=1):
                flush_print(i, self.new_room_urls, "Processing new rooms")

                room_obj = GetRoomInfo(url, page, self.domain)
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
                worksheet.write_url(row_num, 2, url, link_format, string="link")

            # Autofit columns (works in pandas >=2.2 with xlsxwriter)
            worksheet.autofit()

        logger.info(f"Saved database to {self.filename}.")

    @staticmethod
    def _read_pickle_file(path: str) -> list:
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []
        logger.info(f"Database currently has {len(rows)} listings")
    
    @staticmethod
    def _write_pickle_file(path: str, ls: list[Room]) -> None:
        with open(path, "wb") as f:
            pickle.dump(ls, f)
        logger.info(f"File now has {len(ls)} listings")

    @staticmethod
    def _read_json_file(path: str) -> list:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            SpareRoomManager._write_json_file(path=path, ls=[])
            logger.info(f'Remaking {path}')            
            return []
        
    @staticmethod
    def _write_json_file(path: str, ls: list) -> None:
        with open(path, 'w') as f:
            json.dump(ls, f, indent=2)
