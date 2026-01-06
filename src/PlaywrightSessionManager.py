from playwright.sync_api import sync_playwright
from src.logger_config import logger


class PlaywrightSession:
    def __init__(self, headless: bool) -> None:
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

        if self.headless:
            self.page = self.browser.new_page()
        else:
            self.context = self.browser.new_context(viewport={"width": 1200, "height": 1200})
            self.page = self.context.new_page()

        logger.info("Launched browser.")
        return self
    
    def __exit__(self, exc_type, exec_value, traceback):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Closed playwright session")
