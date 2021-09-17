import scrapy
import json
import datetime
import re
import requests
from bs4 import BeautifulSoup
from ..items import RadItem
from ..pipelines import RadPipeline


def drop_price_table(page):
    # Цена в случае отсутствия таблицы с данными о снижении цен
    try:
        price = page.css('div.start_price bdi span::text').get().replace("\xa0", "")
    except:
        price = page.css("#tygh_main_container > div.tygh-content.clearfix > div > div:nth-child("
                         "2) > div > div.ty-product-block.ty-product-detail > div > div.rad-product-block__main > "
                         "div.rad-product-block__main-info.clearfix > div.ty-product-block__left > form > "
                         "div:nth-child(7) > span::text").get().replace("\r", "").replace("\n", "").strip()
    # Списки с данными из таблицы
    # Время начала периода, начала приема заявок
    start_date = page.css("#tab_rad_reduction table tr td:nth-child(1)::text").extract()
    # Предложение (Текущая цена)
    price_time = page.css("#tab_rad_reduction table tr td:nth-child(5)::text").extract()
    # Время окончания периода
    end_date = page.css("#tab_rad_reduction table tr td:nth-child(3)::text").extract()
    # Величина изменения (Шаг цены)
    step_price = page.css("#tab_rad_reduction table tr td:nth-child(4)::text").extract()
    # Сумма задатка
    deposit = page.css("#tab_rad_reduction table tr td:nth-child(6)::text").extract()
    # Данные по графику цены
    chart_price = dict(zip(start_date, price_time))
    # Получаем текщее время
    now = datetime.datetime.now()
    cur_date = now.strftime("%d.%m.%Y %H:%M")
    # Преобразование к объекту типа date для сравнения
    obj_cur_datetime = datetime.datetime.strptime(cur_date, "%d.%m.%Y %H:%M")
    prices = {"price_actual": price, "deposit": None, "price_step": None, "chart_price": chart_price}

    for idx, itm in enumerate(end_date):
        end_date_item = datetime.datetime.strptime(itm, "%d.%m.%Y %H:%M")
        if obj_cur_datetime <= end_date_item:
            prices['price_actual'] = price_time[idx]
            prices['deposit'] = deposit[idx]
            prices['price_step'] = step_price[idx]

    return prices


def find_cadastral_value(text):
    # Итоговый список номеров
    numbers = []
    # Поиск кадастровых номеров в тексте полного описания
    values = list(re.findall(r'([0-9]+):([0-9]+):([0-9]+):([0-9]+)', text))
    # Собирает полученые данные в правильном формате
    if len(values) >= 1:
        for idx, val in enumerate(values):
            numbers.append(":".join(values[idx]))
    else:
        # Передается для создания url адреса в функции получения данных из росреестра
        numbers.append("11:11:11:11")
    return numbers


def bankruptcy_info(html):
    answers = {
        'bankrupt': None,
        "bankrupt_href": None,
        "inn_bankruptcy": None,
        "trading_number": None,
        "fedresurs": None
    }
    try:
        table_keys = list(i.replace("\r", "").replace("\n", "").strip() for i in html.css(
            ".ty-product-block_product_debtor table tr td:nth-child(1)::text").extract())
        table_values = list(i.replace("\r", "").replace("\n", "").strip() for i in html.css(
            ".ty-product-block_product_debtor table tr td:nth-child(2)::text").extract())
        bankruptcy_dict = dict(zip(table_keys, table_values))

        if "Юри" in bankruptcy_dict['Статус']:
            answers["bankrupt"] = bankruptcy_dict["Наименование"]
        else:
            answers["bankrupt"] = bankruptcy_dict["ФИО"]
        answers["inn_bankruptcy"] = bankruptcy_dict["ИНН"]
        answers["bankrupt_href"] = "https://fedresurs.ru/search/entity?code=" + bankruptcy_dict["ИНН"]
        answers["fedresurs"] = "https://fedresurs.ru/search/entity?code=" + bankruptcy_dict["ИНН"]
        answers["trading_number"] = bankruptcy_dict["Номер объявления о проведении торгов в ЕФРСБ"]
        return answers
    except:
        return answers


