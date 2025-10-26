#!/usr/bin/env python3
"""Check if parser is extracting basic fields"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.worker import submit_search_prefix
from scraper.parser import parse_search_results
from scraper.session import create_session

session = create_session()

print("Searching for 'a'...")
response = submit_search_prefix(session, 'a')

if response:
    cards = parse_search_results(response.text)
    print(f"\nFound {len(cards)} cards\n")
    
    for i, card in enumerate(cards[:5]):
        print(f"Card {i+1}: {card.get('name')}")
        print(f"  RPPS: {card.get('rpps')}")
        print(f"  Profession: {card.get('profession')}")
        print(f"  Organization: {card.get('organization')}")
        print(f"  Address: {card.get('address')}")
        print(f"  Phone: {card.get('phone')}")
        print(f"  Email: {card.get('email')}")
        print()

