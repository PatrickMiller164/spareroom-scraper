from src.scraping.PlaywrightSessionManager import PlaywrightSession
from src.scraping.SpareRoomSearcher import SpareRoomSearcher
from src.scraping.SpareRoomScraper import SpareRoomScraper
from src.persistence.DatabaseManager import DatabaseManager
from src.pipeline.NewRoomProcessor import NewRoomProcessor
from src.persistence.ExcelExporter import ExcelExporter
from src.persistence.MapCreator import CreateMap
from src.utils.types import PipelineConfig


class Pipeline:
    def __init__(self, config: PipelineConfig) -> None:
        """Initialise the SpareRoom pipeline

        Args:
            config: Immutable pipeline configuration containing scraping,
                    database, and output settings.
        """
        self.config = config

    def run(self) -> None:
        """Run the full room scraping and processing workflow.

        Reads existing rooms from disk, optionally checks for expired rooms and removes
        them from database, removes unwanted rooms, searches for new listings, processes 
        any new rooms found, and writes the updated results to disk.
        """
        with PlaywrightSession(headless=self.config.headless) as session: 
            page = session.page
            if page is None:
                raise RuntimeError("Playwright session did not create a page")

            # Update database
            db_manager = DatabaseManager(
                database_path=self.config.database_path,
                check_for_expired_rooms=self.config.check_for_expired_rooms,
                output_path=self.config.output_path,
                ignored_ids_path=self.config.ignored_ids_path,
                favourite_ids_path=self.config.favourite_ids_path,
                messaged_ids_path=self.config.messaged_ids_path
            )
            db_manager.load()
            db_manager.update_database(page=page)

            # Search Spareroom, and get room urls
            if self.config.number_of_pages > 0:
                search = SpareRoomSearcher(page=page, domain=self.config.domain)
                search.run(min_rent=self.config.min_rent, max_rent=self.config.max_rent)

                scraper = SpareRoomScraper(page=page, domain=self.config.domain)
                room_urls = scraper.collect_room_urls(pages=self.config.number_of_pages)

                # Process new rooms and add to database
                processor = NewRoomProcessor(db_manager=db_manager,domain=self.config.domain)
                new_urls = processor.filter_new_rooms(room_urls=room_urls)
                processor.process_new_rooms(page=page, room_urls=new_urls)

            # Save database as pickle object
            db_manager.save()
            
            # Export database into excel
            exporter = ExcelExporter(
                db_manager=db_manager,
                output_path=self.config.output_path,
                min_rent=self.config.min_rent
            )
            exporter.create_and_export_dataframe()

            # Create Folium map to visualise rooms
            cm = CreateMap(rooms=db_manager.database)
            cm.run()
