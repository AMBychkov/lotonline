# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RadItem(scrapy.Item):
    # define the fields for your item here like:
    lot_id = scrapy.Field()
    etp = scrapy.Field()
    lot_number = scrapy.Field()
    description_short = scrapy.Field()
    price_actual = scrapy.Field()
    lot_link = scrapy.Field()
    description = scrapy.Field()
    price_start = scrapy.Field()
    chart_price = scrapy.Field()
    price_market = scrapy.Field()
    price_step = scrapy.Field()
    deposit = scrapy.Field()
    cadastral_value = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    address = scrapy.Field()
    auction_type = scrapy.Field()
    auction_status = scrapy.Field()
    application_start = scrapy.Field()
    application_deadline = scrapy.Field()
    bankrupt = scrapy.Field()
    bankrupt_href = scrapy.Field()
    inn_bankruptcy = scrapy.Field()
    contact_person = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    inn_organizer = scrapy.Field()
    trading_number = scrapy.Field()
    lot_online = scrapy.Field()
    fedresurs = scrapy.Field()
    organizer = scrapy.Field()
    organizer_link = scrapy.Field()
    image_links = scrapy.Field()
    etp_latitude = scrapy.Field()
    etp_longitude = scrapy.Field()
    kadastr_price = scrapy.Field()
    market_price = scrapy.Field()
    square_value = scrapy.Field()
    square_zem_value = scrapy.Field()
    flat_rooms = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    image_links_external = scrapy.Field()
