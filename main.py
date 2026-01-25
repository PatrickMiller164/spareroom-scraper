from src.pipeline.Pipeline import Pipeline
from src.utils.logger_config import logger
from src.utils.types import PipelineConfig
from config import CONFIG
from src.utils.test import test


def main():

    test([CONFIG['output_path'], CONFIG['database_path'], CONFIG['ignored_ids_path'], CONFIG['favourite_ids_path']])

    logger.info("STARTING PROGRAM")
    
    config = PipelineConfig(**CONFIG)
    Pipeline(config=config).run()

    logger.info("STOPPING PROGRAM")  


if __name__ == "__main__":
    main()