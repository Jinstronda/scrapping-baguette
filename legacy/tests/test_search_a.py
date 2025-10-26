#!/usr/bin/env python3
"""Test search with letter 'a'"""

from scraper.worker import submit_search_prefix, paginate_results
from scraper.session import create_session
from scraper.logger import logger

def test_search_a():
    session = create_session()
    
    logger.info("=== Testing search for 'a' ===")
    
    # Submit search
    logger.info("Submitting search for 'a'")
    response = submit_search_prefix(session, 'a')
    
    if response:
        logger.info(f"Search submission status: {response.status_code}")
        with open('debug_search_a_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Saved search response ({len(response.text)} bytes)")
    
    # Try pagination
    logger.info("\nFetching first 3 pages")
    pages_data = paginate_results(session, 'a', max_pages=3)
    
    logger.info(f"Got {len(pages_data)} pages")
    for page_num, cards in pages_data:
        logger.info(f"  Page {page_num}: {len(cards)} cards")
        if cards:
            logger.info(f"    First card: {cards[0].get('name')} - {cards[0].get('profession')} - RPPS:{cards[0].get('rpps')}")

if __name__ == '__main__':
    test_search_a()

