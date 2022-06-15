import random
import sys
import time
import requests
from bs4 import BeautifulSoup as bf
import json
import numpy
from broomstick import settings
from broomstick.data_manager import DataHandler, DetailInfo
import re
import logging
logger = logging.getLogger(__name__)


class BroomstickGmarket(object):
    def __init__(self, config_dict) -> None:
        self.header = {            
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
                }
        self.seller_ids_file = config_dict.get('broomstick_gmarket').get('cate_url_file')
        self.seller_ids = self.bring_seller_ids()
        # self.seller_ids = {'fancyhouse2019'}
        self.seller_url = config_dict.get('broomstick_gmarket').get('seller_url')
        self.product_url = config_dict.get('broomstick_gmarket').get('product_url')
        self.review_url = config_dict.get('broomstick_gmarket').get('review_url')
        self.session = None
        self.file_name = 'here'
        self.here = set()
        self.handler = DataHandler()
        self.wtime = numpy.arange(0.5, 2, 0.5)

    def set_session(self):
        s = requests.session()
        s.headers.update(self.header)
        s.cookies.set(**{"name": "sguid",
                        "value": "31653457139375001852000000",
                        "domain": ".gmarket.co.kr",})
        s.cookies.set(**{"name": "pguid",
                        "value": "21653457139375001852010000",
                        "domain": ".gmarket.co.kr",})
        s.cookies.set(**{"name": "cguid",
                        "value": "11653457139375001852000000",
                        "domain": ".gmarket.co.kr",})
        s.cookies.set(**{"name": "cguid",
                                "value": "11653457139375001852000000",
                                "domain": ".gmarket.co.kr",})
        s.cookies.set(**{"name": "kwid",
                        "value": "go16169957315424414",
                        "domain": ".gmarket.co.kr",})
        s.cookies.set(**{"name": "kwid",
                        "value": "go16169957315424414",
                        "domain": ".gmarket.co.kr",})
        return s

    def bring_seller_ids(self):
        with open(self.seller_ids_file, encoding='utf-8') as file:
            sellers = file.read()
            sellers = eval(sellers)
        return sellers

    def main(self):        
        _name = 'main'
        self.session = self.set_session()
        checking = self.handler.file_checking(self.file_name)
        if checking:
            self.here = self.handler.read_current(self.file_name)            
            if len(self.here) < len(self.seller_ids):
                self.seller_ids = self.seller_ids - self.here           
        for id in self.seller_ids:
            print(id)
            data = dict()
            store_url = self.seller_url.format(seller_id=id)
            store_info = self.status_validation(store_url, _name)
            if not store_info:
                continue
            seller_info = self.bring_seller_info(id, store_info)            
            if not seller_info:
                continue
            product_url = self.product_url.format(seller_id=id)            
            product_links = self.collect_products_link(product_url)
            if not product_links:
                product_links = self.collect_products_link_table(product_url)
            products_info = self.collect_products_info(id, product_links)
            data[f"g_{id}"] = {
                "seller_info": seller_info,
                "products_info": products_info
            }                             
            self.handler.data_save(**data)    

    def bring_seller_info(self, id, info):
        _name = "bring_seller_info"
        seller_info = {"seller_id": id}
        data = bf(info, 'html.parser')
        div = data.find('div', {'class': 'seller_info_box'})
        info = div.find_all('dd')
        if not info:
            return None
        seller_info['represent_name'] = info[0].text
        seller_info['representative_name'] = info[1].text
        seller_info['call_number'] = info[2].text
        seller_info['email'] = info[-3].text
        seller_info['business_registration_number'] = info[-2].text
        seller_info['address'] = info[-1].text
        return seller_info

    def collect_products_link(self, url):
        _name = "bring_seller_info"
        info = self.status_validation(url, _name)
        data = bf(info, 'html.parser')        
        for i in range(1, 4):
            ul = data.find('ul', {'class': f'type{i}'})      
            if ul:
                break
        if not ul:
            return None   
        a_tags = ul.find_all('a', href=True)
        p_links = []
        for i, a in enumerate(a_tags):
            if i == 10:
                break
            p_links.append(a['href'])
        return p_links

    def collect_products_link_table(self, url):
        _name = "collect_products_link_table"
        info = self.status_validation(url, _name)
        data = bf(info, 'html.parser')        
        p_tag = data.find_all('p', {'class': 'img'})
        p_links = []
        for i, p in enumerate(p_tag):
            if i == 10:
                break
            p_links.append(p.a['href'])
        return p_links

    def collect_products_info(self, seller_id, links):
        def get_last_code(category):
            last_key = list(category)[-1]
            return category[last_key]
        _name = "collect_products_info"
        products = []
        for l in links: 
            product_id = re.search('\d+', l).group()            
            info = self.status_validation(l, _name)
            data = bf(info, 'html.parser')          
            origin_price = data.find('span', {"class": "price_original"})
            if origin_price:
                origin_price = re.sub('[^0-9]','',origin_price.text)            
            sale_price = data.find('strong', {"class": "price_real"})
            sale_price = re.sub('[^0-9]','',sale_price.text)
            product_name = data.find('h1', {'class': "itemtit"}).text     
            cates = data.find('div', {"class": "location-navi"})
            img_url = data.find('ul', {"class": "viewer"})  
            img = img_url.li.img['src']         
            categories = self.set_category(cates)
            review_count = self.set_review(product_id)
            if not categories:
                continue
            last_code = get_last_code(categories)
            products.append({
                "id": product_id,
                'name': product_name,
                "origin_price": origin_price,
                "discounted_sale_price": sale_price,
                "representative_image_url": img,
                "review_count": review_count,
                "seller": seller_id,
                "category": last_code,
                "category_info": categories,
            })  
        return products
        
    def set_review(self, product_id):
        _name = 'set_review'
        post_data = {'goodsCode': product_id}
        info = self.status_validation(self.review_url, _name, post_data)
        data = bf(info, 'html.parser')
        cont = data.find_all('span', {'class': 'num'})        
        review_count = 0
        for t in cont:          
            num = re.sub('[^0-9]+','',t.text)
            review_count += int(num)
        return review_count

    def set_category(self, data):
        name_num = ['first_category', 'second_category', 'third_category', 'fourth_category', 'fifth_category']
        code_num = ['first_category_code', 'second_category_code', 'third_category_code', 'fourth_category_code', 'fifth_category_code']
        category = dict()
        ul = data.find('ul')
        cates = ul.find_all('li')
        for i, cate in enumerate(cates):
            code = cate.a['data-montelena-acode']
            name = cate.a.text            
            category[name_num[i]] = name
            category[code_num[i]] = int(code)
        return category

    def status_validation(self, url, func_name, post_data=None):
        _name = "status_validation"
        logger.info(f"{_name} started")
        time.sleep(random.choice(self.wtime))
        if not post_data:            
            res = self.session.get(url)            
        else:
            res = self.session.post(url, data=post_data)

        status = res.status_code
        if status == 200:            
            try:                
                return res.content.decode()
            except:
                if "error" in res.text:
                    return None
                return res.text
        else:
            return None