def sales_rep(contact):
    answers = {
        "organizer": None,
        "organizer_link": None,
        "contact_person": None,
        "phone": None,
        "email": None,
        "inn_organizer": None
    }
    try:
        sales_dict = dict(zip(contact.css("#content_organizer label::text").extract(),
                              contact.css("#content_organizer span::text").extract()))
        answers["organizer"] = sales_dict["Наименование"]
        answers["phone"] = sales_dict["Электронная почта"]
        answers["email"] = contact.css("#content_organizer a::text").get()
        if "@auction" in contact.css("#content_organizer a::text").get():
            answers["inn_organizer"] = "7838430413"
        answers["contact_person"] = sales_dict["Контактное лицо"]
        return answers
    except:
        return answers


def rosreestr(numbers):
    cad_data = []
    cad_data1 = []
    house, street, place, merge = '', '', '', ''
    for item in numbers:
        a, b, c, d = int(item.split(":")[0]), int(item.split(":")[1]), int(item.split(":")[2]), int(item.split(":")[3])
        url = (f"https://rosreestr.gov.ru/api/online/fir_object/{a}:{b}:{c}:{d}")
        body = requests.get(url)
        if body.status_code != 200:
            cad_data.append("Not connect")
            cad_data1.append("Not connect")
            continue
        else:
            try:
                cadastr_json = json.loads(body.text)
                cad_data.append(cadastr_json["parcelData"]['cadCost'])
                house = cadastr_json['objectData']['objectAddress']['house']
                street = cadastr_json['objectData']['objectAddress']['street'] + " " + cadastr_json['objectData'][
                    'objectAddress']['streetType'] + "."
                if cadastr_json["parcelData"]['areaValue'] == '' or None:
                    cad_data1.append(cadastr_json["parcelData"]['areaUnitValue'])
                else:
                    cad_data1.append(cadastr_json["parcelData"]['areaValue'])
                if cadastr_json['objectData']['objectAddress']['place'] is None:
                    if cadastr_json['objectData']['objectAddress']['region'] == 78:
                        place = "Санкт-Петербург"
                    elif cadastr_json['objectData']['objectAddress']['region'] == 77:
                        place = "Москва"
                    else:
                        place = cadastr_json['objectData']['objectAddress']['locality']
                else:
                    place = cadastr_json['objectData']['objectAddress']['place']
                if street is None:
                    merge = cadastr_json['objectData']['addressNote']
                    if merge is None:
                        merge = cadastr_json['objectData']['objectAddress']['addressNotes']
                else:
                    merge = cadastr_json['objectData']['objectAddress']['mergedAddress']
                    if merge is None:
                        merge = cadastr_json['objectData']['objectAddress']['addressNotes']
            except:
                merge = cadastr_json['objectData']['addressNote']
                continue
    osm_dict = {"osm_house": house, "osm_street": street, "osm_place": place, "osm_alt": merge}
    return cad_data, cad_data1, osm_dict


