import polars as pl
import pandas as pd
from src.utils.logger_config import logger
from dataclasses import asdict

output_cols = [
    "status", "id", "url", "poster_type", "date_added", "type", "area", "score", "collective_word_count", 
    "average_price", "average_deposit", "location_1", "location_2", "direct_line_to_office", 
    "location", "nearest_station", "available", "minimum_term", "maximum_term", "bills_included",
    "broadband_included", "furnishings", "garden_or_patio", "living_room",
    "balcony_or_roof_terrace", "number_of_flatmates", "total_number_of_rooms"
]

class ExcelExporter:
    def __init__(self, db_manager, output_path: str, min_rent: int) -> None:
        self.db_manager = db_manager
        self.output_path = output_path
        self.min_rent = min_rent

    def create_and_export_dataframe(self) -> None:
        dict_list = [asdict(room) for room in self.db_manager.database]
        df = (
            pl.LazyFrame(dict_list, infer_schema_length=len(dict_list))
            .select(output_cols)
            .filter(pl.col("average_price") > self.min_rent)
            .sort("score", descending=True)
        ).collect()
        df = df.to_pandas()
        df["date_added"] = df["date_added"].dt.strftime("%d-%b")

        with pd.ExcelWriter(self.output_path, engine="xlsxwriter") as writer:
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

        logger.info(f"Saved database to {self.output_path}.")