import polars as pl
import pandas as pd
from src.SpareRoom import SpareRoom
from src.RoomInfo import RoomInfo
from src.lists import final_cols, output_cols
from src.logger_config import logger
from src.get_score_and_price import get_score_and_price
from src.get_commute_time import get_commute_time
from src.utils import flush_print
import pickle
from datetime import datetime
from src.create_map import CreateMap
from config import MAIN

domain = "https://www.spareroom.co.uk"


def read_from_database():
    try:
        with open("data/rows.pkl", "rb") as f:
            rows = pickle.load(f)
    except FileNotFoundError:
        rows = []

    logger.info(f"Database currently has {len(rows)} listings")
    return rows


def write_to_database(rows):
    with open("data/rows.pkl", "wb") as f:
        pickle.dump(rows, f)
    logger.info(f"Database now has {len(rows)} listings")


def filter_for_new_listings_only(rows, listing_urls):
    existing_ids = [row["id"] for row in rows]
    listing_ids = [url.split("=")[1].split("&")[0] for url in listing_urls]
    return [
        url for (url, id) in zip(listing_urls, listing_ids) if id not in existing_ids
    ]


def process_new_listings(listing_urls, x, rows):
    logger.info(f"Processing {len(listing_urls)} new listings")
    for i, url in enumerate(listing_urls, start=1):
        flush_print(i, listing_urls)
        room = RoomInfo(url, x.page, domain)
        if (
            getattr(room, "room_1_bed_size", None) is not None
            and getattr(room, "location", None) != "None, None"
        ):
            rows.append({col: getattr(room, col, None) for col in final_cols})
    return rows


def get_final_info_for_all_listings(rows):
    # Final updates plus gettting score, average price and commute times
    logger.info(f"Getting final info for {len(rows)} listings")
    for i, row in enumerate(rows, start=1):
        print(f"\r{i}/{len(rows)}. ", end="", flush=True)
        if "date_added" not in row.keys():
            row["date_added"] = datetime.today().date()
        if row["#_flatmates"] is None:
            row["#_flatmates"] = 0
        if row["total_#_rooms"] is None:
            row["total_#_rooms"] = 1
        if row["location"] is not None and row["id"] is not None:
            commutes = get_commute_time(row["location"], row["id"])
            row["commute_to_office"] = commutes.commute_to_office
            row["commute_to_central"] = commutes.commute_to_central
        row["score"], row["average_price"] = get_score_and_price(row)
    return rows


def create_and_export_dataframe(rows, filename, min_rent):
    df = (
        pl.LazyFrame(rows)
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


def main(
    use_with_database,
    update_database,
    headless,
    number_of_pages,
    min_rent,
    max_rent,
    filename,
):
    logger.info(f""" STARTING PROGRAM
                
    Use with database:  {use_with_database}, 
    Number of pages:    {number_of_pages}, 
    Minimum rent:       {min_rent}, 
    Maximmum rent:      {max_rent},
    Filename:           {filename}
    """)

    if not use_with_database and number_of_pages == 0:
        raise ValueError(
            "Use database must be set to True or number_of_pages must be greater than 0"
        )

    # Import database and idenitfy new listings
    rows = read_from_database() if use_with_database else []

    # Search listings on Spareroom and process new listings
    if number_of_pages > 0:
        x = SpareRoom(domain, headless)
        x.search_spareroom(min_rent, max_rent)
        x.iterate_through_pages(number_of_pages)
        listing_urls = x.listing_urls
        listing_urls = filter_for_new_listings_only(rows, listing_urls)
        rows = process_new_listings(listing_urls, x, rows)

    if update_database and use_with_database:
        valid_rows = []
        y = SpareRoom(domain, headless)
        for i, row in enumerate(rows):
            y.page.goto(row["url"], timeout=10000)
            final_url = y.page.url
            if row["url"] != final_url:
                logger.warning(f"listing no longer detected {i}")
                continue
            valid_rows.append(row)
        rows = valid_rows

    # Get info for all listings
    rows = get_final_info_for_all_listings(rows)
    logger.info("Processed all listings")

    # If using database, save new listings to database
    if use_with_database:
        write_to_database(rows)

    # Create and export dataframe
    create_and_export_dataframe(rows, filename, min_rent)
    CreateMap(rows)

    logger.info("STOPPING PROGRAM")


if __name__ == "__main__":
    main(
        use_with_database=MAIN["use_with_database"],
        update_database=MAIN["update_database"],
        headless=MAIN["headless"],
        number_of_pages=MAIN["number_of_pages"],
        min_rent=MAIN["min_rent"],
        max_rent=MAIN["max_rent"],
        filename=MAIN["filename"],
    )
