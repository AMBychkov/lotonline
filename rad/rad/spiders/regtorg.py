import scrapy
import re


class TorgSpider(scrapy.Spider):
    name = 'regtorg'
    start_urls = [
        "https://www.regtorg.com/etp/trade/list.html?subject=&number=&numberOfLot=&debtorTitle=&organizerTitle"
        "=&arbitrationManagerTitle=&bidSubmissionStartDateFrom=&bidSubmissionStartDateTo=&bidSubmissionEndDateFrom"
        "=&bidSubmissionEndDateTo=&procurementMethod=any&procurementClassifier=100949636%2C100949654%2C100949655"
        "%2C100949789&processStatus=BID_SUBMISSION&eventSubmit_doList=%CF%EE%E8%F1%EA&eventSubmit_doList=",
        "https://www.regtorg.com/etp/trade/list.html?bidSubmissionEndDateFrom=&bidSubmissionStartDateFrom"
        "=&bidSubmissionStartDateTo=&debtorTitle=&procurementMethod=any&processStatus=BID_SUBMISSION&subject"
        "=&organizerTitle=&bidSubmissionEndDateTo=&arbitrationManagerTitle=&number=&eventSubmit_doList=%CF%EE%E8%F1"
        "%EA&numberOfLot=&procurementClassifier=100949636%2C100949654%2C100949655%2C100949789&page=2",
        "https://www.regtorg.com/etp/trade/list.html?bidSubmissionEndDateFrom=&bidSubmissionStartDateFrom"
        "=&bidSubmissionStartDateTo=&debtorTitle=&procurementMethod=any&processStatus=BID_SUBMISSION&subject"
        "=&organizerTitle=&bidSubmissionEndDateTo=&arbitrationManagerTitle=&number=&eventSubmit_doList=%CF%EE%E8%F1"
        "%EA&numberOfLot=&procurementClassifier=100949636%2C100949654%2C100949655%2C100949789&page=3",
        "https://www.regtorg.com/etp/trade/list.html?bidSubmissionEndDateFrom=&bidSubmissionStartDateFrom"
        "=&bidSubmissionStartDateTo=&debtorTitle=&procurementMethod=any&processStatus=BID_SUBMISSION&subject"
        "=&organizerTitle=&bidSubmissionEndDateTo=&arbitrationManagerTitle=&number=&eventSubmit_doList=%CF%EE%E8%F1"
        "%EA&numberOfLot=&procurementClassifier=100949636%2C100949654%2C100949655%2C100949789&page=4"
    ]

    def parse(self, response):
        for data in response.css('.data tr'):
            if data.css('tr::attr(onclick)').get() is None:
                pass
            else:
                lot_link = f"https://www.regtorg.com{data.css('tr::attr(onclick)').get()[-50:-4]}"
                lot_id = data.css('td:nth-child(1)::text').get()
                organaizer = data.css('td:nth-child(2)::text').get().strip()
                application_start = data.css('td:nth-child(4)::text').get()
                application_deadline = data.css('td:nth-child(5)::text').get()
                bankrupt = data.css('td:nth-child(3) div:nth-child(1)::text').get()
                description_short = re.sub(r'(<(/?[^>]+)>)', '', data.css('td:nth-child(3) div:nth-child(2)').get())

                yield response.follow(lot_link, meta={
                    'lot_id': lot_id,
                    'etp': "Региональная торговая площадка",
                    'lot_number': None,
                    'description_short': description_short,
                    'price_actual': None,
                    'lot_link': lot_link,
                    'description': None,
                    'price_start': None,
                    'chart_price': None,
                    'price_market': None,
                    'price_step': None,
                    'deposit': None,
                    'cadastral_value': None,
                    'category': None,
                    'subcategory': None,
                    'address': None,
                    'auction_type': None,
                    'auction_status': None,
                    'application_start': application_start,
                    'application_deadline': application_deadline,
                    'bankrupt': bankrupt,
                    'bankrupt_href': None,
                    'inn_bankruptcy': None,
                    'contact_person': None,
                    'phone': None,
                    'email': None,
                    'inn_organizer': None,
                    'trading_number': None,
                    'lot_online': None,
                    'fedresurs': None,
                    'organizer': organaizer,
                    'organizer_link': None,
                    'image_links': None,
                    'etp_latitude': None,
                    'etp_longitude': None,
                    'kadastr_price': None,
                    'market_price': None,
                    'square_value': None,
                    'square_zem_value': None,
                    'flat_rooms': None,
                    'latitude': None,
                    'longitude': None,
                    'image_links_external': None,
                }, callback=self.lot_page)

    def lot_page(self, response):
        contact_person = response.css('#info > div:nth-child(1) > table:nth-child(1) td::text').extract()[1].strip()
        phone = response.css('#info > div:nth-child(1) > table:nth-child(1) td::text').extract()[3].strip()
        email = response.css('#info > div:nth-child(1) > table:nth-child(1) td::text').extract()[5].strip()
        trading_number = response.css('#info div:nth-child(1) > table:nth-child(3) td:nth-child(2)::text').get().strip()
        if len(response.css('#info > div:nth-child(1) > table:nth-child(4) td::text').extract()) > 4:
            inn_bankruptcy = response.css('#info div:nth-child(1) > table:nth-child(4) td::text').extract()[-1].strip()
        else:
            inn_bankruptcy = response.css('#info > div:nth-child(1) > table:nth-child(4) td::text').extract()[3].strip()
        fedresurs = f"https://fedresurs.ru/search/entity?code={inn_bankruptcy}"
        bankrupt_href = f"https://fedresurs.ru/search/entity?code={inn_bankruptcy}"
        auction_type = response.css('#info > div:nth-child(1) > table:nth-child(6) > tbody > tr:nth-child(1) > '
                                    'td:nth-child(2)::text').get().strip()
        # Ссылка на страницу с информацией о цене и лоте
        # https://www.regtorg.com/etp/trade/inner-view-lots.html?id=101960022&perspective=inline
        yield {
                    'lot_id': response.meta['lot_id'],
                    'etp': "Региональная торговая площадка",
                    'lot_number': None,
                    'description_short': response.meta['description_short'],
                    'price_actual': None,
                    'lot_link': response.meta['lot_link'],
                    'description': None,
                    'price_start': None,
                    'chart_price': None,
                    'price_market': None,
                    'price_step': None,
                    'deposit': None,
                    'cadastral_value': None,
                    'category': None,
                    'subcategory': None,
                    'address': None,
                    'auction_type': auction_type,
                    'auction_status': None,
                    'application_start': response.meta['application_start'],
                    'application_deadline': response.meta['application_deadline'],
                    'bankrupt': response.meta['bankrupt'],
                    'bankrupt_href': bankrupt_href,
                    'inn_bankruptcy': inn_bankruptcy,
                    'contact_person': contact_person,
                    'phone': phone,
                    'email': email,
                    'inn_organizer': None,
                    'trading_number': trading_number,
                    'lot_online': response.meta['lot_link'],
                    'fedresurs': fedresurs,
                    'organizer': response.meta['organizer'],
                    'organizer_link': 'электронная торговая площадка «Региональная Торговая площадка", размещенная на '
                                      'сайте www.regtorg.com в сети Интернет.',
                    'image_links': None,
                    'etp_latitude': None,
                    'etp_longitude': None,
                    'kadastr_price': None,
                    'market_price': None,
                    'square_value': None,
                    'square_zem_value': None,
                    'flat_rooms': None,
                    'latitude': None,
                    'longitude': None,
                    'image_links_external': None,
                }