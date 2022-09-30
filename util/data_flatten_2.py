import glob
import json
from os import path
import os

from xlsxwriter import Workbook


data_saves = 'data_save\\*.json'
# data_saves = [f'data_save\{id}.json' for id in id_lst]
data_list = glob.glob(data_saves)
collect = []
wb = Workbook("sample_data.xlsx")
ws = wb.add_worksheet()
first_row = 0
ordered_list = ['seller_id', 'represent_name', 'representative_name', 'email', 'call_number']
for header in ordered_list:
    col = ordered_list.index(header)
    ws.write(first_row,col,header)

row = 1
for i, data in enumerate(data_list):
    with open(os.path.join(os.getcwd(), data), 'rt', encoding='utf-8-sig') as f:
        data = f.read()
    try:
        data_dict = json.loads(data)
    except:
        print(data)
        continue
    
    data = data_dict['seller_info']
    [ws.write(row, i, data[o]) for i, o in enumerate(ordered_list)]
    row += 1    
wb.close()

    