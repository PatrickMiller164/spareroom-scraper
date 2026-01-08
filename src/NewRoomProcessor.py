import src.utils.utils as ut
from src.GetRoomDetails import GetRoomDetails
from src.calculate_score import get_score
from src.utils.logger_config import logger

class NewRoomProcessor:
    def __init__(self, db_manager, domain: str):
        self.db_manager = db_manager
        self.domain = domain

    def filter_new_rooms(self, room_urls: list[str]) -> list[str]:
        existing_ids = [room.id for room in self.db_manager.database]
        ignored_ids = self.db_manager.ignored

        return [
            url
            for url in room_urls
            if (room_id := ut.get_id_from_url(url)) not in existing_ids
            and room_id not in ignored_ids
        ]

    def process_new_rooms(self, page, room_urls: list[str]) -> None:
        logger.info(f"Processing {len(room_urls)} new rooms")
        print()
        for i, url in enumerate(room_urls, start=1):
            ut.flush_print(i, room_urls, "Processing new rooms")

            url = f"{self.domain}/{url}"
            room_obj = GetRoomDetails(url=url, page=page)
            room = room_obj.room
            room.score = get_score(room)

            if room.room_sizes is not None and room.location != ("None, None"):
                self.db_manager.database.append(room)
        print()