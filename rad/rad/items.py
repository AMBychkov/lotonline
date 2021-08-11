# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RadItem(scrapy.Item):
    # define the fields for your item here like:
    lot_number = scrapy.Field()
    description_short = scrapy.Field()
    lot_link = scrapy.Field()
    start_price = scrapy.Field()
    auction_status = scrapy.Field()
    lot_id = scrapy.Field()
    description = scrapy.Field()
    cadastral_value = scrapy.Field()
    kadastr_price = scrapy.Field()