from audioop import add
import os
import glob
import json
import re
import sys
import time
import replace
from xlsxwriter import Workbook
import pandas as pd

def isValid(s: str) -> bool:
        check_dic = {
            ")":"(",
            "]":"[",
            "}":"{"
        }   
        parenthesis = [')', '(', ']', '[', '{', '}']
        stack = [s[0]] if s[0] in parenthesis else []
        for s_ in s[1:]:                        
            if s_ not in [')', '(', ']', '[', '{', '}']: 
                    continue
            if s_ not in check_dic or not stack or stack[-1] != check_dic[s_]:
                stack.append(s_)            
            else:
                del stack[-1]
                
        if stack:
            return False
        return True 


def split_phone_nums(call_nums):    
    info_dict = {}    
    if not call_nums:
        return None
    splited_nums = call_nums.split('-')    
    if len(splited_nums)==2:
        info_dict['전화 첫단'] = ''
        info_dict['전화 중간'] = splited_nums[0]
        info_dict['전화 마지막'] = splited_nums[1]
    elif len(splited_nums) == 3:
        info_dict['전화 첫단'] = splited_nums[0]
        info_dict['전화 중간'] = splited_nums[1]
        info_dict['전화 마지막'] = splited_nums[2]
    elif len(splited_nums) == 1:
        info_dict['전화 첫단'] = ''
        info_dict['전화 중간'] = ''
        info_dict['전화 마지막'] = splited_nums[0]
    else:
        return None
    return info_dict

def split_province(address, info):    
    pat = r"(서울[특별시]*|경기[도]*|전[라|북|남][북도|남도|도]*|인천[광역시]*|부산[광역시]*|대[전|구][광역시]*|울산[광역시]*|강원[도]*|제주[도|특별자치도]*|광주[광역시]*|충[청|남|북][남도|북도|도]*|경[상|남|북][북도|남도|도]*|세종[특별시]*)"
    pattern2 = re.compile(pat)    
    try:
        province = re.match(pattern2, address).group()
    except:
        try:
            province = re.search(pattern2, address).group()
        except:
            province = ''


    address = re.sub(pat, '', address, 1)
    
    return province, address

def split_area(address, info):
    pat_1 = r"(?=[가-힣]+시\s*[가-힣]+구)([가-힣]+시\s*[가-힣]+구)|[가-힣]+시"
    pat_2 = r"(?=[가-힣]+구[가-힣]?구)(.*?구(?<=[가-힣]{2}구))|[가-힣]+구"
    pat_3 = r"[가-힣]+군"
    pat = f"{pat_1}|{pat_2}|{pat_3}"
    pattern2 = re.compile(pat)
    # print(address)
    try:
        area = re.match(address, pattern2).group()
    except:
        try:
            area = re.search(pattern2, address).group()
        except:
            area = ''

    address = re.sub(area, '', address, 1)
    return area, address    

def split_village(address, info):
    pat_eup = r"((?=[가-힣]+읍(| )[가-힣\d]+로)([가-힣]+읍(| )[가-힣\d]+로)|(?=[가-힣]+읍(| )[가-힣]+리)([가-힣]+읍(| )[가-힣]+리)|[가-힣]+읍)"
    pat_dong = r"((?=[가-힣\d]+동\d가)([가-힣\d]+동\d가)|(?=[가-힣\d]+동[가-힣\d ]{2,4}로)([가-힣\d]+동[가-힣\d ]{2,4}로)|(?=[가-힣\d]+동길)(?<!=길)|[가-힣\d]+동)"
    pat_ro = r"((?=[가-힣\d]+로\d가)([가-힣\d]+로\d가)|[가-힣\d]+로)"
    pat_myun = r"((?=북면|동면)(북면|동면)|(?=[가-힣]+면(| )[가-힣]{2,}리)([가-힣 ]+리)|(?=[가-힣]+면.*로)([가-힣 ]+로)|(?=[가-힣]+면(| )[가-힣]+로)([가-힣]+면(| )[가-힣]+로)|[가-힣]{2,}면)"
    pat_gil = r"(?=[가-힣\d]+[가-하]길)([가-힣\d]+[가-하]길)|(?=[가-힣\d]+[가-하]동길)([가-힣\d]+[가-하]동길)|(?=[가-힣]+(읍|면|동)( |)[가-힣]+\d길)([가-힣]+(읍|면|동)( |)[가-힣]+\d길)|[가-힣]+\d길"
    pat_ri = r"([가-힣\d]+리)"
    pat_etc = r"((?=[가-힣\d]+가(| )[가-힣]{2,}로)([가-힣\d]+가(| )[가-힣]{2,}로)|[가-힣]+\d가)"
    pat = f"{pat_etc}|{pat_eup}|{pat_myun}|{pat_dong}|{pat_ro}|{pat_gil}|{pat_ri}"
    pattern = re.compile(pat)
    # print(address)
    try:
        village = re.match(address, pattern).group()
    except:        
        try:
            village = re.search(pattern, address).group()
        except:            
            village = ''
    address = re.sub(village, '', address, 1)
    return village, address

