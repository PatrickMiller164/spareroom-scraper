from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.logger_config import logger


class SpareRoom:
    def __init__(self, domain, headless):
        self.playwright = sync_playwright().start()
        self.domain = domain
        self.listing_urls = []
        self.soups = []
        self.launch_browser(headless)

    def launch_browser(self, headless):
        # Launch browser either headless or with header
        if headless:
            browser = self.playwright.chromium.launch(headless=True)
            self.page = browser.new_page()
        else:
            browser = self.playwright.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1200, "height": 1200})
            self.page = context.new_page()
        logger.info("Launched browser.")

    def search_spareroom(self, min_rent, max_rent):
        # Enter params and go to results
        search_url = "/flatshare/search.pl?searchtype=advanced"
        self.page.goto(self.domain + search_url, timeout=10000)

        self.page.wait_for_selector("#search_by_location_field")
        self.page.fill("#search_by_location_field", "London")
        self.page.wait_for_timeout(500)

        self.page.wait_for_selector("#min-rent")
        self.page.fill("#min-rent", min_rent)

        self.page.wait_for_selector("#max-rent")
        self.page.fill("#max-rent", max_rent)

        self.page.evaluate(
            """document.getElementById('oneBedOrStudio').checked = false;"""
        )
        self.page.evaluate(
            """document.getElementById('wholeProperty').checked = false;"""
        )
        self.page.evaluate("""document.getElementById('wholeWeek').checked = true;""")
        self.page.evaluate("""document.getElementById('doubleRoom').checked = true;""")
        self.page.evaluate(
            """document.getElementById('adsWithPhoto').checked = true;"""
        )
        self.page.evaluate("""document.getElementById('liveOut').checked = true;""")
        self.page.evaluate(
            """document.querySelector('select[name="min_term"]').value = '6';"""
        )

        self.page.press("#search_by_location_field", "Enter")

        logger.info("Searching Spareroom.")

    def iterate_through_pages(self, number_of_pages):
        # Sort by newest ads first
        self.page.select_option("#sort_by", value="days_since_placed")

        # Get listing urls from first x pages
        for i in range(1, number_of_pages + 1):
            print(f"\rExtracted listing urls for page {i}", end="", flush=True)
            self.get_listing_urls()

            next_button = self.page.query_selector("#paginationNextPageLink")
            if not next_button:
                logger.warning("No more pages")
                break

            href = next_button.get_attribute("href")
            if not href:
                logger.warning("No href found on next button")
                break

            next_page = self.domain + "/flatshare/" + href
            self.page.goto(next_page, wait_until="load")

        logger.info(f"Retrieved {len(self.listing_urls)} listings")

    def get_listing_urls(self):
        # Get listing urls for a page
        self.page.wait_for_selector("ul.listing-results")
        html = self.page.content()
        soup = BeautifulSoup(html, "html.parser")

        ul = soup.select_one("ul.listing-results")  # Get listings section
        listings = ul.find_all("li")  # Get all listings
        for i in listings:
            listing_url = i.get("data-listing-url")  # Get URL of each listing
            if listing_url is not None:
                self.listing_urls.append(listing_url)