def room_finder(description):
    room_in_digit = {
        "Однокомнатная": 1,
        "1-а ком": 1,
        "1-ком": 1,
        "1 ком": 1,
        "1 - ком": 1,
        "1- ком": 1,
        "Двухкомнатная": 2,
        "2-х ком": 2,
        "2-ком": 2,
        "2 ком": 2,
        "2 - ком": 2,
        "2- ком": 2,
        "Трехкомнатная": 3,
        "Трёхкомнатная": 3,
        "3-а ком": 3,
        "3-ком": 3,
        "3 ком": 3,
        "3 - ком": 3,
        "3- ком": 3,
        "Четырехкомнатная": 4,
        "Четырёхкомнатная": 4,
        "4-х ком": 4,
        "4-ком": 4,
        "4 ком": 4,
        "4 - ком": 4,
        "4- ком": 4,
        "Свободная планировка": 0,
        "Пятикомнатная": 5,
        "5-и ком": 5,
        "5-ком": 5,
        "5 ком": 5,
        "5 - ком": 5,
        "5- ком": 5,
    }
    patterns = [
        "Однокомнатная", "Двухкомнатная", "Трехкомнатная", "Трёхкомнатная", "Четырехкомнатная",
        "Четырёхкомнатная", "Пятикомнатная", "Свободная планировка",
        "\d+-а ком", "\d+-ком", "\d+ ком", "\d+ - ком", "\d+- ком"
    ]

    for pat in patterns:
        a = re.findall(pat, description)
        for i in a:
            if i in room_in_digit.keys():
                return (room_in_digit[i])
            else:
                try:
                    digit = int(re.findall(r'\d+', i)[0])
                    if digit > 5:
                        return (digit)
                    else:
                        return (room_in_digit[i])
                except:
                    continue


def osm_data(data_from_rosreestr, lat, lon):
    # Перемпнные для составления адреса запроса
    osm_house, osm_street = data_from_rosreestr['osm_house'], data_from_rosreestr['osm_street']
    osm_town = data_from_rosreestr['osm_place']
    # Первый альтернативный адрес для поска коордиат
    # osm_alt_address = data_from_rosreestr['osm_alt']
    url = ''
    osm_coordinates = f"https://nominatim.openstreetmap.org/search?q={lat},{lon}&format=json"
    # alt_osm_address = f"https://nominatim.openstreetmap.org/search?q={osm_alt_address}&format=json"
    main_osm_address = f"https://nominatim.openstreetmap.org/search?q={osm_house}+{osm_street}+{osm_town}&format=json"
    # osm_lot_address = f"https://nominatim.openstreetmap.org/search?q={address}&format=json"
    if osm_street == '' or None:
        url = osm_coordinates
    else:
        url = main_osm_address
    try:
        a = requests.get(url)
        json_osm = json.loads(a.text)
        return json_osm[0]
    except:
        json_osm_err = {
            'lat': "Not found",
            'lon': "Not found",
            'display_name': "Not found"
        }
        return json_osm_err


def yandex_market_price(adr, room):
    ya_url = ''
    url = f"https://realty.yandex.ru/otsenka-kvartiry-po-adresu-onlayn/{adr}/kupit/kvartira/"
    rooms = f'?roomsTotal={room}'
    if room is not None:
        ya_url = url + rooms
    else:
        ya_url = url
    ya_page = requests.get(ya_url).text.encode('ISO-8859-1')
    soup = BeautifulSoup(ya_page, 'lxml')
    ya_price = soup.find_all(class_="OffersArchiveSearchOffers__price")
    ya_square = soup.find_all(class_="OffersArchiveSearchOffers__title")
    ya_list_price = list(
        i.span.get_text(strip=True).replace(" ₽", "").replace(" млн", "").replace("\xa0", "") for i in ya_price)
    ya_list_square = list(
        i.span.get_text(strip=True).replace("&nbsp;", "").replace("\xa0", "") for i in ya_square)
    dictionary = dict(zip(ya_list_square, ya_list_price))
    #
    try:
        if len(soup.find("div", class_="OffersArchive__related-offers")) < 1:
            similar_dictionary = {"0": "Ничего не найдено"}
        else:
            similar_ya_head = soup.find_all(class_="OffersArchive__related-offers")
            similar_ya_description = list(i.h3.get_text(strip=True).replace("&nbsp;", "").replace(
                "\xa0", "") for i in similar_ya_head)
            similar_ya_price = list(i.find("span", class_="price").get_text(strip=True).replace(
                " ₽", "").replace(" млн", "").replace("\xa0", "") for i in similar_ya_head)
            similar_dictionary = dict(zip(similar_ya_description, similar_ya_price))
    except:
        similar_dictionary = {"0": "Ничего не найдено"}
    if len(dictionary) < 1:
        return "Нет данных", similar_dictionary
    else:
        return dictionary, similar_dictionary


