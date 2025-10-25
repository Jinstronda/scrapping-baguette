#!/usr/bin/env python3
"""Extract p_auth from home page and use it"""

import requests
import re
from bs4 import BeautifulSoup
from scraper.config import BASE_URL, REQUEST_TIMEOUT
from scraper.logger import logger

def test_with_auth():
    session = requests.Session()
    
    # Get home page first to extract p_auth
    logger.info("Getting home page to extract p_auth...")
    home_response = session.get(f"{BASE_URL}/web/site-pro", timeout=REQUEST_TIMEOUT)
    
    logger.info(f"Home page status: {home_response.status_code}")
    
    # Extract p_auth from the form action or links
    soup = BeautifulSoup(home_response.text, 'html.parser')
    form = soup.find('form', attrs={'name': 'fmRecherche'})
    
    p_auth = ''
    if form:
        action = form.get('action', '')
        logger.info(f"Form action: {action[:150]}...")
        
        # Extract p_auth from URL
        match = re.search(r'p_auth=([^&]+)', action)
        if match:
            p_auth = match.group(1)
            logger.info(f"Extracted p_auth: {p_auth}")
    
    # Now submit search with the correct p_auth
    url = f"{BASE_URL}/web/site-pro/home"
    params = {
        'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
        'p_p_lifecycle': '1',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
        'p_auth': p_auth
    }
    
    data = {
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': 'a',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
    }
    
    logger.info("\nSubmitting search with correct p_auth...")
    response = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response URL: {response.url}")
    logger.info(f"Redirect history: {[(r.status_code, r.url[:80]) for r in response.history]}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.find_all('div', class_='contenant_resultat')
    logger.info(f"Found {len(cards)} cards")
    
    if cards:
        logger.info("✓ SUCCESS! Cards found after using correct p_auth")
    else:
        with open('with_auth_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Saved to with_auth_response.html")

if __name__ == '__main__':
    test_with_auth()

