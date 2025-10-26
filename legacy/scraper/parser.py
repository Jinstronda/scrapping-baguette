from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

def extract_search_form_names(html):
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        return {}
    
    inputs = {}
    for inp in form.find_all(['input', 'select', 'textarea']):
        name = inp.get('name')
        if name:
            value = inp.get('value', '')
            inputs[name] = value
    
    return {
        'action': form.get('action', ''),
        'method': form.get('method', 'GET'),
        'inputs': inputs
    }

def parse_basic_info(card_html):
    soup = BeautifulSoup(str(card_html), 'html.parser')
    
    info = {
        'name': '',
        'profession': '',
        'organization': '',
        'address': '',
        'phone': '',
        'email': '',
        'finess': '',
        'siret': ''
    }
    
    link = soup.find('a')
    if link:
        info['name'] = link.get_text(strip=True)
    
    generics = soup.find_all('generic')
    if len(generics) > 1:
        info['profession'] = generics[1].get_text(strip=True) if len(generics) > 1 else ''
        if len(generics) > 2:
            info['organization'] = generics[2].get_text(strip=True)
        if len(generics) > 3:
            address_parts = [t.strip() for t in generics[3].get_text('\n').split('\n') if t.strip()]
            info['address'] = ' '.join(address_parts)
        if len(generics) > 4:
            info['phone'] = generics[4].get_text(strip=True)
        
        for gen in generics:
            text = gen.get_text(strip=True)
            if 'mssante' in text.lower() or '@' in text:
                if '@' in text and not info['email']:
                    info['email'] = text
    
    text = soup.get_text()
    finess_match = re.search(r'FINESS[:\s]*(\d+)', text, re.IGNORECASE)
    if finess_match:
        info['finess'] = finess_match.group(1)
    
    siret_match = re.search(r'SIRET[:\s]*(\d+)', text, re.IGNORECASE)
    if siret_match:
        info['siret'] = siret_match.group(1)
    
    return info

def extract_params_from_url(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    result = {}
    for key, value in params.items():
        result[key] = value[0] if value else ''
    
    return result

def parse_search_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    cards = soup.find_all('div', class_='contenant_resultat')
    
    for card in cards:
        nom_prenom = card.find('div', class_='nom_prenom')
        if not nom_prenom:
            continue
            
        link = nom_prenom.find('a', href=True)
        if not link or 'DetailsPPAction' not in link.get('href', ''):
            continue
        
        href = link['href']
        params = extract_params_from_url(href)
        
        if not params.get('_mapportlet_idRpps'):
            continue
        
        info = {
            'rpps': params.get('_mapportlet_idRpps', ''),
            'name': link.get_text(strip=True),
            'profession': '',
            'organization': '',
            'address': '',
            'phone': '',
            'email': '',
            'finess': '',
            'siret': ''
        }
        
        profession_divs = card.find_all('div', class_='profession')
        if profession_divs:
            texts = [p.get_text(strip=True) for p in profession_divs if p.get_text(strip=True)]
            if texts:
                info['profession'] = texts[0]
            if len(texts) > 1:
                info['organization'] = ' | '.join(texts[1:])
        
        address_div = card.find('div', class_='adresse')
        if address_div:
            info['address'] = address_div.get_text(' ', strip=True).replace('<br>', ' ')
        
        tel_div = card.find('div', class_='tel')
        if tel_div:
            info['phone'] = tel_div.get_text(strip=True)
        
        mssante_div = card.find('div', class_='mssante')
        if mssante_div:
            email_span = mssante_div.find('span', class_='mssante_txt')
            if email_span:
                info['email'] = email_span.get_text(strip=True)
        
        info['_ids'] = {
            'idRpps': params.get('_mapportlet_idRpps', ''),
            'idExePro': params.get('_mapportlet_idExePro', ''),
            'idSituExe': params.get('_mapportlet_idSituExe', ''),
            'siteId': params.get('_mapportlet_siteId', ''),
            'coordonneesId': params.get('_mapportlet_coordonneesId', ''),
            'etatPP': params.get('_mapportlet_etatPP', 'OUVERT'),
            'resultatIndex': params.get('_mapportlet_resultatIndex', ''),
            'p_auth': params.get('p_auth', '')
        }
        
        results.append(info)
    
    return results

def parse_pagination(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    last_page_link = soup.find('a', string=re.compile('Derniere|derniere|last', re.IGNORECASE))
    if last_page_link and last_page_link.get('href'):
        params = extract_params_from_url(last_page_link['href'])
        last_page = int(params.get('_resultatportlet_cur', 1))
        return last_page
    
    return 1

def extract_detail_params(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    params = {
        'idNat': '',
        'idExePro': '',
        'idRpps': '',
        'resultatIndex': '',
        'etat': 'OUVERT',
        'p_auth': '',
        'siteId': '',
        'coordonneId': ''
    }
    
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        if 'resultatsportlet' in href and 'detailsPP' in href:
            url_params = extract_params_from_url(href)
            
            if url_params.get('_resultatsportlet_idNat'):
                params['idNat'] = url_params.get('_resultatsportlet_idNat', '')
            if url_params.get('_resultatsportlet_idExePro'):
                params['idExePro'] = url_params.get('_resultatsportlet_idExePro', '')
            if url_params.get('_resultatsportlet_idRpps'):
                params['idRpps'] = url_params.get('_resultatsportlet_idRpps', '')
            if url_params.get('_resultatsportlet_resultatIndex'):
                params['resultatIndex'] = url_params.get('_resultatsportlet_resultatIndex', '')
            if url_params.get('_resultatsportlet_etat'):
                params['etat'] = url_params.get('_resultatsportlet_etat', 'OUVERT')
            if url_params.get('p_auth'):
                params['p_auth'] = url_params.get('p_auth', '')
            if url_params.get('_resultatsportlet_siteId'):
                params['siteId'] = url_params.get('_resultatsportlet_siteId', '')
            if url_params.get('_resultatsportlet_coordonneId'):
                params['coordonneId'] = url_params.get('_resultatsportlet_coordonneId', '')
            
            if params['idNat']:
                break
    
    return params

def get_tab_actions():
    return {
        'situation': 'detailsPPSituation',
        'dossier': 'detailsPPDossierPro',
        'diplomes': 'detailsPPDiplomes',
        'personne': 'detailsPPPersonne'
    }

