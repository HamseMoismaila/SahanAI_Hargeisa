import asyncio
import re
import pandas as pd
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

class PropertyScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.data = []

    def _normalize_price(self, price_str: str) -> float:
        """
        Parses USD and Somaliland Shilling prices and normalizes to USD.
        Example logic:
        - If contains '$' or 'USD', extract numbers.
        - If contains 'SLSH' or 'Somaliland Shilling', divide by current exchange rate (~8500).
        """
        if not price_str:
            return None
        
        # Simple extraction for skeleton
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        if not numbers:
            return None
            
        value = float(numbers[0])
        
        if 'SLSH' in price_str.upper() or 'SHILLING' in price_str.upper():
            # Example rate, should be fetched dynamically in a real scenario
            exchange_rate = 8500 
            value = value / exchange_rate
            
        return value

    async def scrape_page(self, page, url: str):
        """Scrape a single page of property listings."""
        await page.goto(url)
        # TODO: Add specific selectors for the target website
        # example: 
        # properties = await page.locator('.property-listing').all()
        # for prop in properties:
        #     title = await prop.locator('.title').inner_text()
        #     price_text = await prop.locator('.price').inner_text()
        #     price_usd = self._normalize_price(price_text)
        #     description = await prop.locator('.desc').inner_text()
        #     self.data.append({...})
        print(f"Scraping {url}...")
        # Simulating data extraction
        await asyncio.sleep(1)

    async def run(self, max_pages: int = 1):
        """Main execution method to start the Playwright browser and scrape."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            for i in range(1, max_pages + 1):
                url = f"{self.base_url}?page={i}"
                await self.scrape_page(page, url)
                
            await browser.close()
            
    def save_data(self, output_path: str):
        """Save scraped data to CSV or Parquet."""
        df = pd.DataFrame(self.data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Data saved to {output_path}")

if __name__ == "__main__":
    scraper = PropertyScraper(base_url="https://example-hargeisa-homes.com/properties")
    asyncio.run(scraper.run(max_pages=2))
    scraper.save_data("data/raw/scraped_properties.csv")