class TestSpider(scrapy.Spider):
    name = 'fly'

    start_urls = [
        "https://catalog.lot-online.ru/index.php?dispatch=categories.view&category_id=1&features_hash=174-31371"
        "&sort_by=timestamp&sort_order=desc&layout=short_list&items_per_page=2555",
    ]

    def parse(self, response):

        for data in response.css('div.ty-compact-list__item'):
            auction_status = data.css('div.list-lot-info-status span.ty-control-group__item::text').get()
            description_short = data.css('div.lot-info-name a::attr(title)').get()
            lot_link = data.css('div.lot-info-name bdi a::attr(href)').get()
            lot_id = data.css('div.lot-info-sku span.ty-control-group__item::text').get()
            price_start = data.css('div.lot-info-price span.ty-price-num::text').get()
            yield response.follow(lot_link, meta={
                'lot_id': lot_id,
                'etp': "Российский аукционный дом",
                'lot_number': None,
                'description_short': description_short,
                'price_actual': None,
                'lot_link': lot_link,
                'description': None,
                'price_start': price_start,
                'chart_price': None,
                'price_market': None,
                'price_step': None,
                'deposit': None,
                'cadastral_value': None,
                'category': None,
                'subcategory': None,
                'address': None,
                'auction_type': None,
                'auction_status': auction_status,
                'application_start': None,
                'application_deadline': None,
                'bankrupt': None,
                'bankrupt_href': None,
                'inn_bankruptcy': None,
                'contact_person': None,
                'phone': None,
                'email': None,
                'inn_organizer': None,
                'trading_number': None,
                'lot_online': None,
                'fedresurs': None,
                'organizer': None,
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
        # Полное описание на 04 августа 2021  было найдено три возвозможных варианта представления на странице
        # В первом варианте получаем строку с текстом описания
        description_one = str(response.css('div.ty-product__full-description::text').get()).replace("\r", "").replace(
            "\n", "").strip()
        if description_one == '':
            # Во втором варианте получаем список если описание разложено по тегам <span>
            description_two = response.css('.ty-product__full-description span::text').extract()
            if len(description_two) == 0:
                # В третьем варианте получаем список если описание разложено по тегам <p>
                description_three = response.css('.ty-product__full-description p::text').extract()
                if len(description_three) == 1:
                    description = description_three[0].replace("\r", "").replace("\n", "").strip()
                else:
                    description_temp = []
                    for i in description_three:
                        description_temp.append(i.replace("\r", "").replace("\n", "").strip())
                    description = " ".join(description_temp)
            else:
                if len(description_two) == 1:
                    description = description_two[0].replace("\r", "").replace("\n", "").strip()
                else:
                    description_temp = []
                    for i in description_two:
                        description_temp.append(i.replace("\r", "").replace("\n", "").strip())
                    description = " ".join(description_temp)
        else:
            description = description_one

        # Две переменные с адресом нужны на случай если на странице не указан полный адрес,
        try:
            address_region = response.css(".ty-product-block_product_main div.ty-product__address span::text").get()
            address_main = response.css(".ty-product-block_product_main div.ty-product__address span::text").extract()[
                1]
            if address_main is None:
                # в этом случае берем данные из address_region
                address = address_region
            elif address_region is None:
                # Если и в переменной address_region ничего нет возвращаем None
                address = None
            else:
                address = address_main
        except:
            address = None

        # Номер лота
        lot_number = response.css('.ty-product__tender_code a::text').get()

        # Получение текущей цены через функцию для объявлений с конкретными точками снижения цены
        price_actual = drop_price_table(response.css('body'))

        # Получение кадастровых номеров
        cadastral_value = find_cadastral_value(description)

        # Категория и подкатегория
        categories = response.css(".ty-breadcrumbs__products a::text").getall()

        # Тип аукциона
        auction_type = list(i.replace("\r", "").replace("\n", "").strip() for i in response.css(
            ".ty-product__aution_type_name span::text").extract())

        # Информация о банкротсве
        bankrot = bankruptcy_info(response.css(".ty-product-block_product_debtor"))

        # Организатор/продавец контактная информация
        contacts = sales_rep(response.css("#content_organizer"))

        # Ссылка на вторую страницу
        lot_link = response.css(".ty-sku-item a::attr(href)").get()

        # Поиск количества комнат в описании лота
        room = room_finder(description)

        # Ссылка на изображение
        images_link = response.css('div.ty-product-block__img-wrapper a::attr(href)').extract()

        # Координаты с площадки
        gps_yandex = str(re.findall(r"k\([[0-9]+.[0-9]+, [0-9]+.[0-9]+],", str(response.css(
            'script::text').extract())))
        if not re.findall(r'[0-9]+\.[0-9]+', gps_yandex):
            coordinates = ["00", "00"]
        else:
            coordinates = re.findall(r'[0-9]+\.[0-9]+', gps_yandex)

        # Ссылка на внеший источник с изображениями
        if coordinates[0] == "00":
            ext_img_link = f"https://www.google.com/maps/place/{address}"
        else:
            ext_img_link = f"https://maps.google.com/maps?q=&layer=c&cbll={coordinates[0]},{coordinates[1]}"

        # Переменная содержащая список с ответами от api росреестра
        reestr = rosreestr(cadastral_value)

        # распределение и поиск объектов в тексте описания которых указан земельный участое
        zem_area = ''
        if "Земел" in categories[-2]:
            zem_area = reestr[1]

        # Координаты с внешнего сайта OpenStreets.com
        osm_coordinates = osm_data(reestr[2], coordinates[0], coordinates[1])

        # Поиск информации о рыночной цене наа яндекс.недвижимость
        market_price = yandex_market_price(address, room)
        etp = "Российский аукционный дом"
        yield response.follow(lot_link, meta={
            'lot_id': response.meta['lot_id'],
            'etp': etp,
            'lot_number': lot_number,
            'description_short': response.meta['description_short'],
            'price_actual': price_actual['price_actual'],
            'lot_link': response.meta['lot_link'],
            'description': description,
            'price_start': response.meta['price_start'],
            'chart_price': price_actual['chart_price'],
            'price_market': market_price[0],
            'price_step': price_actual['price_step'],
            'deposit': price_actual['deposit'],
            'cadastral_value': cadastral_value,
            'category': categories[-2],
            'subcategory': categories[-1],
            'address': address,
            'auction_type': auction_type,
            'auction_status': response.meta['auction_status'],
            'application_start': None,
            'application_deadline': None,
            'bankrupt': bankrot['bankrupt'],
            'bankrupt_href': bankrot['bankrupt_href'],
            'inn_bankruptcy': bankrot['inn_bankruptcy'],
            'contact_person': contacts['contact_person'],
            'phone': contacts['phone'],
            'email': contacts['email'],
            'inn_organizer': contacts['inn_organizer'],
            'trading_number': bankrot["trading_number"],
            'lot_online': lot_link,
            'fedresurs': bankrot['fedresurs'],
            'organizer': contacts['organizer'],
            'organizer_link': lot_link,
            'image_links': images_link,
            'etp_latitude': coordinates[0],
            'etp_longitude': coordinates[1],
            'kadastr_price': reestr[0],
            'market_price': market_price[1],
            'square_zem_value': zem_area,
            'square_value': reestr[1],
            'flat_rooms': room,
            'latitude': osm_coordinates['lat'],
            'longitude': osm_coordinates['lon'],
            'image_links_external': ext_img_link,
        }, callback=self.right_block)

    def right_block(self, response):
        items = RadItem()
        # Базовые значения в случае ошибок при парсинге
        application_start = None
        application_deadline = None
        deposit = response.meta['deposit']
        price_step = response.meta['price_step']

        # Если ссылка на адрес rad
        if response.url[8:11] == 'rad':
            # Ряды из таблицы с нуддными данными
            for p in response.css('p.row'):
                # Проверка на даты проведения
                if p.css('strong.label::text').get() == 'Tender time:':
                    application_deadline = p.css('span.field::text').getall()[1][3:19]
                    application_start = p.css('span.field::text').getall()[0][-17:-1:1]
                # Проверка на депозит
                if p.css('strong.label::text').get() == 'Deposit price:':
                    if deposit is None:
                        deposit = p.css('span.field::text').get()
                    else:
                        deposit = response.meta['deposit']
            if price_step is None:
                price_step = "Предварительная квалификация"
            else:
                price_step = response.meta['price_step']
        else:
            for p in response.css('div.tender p'):
                if "Период" in str(p.css('p::text').get()):
                    # Список из двух дат, начало и конец приема заявок

                    application_start = p.css('span::text').getall()[0]
                    application_deadline = p.css('span::text').getall()[-1]
            if price_step is None:
                price_step = response.css("div#formMain\:opStepValue span::text").getall()
            else:
                price_step = response.meta['price_step']
            if deposit is None:
                deposit = response.css("div#formMain\:opDepositsValue span::text").getall()
            else:
                deposit = response.meta['deposit']

        items['lot_id'] = str(response.meta['lot_id'])
        items['etp'] = str("Российский аукционный дом")
        items['lot_number'] = str(response.meta['lot_number'])
        items['description_short'] = str(response.meta['description_short'])
        items['price_actual'] = str(response.meta['price_actual'])
        items['lot_link'] = str(response.meta['lot_link'])
        items['description'] = str(response.meta['description'])
        items['price_start'] = str(response.meta['price_start'])
        items['chart_price'] = str(response.meta['chart_price'])
        items['price_market'] = str(response.meta['price_market'])
        items['price_step'] = str(price_step)
        items['deposit'] = str(deposit)
        items['cadastral_value'] = str(response.meta['cadastral_value'])
        items['category'] = str(response.meta['category'])
        items['subcategory'] = str(response.meta['subcategory'])
        items['address'] = str(response.meta['address'])
        items['auction_type'] = str(response.meta['auction_type'])
        items['auction_status'] = str(response.meta['auction_status'])
        items['application_start'] = str(application_start)
        items['application_deadline'] = str(application_deadline)
        items['bankrupt'] = str(response.meta['bankrupt'])
        items['bankrupt_href'] = str(response.meta['bankrupt_href'])
        items['inn_bankruptcy'] = str(response.meta['inn_bankruptcy'])
        items['contact_person'] = str(response.meta['contact_person'])
        items['phone'] = str(response.meta['phone'])
        items['email'] = str(response.meta['email'])
        items['inn_organizer'] = str(response.meta['inn_organizer'])
        items['trading_number'] = str(response.meta['trading_number'])
        items['lot_online'] = str(response.meta['lot_online'])
        items['fedresurs'] = str(response.meta['fedresurs'])
        items['organizer'] = str(response.meta['organizer'])
        items['organizer_link'] = str(response.meta['organizer_link'])
        items['image_links'] = str(response.meta['image_links'])
        items['etp_latitude'] = str(response.meta['etp_latitude'])
        items['etp_longitude'] = str(response.meta['etp_longitude'])
        items['kadastr_price'] = str(response.meta['kadastr_price'])
        items['market_price'] = str(response.meta['market_price'])
        items['square_zem_value'] = str(response.meta['square_zem_value'])
        items['square_value'] = str(response.meta['square_value'])
        items['flat_rooms'] = str(response.meta['flat_rooms'])
        items['latitude'] = str(response.meta['latitude'])
        items['longitude'] = str(response.meta['longitude'])
        items['image_links_external'] = str(response.meta['image_links_external'])

        yield items
