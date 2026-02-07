import os
import pickle
import json
import polars as pl
from src.utils.logger_config import logger
from config import IGNORE_KEYWORDS, FAVOURITE_KEYWORDS, MESSAGED_KEYWORDS
from src.utils.types import Room
import src.utils.utils as ut
from playwright.sync_api import Page
 
class DatabaseManager:
    def __init__(
        self, 
        check_for_expired_rooms: bool, 
        database_path: str, 
        output_path: str,
        ignored_ids_path: str,
        favourite_ids_path: str,
        messaged_ids_path: str

    ):
        self.check_for_expired_rooms = check_for_expired_rooms
        self.database_path = database_path
        self.output_path = output_path
        self.ignored_ids_path = ignored_ids_path
        self.favourite_ids_path = favourite_ids_path
        self.messaged_ids_path = messaged_ids_path

        self.database: list[Room] = []
        self.ignored: set[str] = set()
        self.favourites: set[str] = set()
        self.messaged: set[str] = set()

    def load(self) -> None:
        self.database = DatabaseManager._read_pickle_file(path=self.database_path)
        self.ignored = set(self._read_json_file(self.ignored_ids_path))
        self.favourites = set(self._read_json_file(self.favourite_ids_path))
        self.messaged = set(self._read_json_file(self.messaged_ids_path))

    def update_database(self, page: Page) -> None:
        if self.check_for_expired_rooms:
            self._check_for_expired_rooms_from_database(page=page)

        # Process ignore and favourite requests
        if os.path.exists(self.output_path):
            tuples = self._read_status_updates()
            self._update_id_lists(tuples=tuples)
            self._apply_statuses_to_database()

    def save(self) -> None:
        self._write_pickle_file(self.database_path, self.database)

    def _read_status_updates(self) -> list[tuple[str, str | None]]:
        df = pl.read_excel(self.output_path)
        tuples = list(df.select(['id', 'status']).iter_rows())
    
        # Validate statuses
        for room_id, status in tuples:
            if status and status.lower() not in (IGNORE_KEYWORDS + FAVOURITE_KEYWORDS + MESSAGED_KEYWORDS):
                logger.warning(f"room with id: {room_id} had an invalid status: {status}")

        return tuples

    def _update_id_lists(self, tuples) -> None:
        configs = [
            ('ignored', self.ignored_ids_path, IGNORE_KEYWORDS),
            ('favourites', self.favourite_ids_path, FAVOURITE_KEYWORDS),
            ('messaged', self.messaged_ids_path, MESSAGED_KEYWORDS)
        ]
        for attr, path, keywords in configs:
            current_id_list = getattr(self, attr)
            new_ids = [
                room_id for room_id, status in tuples 
                if status and status.lower() in keywords and room_id not in current_id_list
            ]
            if new_ids:
                logger.info(f"Added to {attr} list: {new_ids}")
                current_id_list.update(new_ids)
                self._write_json_file(path=path, data=sorted(current_id_list))    

    def _apply_statuses_to_database(self) -> None:
        """Remove ignored rooms from database and update status of favourited rooms
        
        When applying statuses to each room id, we use two if-statements instead of one
        elif statement so that a room with an id in favourites and messaged will show messaged.
        Correct approach if room was first saved as a favourite, and then later on status changed to Messaged.
        """
        self.database = [room for room in self.database if room.id not in self.ignored]
        for room in self.database:
            if room.id in self.favourites:
                room.status = 'FAVOURITE'
            
            if room.id in self.messaged: 
                room.status = 'MESSAGED'

    def _check_for_expired_rooms_from_database(self, page: Page) -> None:
        """Exclude listings that have been taken off Spareroom"""
        valid_rows = []

        for i, room in enumerate(self.database, start=1):
            ut.flush_print(i, self.database, "Checking room still exists")

            try:
                page.goto(room.url, timeout=10000)
            except Exception as e:
                logger.warning(f"Failed to load {room.url}: {e}")
                continue

            current_url = page.url
            if room.url != current_url:
                logger.debug(f"room {i} no longer found")
                continue

            valid_rows.append(room)

        self.database = valid_rows

    @staticmethod
    def _read_pickle_file(path: str) -> list[Room]:
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            data = []
        logger.info(f"Database currently has {len(data)} listings")
        return data

    @staticmethod
    def _write_pickle_file(path: str, data: list[Room]) -> None:
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Database currently has {len(data)} listings")

    @staticmethod
    def _read_json_file(path: str) -> list[str]:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            DatabaseManager._write_json_file(path=path, data=[])
            logger.info(f'Remaking {path}')            
            return []
        
    @staticmethod
    def _write_json_file(path: str, data: list) -> None:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)