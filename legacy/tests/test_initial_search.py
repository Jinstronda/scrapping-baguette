#!/usr/bin/env python3
"""Test to understand the search form"""

from scraper.session import create_session, get_with_retry, post_with_retry
from scraper.config import BASE_URL
from scraper.logger import logger
from bs4 import BeautifulSoup

def test_search_form():
    session = create_session()
    
    # First, get the home page to see the search form
    logger.info("Getting home page to analyze search form")
    response = get_with_retry(session, f"{BASE_URL}/web/site-pro", retries=1)
    
    if response and response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the search form
        forms = soup.find_all('form')
        logger.info(f"Found {len(forms)} forms")
        
        for i, form in enumerate(forms):
            logger.info(f"\nForm {i+1}:")
            logger.info(f"  Action: {form.get('action')}")
            logger.info(f"  Method: {form.get('method')}")
            
            inputs = form.find_all(['input', 'select', 'textarea'])
            logger.info(f"  Inputs: {len(inputs)}")
            for inp in inputs[:10]:  # First 10
                name = inp.get('name', '')
                value = inp.get('value', '')
                inp_type = inp.get('type', inp.name)
                if name:
                    logger.info(f"    {inp_type}: {name} = {value}")
        
        # Also save it for manual inspection
        with open('debug_home_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("\nSaved home page to debug_home_page.html")

if __name__ == '__main__':
    test_search_form()

