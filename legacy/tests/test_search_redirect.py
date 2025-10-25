#!/usr/bin/env python3
"""Test if search redirects"""

from scraper.session import create_session, post_with_retry
from scraper.config import BASE_URL
from scraper.logger import logger

def test_redirect():
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
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_rechercheProximite': 'active',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
        '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
    }
    
    response = session.post(url, params=params, data=data, allow_redirects=False)
    
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Headers: {dict(response.headers)}")
    
    if response.status_code in (301, 302, 303, 307, 308):
        logger.info(f"REDIRECT to: {response.headers.get('Location')}")
        
        # Follow redirect manually
        redirect_url = response.headers.get('Location')
        if redirect_url:
            logger.info("\nFollowing redirect...")
            response2 = session.get(redirect_url)
            logger.info(f"After redirect status: {response2.status_code}")
            logger.info(f"Final URL: {response2.url}")
            
            with open('after_redirect.html', 'w', encoding='utf-8') as f:
                f.write(response2.text)
            
            # Check for cards
            html = response2.text
            has_details = 'DetailsPPAction' in html
            has_rpps = '_mapportlet_idRpps' in html
            has_aucun = 'aucun' in html.lower()
            
            logger.info(f"Has DetailsPPAction links: {has_details}")
            logger.info(f"Has _mapportlet_idRpps: {has_rpps}")
            logger.info(f"Has 'aucun' (no results): {has_aucun}")

if __name__ == '__main__':
    test_redirect()

