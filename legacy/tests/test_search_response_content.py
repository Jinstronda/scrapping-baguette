#!/usr/bin/env python3
"""Check search response content"""

from scraper.session import create_session
from scraper.config import BASE_URL
from scraper.logger import logger
from bs4 import BeautifulSoup

def test_search_response():
    session = create_session()
    
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
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': 'médecin',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_rechercheProximite': 'active',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
    }
    
    response = session.post(url, params=params, data=data)
    
    logger.info(f"Search response status: {response.status_code}")
    logger.info(f"Response URL: {response.url}")
    logger.info(f"Response length: {len(response.text)} bytes")
    
    with open('search_response_medecin.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for cards
    detail_links = soup.find_all('a', href=lambda x: x and 'DetailsPPAction' in x if x else False)
    logger.info(f"Links with DetailsPPAction: {len(detail_links)}")
    
    rpps_in_html = '_mapportlet_idRpps' in html
    logger.info(f"Has _mapportlet_idRpps: {rpps_in_html}")
    
    aucun = 'aucun' in html.lower()
    logger.info(f"Has 'aucun': {aucun}")
    
    resultat_count = html.lower().count('résultat')
    logger.info(f"'résultat' appears {resultat_count} times")
    
    # Check if it's the results page
    if 'resultats' in response.url or 'recherche/resultats' in html:
        logger.info("✓ Response appears to be results page")

if __name__ == '__main__':
    test_search_response()

