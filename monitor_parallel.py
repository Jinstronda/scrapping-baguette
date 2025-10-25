#!/usr/bin/env python3
"""
Real-time monitor for parallel_scraper.py
Shows live progress and statistics
"""

import sqlite3
import time
import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def monitor():
    db_path = 'db/health_professionals.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Run: python parallel_scraper.py")
        return
    
    start_time = time.time()
    prev_count = 0
    
    try:
        while True:
            clear_screen()
            
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Total count
            c.execute('SELECT COUNT(*) FROM professionals')
            total = c.fetchone()[0]
            
            # By prefix
            c.execute('''
                SELECT search_prefix, COUNT(*) 
                FROM professionals 
                GROUP BY search_prefix 
                ORDER BY search_prefix
            ''')
            prefixes = c.fetchall()
            
            # Data quality
            c.execute('SELECT COUNT(*) FROM professionals WHERE LENGTH(situation_data) > 100')
            complete = c.fetchone()[0]
            
            # Recent additions
            c.execute('''
                SELECT name, search_prefix, created_at 
                FROM professionals 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent = c.fetchall()
            
            conn.close()
            
            # Calculate stats
            elapsed = time.time() - start_time
            rate = total / elapsed if elapsed > 0 else 0
            new_since_last = total - prev_count
            prev_count = total
            
            # Display
            print("="*80)
            print(" "*25 + "PARALLEL SCRAPER MONITOR")
            print("="*80)
            print(f"\nTime Elapsed: {elapsed:.0f}s ({elapsed/60:.1f} min)")
            print(f"Total Doctors: {total}")
            print(f"Speed: {rate:.2f} doctors/second")
            print(f"Data Quality: {complete}/{total} ({100*complete/total if total > 0 else 0:.0f}%) complete")
            
            print(f"\n{'Prefix':<8} {'Count':<10} {'Bar'}")
            print("-"*40)
            max_count = max([p[1] for p in prefixes], default=1)
            for prefix, count in prefixes:
                bar_len = int(30 * count / max_count) if max_count > 0 else 0
                bar = '█' * bar_len
                print(f"{prefix:<8} {count:<10} {bar}")
            
            print(f"\n{'Recently Added:':<25} {'Prefix'}")
            print("-"*40)
            for name, prefix, created in recent[:5]:
                print(f"{name[:23]:<25} {prefix}")
            
            print("\n" + "="*80)
            print("Press Ctrl+C to stop monitoring")
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        print(f"Final count: {total} doctors in {elapsed/60:.1f} minutes")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    monitor()

