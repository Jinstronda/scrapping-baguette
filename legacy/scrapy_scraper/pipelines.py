import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for importing our extractors
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.content_extractor import (
    extract_situation_content,
    extract_dossier_content,
    extract_diplomes_content,
    extract_personne_content
)

class DataCleanerPipeline:
    """Extract clean JSON from raw HTML"""
    
    def __init__(self):
        self.debug_counter = 0
    
    def process_item(self, item, spider):
        # DEBUG: Save first doctor's HTML for inspection
        if self.debug_counter == 0:
            rpps = item.get('rpps', 'unknown')
            if item.get('situation_html'):
                with open(f'debug_{rpps}_situation.html', 'w', encoding='utf-8') as f:
                    f.write(item['situation_html'])
                spider.logger.info(f"DEBUG: Saved situation HTML to debug_{rpps}_situation.html (length: {len(item['situation_html'])})")
            
            if item.get('dossier_html'):
                with open(f'debug_{rpps}_dossier.html', 'w', encoding='utf-8') as f:
                    f.write(item['dossier_html'])
                spider.logger.info(f"DEBUG: Saved dossier HTML to debug_{rpps}_dossier.html (length: {len(item['dossier_html'])})")
            
            self.debug_counter += 1
        
        # Extract clean JSON from HTML
        if item.get('situation_html'):
            item['situation_data'] = extract_situation_content(item['situation_html'])
            if item['situation_data'] == '{}':
                spider.logger.warning(f"Situation extraction returned empty for {item.get('rpps')}")
        
        if item.get('dossier_html'):
            item['dossier_data'] = extract_dossier_content(item['dossier_html'])
            if item['dossier_data'] == '{}':
                spider.logger.warning(f"Dossier extraction returned empty for {item.get('rpps')}")
        
        if item.get('diplomes_html'):
            item['diplomes_data'] = extract_diplomes_content(item['diplomes_html'])
        
        if item.get('personne_html'):
            item['personne_data'] = extract_personne_content(item['personne_html'])
            if item['personne_data'] == '{}':
                spider.logger.warning(f"Personne extraction returned empty for {item.get('rpps')}")
        
        # Remove raw HTML to save space
        item.pop('situation_html', None)
        item.pop('dossier_html', None)
        item.pop('diplomes_html', None)
        item.pop('personne_html', None)
        
        return item

class DatabasePipeline:
    """Save items to SQLite database"""
    
    def open_spider(self, spider):
        """Initialize database connection"""
        db_path = spider.settings.get('DATABASE_PATH', 'db/scrapy_health.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS professionals (
                rpps TEXT PRIMARY KEY,
                name TEXT,
                profession TEXT,
                organization TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                finess TEXT,
                siret TEXT,
                situation_data TEXT,
                dossier_data TEXT,
                diplomes_data TEXT,
                personne_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        self.conn.commit()
        
        spider.logger.info(f"Database initialized at {db_path}")
    
    def close_spider(self, spider):
        """Close database connection"""
        self.conn.close()
    
    def process_item(self, item, spider):
        """Insert or update item in database"""
        if not item.get('rpps'):
            return item
        
        from datetime import datetime
        now = datetime.now().isoformat()
        
        self.cursor.execute("""
            INSERT INTO professionals (
                rpps, name, profession, organization, address, phone, email,
                finess, siret, situation_data, dossier_data, diplomes_data,
                personne_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rpps) DO UPDATE SET
                name=COALESCE(excluded.name, name),
                profession=COALESCE(excluded.profession, profession),
                organization=COALESCE(excluded.organization, organization),
                address=COALESCE(excluded.address, address),
                phone=COALESCE(excluded.phone, phone),
                email=COALESCE(excluded.email, email),
                finess=COALESCE(excluded.finess, finess),
                siret=COALESCE(excluded.siret, siret),
                situation_data=COALESCE(excluded.situation_data, situation_data),
                dossier_data=COALESCE(excluded.dossier_data, dossier_data),
                diplomes_data=COALESCE(excluded.diplomes_data, diplomes_data),
                personne_data=COALESCE(excluded.personne_data, personne_data),
                updated_at=excluded.updated_at
        """, (
            item.get('rpps'),
            item.get('name'),
            item.get('profession'),
            item.get('organization'),
            item.get('address'),
            item.get('phone'),
            item.get('email'),
            item.get('finess'),
            item.get('siret'),
            item.get('situation_data'),
            item.get('dossier_data'),
            item.get('diplomes_data'),
            item.get('personne_data'),
            now
        ))
        
        self.conn.commit()
        
        spider.logger.info(f"Saved: {item.get('name')} (RPPS: {item.get('rpps')})")
        
        return item

