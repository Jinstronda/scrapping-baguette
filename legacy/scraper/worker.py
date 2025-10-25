from scraper.config import SEARCH_URL, INFO_URL, RETRY_COUNT, REQUEST_TIMEOUT, BASE_URL
from scraper.session import create_session, get_with_retry, post_with_retry
from scraper.parser import (
    parse_search_results, parse_pagination, extract_detail_params, get_tab_actions
)
from scraper.database import upsert_professional
from scraper.logger import log_prefix_start, log_doctor_open, log_tab_fetch, log_upsert, log_error
from scraper.content_extractor import extract_all_detail_content
import string

def extract_p_auth(session):
    try:
        import re
        from bs4 import BeautifulSoup
        
        response = session.get(f"{BASE_URL}/web/site-pro", timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return ''
        
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', attrs={'name': 'fmRecherche'})
        
        if form:
            action = form.get('action', '')
            match = re.search(r'p_auth=([^&]+)', action)
            if match:
                return match.group(1)
        
        return ''
    except:
        return ''

def submit_search_prefix(session, prefix):
    try:
        import time
        time.sleep(0.1)
        
        p_auth = extract_p_auth(session)
        
        url = f"{BASE_URL}/web/site-pro/home"
        params = {
            'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
            'p_auth': p_auth
        }
        
        data = {
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': prefix,
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
            '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
        }
        
        response = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        return response
    except Exception as e:
        log_error(f"Failed to submit search for prefix {prefix}: {e}")
        return None

def paginate_results(session, prefix, max_pages=10):
    pages_data = []
    
    for page_num in range(1, max_pages + 1):
        try:
            params = {
                'p_p_id': 'resultatportlet',
                'p_p_lifecycle': '0',
                'p_p_state': 'normal',
                'p_p_mode': 'view',
                '_resultatportlet_delta': '10',
                '_resultatportlet_resetCur': 'false',
                '_resultatportlet_cur': str(page_num)
            }
            
            response = get_with_retry(session, SEARCH_URL, params=params, retries=RETRY_COUNT)
            
            if not response or response.status_code != 200:
                log_error(f"Failed to fetch page {page_num} for prefix {prefix}", 
                         url=SEARCH_URL, status=response.status_code if response else 'None')
                break
            
            html = response.text
            cards = parse_search_results(html)
            
            log_prefix_start(prefix, page_num, len(cards))
            
            if not cards:
                break
            
            pages_data.append((page_num, cards))
            
        except Exception as e:
            log_error(f"Error during pagination for prefix {prefix} page {page_num}: {e}")
            break
    
    return pages_data

def fetch_doctor_details(session, doctor_ids):
    details = {
        'situation_data': None,
        'dossier_data': None,
        'diplomes_data': None,
        'personne_data': None
    }
    
    try:
        import time
        time.sleep(0.2)
        
        if not doctor_ids.get('idRpps'):
            return details
        
        step1_params = {
            'p_p_id': 'mapportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_mapportlet_javax.portlet.action': 'DetailsPPAction',
            '_mapportlet_idSituExe': doctor_ids.get('idSituExe', ''),
            '_mapportlet_idExePro': doctor_ids.get('idExePro', ''),
            '_mapportlet_resultatIndex': doctor_ids.get('resultatIndex', ''),
            '_mapportlet_idRpps': doctor_ids.get('idRpps', ''),
            '_mapportlet_siteId': doctor_ids.get('siteId', ''),
            '_mapportlet_coordonneesId': doctor_ids.get('coordonneesId', ''),
            '_mapportlet_etatPP': doctor_ids.get('etatPP', 'OUVERT'),
            'p_auth': doctor_ids.get('p_auth', '')
        }
        
        step1_response = post_with_retry(session, SEARCH_URL, params=step1_params, data='', retries=RETRY_COUNT)
        
        if not step1_response or step1_response.status_code != 200:
            log_doctor_open(doctor_ids.get('idRpps', ''), step1_response.status_code if step1_response else 'None')
            return details
        
        log_doctor_open(doctor_ids.get('idRpps', ''), 200)
        time.sleep(1.0)  # Longer delay to ensure session state is maintained
        
        step2_params = {
            'p_p_id': 'mapportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_mapportlet_javax.portlet.action': 'infoDetailPP',
            '_mapportlet_idSituExePourDetail': doctor_ids.get('idSituExe', ''),
            '_mapportlet_idNat': '8' + doctor_ids.get('idRpps', ''),
            '_mapportlet_idExeProPourDetail': doctor_ids.get('idExePro', ''),
            '_mapportlet_coordonneIdPourDetail': doctor_ids.get('coordonneesId', ''),
            '_mapportlet_resultatIndex': doctor_ids.get('resultatIndex', ''),
            '_mapportlet_idRpps': doctor_ids.get('idRpps', ''),
            '_mapportlet_etat': doctor_ids.get('etatPP', 'OUVERT'),
            '_mapportlet_siteIdPourDetail': doctor_ids.get('siteId', ''),
            'p_auth': doctor_ids.get('p_auth', '')
        }
        
        step2_response = session.post(SEARCH_URL, params=step2_params, data='', timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        if not step2_response or step2_response.status_code != 200:
            return details
        
        details['situation_data'] = step2_response.text
        
        tab_actions = {
            'dossier': 'detailsPPDossierPro',
            'diplomes': 'detailsPPDiplomes',
            'personne': 'detailsPPPersonne'
        }
        
        for tab_name, action in tab_actions.items():
            try:
                tab_params = {
                    'p_p_id': 'resultatsportlet',
                    'p_p_lifecycle': '1',
                    'p_p_state': 'normal',
                    'p_p_mode': 'view',
                    '_resultatsportlet_javax.portlet.action': action,
                    '_resultatsportlet_idNat': '8' + doctor_ids.get('idRpps', ''),
                    '_resultatsportlet_resultatIndex': doctor_ids.get('resultatIndex', ''),
                    '_resultatsportlet_idRpps': doctor_ids.get('idRpps', ''),
                    '_resultatsportlet_siteId': doctor_ids.get('siteId', ''),
                    '_resultatsportlet_coordonneId': doctor_ids.get('coordonneesId', ''),
                    '_resultatsportlet_etat': doctor_ids.get('etatPP', 'OUVERT'),
                    'p_auth': doctor_ids.get('p_auth', ''),
                    '_resultatsportlet_idExePro': doctor_ids.get('idExePro', '')
                }
                
                tab_response = post_with_retry(session, INFO_URL, params=tab_params, data='', retries=RETRY_COUNT)
                
                if tab_response and tab_response.status_code == 200:
                    log_tab_fetch(doctor_ids.get('idRpps', ''), tab_name, 200)
                    details[f'{tab_name}_data'] = tab_response.text
                else:
                    log_tab_fetch(doctor_ids.get('idRpps', ''), tab_name, 
                                tab_response.status_code if tab_response else 'None')
                    
            except Exception as e:
                log_error(f"Error fetching tab {tab_name} for doctor {doctor_ids.get('idRpps', '')}: {e}")
        
    except Exception as e:
        log_error(f"Error fetching doctor details: {e}")
    
    return details

def process_prefix(prefix, db_path, seen_prefixes):
    session = create_session()
    sub_prefixes = []
    
    try:
        response = submit_search_prefix(session, prefix)
        
        if not response or response.status_code != 200:
            log_error(f"Search submission failed for prefix {prefix}")
            return sub_prefixes
        
        pages_data = []
        cards = parse_search_results(response.text)
        log_prefix_start(prefix, 1, len(cards))
        
        if cards:
            pages_data.append((1, cards))
        
        for page_num in range(2, 11):
            params = {
                'p_p_id': 'resultatportlet',
                'p_p_lifecycle': '0',
                'p_p_state': 'normal',
                'p_p_mode': 'view',
                '_resultatportlet_delta': '10',
                '_resultatportlet_resetCur': 'false',
                '_resultatportlet_cur': str(page_num)
            }
            
            page_response = get_with_retry(session, SEARCH_URL, params=params, retries=RETRY_COUNT)
            
            if not page_response or page_response.status_code != 200:
                break
            
            cards = parse_search_results(page_response.text)
            log_prefix_start(prefix, page_num, len(cards))
            
            if not cards:
                break
            
            pages_data.append((page_num, cards))
        
        if len(pages_data) >= 3:
            for letter in string.ascii_lowercase:
                new_prefix = prefix + letter
                if new_prefix not in seen_prefixes:
                    sub_prefixes.append(new_prefix)
                    seen_prefixes.add(new_prefix)
        
        for page_num, cards in pages_data:
            for card in cards:
                try:
                    if not card.get('rpps'):
                        continue
                    
                    upsert_professional(db_path, card)
                    
                    if card.get('_ids'):
                        details = fetch_doctor_details(session, card['_ids'])
                        
                        try:
                            clean_details = extract_all_detail_content(details)
                            
                            detail_update = {
                                'rpps': card['rpps'],
                                'situation_data': clean_details.get('situation_data'),
                                'dossier_data': clean_details.get('dossier_data'),
                                'diplomes_data': clean_details.get('diplomes_data'),
                                'personne_data': clean_details.get('personne_data')
                            }
                            upsert_professional(db_path, detail_update)
                            
                            log_upsert(card['rpps'])
                        except Exception as e:
                            log_error(f"Error extracting details for {card['rpps']}: {e}")
                        
                except Exception as e:
                    log_error(f"Error processing doctor {card.get('rpps', 'unknown')}: {e}")
                    continue
                    
    except Exception as e:
        log_error(f"Error processing prefix {prefix}: {e}")
    
    return sub_prefixes

