import scrapy
from scrapy import Request, FormRequest
from bs4 import BeautifulSoup
import re
import string
from items import ProfessionalItem

class HealthSpider(scrapy.Spider):
    name = 'health_professionals'
    allowed_domains = ['annuaire.sante.fr']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'DOWNLOAD_DELAY': 0.3,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefixes = list(string.ascii_lowercase)
        self.seen_prefixes = set(self.prefixes)
        self.pages_per_prefix = {}
        # CRITICAL: Each doctor gets unique cookiejar to prevent session conflicts
        self.cookiejar_counter = 0
    
    def start_requests(self):
        """Start by getting home page to extract p_auth"""
        yield Request(
            'https://annuaire.sante.fr/web/site-pro',
            callback=self.parse_home,
            dont_filter=True
        )
    
    def parse_home(self, response):
        """Extract p_auth and start searching"""
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', attrs={'name': 'fmRecherche'})
        
        p_auth = ''
        if form:
            action = form.get('action', '')
            match = re.search(r'p_auth=([^&]+)', action)
            if match:
                p_auth = match.group(1)
        
        self.logger.info(f"Extracted p_auth: {p_auth}")
        
        # Test with just 'a' prefix (will get ~50 doctors from 5 pages)
        yield self.make_search_request('a', p_auth)
    
    def make_search_request(self, prefix, p_auth):
        """Submit search for a prefix"""
        return FormRequest(
            url='https://annuaire.sante.fr/web/site-pro/home',
            formdata={
                'p_p_id': 'rechercheportlet_INSTANCE_blk14HrIzEMS',
                'p_p_lifecycle': '1',
                'p_p_state': 'normal',
                'p_p_mode': 'view',
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_javax.portlet.action': 'rechercheAction',
                'p_auth': p_auth,
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_texttofind': prefix,
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_adresse': '',
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_cordonneesGeo': '',
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_integralite': 'active_only',
                '_rechercheportlet_INSTANCE_blk14HrIzEMS_typeRecherche': 'textLibre'
            },
            callback=self.parse_results,
            dont_filter=True,
            meta={'prefix': prefix, 'page': 1, 'p_auth': p_auth}
        )
    
    def parse_results(self, response):
        """Parse search results and extract doctor cards"""
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', class_='contenant_resultat')
        
        self.logger.info(f"Prefix {response.meta['prefix']} page {response.meta['page']}: {len(cards)} doctors")
        
        for i, card in enumerate(cards):
            if i >= 1:  # TEST: Only first doctor
                break
            doctor_data = self.extract_card_data(card)
            if doctor_data and doctor_data.get('rpps'):
                # TEST: Use single shared cookiejar to see if that fixes session issues
                cookiejar_id = 0
                # cookiejar_id = self.cookiejar_counter
                # self.cookiejar_counter += 1
                
                # Create item with basic data
                item = ProfessionalItem()
                for key, value in doctor_data.items():
                    if key != '_ids':
                        item[key] = value

                # Fetch details with unique cookiejar
                ids = doctor_data.get('_ids', {})
                if ids.get('idRpps'):
                    yield self.make_detail_request(item, ids, cookiejar_id)
                else:
                    yield item
        
        # Track pages for prefix expansion
        prefix = response.meta['prefix']
        page = response.meta['page']
        if prefix not in self.pages_per_prefix:
            self.pages_per_prefix[prefix] = 0
        self.pages_per_prefix[prefix] = max(self.pages_per_prefix[prefix], page)

        # Pagination (limit to 5 pages = ~50 doctors for test)
        if len(cards) > 0 and page < 5:
            next_page = page + 1
            params = {
                'p_p_id': 'resultatportlet',
                'p_p_lifecycle': '0',
                'p_p_state': 'normal',
                'p_p_mode': 'view',
                '_resultatportlet_delta': '10',
                '_resultatportlet_resetCur': 'false',
                '_resultatportlet_cur': str(next_page)
            }
            query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
            url = f'https://annuaire.sante.fr/web/site-pro/recherche/resultats?{query_string}'

            yield Request(
                url=url,
                callback=self.parse_results,
                dont_filter=True,
                meta={
                    'prefix': prefix,
                    'page': next_page,
                    'p_auth': response.meta['p_auth']
                },
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-PJAX': 'true'
                }
            )

        # Prefix expansion if reached many pages
        elif len(cards) == 0 and self.pages_per_prefix.get(prefix, 0) >= 3:
            # Generate sub-prefixes
            p_auth = response.meta['p_auth']
            for letter in string.ascii_lowercase:
                new_prefix = prefix + letter
                if new_prefix not in self.seen_prefixes:
                    self.seen_prefixes.add(new_prefix)
                    self.logger.info(f"Expanding prefix: {prefix} -> {new_prefix}")
                    yield self.make_search_request(new_prefix, p_auth)
    
    def extract_card_data(self, card):
        """Extract data from a result card"""
        data = {
            'rpps': '',
            'name': '',
            'profession': '',
            'organization': '',
            'address': '',
            'phone': '',
            'email': ''
        }
        
        nom_prenom = card.find('div', class_='nom_prenom')
        if not nom_prenom:
            return None
        
        link = nom_prenom.find('a', href=True)
        if not link or 'DetailsPPAction' not in link.get('href', ''):
            return None
        
        # Extract IDs from URL
        href = link['href']
        params = self.extract_params_from_url(href)
        
        data['rpps'] = params.get('_mapportlet_idRpps', '')
        data['name'] = link.get_text(strip=True)
        
        # Profession and organization
        profession_divs = card.find_all('div', class_='profession')
        if profession_divs:
            texts = [p.get_text(strip=True) for p in profession_divs if p.get_text(strip=True)]
            if texts:
                data['profession'] = texts[0]
            if len(texts) > 1:
                data['organization'] = ' | '.join(texts[1:])
        
        # Address
        address_div = card.find('div', class_='adresse')
        if address_div:
            data['address'] = address_div.get_text(' ', strip=True)
        
        # Phone
        tel_div = card.find('div', class_='tel')
        if tel_div:
            data['phone'] = tel_div.get_text(strip=True)
        
        # Email
        mssante_div = card.find('div', class_='mssante')
        if mssante_div:
            email_span = mssante_div.find('span', class_='mssante_txt')
            if email_span:
                data['email'] = email_span.get_text(strip=True)
        
        # Store IDs for detail requests
        data['_ids'] = {
            'idRpps': params.get('_mapportlet_idRpps', ''),
            'idExePro': params.get('_mapportlet_idExePro', ''),
            'idSituExe': params.get('_mapportlet_idSituExe', ''),
            'siteId': params.get('_mapportlet_siteId', ''),
            'coordonneesId': params.get('_mapportlet_coordonneesId', ''),
            'etatPP': params.get('_mapportlet_etatPP', 'OUVERT'),
            'resultatIndex': params.get('_mapportlet_resultatIndex', ''),
            'p_auth': params.get('p_auth', '')
        }
        
        return data
    
    def extract_params_from_url(self, url):
        """Extract query parameters from URL"""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        result = {}
        for key, value in params.items():
            result[key] = value[0] if value else ''
        return result
    
    def make_detail_request(self, item, ids, cookiejar_id):
        """Step 1: Open doctor detail popup - CRITICAL: params in URL, empty body"""
        base_url = 'https://annuaire.sante.fr/web/site-pro/recherche/resultats'
        
        params = {
            'p_p_id': 'mapportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_mapportlet_javax.portlet.action': 'DetailsPPAction',
            '_mapportlet_idSituExe': ids.get('idSituExe', ''),
            '_mapportlet_idExePro': ids.get('idExePro', ''),
            '_mapportlet_resultatIndex': ids.get('resultatIndex', ''),
            '_mapportlet_idRpps': ids.get('idRpps', ''),
            '_mapportlet_siteId': ids.get('siteId', ''),
            '_mapportlet_coordonneesId': ids.get('coordonneesId', ''),
            '_mapportlet_etatPP': ids.get('etatPP', 'OUVERT'),
            'p_auth': ids.get('p_auth', '')
        }
        
        # Build URL with params (mimics original scraper: params in URL, body empty)
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        
        return Request(
            url=url,
            method='POST',
            body='',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            callback=self.parse_detail_popup,
            dont_filter=True,
            meta={
                'cookiejar': cookiejar_id,
                'item': item,
                'ids': ids
            }
        )
    
    def parse_detail_popup(self, response):
        """Step 2: Navigate to full detail page - CRITICAL: params in URL"""
        item = response.meta['item']
        ids = response.meta['ids']
        cookiejar_id = response.meta['cookiejar']

        base_url = 'https://annuaire.sante.fr/web/site-pro/recherche/resultats'
        
        params = {
            'p_p_id': 'mapportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_mapportlet_javax.portlet.action': 'infoDetailPP',
            '_mapportlet_idSituExePourDetail': ids.get('idSituExe', ''),
            '_mapportlet_idNat': '8' + ids.get('idRpps', ''),
            '_mapportlet_idExeProPourDetail': ids.get('idExePro', ''),
            '_mapportlet_coordonneIdPourDetail': ids.get('coordonneesId', ''),
            '_mapportlet_resultatIndex': ids.get('resultatIndex', ''),
            '_mapportlet_idRpps': ids.get('idRpps', ''),
            '_mapportlet_etat': ids.get('etatPP', 'OUVERT'),
            '_mapportlet_siteIdPourDetail': ids.get('siteId', ''),
            'p_auth': ids.get('p_auth', '')
        }
        
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        
        return Request(
            url=url,
            method='POST',
            body='',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            callback=self.parse_situation_tab,
            dont_filter=True,
            meta={
                'cookiejar': cookiejar_id,
                'item': item,
                'ids': ids
            }
        )
    
    def parse_situation_tab(self, response):
        """Parse situation tab (default page after infoDetailPP)"""
        item = response.meta['item']
        ids = response.meta['ids']
        cookiejar_id = response.meta['cookiejar']

        item['situation_html'] = response.text

        # Fetch dossier tab
        yield self.make_tab_request('dossier', 'detailsPPDossierPro', item, ids, cookiejar_id, self.parse_dossier_tab)

    def parse_dossier_tab(self, response):
        """Parse dossier tab"""
        item = response.meta['item']
        ids = response.meta['ids']
        cookiejar_id = response.meta['cookiejar']

        item['dossier_html'] = response.text

        # Fetch diplomes tab
        yield self.make_tab_request('diplomes', 'detailsPPDiplomes', item, ids, cookiejar_id, self.parse_diplomes_tab)

    def parse_diplomes_tab(self, response):
        """Parse diplomes tab"""
        item = response.meta['item']
        ids = response.meta['ids']
        cookiejar_id = response.meta['cookiejar']

        item['diplomes_html'] = response.text

        # Fetch personne tab
        yield self.make_tab_request('personne', 'detailsPPPersonne', item, ids, cookiejar_id, self.parse_personne_tab)
    
    def parse_personne_tab(self, response):
        """Parse personne tab and yield complete item"""
        item = response.meta['item']
        
        item['personne_html'] = response.text
        
        # Item now has all data - pipeline will clean and save
        yield item
    
    def make_tab_request(self, tab_name, action, item, ids, cookiejar_id, callback):
        """Make a detail tab request - CRITICAL: params in URL"""
        base_url = 'https://annuaire.sante.fr/web/site-pro/information-detaillees'
        
        params = {
            'p_p_id': 'resultatsportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            '_resultatsportlet_javax.portlet.action': action,
            '_resultatsportlet_idNat': '8' + ids.get('idRpps', ''),
            '_resultatsportlet_resultatIndex': ids.get('resultatIndex', ''),
            '_resultatsportlet_idRpps': ids.get('idRpps', ''),
            '_resultatsportlet_siteId': ids.get('siteId', ''),
            '_resultatsportlet_coordonneId': ids.get('coordonneesId', ''),
            '_resultatsportlet_etat': ids.get('etatPP', 'OUVERT'),
            'p_auth': ids.get('p_auth', ''),
            '_resultatsportlet_idExePro': ids.get('idExePro', '')
        }
        
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        
        return Request(
            url=url,
            method='POST',
            body='',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            callback=callback,
            dont_filter=True,
            meta={
                'cookiejar': cookiejar_id,
                'item': item,
                'ids': ids
            }
        )

