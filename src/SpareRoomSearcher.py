from src.logger_config import logger


class SpareRoomSearcher:
    def __init__(self, page, domain: str) -> None:
        self.page = page
        self.domain = domain

        search_url = "flatshare/search.pl?searchtype=advanced"
        self.page.goto(f"{self.domain}/{search_url}", timeout=10000)

    def run(self, min_rent: str, max_rent: str) -> None:
        """Perform a search on Spareroom with specified rent filters.

        Fills the search form on the Spareroom website for London listings,
        applies the given minimum and maximum rent, sets predefined search
        filters (room type, availability, photos, etc.), and submits the search.

        Args:
            min_rent: Minimum rent filter (as a string, e.g., "500").
            max_rent: Maximum rent filter (as a string, e.g., "1200").
        """
        # Fill input boxes
        self._fill_element(selector='#search_by_location_field', value="London")
        self._fill_element(selector='#min-rent', value=min_rent)
        self._fill_element(selector='#max-rent', value=max_rent)

        # Check boxes
        self.page.evaluate("""document.getElementById('oneBedOrStudio').checked = false;""")
        self.page.evaluate("""document.getElementById('wholeProperty').checked = false;""")
        self.page.evaluate("""document.getElementById('wholeWeek').checked = true;""")
        self.page.evaluate("""document.getElementById('doubleRoom').checked = true;""")
        self.page.evaluate("""document.getElementById('adsWithPhoto').checked = true;""")
        self.page.evaluate("""document.getElementById('liveOut').checked = true;""")
        self.page.evaluate("""document.querySelector('select[name="min_term"]').value = '6';""")

        # Search
        self.page.press("#search_by_location_field", "Enter")
        logger.info("Searching Spareroom.")

    def _fill_element(self, selector: str, value: str) -> None:
        self.page.wait_for_selector(selector)
        self.page.fill(selector, value)
        self.page.wait_for_timeout(500)

