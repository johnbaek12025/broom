import os
import json
import requests
import logging
logger = logging.getLogger(__name__)

class DetailInfo:
    def __init__(self):
        pass

    def print(self, **kwargs):
        var_dict = kwargs
        print("------------------------------------------------")
        print(f"* {self.__class__.__name__} *")
        for i in var_dict:
            var = var_dict[i]
            print(f"[{i}]: {var}")


class DataHandler:
    def __init__(self, post_url):
        self.post_url = post_url

    def data_save(self, **kwargs):
        _name = 'data_save'
        logger.info(f"broomstick data saving in {self.__class__.__name__}.{_name}")
        for key in kwargs:
            # key is vendor_id
            # key is dict{seller_info: {}, products_info: [{}]}
            print(kwargs[key])
            with open(f"../data_save/{key}.json", "w", encoding='utf-8-sig') as file:
                x = json.dumps(kwargs[key], ensure_ascii=False)
                file.write(str(x))
            self.post_request(kwargs[key])

    def post_request(self, data):
        _name = 'post_request'
        logger.info(f"broomstick data request post {_name}")
        seller_info = json.dumps(data['seller_info'])
        products_info = json.dumps(data['products_info'])
        # table = ['coupangseller', 'coupangproduct', 'coupangproductreviewcountlog']
        # dictionary = [seller_info, products_info, products_info]
        seller_res = requests.post(self.post_url.format(table_name='coupangseller'), data=seller_info)
        products_res = requests.post(self.post_url.format(table_name='coupangproduct'), data=products_info)
        review_res = requests.post(self.post_url.format(table_name='coupangproductreviewcountlog'), data=products_info)
        print(seller_res.status_code)
        print(products_res.status_code)
        print(review_res.status_code)



    def save_current(self, id):
        cur = int(id[1:])
        with open(f"../data_save/current", "w", encoding='utf-8') as file:
            file.write(str(cur))

    def read_current(self):
        with open(f"../data_save/current", "r") as file:
            x = file.read()
        return eval(x)

    def file_checking(self):
        x = os.path.isfile('../data_save/current')
        return x

