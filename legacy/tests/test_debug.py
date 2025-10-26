#!/usr/bin/env python3
"""Debug script to see actual HTML responses"""

from scraper.session import create_session, get_with_retry, post_with_retry
from scraper.config import SEARCH_URL
from scraper.logger import logger

def test_search_flow():
    session = create_session()
    
    logger.info("=== Testing search flow ===")
    
    # Test 1: Try to submit search for 'z'
    logger.info("Step 1: Submitting search for 'z'")
    params = {
        'p_p_id': 'rechercheportlet_INSTANCE_ctPdpHA24ctE',
        'p_p_lifecycle': '1',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        '_rechercheportlet_INSTANCE_ctPdpHA24ctE_javax.portlet.action': 'rechercheAction'
    }
    
    data = {
        '_rechercheportlet_INSTANCE_ctPdpHA24ctE_qui': 'z',
        '_rechercheportlet_INSTANCE_ctPdpHA24ctE_ou': ''
    }
    
    try:
        response = post_with_retry(session, SEARCH_URL, params=params, data=data, retries=1)
        logger.info(f"Search submission status: {response.status_code if response else 'None'}")
        if response:
            with open('debug_search_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Saved search response to debug_search_response.html ({len(response.text)} bytes)")
    except Exception as e:
        logger.error(f"Search submission failed: {e}")
        return
    
    # Test 2: Try pagination page 1
    logger.info("\nStep 2: Getting page 1 results")
    params = {
        'p_p_id': 'resultatportlet',
        'p_p_lifecycle': '0',
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        '_resultatportlet_delta': '10',
        '_resultatportlet_resetCur': 'false',
        '_resultatportlet_cur': '1'
    }
    
    try:
        response = get_with_retry(session, SEARCH_URL, params=params, retries=1)
        logger.info(f"Page 1 status: {response.status_code if response else 'None'}")
        if response:
            with open('debug_page1_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Saved page 1 response to debug_page1_response.html ({len(response.text)} bytes)")
            
            # Quick check for card indicators
            html = response.text.lower()
            has_rpps = 'idRpps' in html or 'rpps' in html
            has_mapportlet = 'mapportlet' in html
            has_details = 'DetailsPPAction' in html
            
            logger.info(f"Quick checks - has_rpps: {has_rpps}, has_mapportlet: {has_mapportlet}, has_details: {has_details}")
            
    except Exception as e:
        logger.error(f"Page 1 failed: {e}")

if __name__ == '__main__':
    test_search_flow()

