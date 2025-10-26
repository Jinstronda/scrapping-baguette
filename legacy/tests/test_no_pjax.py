#!/usr/bin/env python3
"""Test without PJAX headers"""

import requests
from scraper.config import BASE_URL, REQUEST_TIMEOUT
from scraper.logger import logger
from bs4 import BeautifulSoup

def test_without_pjax():
    session = requests.Session()
    
    # Headers WITHOUT X-PJAX
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    
    url = f"{BASE_URL}/web/site-pro/home"
    params = {
        'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
        'p_p_lifecycle': '1',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
        'p_auth': ''
    }
    
    data = {
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': 'a',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
    }
    
    logger.info("POST without PJAX headers...")
    response = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    
    logger.info(f"Final status: {response.status_code}")
    logger.info(f"Final URL: {response.url}")
    logger.info(f"Redirect history: {[r.status_code for r in response.history]}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.find_all('div', class_='contenant_resultat')
    logger.info(f"Found {len(cards)} cards")
    
    if cards:
        logger.info("SUCCESS! Cards found")
        first_card = cards[0]
        nom_prenom = first_card.find('div', class_='nom_prenom')
        if nom_prenom:
            link = nom_prenom.find('a')
            if link:
                logger.info(f"First doctor: {link.get_text(strip=True)}")
                logger.info(f"Link href: {link['href'][:100]}...")
    else:
        with open('no_pjax_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Saved to no_pjax_response.html")

if __name__ == '__main__':
    test_without_pjax()

