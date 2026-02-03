from src.pipeline.Pipeline import Pipeline
from src.utils.logger_config import logger
from src.utils.types import PipelineConfig
from config import CONFIG
from src.utils.test import test
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--number_of_pages", type=int)
    parser.add_argument("--check_for_expired_rooms", action="store_true")
    parser.add_argument("--update_database_only", action="store_true")
    args = parser.parse_args()

    logger.info("STARTING PROGRAM")
    
    config = PipelineConfig(**CONFIG)

    if args.number_of_pages is not None:
        print(f"{args.number_of_pages=}")
        config.number_of_pages = args.number_of_pages

    if args.check_for_expired_rooms:
        print(f"{args.check_for_expired_rooms=}")
        config.check_for_expired_rooms = True

    if args.update_database_only:
        print("Updating database only (number_of_pages=0)")
        config.number_of_pages = 0

    Pipeline(config=config).run()

    logger.info("STOPPING PROGRAM")  


if __name__ == "__main__":
    main()