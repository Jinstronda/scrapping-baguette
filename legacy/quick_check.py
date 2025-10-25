import sqlite3
conn = sqlite3.connect('db/test_100_workers.db')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM professionals')
total = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE situation_data IS NOT NULL AND LENGTH(situation_data) > 100')
with_sit = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM professionals WHERE dossier_data IS NOT NULL AND LENGTH(dossier_data) > 100')
with_dos = cur.fetchone()[0]

print(f'Total: {total}')
print(f'With Situation (>100): {with_sit}')
print(f'With Dossier (>100): {with_dos}')

# Show sample
cur.execute('SELECT rpps, name, situation_data, dossier_data FROM professionals WHERE LENGTH(dossier_data) > 100 LIMIT 3')
rows = cur.fetchall()

print('\nSample doctors WITH data:')
for r in rows:
    print(f'{r[0]} | {r[1]}')
    print(f'  Situation: {len(r[2]) if r[2] else 0} bytes')
    print(f'  Dossier: {len(r[3]) if r[3] else 0} bytes')
    if r[3]:
        print(f'  Dossier content: {r[3][:100]}...')

conn.close()

