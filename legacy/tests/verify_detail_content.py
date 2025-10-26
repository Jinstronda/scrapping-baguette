#!/usr/bin/env python3
"""Verify the detail data contains actual content"""

import sqlite3

db_path = "db/test_letter_a.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('''SELECT rpps, name, 
               LENGTH(situation_data), 
               LENGTH(dossier_data), 
               LENGTH(diplomes_data), 
               LENGTH(personne_data) 
               FROM professionals WHERE situation_data IS NOT NULL LIMIT 5''')

rows = cur.fetchall()

print("RPPS | Name | Situation bytes | Dossier bytes | Diplomes bytes | Personne bytes")
print("-" * 100)

for r in rows:
    print(f"{r[0]} | {r[1][:20]:20} | {r[2]:15} | {r[3]:13} | {r[4]:14} | {r[5]}")

cur.execute('SELECT situation_data FROM professionals WHERE rpps="10006415128" LIMIT 1')
row = cur.fetchone()

if row and row[0]:
    data = row[0]
    print(f"\n=== Situation Data Sample (first 500 chars) ===")
    print(data[:500])
    print(f"\nContains 'ACTIVITÉ': {'ACTIVITÉ' in data}")
    print(f"Contains 'STRUCTURE': {'STRUCTURE' in data}")
    mode_exercice = "Mode d'exercice" in data
    print(f"Contains 'Mode d'exercice': {mode_exercice}")

cur.execute('SELECT dossier_data FROM professionals WHERE rpps="10006415128" LIMIT 1')
row = cur.fetchone()

if row and row[0]:
    data = row[0]
    print(f"\n=== Dossier Data Sample (first 500 chars) ===")
    print(data[:500])
    print(f"\nContains 'EXERCICE PROFESSIONNEL': {'EXERCICE PROFESSIONNEL' in data}")
    print(f"Contains 'SAVOIR-FAIRE': {'SAVOIR-FAIRE' in data}")

conn.close()

