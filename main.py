from src.pipeline.Pipeline import Pipeline
from src.utils.logger_config import logger
from src.utils.types import PipelineConfig
from config import CONFIG


def main():

    logger.info("STARTING PROGRAM")
    
    config = PipelineConfig(**CONFIG)
    Pipeline(config=config).run()

    logger.info("STOPPING PROGRAM")  


if __name__ == "__main__":
    main()