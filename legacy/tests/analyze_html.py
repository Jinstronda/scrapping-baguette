#!/usr/bin/env python3
"""Analyze the actual HTML structure"""

from bs4 import BeautifulSoup
from scraper.session import create_session, get_with_retry
from scraper.config import SEARCH_URL
from scraper.worker import submit_search_prefix
from scraper.logger import logger

def analyze_response():
    session = create_session()
    
    # Submit search for 'a'
    submit_search_prefix(session, 'a')
    
    # Get page 1
    params = {
        'p_p_id': 'resultatportlet',
        'p_p_lifecycle': '0',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        '_resultatportlet_delta': '10',
        '_resultatportlet_resetCur': 'false',
        '_resultatportlet_cur': '1'
    }
    
    response = get_with_retry(session, SEARCH_URL, params=params, retries=1)
    
    if response:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save for inspection
        with open('page1_actual.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Saved actual HTML to page1_actual.html ({len(html)} bytes)")
        
        # Look for doctor cards - try different selectors
        logger.info("\nLooking for doctor cards:")
        
        # Try finding by class
        result_items = soup.find_all('div', class_=lambda x: x and 'result' in x.lower() if x else False)
        logger.info(f"  Found {len(result_items)} divs with 'result' in class")
        
        # Try finding links with rpps
        rpps_links = soup.find_all('a', href=lambda x: x and 'rpps' in x.lower() if x else False)
        logger.info(f"  Found {len(rpps_links)} links with 'rpps' in href")
        
        # Try finding links with DetailsPPAction
        detail_links = soup.find_all('a', href=lambda x: x and 'DetailsPPAction' in x if x else False)
        logger.info(f"  Found {len(detail_links)} links with 'DetailsPPAction' in href")
        
        if detail_links:
            logger.info(f"\nFirst detail link href: {detail_links[0]['href'][:200]}")
            logger.info(f"First detail link text: {detail_links[0].get_text(strip=True)}")
            
            # Find parent structure
            parent = detail_links[0].parent
            for i in range(5):
                if parent:
                    logger.info(f"  Parent {i+1}: {parent.name} class={parent.get('class')}")
                    parent = parent.parent
        
        # Look for specific patterns
        if 'rpps' in html.lower():
            logger.info("\n✓ HTML contains 'rpps'")
        if 'DetailsPPAction' in html:
            logger.info("✓ HTML contains 'DetailsPPAction'")
        
        # Count result-related elements
        result_count = html.lower().count('rpps')
        logger.info(f"\nString 'rpps' appears {result_count} times in HTML")

if __name__ == '__main__':
    analyze_response()

