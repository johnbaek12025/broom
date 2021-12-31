import requests
from bs4 import BeautifulSoup as bf
import logging
import time
import re
logger = logging.getLogger(__name__)
import json
from json.decoder import JSONDecodeError
import replace
from math import ceil
import multiprocessing as mp
from multiprocessing import Process, Pool
from broomstick.data_manager import ErrorHandle, DetailInfo
from . import list_chunk
import socket
from collections import defaultdict


class BroomstickManager(object):

    def __init__(self, config_dict):
        logger.info("broomstick started")
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}
        self.product_url = config_dict["broomstick_manager"]['url_product']
        self.category_url = config_dict["broomstick_manager"]['url_category']
        self.vendor_url = config_dict["broomstick_manager"]['url_vendor']
        self.limit = 100000000

    def run(self):
        _name = 'run'
        logger.info(f"{_name} started")
        # url formating
        handler = ErrorHandle()
        checking = handler.file_checking()
        if checking:
            current = handler.read_current()
            if current < self.limit:
                vendors = [f"A{str(i).zfill(8)}" for i in range(current, self.limit)]
            else:
                vendors = [f"A{str(i).zfill(8)}" for i in range(1, self.limit)]
        else:
            vendors = [f"A{str(i).zfill(8)}" for i in range(1, self.limit)]
        data = self.get_data(vendors)
        handler.data_save(**data)

    def get_data(self, vendors):
        data = dict()
        for vendor_id in vendors:
            try:
                products = self.set_vendor_url(vendor_id=vendor_id)
                if not products:
                    continue
                print(vendor_id)
                product_id = products[0]['productId']
                item_id = products[0]['itemId']
                vendor_item_id = products[0]['vendorItemId']
                product_url = self.product_url.format(product_id=product_id, item_id=item_id, vendor_item_id=vendor_item_id)
                seller_info = self.bring_seller_info(product_url, vendor_id)
                products_info = []
                pages = ceil(seller_info['product_count'] / 30)
                for page in range(1, pages+1):
                    products = self.set_vendor_url(vendor_id=vendor_id, page=page)
                    if not products:
                        break
                    items = self.distribution_products(products)
                    products_info.extend(items)

                data[vendor_id] = {
                "seller_info": seller_info,
                "products_info": products_info
                }
                # DetailInfo.print(**data)

            except KeyboardInterrupt:
                handler = ErrorHandle()
                handler.save_current(vendor_id)
                if data:
                    handler.data_save(**data)
                    return data

            except Exception:
                handler = ErrorHandle()
                handler.save_current(vendor_id)
                if data:
                    handler.data_save(**data)
                    return data
        return data

    def set_vendor_url(self, vendor_id, page='1'):
        _name = 'set_vendor_url'
        logger.info(f"{_name} started")
        vendor_url = self.vendor_url.format(vendor_id=vendor_id, page_num=page)
        info = self.status_validation(vendor_url, func_name=_name)
        try:
            data = info['data']
        except KeyError as e:
            logger.info(f"keyerror {e}")
            return None
        except TypeError as e:
            logger.info(f'TypeError {e}')
            return None

        else:
            products = data['products']
            return products



    def distribution_products(self, products):
        _name = 'bring_product_info'
        logger.info(f"{_name} started")
        items = []
        for p in products:
            product_id = p['productId']
            category_url = self.category_url.format(product_id=product_id)
            categories = self.bring_category_info(category_url)
            product = {
                "product_id": p.get('productId', None),
                'product_name': p.get('title', None),
                "sale_price": p.get('originalPrice', None),
                "discounted_sale_price": p.get('salePrice', None),
                "img_url": p.get('imageUrl', None),
                "total_review_count": p.get('reviewRatingCount', 0.0),
                "product_satisfaction_count": p.get('reviewRatingAverage', 0.0),
                "category_name": categories.get('category_name', []),
                "category_code": categories.get('category_code', []),
            }
            items.append(product)
        if items:
            return items
        else:
            return None


    def bring_category_info(self, category_url):
        _name = 'bring_category_info'
        logger.info(f"{_name} started")
        info = self.status_validation(category_url, func_name=_name)
        data = bf(info, 'html.parser')
        a = data.find_all('a', {'class': 'breadcrumb-link'}, href=True, title=True)
        category_name = {}
        category_code = {}
        name_num = ['first_category', 'second_category', 'third_category', 'fourth_category', 'fifth_category']
        code_num = ['first_category_code', 'second_category_code', 'third_category_code', 'fourth_category_code', 'fifth_category_code']
        for i, b in enumerate(a):
            code = re.sub(r'\D', '', b['href'])
            name = b['title']
            category_name[name_num[i]] = name
            category_code[code_num[i]] = code
        category = {
            'category_name': category_name,
            'category_code': category_code
        }
        return category

    def get_products_count(self, vendor_id):
        _name = 'get_products_count'
        vendor_url = self.vendor_url.format(vendor_id=vendor_id, page_num='1')
        info = self.status_validation(vendor_url, func_name=_name)
        data = info['data']
        count = data['itemTotalCount']
        return count

    def bring_seller_info(self, product_url, vendor_id):
        _name = "bring_seller_info"
        logger.info(f"{_name} started")
        count = self.get_products_count(vendor_id)
        info = self.status_validation(product_url, func_name=_name)
        data = info['returnPolicyVo']
        detail = data['sellerDetailInfo']
        seller_info = {
                        "seller_id": vendor_id,
                        "represent_name": detail.get('vendorName', None),
                        "representative_name": detail.get('repPersonName', None),
                        "email": detail.get('repEmail', None),
                        "address": detail.get('repAddress', None),
                        "business_registration_number": detail.get('bizNum', None),
                        "call_number": detail.get('repPhoneNum', None),
                        "product_count": count,
                    }
        return seller_info


    def status_validation(self, url, func_name):
        _name = "status_validation"
        time.sleep(1)
        logger.info(f"{_name} is working for {func_name}")
        response = requests.get(url, headers=self.header)
        status = response.status_code

        if status == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                if "error-layout" in response.text:
                    return None
                return response.text

        else:
            logger.info(msg=f'{func_name} status error')
            print(f'{func_name} status error')
            return None



    def connect(self, config_dict):
        logger.info("connect to all")

    def disconnect(self):
        logger.info("disconnect from all")