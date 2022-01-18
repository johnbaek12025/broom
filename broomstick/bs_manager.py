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
from broomstick.data_manager import DataHandler, DetailInfo
from . import list_chunk
import socket
from collections import defaultdict
import traceback


class BroomstickManager(object):

    def __init__(self, config_dict):
        logger.info("broomstick started")
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}
        self.product_url = config_dict["broomstick_manager"]['url_product']
        self.category_url = config_dict["broomstick_manager"]['url_category']
        self.vendor_url = config_dict["broomstick_manager"]['url_vendor']
        self.post_url = config_dict['crud']['post_url']
        self.limit = 100000000
        self.handler = DataHandler(self.post_url)

    def run(self):
        _name = 'run'
        logger.info(f"{_name} started")
        # url formating
        checking = self.handler.file_checking()
        if checking:
            current = self.handler.read_current()
            if current < self.limit:
                vendors = [f"A{str(i).zfill(8)}" for i in range(current, self.limit)]
            else:
                vendors = [f"A{str(i).zfill(8)}" for i in range(1, self.limit)]
        else:
            vendors = [f"A{str(i).zfill(8)}" for i in range(1, self.limit)]
        # vendors = ['A00005082']
        data = self.set_data(vendors)
        print(data)
        self.handler.data_save(**data)

    def set_data(self, vendors):
        data = dict()
        for vendor_id in vendors:
            try:
                details = self.vendor_data(vendor_id)
            except KeyboardInterrupt:
                print('-------------------KeyboardInterrupt')
                logger.info(f"KeyboardInterrupt")
                break
            except Exception:
                x = traceback.format_exc()
                print(f"{x}")
                logger.info(f"error {x}")
                break
            else:
                if not details:
                    continue
                data[vendor_id] = details

        self.handler.save_current(vendor_id)
        return data

    def vendor_data(self, vendor_id):
        products = self.set_vendor_url(vendor_id=vendor_id)
        if not products:
            # vendor is registered but there is no information
            return None
        print(vendor_id)
        set_product = self.set_valdation_info(products)
        if not set_product:
            # vendor's item is only one and this vendor changed to coupang
            return None
        product_url = self.product_url.format(product_id=set_product['product_id'], item_id=set_product['item_id'],
                                              vendor_item_id=set_product['vendor_item_id'])
        seller_info = self.bring_seller_info(product_url, vendor_id)
        products_info = []
        pages = ceil(seller_info['product_count'] / 30)
        for page in range(1, pages + 1):
            products = self.set_vendor_url(vendor_id=vendor_id, page=page)
            if not products:
                break
            items = self.distribution_products(vendor_id, products)
            if not items:
                continue
            products_info.extend(items)

        data = {
            "seller_info": seller_info,
            "products_info": products_info
        }
        return data

    def set_valdation_info(self, products):
        p_id = dict()
        for product in products:
            if product['rocketMerchant']:
                continue
            p_id['product_id'] = product['productId']
            p_id['item_id'] = product['itemId']
            p_id['vendor_item_id'] = product['vendorItemId']
            break
        return p_id

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



    def distribution_products(self, vendor_id, products):
        def get_last_code(category):
            last_key = list(category)[-1]
            return category[last_key]

        _name = 'bring_product_info'
        logger.info(f"{_name} started")
        items = []
        for p in products:
            product_id = p['productId']
            category_url = self.category_url.format(product_id=product_id)
            categories = self.bring_category_info(category_url)
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
        if items:
            return items
        else:
            return None


    def bring_category_info(self, category_url):
        _name = 'bring_category_info'
        logger.info(f"{_name} started")
        category = dict()
        info = self.status_validation(category_url, func_name=_name)
        try:
            data = bf(info, 'html.parser')
        except TypeError:
            logger.info(f'generated Exception of TypeError because of html_parser')
            time.sleep(3)
            data = bf(info, 'html.parser')
        finally:
            a = data.find_all('a', {'class': 'breadcrumb-link'}, href=True, title=True)
            name_num = ['first_category', 'second_category', 'third_category', 'fourth_category', 'fifth_category']
            code_num = ['first_category_code', 'second_category_code', 'third_category_code', 'fourth_category_code', 'fifth_category_code']
            for i, b in enumerate(a):
                code = re.sub(r'\D', '', b['href'])
                name = b['title']
                category[name_num[i]] = name
                category[code_num[i]] = int(code)
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