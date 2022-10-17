import enum
from msilib.schema import Error
import random
import sys
import time
import requests
from bs4 import BeautifulSoup as bf
import json
import numpy
from broomstick.utility.data_manager import DataHandler, DetailInfo
import re
import logging
import ast

logger = logging.getLogger(__name__)


class BroomstickAuction(object):
    def __init__(self, config_dict) -> None:
        self.header = {            
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
                }
        self.seller_ids_file = config_dict.get('broomstick_auction').get('cate_url_file')
        self.seller_ids = self.bring_seller_ids() 
        # self.seller_ids = {'ALJALDDAG'}
        self.seller_url = config_dict.get('broomstick_auction').get('seller_url')
        self.product_url = config_dict.get('broomstick_auction').get('product_url')
        self.session = None
        self.wtime = numpy.arange(1, 3, 0.5)
        self.file_name = 'there'
        self.handler = DataHandler()
        self.there = set()

    def main(self):
        _name = 'main'
        self.session = self.set_session()
        checking = self.handler.file_checking(self.file_name)
        if checking:
            self.there = self.handler.read_current(self.file_name)            
            if len(self.there) < len(self.seller_ids):
                self.seller_ids = self.seller_ids - self.there
                       
        for id in self.seller_ids:            
            check = self.get_collecting_data(id)
            if not check:
                continue

    def get_collecting_data(self, id):
        _name = 'get_collecting_data'
        data = dict()
        print(id)
        self.there.add(id)           
        store_url = self.seller_url.format(seller_id=id)
        store_info = self.status_validation(store_url, _name)                       
        if not store_info:
            return False            
        seller_info = self.bring_seller_info(id, store_info)
        if not seller_info:
            return False
        product_url = self.product_url.format(seller_id=id)            
        product_links = self.collect_products_link(product_url, id)
        if not product_links:
            data[f"a_{id}"] = {
            "seller_info": seller_info,                
            }
            self.handler.data_save(**data)    
            return False            
        products_info = self.collect_products_info(id, product_links)
        if not products_info:
            data[f"a_{id}"] = {
            "seller_info": seller_info,                
            }
            self.handler.data_save(**data)    
            return False    
        data[f"a_{id}"] = {
            "seller_info": seller_info,
            "products_info": products_info
        }                             
        self.handler.data_save(**data)            
        self.handler.save_current(self.file_name, self.there)

    def set_session(self):
        s = requests.session()
        s.headers.update(self.header)
        s.cookies.set(**{"name": "pguid",
                        "value": "21653457139375001852010000",
                        "domain": ".auction.co.kr",})
        s.cookies.set(**{"name": "cguid",
                        "value": "11651827531769000481000000",
                        "domain": ".auction.co.kr",})
        s.cookies.set(**{"name": "sguid",
                        "value": "31654838270866000981200000",
                        "domain": ".auction.co.kr",})        
        s.cookies.set(**{"name": "pcid",
                        "value": "1651827532908",
                        "domain": ".auction.co.kr",})
        s.cookies.set(**{"name": "sguid",
                                "value": "31654838270866000981200000",
                                "domain": ".auction.co.kr",})        
        return s

    def bring_seller_ids(self):
        with open(self.seller_ids_file, encoding='utf-8') as file:
            sellers = file.read()
            sellers = ast.literal_eval(sellers)
        return sellers

    def bring_seller_info(self, id, info):
        _name = "bring_seller_info"                
        seller_info = {"seller_id": id}        
        data = bf(info, 'html.parser')        
        product_count = self.bring_total_products_count(data)
        div = data.find('div', {'class': 'seller_info_box'})
        if not div:
            return None
        info = div.find_all('dd')
        if not info:
            return None
        if len(info) < 3:
            return None
        email = re.sub('\s', '', info[-3].text)
        seller_info['represent_name'] = info[0].text
        seller_info['representative_name'] = info[1].text
        seller_info['call_number'] = info[2].text
        seller_info['email'] = email
        seller_info['business_registration_number'] = info[-2].text
        seller_info['address'] = info[-1].text
        seller_info['product_count'] = product_count
        return seller_info
    
    def bring_total_products_count(self, data):
        li_tags = data.find_all("li", {"class": "splt_ico"})        
        product_num = 0
        for li in li_tags:
            product_num_text = li.find("span", {"class": "data_num"})            
            if product_num_text:
                product_num += int(re.sub('[^0-9]+', '', product_num_text.text))
            else:
                product_num += 0
        return product_num
        
    def collect_products_link(self, url, id):
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

    def collect_products_info(self, seller_id, links):
        def get_last_code(category):
            last_key = list(category)[-1]
            return category[last_key]
        _name = "collect_products_info"
        products = []
        for l in links:
            product_id = re.search(r'[A-Z][0-9]+', l).group()            
            info = self.status_validation(l, _name)
            data = bf(info, 'html.parser')
            if not data.text:
                continue
            elif '로그인' in data.text:
                continue
            origin_price = data.find('span', {"class": "price_original"})
            if origin_price:            
                origin_price = re.sub('[^0-9]','',origin_price.text)
            else:
                origin_price = ''
            sale_price = data.find('strong', {"class": "price_real"})
            if not sale_price:
                for i in ["monthly_price", "plan_price"]:
                    sale_price = data.find('span', {"class": i})
            
            sale_price = re.sub('[^0-9]','',sale_price.text)
            product_name = data.find('h1', {'class': "itemtit"}).text     
            cates = data.find_all('div', {"class": "category_wrap"})
            img_url = data.find('ul', {"class": "viewer"})  
            img = img_url.li.img['src']
            categories = self.set_category(cates)            
            review_count = self.set_review(data)            
            if not categories:
                continue
            last_code = get_last_code(categories)
            products.append({
                "id": product_id,
                'name': product_name,
                "origin_price": int(origin_price) if origin_price else 0,
                "discounted_sale_price": int(sale_price),
                "representative_image_url": img,
                "total_review_count": int(review_count),
                "seller": seller_id,
                "category": last_code,
                "category_info": categories,
            })        
        return products
    
    def set_category(self, data):
        name_num = ['first_category', 'second_category', 'third_category', 'fourth_category', 'fifth_category']
        code_num = ['first_category_code', 'second_category_code', 'third_category_code', 'fourth_category_code', 'fifth_category_code']
        category = dict()        
        for i, d in enumerate(data):
            code = re.sub('[^0-9]+', '', d.a['href'])
            name = re.sub('더보기\n', '', d.a.text)
            category[name_num[i]] = name
            category[code_num[i]] = int(code)        
        return category
        
    def set_review(self, data):
        review_count = data.find('span', {'id': 'spnTotalItemTalk_display'})
        review_count = review_count.text
        review_count = re.sub("[^0-9]+", '', review_count)
        return review_count
        
    def status_validation(self, url, func_name):
        _name = "status_validation"
        logger.info(f"{_name} started for {func_name}")
        time.sleep(random.choice(self.wtime))
        try:
            res = self.session.get(url)
        except:
            time.sleep(2)
            res = self.session.get(url)
        status = res.status_code
        if status == 200:            
            try:                
                return res.content.decode()
            except:
                # if "error" in res.text:
                #     return None
                return res.text
        else:
            return None
