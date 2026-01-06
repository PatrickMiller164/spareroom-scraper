from src.logger_config import logger


class SpareRoomScraper:
    def __init__(self, page, domain: str) -> None:
        self.page = page
        self.domain = domain

    def collect_room_urls(self, pages: int) -> list[str]:
        """Iterate through listing pages and collect room URLs.

        Navigates through the specified number of pages on the site, sorts listings
        by newest first, and collects URLs of all room listings found.

        Args:
            pages: Number of pages to scan for room listings.
        """
        # Sort by newest listings first
        self.page.select_option("#sort_by", value="days_since_placed")

        all_urls = []
        for i in range(pages):
            logger.info(f"Scanning page {i+1}")

            page_urls = self._get_room_urls_on_page()
            all_urls.extend(page_urls)

            try:
                self._click_next_page()
            except (StopIteration, ValueError):
                logger.info("No more pages to scrape")
                break

        logger.info(f"Retrieved {len(all_urls)} rooms")
        
        all_urls = list(dict.fromkeys(all_urls))
        return all_urls

    def _get_room_urls_on_page(self) -> list[str]:
        self.page.wait_for_selector("ul.listing-results")
        rooms = self.page.query_selector_all("ul.listing-results li")
        urls = []

        for room in rooms:
            room_url = room.get_attribute("data-listing-url")
            if room_url:
                urls.append(room_url)

        return urls
    
    def _click_next_page(self) -> None:
        next_button = self.page.query_selector("#paginationNextPageLink")
        if not next_button:
            logger.warning("No more pages")
            raise StopIteration("No next page")

        href = next_button.get_attribute("href")
        if not href:
            logger.warning("Next button has no href")
            raise ValueError("Invalid next page link")
        
        self.page.goto(f"{self.domain}/flatshare/{href}", wait_until="load")