def split_dong_ho_f(address):    
    pattern_2 = re.compile(r'[A-Z]*\d+동')
    try:
        dong = re.match(pattern_2, address).group()         
    except:
        try:
            dong = re.search(pattern_2, address).group()                        
        except:
            dong = ''
    if dong:
        address = re.sub(dong, '', address, 1)
        dong = f"{dong}동" if dong else ''

    pattern_3 = re.compile(r'\s\d+층.(지하)*\d+(?=층|F)|\d+-\d+(?=층|F)|(?![가-힣])\d+(?=층|F)|\d, \d(?=층|F)| \d+(?=층|F)|지하\d(?=층|F)|\d(?=층|F)|B\d(?=층|F)|\s(지하)*\d+,\d+(?=층|F)')
    try:
        floor = re.match(pattern_3, address).group()         
    except:
        try:
            floor = re.search(pattern_3, address).group()
        except:
            floor = ''
    if floor:
        address = address.replace(f"{floor}층", '').replace(f"{floor}F", '')
        floor = f"{floor}층" if floor else ''

    pattern_4 = re.compile(r'\d+호(| )내(| )\d+(?=호)|(\d+-\d+,*)+(?=호)|(\d+~\d+,*)+(?=호)|[A-Z]*[비\d,]*\d+(?=호)|(케이|비|티|와이|제오|이에스)*나*[A-Za-b]*\d*-\d+(?=호)|[A-Z]*\d+~\d+(?=호)|(B|b|비|씨)\d*(?=호)')
    try:
        ho = re.match(pattern_4, address).group()        
    except:
        try:
            ho = re.search(pattern_4, address).group()            
        except:
            ho = ''
    if ho:
        address = address.replace(f"{ho}호", '')
        ho = f"{ho}호"if ho else''

    pattern_5 = re.compile(r'(\((.*?)[^주]\)*\))')
    try:
        parentheses = re.match(pattern_5, address).group()        
    except:
        try:
            parentheses = re.search(pattern_5, address).group()            
        except:
            parentheses = ''
    
    address = address.replace(parentheses, '')
    

    detail = f"{parentheses}{dong}{floor}{ho}"
    
    return detail, address

def split_detail(address):
    pat = r"^\d+번[가-하](?=길)|^[가-힣]+\d+번+(?=길)|^\d+번*(?=길)|^[가-힣]+\d*(?=길)|^\d*[가-힣](?=길)"
    pattern = re.compile(pat)
    address = re.sub('^\s', '', address)

    try:
        gil = re.match(address, pat).group()        
    except:        
        try:
            gil = re.search(pattern, address).group()
        except:
            gil = ''
    if gil:
        address = address.replace(f"{gil}길", '')
        gil = f"{gil}길"if gil else ''
    address = re.sub('^\s', '', address)

    pat_1 = r"^(APEC로(| )\d+|\d+번길(| )\d+|\d+-\d+(번지)*|\d+번지|^[가-힣]*\d*로(| )\d+(번길)*|\d+|^(길|로)(| )\d+(-\d+)*길*|\d+(?=\d+통))"
    pattern = re.compile(pat_1)
    address = re.sub('^\s', '', address)

    try:
        etc = re.match(address, pat_1).group()        
    except:        
        try:
            etc = re.search(pattern, address).group()
        except:
            etc = ''
    
    address = address.replace(f"{etc}", '')
    etc = f"{etc}"if etc else ''
    address = re.sub('^\s', '', address)
    detail = f"{gil} {etc}"
    return detail, address

