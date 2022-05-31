import random
import time
import requests
from bs4 import BeautifulSoup as bf
import json
import numpy
from broomstick.data_manager import DataHandler, DetailInfo
import re
import logging
logger = logging.getLogger(__name__)


class BroomstickCoupang(object):
    def __init__(self, config_dict) -> None:
        self.header = {            
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        }
        self.session = None
        self.product_url = config_dict["broomstick_coupang"]['url_product']
        self.category_url = config_dict["broomstick_coupang"]['url_category']
        self.vendor_url = config_dict["broomstick_coupang"]['url_vendor']        
        self.limit = 20290
        self.handler = DataHandler()
        self.wtime = numpy.arange(0.5, 2, 0.5)
    
    def set_session(self):
        s = requests.session()
        s.headers.update(self.header)
        s.cookies.set(**{"domain": ".coupang.com", 
                    "value": "51829479347949486589994", 
                    "path": "/",                 
                    "name": "PCID",
                    "rest": {"httpOnly": False, "sameSite": False},})
        s.cookies.set(**{ "name": "MARKETID",
                    "value": "51829479347949486589994",
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": True, "sameSite": None, "secure": True},})            
        s.cookies.set(**{"name": "sid",
                    "value": "a0438b4751a84b55838f254724e60773d89f10e0",            
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": False, "sameSite": '', "secure": False},})    
        s.cookies.set(**{"name": "x-coupang-origin-region", "value": "	KOREA", "domain": ".coupang.com", 
                        "path": "/","rest": {"httpOnly": False, "sameSite": '', "secure": False}})
        return s
    
    def main(self):
        _name = 'main'
        self.session = self.set_session()
        checking = self.handler.file_checking()        
        if checking:
            current = self.handler.read_current()
            if current < self.limit:
                vendor_nums = [i for i in range(current, self.limit)]
            else:
                vendor_nums = [i for i in range(1, self.limit)]
        else:
            vendor_nums = [i for i in range(1, self.limit)]
        # vendor_nums = [202]
        data = dict()        
        for n in vendor_nums:
            vendor_id = f"A{str(n).zfill(8)}" 
            print(vendor_id)
            self.handler.save_current(vendor_id)
            vendor_url = self.vendor_url.format(vendor_id=vendor_id, page_num='1')
            products_info = self.status_validation(vendor_url, _name)
            if not products_info:
                continue
            products = self.products_validation(products_info)
            if not products:
                continue            
            sample_product_dict = self.set_product_info_for_vendor(products)            
            vendor_info = self.set_vendor_info_dict(vendor_id, sample_product_dict)
            if not vendor_info:
                continue
            products_info = self.set_products_dict(vendor_id, products)
            # print(len(products_info))
            data[vendor_id] = {
                "seller_info": vendor_info,
                "products_info": products_info
            }
            
            self.handler.data_save(**data)

    def set_product_info_for_vendor(self, products):
        p_info = dict()
        for product in products:            
            p_info['product_id'] = product['productId']
            p_info['item_id'] = product['itemId']
            p_info['vendor_item_id'] = product['vendorItemId']
            break
        return p_info
    
    def set_vendor_info_dict(self, vendor_id, sample_dict):
        _name = "set_vendor_info_dict"
        logger.info(f"{_name} started")
        product_url = self.product_url.format(product_id=sample_dict['product_id'], item_id=sample_dict['item_id'],
                                              vendor_item_id=sample_dict['vendor_item_id'])
        products_count = self.get_products_count(vendor_id)
        vendor_info = self.status_validation(product_url, _name)        
        if not vendor_info:
            return None
        data = vendor_info['returnPolicyVo']
        detail = data['sellerDetailInfo']
        seller_info = {
                        "seller_id": vendor_id,
                        "represent_name": detail.get('vendorName', None),
                        "representative_name": detail.get('repPersonName', None),
                        "email": detail.get('repEmail', None),
                        "address": detail.get('repAddress', None),
                        "business_registration_number": detail.get('bizNum', None),
                        "call_number": detail.get('repPhoneNum', None),
                        "product_count": products_count,
                    }
        if not seller_info["representative_name"] and not seller_info["call_number"]:
            return None
        return seller_info
    
    def products_validation(self, products_info):
        _name = "products_validation"     
        logger.info(f"{_name} started")   
        if 'data' in products_info:
            data = products_info["data"]
            if 'products' in data:
                products_info = data['products']
                return products_info
            else:
                return None # there is no products data
        else:
            return None # there is no products data                

    def get_products_count(self, vendor_id):
        _name = 'get_products_count'
        logger.info(f"{_name} started")
        vendor_url = self.vendor_url.format(vendor_id=vendor_id, page_num='1')
        info = self.status_validation(vendor_url, func_name=_name)
        data = info['data']
        count = data['itemTotalCount']
        return count

    def set_products_dict(self, vendor_id, products):
        def get_last_code(category):
            last_key = list(category)[-1]
            return category[last_key]
        _name = 'set_products_dict'
        logger.info(f"{_name} started")
        items = []        
        for i, p in enumerate(products):
            if i >= 10:
                break
            product_id = p['productId']
            category_url = self.category_url.format(product_id=product_id)
            categories = self.set_category_dict(category_url)
            if not categories:
                # if there is no category information of the product
                continue
            last_code = get_last_code(categories)
            product = {
                "id": p.get('productId', None),
                'name': p.get('title', None),
                "sale_price": p.get('originalPrice', None),
                "discounted_sale_price": p.get('salePrice', None),
                "representative_image_url": p.get('imageUrl', None),
                "total_review_count": p.get('reviewRatingCount', 0.0),
                "product_satisfaction_count": p.get('reviewRatingAverage', 0.0),
                "seller": vendor_id,
                "category": last_code,
                "category_info": categories,
            }
            items.append(product)
        return items
        
    def set_category_dict(self, category_url):
        _name = 'set_category_dict'
        logger.info(f"{_name} started")
        category = dict()
        info = self.status_validation(category_url, func_name=_name)
        data = bf(info, 'html.parser')
        a = data.find_all('a', {'class': 'breadcrumb-link'}, href=True, title=True)
        name_num = ['first_category', 'second_category', 'third_category', 'fourth_category', 'fifth_category']
        code_num = ['first_category_code', 'second_category_code', 'third_category_code', 'fourth_category_code', 'fifth_category_code']
        for i, b in enumerate(a):
            code = re.sub(r'\D', '', b['href'])
            name = b['title']
            category[name_num[i]] = name
            category[code_num[i]] = int(code)
        return category

    def status_validation(self, url, func_name):
        _name = "status_validation"
        logger.info(f"{_name} started")
        time.sleep(random.choice(self.wtime))
        res = self.session.get(url)
        status = res.status_code
        if status == 200:            
            try:                
                return res.json()
            except json.JSONDecodeError:
                if "error" in res.text:
                    return None
                return res.text
        else:
            return None