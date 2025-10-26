#!/usr/bin/env python3
"""Simple viewer to see the actual data in the database"""

import sqlite3
import json
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "db/test_single_doctor.db"

print(f"\n{'='*100}")
print(f"VIEWING DATA FROM: {db_path}")
print(f"{'='*100}\n")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all records
cur.execute('''SELECT rpps, name, profession, organization, address, phone, email,
               situation_data, dossier_data, diplomes_data, personne_data
               FROM professionals''')

rows = cur.fetchall()

print(f"Total doctors in database: {len(rows)}\n")

for i, row in enumerate(rows, 1):
    print(f"\n{'-'*100}")
    print(f"DOCTOR {i}: {row[1]} (RPPS: {row[0]})")
    print(f"{'-'*100}")
    
    print(f"\nBASIC INFO:")
    print(f"  Name: {row[1]}")
    print(f"  Profession: {row[2]}")
    print(f"  Organization: {row[3] if row[3] else '(none)'}")
    print(f"  Address: {row[4] if row[4] else '(none)'}")
    print(f"  Phone: {row[5] if row[5] else '(none)'}")
    print(f"  Email: {row[6] if row[6] else '(none)'}")
    
    print(f"\nDETAIL DATA:")
    
    # Situation
    if row[7]:
        try:
            sit_json = json.loads(row[7])
            print(f"  Situation: {len(row[7]):,} bytes JSON - {len(sit_json)} sections")
        except:
            print(f"  Situation: {len(row[7]):,} bytes (raw)")
    else:
        print(f"  Situation: (none)")
    
    # Dossier
    if row[8]:
        try:
            dos_json = json.loads(row[8])
            print(f"  Dossier: {len(row[8]):,} bytes JSON - {len(dos_json)} sections")
            
            if 'EXERCICE PROFESSIONNEL' in dos_json:
                ex = dos_json['EXERCICE PROFESSIONNEL']
                print(f"    EXERCICE PROFESSIONNEL:")
                nom_key = "Nom d'exercice"
                prenom_key = "Prénom d'exercice"
                print(f"      Nom: {ex.get(nom_key, 'N/A')}")
                print(f"      Prenom: {ex.get(prenom_key, 'N/A')}")
                print(f"      Profession: {ex.get('Profession', 'N/A')}")
        except:
            print(f"  Dossier: {len(row[8]):,} bytes (raw)")
    else:
        print(f"  Dossier: (none)")
    
    # Diplomes
    if row[9]:
        try:
            dip_json = json.loads(row[9])
            print(f"  Diplomes: {len(row[9]):,} bytes JSON")
            
            if 'diplomes' in dip_json and dip_json['diplomes']:
                print(f"    Diplomes count: {len(dip_json['diplomes'])}")
                for d in dip_json['diplomes']:
                    if d.get('Libellé'):
                        print(f"      - {d.get('Libellé')} ({d.get('Type', 'N/A')})")
        except:
            print(f"  Diplomes: {len(row[9]):,} bytes (raw)")
    else:
        print(f"  Diplomes: (none)")
    
    # Personne
    if row[10]:
        try:
            per_json = json.loads(row[10])
            print(f"  Personne: {len(row[10]):,} bytes JSON - {len(per_json)} sections")
        except:
            print(f"  Personne: {len(row[10]):,} bytes (raw)")
    else:
        print(f"  Personne: (none)")

conn.close()

print(f"\n{'='*100}")
print(f"DATABASE LOCATION: {db_path}")
print(f"{'='*100}\n")

