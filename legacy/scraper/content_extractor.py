from bs4 import BeautifulSoup
import json

def extract_generic_content(html):
    """Unified extractor for all tabs"""
    soup = BeautifulSoup(html, 'html.parser')
    data = {}
    
    # Find content div - different class for each tab
    content_div = soup.find('div', class_=lambda x: x and any(k in x for k in ['contenu_situation', 'contenu_dossier', 'contenu_personne', 'contenu_diplome']) if x else False)
    
    if not content_div:
        return json.dumps(data)
    
    # Extract all h2 sections
    sections = content_div.find_all('h2')
    for section in sections:
        section_name = section.get_text(strip=True)
        data[section_name] = {}
        
        # Find the container for this section (could be parent or next siblings)
        container = section.parent
        if not container:
            continue
        
        # Extract all label-value pairs
        all_labels = container.find_all('span', class_=lambda x: x and ('label' in x.lower()) if x else False)
        
        for label_span in all_labels:
            label_text = label_span.get_text(strip=True)
            
            # Skip if it's a value span, not a label
            if not label_text or ':' not in label_text:
                continue
            
            # Clean up label text
            if label_text.endswith(':'):
                label_text = label_text[:-1]
            
            # Find the value span - try multiple strategies
            value_span = None
            
            # Strategy 1: Next sibling span
            value_span = label_span.find_next_sibling('span')
            
            # Strategy 2: In parent's next sibling
            if not value_span or not value_span.get_text(strip=True):
                parent_div = label_span.parent
                if parent_div:
                    next_div = parent_div.find_next_sibling('div')
                    if next_div:
                        value_span = next_div.find('span', class_=lambda x: x and 'txt' in x.lower() if x else False)
            
            # Strategy 3: Just find next span with 'txt' in class
            if not value_span or not value_span.get_text(strip=True):
                value_span = label_span.find_next('span', class_=lambda x: x and 'txt' in x.lower() if x else False)
            
            if value_span:
                value = value_span.get_text(strip=True)
                if value and value not in ['&nbsp;', ' ', '']:
                    data[section_name][label_text] = value
        
        # Extract tables in this section
        tables = container.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if rows and len(rows) > 1:
                headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
                table_data = []
                for row in rows[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    if cells and any(cells) and "Pas d'information" not in ' '.join(cells):
                        table_data.append(dict(zip(headers, cells)))
                if table_data:
                    data[section_name]['items'] = table_data
    
    return json.dumps(data, ensure_ascii=False, indent=2)

def extract_situation_content(html):
    return extract_generic_content(html)

def extract_dossier_content(html):
    return extract_generic_content(html)

def extract_diplomes_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {'diplomes': [], 'autres_diplomes': [], 'autorisations': []}
    
    # Find all tables in the content
    tables = soup.find_all('table', class_='cellspacingNone')
    
    for table in tables:
        # Find the preceding h2 to determine which section
        prev_h2 = table.find_previous('h2')
        section_name = prev_h2.get_text(strip=True) if prev_h2 else 'unknown'
        
        rows = table.find_all('tr')
        if not rows:
            continue
        
        headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
        table_data = []
        
        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells and any(cells) and 'Pas d\'information' not in ' '.join(cells):
                table_data.append(dict(zip(headers, cells)))
        
        if 'DIPLÔMES' in section_name or 'DIPLOM' in section_name:
            data['diplomes'].extend(table_data)
        elif 'AUTRES' in section_name:
            data['autres_diplomes'].extend(table_data)
        elif 'AUTORISATION' in section_name:
            data['autorisations'].extend(table_data)
    
    return json.dumps(data, ensure_ascii=False, indent=2)

def extract_personne_content(html):
    return extract_generic_content(html)

def extract_all_detail_content(html_dict):
    """Extract clean data from all 4 tabs"""
    return {
        'situation_data': extract_situation_content(html_dict.get('situation_data', '')) if html_dict.get('situation_data') else None,
        'dossier_data': extract_dossier_content(html_dict.get('dossier_data', '')) if html_dict.get('dossier_data') else None,
        'diplomes_data': extract_diplomes_content(html_dict.get('diplomes_data', '')) if html_dict.get('diplomes_data') else None,
        'personne_data': extract_personne_content(html_dict.get('personne_data', '')) if html_dict.get('personne_data') else None
    }

