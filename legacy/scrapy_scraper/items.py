import scrapy

class ProfessionalItem(scrapy.Item):
    """Health professional data item"""
    rpps = scrapy.Field()
    name = scrapy.Field()
    profession = scrapy.Field()
    organization = scrapy.Field()
    address = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    finess = scrapy.Field()
    siret = scrapy.Field()
    
    # Raw HTML from tabs
    situation_html = scrapy.Field()
    dossier_html = scrapy.Field()
    diplomes_html = scrapy.Field()
    personne_html = scrapy.Field()
    
    # Clean JSON after extraction
    situation_data = scrapy.Field()
    dossier_data = scrapy.Field()
    diplomes_data = scrapy.Field()
    personne_data = scrapy.Field()

