import sqlite3

conn = sqlite3.connect('db/test_3_pages.db')
cur = conn.cursor()

cur.execute("SELECT rpps, name, profession, organization, address, phone, email FROM professionals WHERE rpps='10006415128'")
row = cur.fetchone()

if row:
    print(f'RPPS: {row[0]}')
    print(f'Name: {row[1]}')
    print(f'Profession: {row[2]}')
    print(f'Organization: {row[3]}')
    print(f'Address: {row[4]}')
    print(f'Phone: {row[5]}')
    print(f'Email: {row[6]}')
else:
    print('Record not found')

conn.close()

