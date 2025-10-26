#!/usr/bin/env python3
"""Check POST response status"""

from scraper.session import create_session
from scraper.config import BASE_URL, REQUEST_TIMEOUT
from scraper.logger import logger

def test_post():
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
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': 'a',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
    }
    
    logger.info("Making POST without following redirects...")
    response = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT, allow_redirects=False)
    
    logger.info(f"POST status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    if response.status_code in (301, 302, 303, 307, 308):
        redirect_url = response.headers.get('Location')
        logger.info(f"REDIRECT to: {redirect_url}")
        
        logger.info(f"\nFollowing redirect...")
        response2 = session.get(redirect_url, timeout=REQUEST_TIMEOUT)
        logger.info(f"GET status: {response2.status_code}")
        logger.info(f"Final URL: {response2.url}")
        logger.info(f"Response length: {len(response2.text)}")
        
        # Check for cards
        has_cards = 'contenant_resultat' in response2.text
        logger.info(f"Has contenant_resultat: {has_cards}")
        
        with open('final_results.html', 'w', encoding='utf-8') as f:
            f.write(response2.text)
        logger.info("Saved to final_results.html")
    else:
        logger.info(f"No redirect, response length: {len(response.text)}")

if __name__ == '__main__':
    test_post()

