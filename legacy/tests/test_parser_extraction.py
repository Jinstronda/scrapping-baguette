#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.worker import submit_search_prefix
from scraper.parser import parse_search_results
from scraper.session import create_session
from scraper.logger import logger

def test():
    session = create_session()
    response = submit_search_prefix(session, 'a')
    
    if response:
        cards = parse_search_results(response.text)
        logger.info(f"Parsed {len(cards)} cards\n")
        
        for i, card in enumerate(cards[:3]):
            logger.info(f"Card {i+1}:")
            logger.info(f"  RPPS: {card.get('rpps')}")
            logger.info(f"  Name: {card.get('name')}")
            logger.info(f"  Profession: {card.get('profession')}")
            logger.info(f"  Organization: {card.get('organization')}")
            logger.info(f"  Address: {card.get('address')}")
            logger.info(f"  Phone: {card.get('phone')}")
            logger.info(f"  Email: {card.get('email')}")
            logger.info("")

if __name__ == '__main__':
    test()

