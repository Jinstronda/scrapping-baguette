import sqlite3

conn = sqlite3.connect('db/test_3_pages.db')
cur = conn.cursor()

cur.execute('SELECT rpps, name, organization, address, phone FROM professionals LIMIT 10')
rows = cur.fetchall()

print('RPPS | Name | Org | Address | Phone')
print('-' * 120)

for r in rows:
    org = r[2][:30] if r[2] else ''
    addr = r[3][:30] if r[3] else ''
    phone = r[4] if r[4] else ''
    print(f'{r[0]} | {r[1][:20]:20} | {org:30} | {addr:30} | {phone}')

conn.close()