def read_json(path):
    info_dict = {}
    with open(os.path.join(os.getcwd(), path), 'rt', encoding='utf-8-sig') as f:
        data = f.read()
        data_dict = json.loads(data)    
    for key in data_dict:                
        if key == "seller_info":       
            call_info = split_phone_nums(data_dict[key]['call_number'])
            if not call_info:
                continue
            if not data_dict[key]['representative_name']:
                continue
            info_dict.update(call_info)
            info_dict['수령자'] = data_dict[key]['representative_name']
            f_address = data_dict['seller_info']['address'].replace('&amp;', '').replace('sim;', '').replace('&nbsp;', '').replace('&quot;', '')
            r2 = re.sub(r'\B\-', '', f_address)
            # r3 = re.sub(r'[\d]+∼[\d]+', '', r2)
            province, address = split_province(r2, data_dict['seller_info']['seller_id'])                        
            area, address = split_area(address, data_dict['seller_info']['seller_id'])            
            village, address = split_village(address, data_dict['seller_info']['seller_id'])
            # address = re.sub('\d+~\d+', '', address)
            spot, address = split_dong_ho_f(address)                      
            address = re.sub('\s', '', address, 1)
            address = re.sub('\s', '', address, 1)            
            # print(f"{address}  /  {data_dict['seller_info']['seller_id']}")
            detail, address = split_detail(address)
            print(province)
            print(area)
            print(village)
            print(detail)
            print(spot)
            print(address)
            # print(f"{address}  /  {data_dict['seller_info']['seller_id']} {gil}")
            info_dict["vendor_id"] = data_dict['seller_info']['seller_id']
            info_dict['도로명 주소'] = f"{province} {area} {village} {detail}"
            info_dict['상세주소'] = f"{spot} {address}"
    return  info_dict



if __name__ == '__main__':        
    id_lst = ['A00001054', 'A00001520', 'A00001595', 'A00003133', 'A00003134', 'A00004422', 'A00004694', 'A00005011', 'A00010454', 'A00012323', 'A00011779', 'A00011803',  'A00012427', 'A00003302', 'A00013798', 'A00004764']

    data_saves = 'data_save\\g_*.json'
    # data_saves = [f'data_save\{id}.json' for id in id_lst]
    data = glob.glob(data_saves)
    # x = data_saves    
    l = []               
    data_list = []
    # ordered_list = ["옵션1", "옵션2", "옵션3", "전화 첫단", "전화 중간", "전화 마지막", "수령자", "도로명주소", "상세주소"]
    ordered_list = ["옵션1", "옵션2", "vendor_id", '전화 첫단', '전화 중간', '전화 마지막', '수령자', "도로명 주소", "상세주소"]
    wb = Workbook("sample_data.xlsx")
    ws = wb.add_worksheet()
    first_row = 0
    for header in ordered_list:
        col = ordered_list.index(header)
        ws.write(first_row,col,header)

    row = 1
    # # sys.stdout = open('result.txt', 'w')
    for i, d in enumerate(data):
        # f = d.replace('data_save\\', '')        
        # try:
        #     f_r = re.match(r'A[0-9]+',f).group()
        # except:
        #     print(i)
        #     break
        if i < 20000:
            continue
        elif i > 30000:
            break
        data = read_json(d)        
        print('-------------------------')
        for key in data:
            col = ordered_list.index(key)
            ws.write(row, col, data[key])
        row += 1
        time.sleep(1)
        data_list.append(data)        
    wb.close()
    # sys.stdout.close()    