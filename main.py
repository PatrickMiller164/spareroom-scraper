from src.SpareRoomManager import SpareRoomManager
from src.logger_config import logger
from src.create_map import CreateMap
from config import CONFIG

DOMAIN = "https://www.spareroom.co.uk"
DATABASE_FILE = "data/rooms.pkl"


def main():
    logger.info("STARTING PROGRAM")

    spm = SpareRoomManager(
        check_for_expired_rooms=CONFIG["check_for_expired_rooms"],
        headless=CONFIG["headless"],
        number_of_pages=CONFIG["number_of_pages"],
        min_rent=CONFIG["min_rent"],
        max_rent=CONFIG["max_rent"],
        filename=CONFIG["filename"],
        db_path=DATABASE_FILE,
        domain=DOMAIN
    )
    spm.run()

    cm = CreateMap(rooms=spm.rooms)
    cm.run()

    logger.info("STOPPING PROGRAM")  


if __name__ == "__main__":
    main()