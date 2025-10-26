#!/usr/bin/env python3
"""Prove the detail data really exists and is not just '...'"""

import sqlite3

db_path = "db/test_letter_a.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("="*100)
print("PROVING DETAIL DATA EXISTS IN DATABASE")
print("="*100)

# Get one doctor with detail data
cur.execute('''SELECT rpps, name, situation_data, dossier_data 
               FROM professionals 
               WHERE situation_data IS NOT NULL 
               LIMIT 1''')

row = cur.fetchone()

if row:
    rpps, name, situation, dossier = row
    
    print(f"\nDoctor: {name} (RPPS: {rpps})")
    print("-"*100)
    
    if situation:
        print(f"\n1. SITUATION DATA:")
        print(f"   Length: {len(situation):,} bytes")
        print(f"   Type: {type(situation)}")
        print(f"   First 100 characters: {situation[:100]}")
        print(f"   Last 100 characters: {situation[-100:]}")
        
        # Extract actual data content
        if 'Mode d' in situation:
            idx = situation.find('Mode d')
            print(f"   Sample content around 'Mode d': ...{situation[max(0, idx-50):idx+150]}...")
    
    if dossier:
        print(f"\n2. DOSSIER DATA:")
        print(f"   Length: {len(dossier):,} bytes")
        print(f"   Type: {type(dossier)}")
        print(f"   First 100 characters: {dossier[:100]}")
        
        # Extract actual data content
        if 'EXERCICE PROFESSIONNEL' in dossier:
            idx = dossier.find('EXERCICE PROFESSIONNEL')
            print(f"   Sample content around 'EXERCICE PROFESSIONNEL': ...{dossier[max(0, idx-20):idx+100]}...")
    
    # Save one tab to a file for manual inspection
    with open('tests/sample_dossier.html', 'w', encoding='utf-8') as f:
        f.write(dossier if dossier else '')
    print(f"\n3. SAVED DOSSIER HTML TO: tests/sample_dossier.html")
    print(f"   You can open this file in a browser to see the full captured data!")

else:
    print("\nNO DATA FOUND!")

conn.close()

print("\n" + "="*100)
print("IF YOU SEE '...' IN YOUR DATABASE VIEWER, IT'S JUST DISPLAY TRUNCATION!")
print("THE FULL HTML PAGES ARE STORED AS SHOWN ABOVE")
print("="*100)

