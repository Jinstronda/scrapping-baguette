#!/usr/bin/env python3
"""Comprehensive verification of all data capture"""

import sqlite3

print("="*100)
print("COMPREHENSIVE DATA VERIFICATION")
print("="*100)

db_path = "db/test_letter_a.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Check basic fields
print("\n1. BASIC DATA (from search results)")
print("-"*100)
cur.execute('''SELECT rpps, name, profession, organization, address, phone, email 
               FROM professionals''')
rows = cur.fetchall()

for r in rows:
    print(f"\nRPPS: {r[0]}")
    print(f"  Name: {r[1]}")
    print(f"  Profession: {r[2]}")
    print(f"  Organization: {r[3] if r[3] else '(none)'}")
    print(f"  Address: {r[4] if r[4] else '(none)'}")
    print(f"  Phone: {r[5] if r[5] else '(none)'}")
    print(f"  Email: {r[6] if r[6] else '(none)'}")

# 2. Check detail data sizes
print("\n" + "="*100)
print("2. DETAIL DATA (from 4 tabs - full HTML pages)")
print("-"*100)
cur.execute('''SELECT rpps, name,
               LENGTH(situation_data) as sit_bytes,
               LENGTH(dossier_data) as dos_bytes,
               LENGTH(diplomes_data) as dip_bytes,
               LENGTH(personne_data) as per_bytes
               FROM professionals''')

rows = cur.fetchall()
total_sit, total_dos, total_dip, total_per = 0, 0, 0, 0

for r in rows:
    sit = r[2] if r[2] else 0
    dos = r[3] if r[3] else 0
    dip = r[4] if r[4] else 0
    per = r[5] if r[5] else 0
    
    total_sit += sit
    total_dos += dos
    total_dip += dip
    total_per += per
    
    print(f"{r[0]} | {r[1][:25]:25} | {sit:15,} | {dos:13,} | {dip:14,} | {per:,}")

print("-"*100)
print(f"{'TOTALS':41} | {total_sit:15,} | {total_dos:13,} | {total_dip:14,} | {total_per:,}")

# 3. Content verification
print("\n" + "="*100)
print("3. CONTENT VERIFICATION (checking for key terms)")
print("-"*100)

cur.execute('SELECT rpps, situation_data, dossier_data, diplomes_data, personne_data FROM professionals LIMIT 1')
row = cur.fetchone()

if row:
    rpps, sit, dos, dip, per = row
    print(f"Checking RPPS {rpps}:")
    
    if sit:
        print(f"\n[OK] Situation data ({len(sit):,} bytes):")
        has_activite = ('ACTIVITÉ' in sit) or ('ACTIVIT' in sit)
        has_structure = 'STRUCTURE' in sit
        has_genre = 'Genre' in sit
        print(f"  - Contains 'ACTIVITE': {has_activite}")
        print(f"  - Contains 'STRUCTURE D EXERCICE': {has_structure}")
        print(f"  - Contains 'Genre d activite': {has_genre}")
    
    if dos:
        print(f"\n[OK] Dossier data ({len(dos):,} bytes):")
        has_exercice = 'EXERCICE PROFESSIONNEL' in dos
        has_rpps = 'RPPS' in dos
        has_profession = 'Profession' in dos
        print(f"  - Contains 'EXERCICE PROFESSIONNEL': {has_exercice}")
        print(f"  - Contains 'RPPS': {has_rpps}")
        print(f"  - Contains 'Profession': {has_profession}")
    
    if dip:
        print(f"\n[OK] Diplomes data ({len(dip):,} bytes):")
        has_diplomes = ('DIPLÔMES' in dip) or ('DIPLOM' in dip)
        has_table = 'table' in dip
        print(f"  - Contains 'DIPLOMES': {has_diplomes}")
        print(f"  - Contains 'table': {has_table}")
    
    if per:
        print(f"\n[OK] Personne data ({len(per):,} bytes):")
        has_etat = ('ÉTAT-CIVIL' in per) or ('TAT-CIVIL' in per)
        has_civilite = 'Civilit' in per
        print(f"  - Contains 'ETAT-CIVIL': {has_etat}")
        print(f"  - Contains 'Civilite': {has_civilite}")

print("\n" + "="*100)
print("VERIFICATION COMPLETE")
print("="*100)

conn.close()

