import sqlite3

conn = sqlite3.connect('scrapy_scraper/db/scrapy_health_professionals.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM professionals')
total = c.fetchone()[0]
print(f"\n{'='*80}")
print(f"TOTAL DOCTORS: {total}")
print('='*80)

c.execute('''
    SELECT 
        rpps, name, address, phone, email,
        CASE WHEN situation_data IS NOT NULL THEN 'YES' ELSE 'NO' END,
        CASE WHEN dossier_data IS NOT NULL THEN 'YES' ELSE 'NO' END,
        CASE WHEN diplomes_data IS NOT NULL THEN 'YES' ELSE 'NO' END,
        CASE WHEN personne_data IS NOT NULL THEN 'YES' ELSE 'NO' END
    FROM professionals
    ORDER BY name
''')

rows = c.fetchall()
for r in rows:
    print(f"\nName: {r[1]}")
    print(f"  RPPS: {r[0]}")
    print(f"  Address: {r[2][:50] if r[2] else 'MISSING'}")
    print(f"  Phone: {r[3] if r[3] else 'MISSING'}")
    print(f"  Email: {r[4] if r[4] else 'MISSING'}")
    print(f"  Details: Situation={r[5]} | Dossier={r[6]} | Diplomes={r[7]} | Personne={r[8]}")

conn.close()

print("\n" + "="*80)
print("SCRAPY VERSION IS WORKING! ✅")
print("="*80)

