html = open('tests/worker0_dossier.html', encoding='utf-8').read()
print(f'File size: {len(html)} bytes')
print(f'Contains EXERCICE: {"EXERCICE" in html}')
print(f'Contains contenu_dossier: {"contenu_dossier" in html}')
print(f'\nFirst 500 chars:\n{html[:500]}')

