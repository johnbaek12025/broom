import random

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
        self.user_agent = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            # 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
            # 'Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36'
        ]
        self.header = {
            "User-Agent": random.choice(self.user_agent),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",            
            "Cookie": '''PCID=51829479347949486589994; MARKETID=51829479347949486589994; sid=aa65fefcabf8446e98bcb0f5567b751ea66f3fd3; FUN="{'search':[{'reqUrl':'/search.pang','isValid':true}]}"; searchKeyword=%EC%97%90%EC%96%B4%EB%A1%9C%20%ED%94%84%EB%A0%88%EC%8A%A4%7C%EC%97%90%EC%96%B4%EB%A1%9C%20%ED%94%84%EB%A0%88%EC%8A%A4%20%EC%BB%A4%ED%94%BC%7C%EC%97%90%EC%96%B4%ED%94%84%EB%A0%88%EC%86%8C%7C%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%8A%A4%7C%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88%20%EC%B4%88%EC%BD%94%EB%B0%94%7C%EB%8B%A5%ED%84%B0%EC%9C%A0%7C%EC%BB%A4%ED%94%BC%EB%B9%88%7C%EC%BB%A4%ED%94%BC%20%EC%97%90%EC%96%B4%ED%94%84%EB%A0%88%EC%8A%A4%7C%EA%B2%AC%EA%B3%BC%EB%A5%98; searchKeywordType=%7B%22%EC%97%90%EC%96%B4%EB%A1%9C%20%ED%94%84%EB%A0%88%EC%8A%A4%22%3A0%7D%7C%7B%22%EC%97%90%EC%96%B4%EB%A1%9C%20%ED%94%84%EB%A0%88%EC%8A%A4%20%EC%BB%A4%ED%94%BC%22%3A0%7D%7C%7B%22%EC%97%90%EC%96%B4%ED%94%84%EB%A0%88%EC%86%8C%22%3A0%7D%7C%7B%22%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%8A%A4%22%3A0%7D%7C%7B%22%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88%20%EC%B4%88%EC%BD%94%EB%B0%94%22%3A0%7D%7C%7B%22%EB%8B%A5%ED%84%B0%EC%9C%A0%22%3A0%7D%7C%7B%22%EC%BB%A4%ED%94%BC%EB%B9%88%22%3A0%7D%7C%7B%22%EC%BB%A4%ED%94%BC%20%EC%97%90%EC%96%B4%ED%94%84%EB%A0%88%EC%8A%A4%22%3A0%7D%7C%7B%22%EA%B2%AC%EA%B3%BC%EB%A5%98%22%3A0%7D; x-coupang-accept-language=ko_KR; X-CP-PT-locale=ko_KR; cto_bundle=XEJ3819LTFVYYnhKWnAyJTJGTHZmWU1QdFJiRXl3UCUyRjVjd0gxbk5US2p1VWpjNkJRbkdENWlxbURGMEx4T3NhbHZhblNtSW9kTW02R2trUSUyQm5Ta3NKQ0xtYVlOMGVWTldvaHZsdTlDdmslMkJyeFFlb096ZGNEJTJCSE9EQ1JBeGw3Q1NuT0IxWE5RaGg1RTltaGpTVFV4dHhCa1g4Y3NBJTNEJTNE; ak_bmsc=B93FF9B76F02B9A43FB1607963A383CC~000000000000000000000000000000~YAAQjgI1Fzgjg+KAAQAAD+1Y9Q9b1TToSrCB9FuToYX+7MiuSFPqNjIhwO3yl8+7eCsSNJURRvj7Eupv1mADvQwyH6R/K+8gREpF+qLlHRwqTrsDj+/3IF2xFXoKtbOZSqVpyyiV1JbR6TQ9eCJDemU/MCqa+cKEn3+tCGREHa/6e8ApxK2Jt1QyUzO+BVMN35IF6pRLW10bgWkU5qLhFqts91t329+Xdp0rtzeIUn3MFv+0rqjuvW69TxZuI8CHnfkxLts/+Cknft6rNlZ1Tem+7eTrRHhq1F0FsY55bVccvfgIIddl3y4O/8MBBdRjr2R32PJRdRllzRi/Gv0+DiTPDldvr1zx7/a4rxKb27o54+oM1Pc02s9oTvXnYMo=; bm_sz=F7901A85CD7B5BFCEADA7C96CDF83524~YAAQjgI1Fzkjg+KAAQAAD+1Y9Q/IhgGhqp4yVHhZnVGIOU0cm7mLpHibHB33CxBrRDPkucmbr7JV/D9IWE55fWNtVoJ2sdXsfp95fX4v33hnHVtYrr8UjOUE9UeTkRQhscB55ncFIj9Fs3jNyJCg/3vIOTFHWu2jjZNymaejomTXEiNNzs7rQf3wWr0KwXdYzlHxT8myU7rurKG614qVgpgIckyBXn3sK/Oeh3BQb/31nvTbWzt3k7AQety1ZYnM3nnNbXoJe1zwJyV+smCVpB99r3Jo4ARA3G99t2L3LSPSM9xZ~3159609~3486020; _abck=FFFEA3B0DAE31E8F4B4521FED9002C7C~-1~YAAQBiPJF5KrA9+AAQAA/pBZ9QfCu386G6nBIZzFNZOLUOAurmAazQtGvq5pV9XknzO2o1BlsyJAoOvrCMdaAvK+SD6i7C6hkIGYWOYN/3qpVth4orf1DVa9UCMdFtQIuLWueILrS6Aq9tMsOJZZyWd7TvJu1gpLKyXq82KyLAuPmC3XSTF6j+Qz8JHpIlW4mCJLnKjBfV2ruLAGuxsx87e/R7w2jSLhTy73MlaT2IO0w1ikeluALsQCGZ84B9G2QOGAmXBjTvGB9chAwO7/E5qoRepXM02uxtJbXtGZ/AzimKH9+4omBuvK3R/fo2NYNdpJtzrv8ov58C42kDGHO4wSLw/uRGIk4VFI1szouUHH+Gd3UoOjvHsbWcy0blq7WvlqGENi7g3WKT/n5qNChs74fw1C0DdyLwY=~-1~-1~-1; bm_sv=41348269395494DEDB6CF93E61AD55CB~YAAQBiPJF5OrA9+AAQAA/pBZ9Q+iv1BIIUNu/z+myNKvhQrsp9+OMLAt2MOAm/KRfMVnG/jDlzSyN2DTujumj1Y8juvM26LD61wKCjUEdUjUceiE7vyRjsmueUScEY2n6e2NcZca939Usb/xapmUtSFQaJfweDkCw7Eud2qaVDWc/b2b3+qFJVUbui86lEPDfZKI/iCYlTexp4hHz/mJ261o2qb6sY+Xu0ov8ls/SwGn47V7oi6NeWRQ024iuf4M8g==~1'''
            },
            
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
        # checking = self.handler.file_checking()
        # signal = 'A'
        # if checking:
        #     current = self.handler.read_current()
        #     if current < self.limit:
        #         vendor_nums = [i for i in range(current, self.limit)]
        #     else:
        #         vendor_nums = [i for i in range(1, self.limit)]
        # else:
        #     vendor_nums = [i for i in range(1, self.limit)]
        vendor_nums = [202]
        self.set_data(vendor_nums)


    def set_data(self, vendor_nums):
        for n in vendor_nums:
            vendor_id = f"A{str(n).zfill(8)}"
            print(vendor_id)
            self.handler.save_current(vendor_id)
            data = dict()
            try:
                details = self.vendor_data(vendor_id)
                print(details)
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
                self.handler.data_save(**data)

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
        if not seller_info:
            return None
        products_info = self.distribution_products(vendor_id, products)
        if not products_info:
            return None
        # products_info = []
        # pages = ceil(seller_info['product_count'] / 30)
        # for page in range(1, pages + 1):
        #     products = self.set_vendor_url(vendor_id=vendor_id, page=page)
        #     if not products:
        #         break
        #     items = self.distribution_products(vendor_id, products)
        #     if not items:
        #         continue
        #     products_info.extend(items)

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
        items_counts = 0
        for p in products:
            items_counts += 1
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
            if items_counts == 10:
                break
        if items:
            return items
        else:
            return None


    def bring_category_info(self, category_url):
        _name = 'bring_category_info'
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
        if not seller_info["representative_name"] and not seller_info["call_number"]:
            return None
        return seller_info


    def status_validation(self, url, func_name):
        _name = "status_validation"
        time.sleep(2)
        logger.info(f"{_name} is working for {url} of {func_name}")
        status = 100

        while status != 200:            
            response = requests.get(url, headers=self.header) 
            print(response)           
            status = response.status_code
            time.sleep(3)
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