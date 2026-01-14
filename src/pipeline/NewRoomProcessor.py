from dataclasses import fields
from playwright.sync_api import Page

import src.utils.utils as ut
from src.scraping.RoomScraper import RoomScraper
from src.processing.RoomNormaliser import RoomNormaliser
from src.processing.RoomEnricher import RoomEnricher
from src.services.CommuteService import CommuteService
from src.processing.calculate_score import get_score
from src.utils.logger_config import logger
from src.utils.types import Room


class NewRoomProcessor:
    def __init__(self, db_manager, domain: str):
        self.db_manager = db_manager
        self.domain = domain
        self.commute_service = CommuteService()
        self.enricher = RoomEnricher(commute_service=self.commute_service)

    def filter_new_rooms(self, room_urls: list[str]) -> list[str]:
        existing_ids = {room.id for room in self.db_manager.database}
        ignored_ids = set(self.db_manager.ignored)
        return [
            url
            for url in room_urls
            if (room_id := ut.get_id_from_url(url)) not in existing_ids
            and room_id not in ignored_ids
        ]

    def process_new_rooms(self, page: Page, room_urls: list[str]) -> None:
        logger.info(f"Processing {len(room_urls)} new rooms")

        for i, url in enumerate(room_urls, start=1):
            ut.flush_print(i, room_urls, "Processing new rooms")

            url = f"{self.domain}/{url}"
            room = self._build_room(url=url, page=page)

            # Add room to database if room is valid
            room_is_valid = self._validate_room(room=room)
            if room_is_valid:
                self.db_manager.database.append(room)
        print()

    def _build_room(self, url: str, page: Page) -> Room:
        # Scrape data
        scraper = RoomScraper(page=page, url=url)
        room_data = scraper.scrape_data()

        # Normalise data
        room_data = RoomNormaliser().normalise(room_data=room_data)
        
        # Enrich data
        room_data = self.enricher.enrich(room_data=room_data)

        # Create Room object
        room = self._create_room_object(room_data=room_data)

        # Calculate room score
        room.score = get_score(room)

        return room
    
    def _create_room_object(self, room_data: dict) -> Room:
        """Keep only valid keys and create Room dataclass object"""
        valid_keys = {f.name for f in fields(Room)}
        filtered_room_data = {k:v for k, v in room_data.items() if k in valid_keys}
        return Room(**filtered_room_data)
    
    def _validate_room(self, room: Room) -> bool:
        if not room.room_sizes or all(size=="single" for size in room.room_sizes):
            logger.info(f"Skipping room due to invalid room_sizes: {room.room_sizes}")
            return False
            
        if room.location is None:
            logger.info(f"Skipping room due to invalid location: {room.location}")
            return False
        
        if not room.available_all_week:
            logger.info("Skipping room as it is not available all week")
            return False
        
        return True