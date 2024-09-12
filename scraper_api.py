from fastapi import FastAPI
from pydantic import BaseModel
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from typing import Dict

app = FastAPI()


# Define the input data model for the scraping
class ScrapeRequest(BaseModel):
    search_query: str
    hl: str
    gl: str
    num: int  # Add the num parameter for the number of results


# Function to run Playwright and scrape Google results for a single query
async def scrape_google(search_query: str, hl: str, gl: str, num: int, filter_param: bool = False) -> Dict[str, int]:
    serp_results = {}

    # Set up the Playwright Crawler
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=10,
        headless=True,  # Run headless in production
        browser_type='chromium'
    )

    # Request handler to process the SERP page
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        await context.page.wait_for_selector('div.g', timeout=10000)

        # Select the search results from the page
        results = await context.page.query_selector_all('div.g')

        # Process each result
        for rank, result in enumerate(results, start=1):
            title_element = await result.query_selector('h3')
            link_element = await result.query_selector('a')

            if title_element and link_element:
                href = await link_element.get_attribute('href')
                if href:
                    serp_results[href] = rank

    # Add filter=0 if filter_param is True
    filter_str = '&filter=0' if filter_param else ''
    google_search_url = f'https://www.google.com/search?q={search_query}&hl={hl}&gl={gl}&num={num}{filter_str}'

    # Run the crawler for the constructed URL
    await crawler.run([google_search_url])

    return serp_results


# Function to compare rankings between two SERP results
def compare_serp_rankings(serp_data1, serp_data2):
    changes = {}
    for url, rank1 in serp_data1.items():
        rank2 = serp_data2.get(url, None)
        if rank2:
            changes[url] = rank2 - rank1  # Calculate rank difference
        else:
            changes[url] = "Not ranked in second set"
    for url, rank2 in serp_data2.items():
        if url not in serp_data1:
            changes[url] = "Newly ranked in second set"
    return changes


@app.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    # Step 1: Scrape Google with and without filter=0
    serp_data_normal = await scrape_google(request.search_query, request.hl, request.gl, request.num,
                                           filter_param=False)
    serp_data_filter_off = await scrape_google(request.search_query, request.hl, request.gl, request.num,
                                               filter_param=True)

    # Step 2: Compare rankings between the two sets
    rank_changes = compare_serp_rankings(serp_data_normal, serp_data_filter_off)

    # Return the ranking changes and the original SERP data for both sets
    return {
        "serp_data_normal": serp_data_normal,
        "serp_data_filter_off": serp_data_filter_off,
        "rank_changes": rank_changes
    }
