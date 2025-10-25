from bs4 import BeautifulSoup

html = open('debug_page1_response.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

print('Total links:', len(soup.find_all('a')))
print('Has resultatportlet:', 'resultatportlet' in html)

links_with_Details = [a for a in soup.find_all('a', href=True) if 'Details' in a['href']]
print('Links with Details:', len(links_with_Details))

links_with_rpps = [a for a in soup.find_all('a', href=True) if 'rpps' in a['href'].lower()]
print('Links with rpps:', len(links_with_rpps))

# Check for result text
if 'Résultats' in html or 'resultats' in html.lower():
    print('Has results text: YES')
else:
    print('Has results text: NO')

# Look for "Aucun résultat" or similar
if 'Aucun' in html or 'aucun' in html.lower():
    print('Has "Aucun" (no results): YES')
    # Find the context
    idx = html.lower().find('aucun')
    if idx != -1:
        print('Context:', html[max(0, idx-50):idx+100])

