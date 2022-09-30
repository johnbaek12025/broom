import glob
import json
from os import path
import os

from xlsxwriter import Workbook


data_saves = 'data_save\\a_*.json'
# data_saves = [f'data_save\{id}.json' for id in id_lst]
data_list = glob.glob(data_saves)
collect = []
wb = Workbook("auction_sample_data.xlsx")
ws = wb.add_worksheet()
first_row = 0
ordered_list = ['seller_id', 'represent_name', 'representative_name', 'call_number', 'email', 'business_registration_number', 'address', 'id', 'name', 'origin_price', 'discounted_sale_price', 'representative_image_url', 'review_count', 'seller', 'category', 'first_category', 'first_category_code', 'second_category', 'second_category_code', 'third_category', 'third_category_code', 'fourth_category', 'fourth_category_code']
for header in ordered_list:
    col = ordered_list.index(header)
    ws.write(first_row,col,header)

row = 1
for i, data in enumerate(data_list):
    with open(os.path.join(os.getcwd(), data), 'rt', encoding='utf-8-sig') as f:
        data = f.read()
        data_dict = json.loads(data)    
    info = data_dict['seller_info']

    for product in data_dict['products_info']:        
        category_info = product['category_info']
        del product['category_info']        
        product.update(category_info)
        info.update(product)                
        [ws.write(row, ordered_list.index(k), v) for k, v in info.items()]
        row += 1
        collect.append(info)
    if i == 9:
        break
wb.close()

    