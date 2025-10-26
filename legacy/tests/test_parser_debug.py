#!/usr/bin/env python3
"""Debug the parser with actual HTML"""

from scraper.worker import submit_search_prefix
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.logger import logger
from bs4 import BeautifulSoup

def test_parser():
    session = create_session()
    
    logger.info("Submitting search for 'a'")
    response = submit_search_prefix(session, 'a')
    
    if response:
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response URL: {response.url}")
        
        html = response.text
        with open('search_response_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for expected elements
        contenant_results = soup.find_all('div', class_='contenant_resultat')
        logger.info(f"Found {len(contenant_results)} div.contenant_resultat")
        
        if contenant_results:
            first = contenant_results[0]
            logger.info(f"\nFirst card HTML:\n{first.prettify()[:500]}")
        
        # Try parsing
        cards = parse_search_results(html)
        logger.info(f"\nParsed {len(cards)} cards")
        
        if cards:
            logger.info(f"First card: {cards[0]}")

if __name__ == '__main__':
    test_parser()

