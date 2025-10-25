"""
Smart prefix expansion for complete database coverage
Automatically expands prefixes that hit pagination limits
"""

def generate_expanded_prefixes(prefix):
    """Generate sub-prefixes: 'a' → ['aa', 'ab', ..., 'az']"""
    return [prefix + letter for letter in 'abcdefghijklmnopqrstuvwxyz']


def should_expand(total_cards, max_pages=10):
    """
    Check if prefix needs expansion
    If we collected ~100 cards (10 pages × 10 cards), there might be more
    """
    return total_cards >= (max_pages * 10 - 5)  # Allow 5 card margin


def smart_scrape(scrape_function, initial_prefixes, num_workers, progress_queue=None):
    """
    Scrape with automatic prefix expansion
    
    Args:
        scrape_function: The scraping function (takes prefix, progress_queue)
        initial_prefixes: Starting prefixes (e.g., ['a', 'b', 'c'])
        num_workers: Number of concurrent workers
        progress_queue: Queue for progress updates
    
    Returns:
        List of all results
    """
    from multiprocessing import Pool
    from functools import partial
    
    to_scrape = list(initial_prefixes)
    all_results = []
    
    while to_scrape:
        # Take next batch
        batch = to_scrape[:num_workers]
        to_scrape = to_scrape[num_workers:]
        
        # Scrape batch in parallel
        scrape_with_queue = partial(scrape_function, progress_queue=progress_queue)
        with Pool(processes=min(num_workers, len(batch))) as pool:
            results = pool.map(scrape_with_queue, batch)
        
        # Check which need expansion
        for result in results:
            all_results.append(result)
            
            # If hit the limit, expand
            if not result.get('error') and should_expand(result.get('total_cards', 0)):
                expanded = generate_expanded_prefixes(result['prefix'])
                to_scrape.extend(expanded)
                print(f"\n🔄 Expanding '{result['prefix']}' ({result['total_cards']} cards) → {len(expanded)} sub-prefixes")
                print(f"   Queue: {len(to_scrape)} prefixes remaining\n")
    
    return all_results

