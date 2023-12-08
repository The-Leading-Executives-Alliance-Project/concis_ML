# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Webpage(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    
    content_hash = scrapy.Field()
    university_name = scrapy.Field()
    faculty = scrapy.Field()
    url = scrapy.Field()
    text = scrapy.Field()
    links = scrapy.Field()

    # Add the meta_data field
    meta_data = scrapy.Field()
