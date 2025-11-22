import polars as pl
import pandas as pd
from src.SpareRoom import SpareRoom
from src.RoomInfo import GetRoomInfo
from src.Room import Room
from src.lists import output_cols
from src.logger_config import logger
from src.get_score_and_price import get_score_and_price
from src.utils import flush_print, read_file, write_file
from src.create_map import CreateMap
from config import MAIN
from dataclasses import asdict


DOMAIN = "https://www.spareroom.co.uk"
FILE = "data/rooms.pkl"


def filter_for_new_rooms_only(rooms, room_urls) -> list[str]:
    existing_ids = [row.id for row in rooms]
    room_ids = [url.split("=")[1].split("&")[0] for url in room_urls]
    return [url for (url, id) in zip(room_urls, room_ids) if id not in existing_ids]


def exclude_expired_rooms(sr: SpareRoom, rooms: list[Room]) -> list[Room]:
    valid_rows = []

    print()
    for i, row in enumerate(rooms, start=1):
        flush_print(i, rooms, "Checking room still exists")

        sr.page.goto(row.url, timeout=10000)
        url = sr.page.url
        if row.url != url:
            logger.warning(f"room {i} no longer found")
            continue
        valid_rows.append(row)
    print()

    return valid_rows


def process_new_rooms(room_urls, x, rooms) -> list[Room]:
    logger.info(f"Processing {len(room_urls)} new rooms")

    print()
    for i, url in enumerate(room_urls, start=1):
        
        flush_print(i, room_urls, "Processing new rooms")

        room_obj = GetRoomInfo(url, x.page, DOMAIN)
        room = room_obj.room
        room.score, room.average_price = get_score_and_price(room)

        if room.room_1_bed_size is not None and room.location != "None, None":
            rooms.append(room)
    print()

    return rooms


def create_and_export_dataframe(rooms, filename, min_rent) -> None:
    dict_list = [asdict(room) for room in rooms]
    df = (
        pl.LazyFrame(dict_list, infer_schema_length=len(dict_list))
        .select(output_cols)
        .filter(pl.col("average_price") > int(min_rent))
        .sort("score", descending=True)
    ).collect()
    df = df.to_pandas()
    df["date_added"] = df["date_added"].dt.strftime("%d-%b")

    with pd.ExcelWriter(f"output/{filename}", engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Define hyperlink format
        link_format = workbook.add_format({"font_color": "blue", "underline": 1})

        # Replace URLs in column A with 'link' text + hyperlink formatting
        for row_num, url in enumerate(
            df["url"], start=1
        ):  # row 1 = Excel row 2 (zero-based index)
            worksheet.write_url(row_num, 0, url, link_format, string="link")

        # Autofit columns (works in pandas >=2.2 with xlsxwriter)
        worksheet.autofit()

    logger.info(f"Saved database to {filename}.")


def main(use_database, update_database, headless, 
         number_of_pages, min_rent, max_rent, filename) -> None:
    logger.info(f""" STARTING PROGRAM
                
    Use with database:  {use_database}, 
    Update database:    {update_database},
    Number of pages:    {number_of_pages}, 
    Minimum rent:       {min_rent}, 
    Maximmum rent:      {max_rent},
    Filename:           {filename}
    """)

    if not use_database and number_of_pages == 0:
        raise ValueError(
            "Use database must be set to True or number_of_pages must be greater than 0"
        )

    # Import database and idenitfy new rooms
    rooms = read_file(file=FILE) if use_database else []

    sr = SpareRoom(DOMAIN, headless)

    # Exclude listings that have been taken off Spareroom
    if update_database and use_database:
        rooms = exclude_expired_rooms(sr, rooms)

    # Search rooms on Spareroom and process new rooms
    if number_of_pages > 0:
        sr.search_spareroom(min_rent, max_rent)
        sr.iterate_through_pages(number_of_pages)
        room_urls = filter_for_new_rooms_only(rooms, sr.room_urls)
        rooms = process_new_rooms(room_urls, sr, rooms)

    # If using database, save new rooms to database
    if use_database:
        write_file(file=FILE, rooms=rooms)

    # Create and export dataframe
    create_and_export_dataframe(rooms, filename, min_rent)
    CreateMap(rooms)

    logger.info("STOPPING PROGRAM")


if __name__ == "__main__":
    main(
        use_database=MAIN["use_database"],
        update_database=MAIN["update_database"],
        headless=MAIN["headless"],
        number_of_pages=MAIN["number_of_pages"],
        min_rent=MAIN["min_rent"],
        max_rent=MAIN["max_rent"],
        filename=MAIN["filename"],
    )
