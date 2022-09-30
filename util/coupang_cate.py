import re
import time
from unicodedata import category
import numpy
import requests
import random
from bs4 import BeautifulSoup as bf
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from broomstick import settings


wtime = numpy.arange(1, 3, 0.5)
s = requests.session()
header = {            
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            "referer": "https://www.coupang.com/vp/products/1491728890?itemId=2560769734&vendorItemId=81960834288&isAddedCart=",            
            "cookie": "PCID=17418002963470725662093; MARKETID=17418002963470725662093; x-coupang-accept-language=ko_KR;",
        }
s.headers.update(header)

def status_validation(url, post_data=None):
    time.sleep(random.choice(wtime))
    if not post_data:            
        res = s.get(url, headers=header)            
    else:
        res = s.post(url, headers=header, data=post_data)

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


def first_cate_nums(info):
    first_category = dict()    
    data = bf(info, 'html.parser')
    fashion = data.find('div', {'class': "depth"})
    li_tag = fashion.find_all('li', {'class': 'second-depth-list'})    
    for f in li_tag:        
        cate_num = re.sub('[^0-9]+','', f.a['href'])        
        first_category[cate_num] = f.a.text
    ul_tag = data.find('ul', {'class': "menu shopping-menu-list"})
    a_tag = ul_tag.find_all('a', {'class': 'first-depth'})
    for a in a_tag:
        cate_num = re.sub('[^0-9]+','', a['href'])
        first_category[cate_num] = a.text
    return first_category

def st_cate_nums(category): # second and third category
    cate_url = f'https://www.coupang.com/np/categories/{category}'    
    info = status_validation(cate_url)
    data = bf(info, 'html.parser')
    cate = data.find('div', {'class': 'search-filter-options search-category-component'})
    category = cate.find_all('li', {'class': 'search-option-item'})
    st_cate = {}
    for i, c in enumerate(category):        
        k = c['data-component-id']
        st_cate[k] = c.label.text
    return st_cate

def f_cate_nums(category): # fourth and fifth category
    cate_url = f'https://www.coupang.com/np/categories/{category}'
    info = status_validation(cate_url)
    data = bf(info, 'html.parser')
    cate = data.find_all('li', {'class': 'search-option-item selected opened'})    
    if not cate:
        return None
    cate = cate[-1]
    category = cate.find_all('li', {'class': 'search-option-item'})    
    f_cate = {}
    for c in category:
        k = c['data-linkcode']
        f_cate[k] = c.label.text
    return f_cate
    # settings.save_file(data, f'{category}.html')


if __name__ == '__main__':
    with open('fifth_cate_copy.txt', 'r', encoding='utf-8') as f:
        cate = f.read()
        fifth_cate_copy = eval(cate)
    print(len(fifth_cate_copy))
    with open('fourth_cate.txt', 'r', encoding='utf-8') as f:
        cate = f.read()
        fourth_cate = eval(cate)    

    with open('fourth_cate_copy.txt', 'r', encoding='utf-8') as f:
        cate = f.read()
        fourth_cate_copy = eval(cate)    

    fifth_cate = {}
    # fourth_cate_copy = {}
    for k, v in fourth_cate.items():
        if k in fourth_cate_copy:
            continue
        cate = f_cate_nums(k)
        if not cate:
            cate[k] = v
        fourth_cate_copy[k] = v
        fifth_cate.update(cate)
        settings.save_file(fourth_cate_copy, 'fourth_cate_copy.txt')
        settings.save_file(fifth_cate, 'fifth_cate.txt')
        
    # main_url = 'https://www.coupang.com/'
    # info = status_validation(main_url)
    # first_cate = first_cate_nums(info)
    # # print(first_cate) 
    # second_cate = {}
    # for k, v in first_cate.items():
    #     cate = second_cate_nums(k)
    #     second_cate.update(cate)    
    
    # settings.save_file(second_cate, 'second_cate.txt')
    # print(second_cate)
    # print(len(first_cate))
    # print(second_cate)
    # print(len(second_cate))    
    # with open('second_cate.txt', 'r', encoding='utf-8') as f:
    #     cate = f.read()
    #     second_cate = eval(cate)

    
    # third_cate = {}
    # second_cate_copy = {}
    # for k, v in second_cate.items():
    #     cate = third_cate_nums(k)        
    #     if not cate:
    #         cate[k] = v
    #     third_cate.update(cate)
    #     second_cate_copy[k] = v
    #     settings.save_file(second_cate_copy, 'second_cate_copy.txt')
    #     settings.save_file(third_cate, 'third_cate.txt')

    # with open('third_cate.txt', 'r', encoding='utf-8') as f:
    #     cate = f.read()
    #     third_cate = eval(cate)    

    # fourth_cate = {}
    # for k, v in third_cate.items():
    #     cate = fourth_cate_nums(k)
    #     if not cate:
    #         cate[k] = v
    #     fourth_cate.update(cate)
    #     settings.save_file(fourth_cate, 'fourth_cate.txt')




    # header = {            
    #         "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
    #         "referer": "https://www.coupang.com/vp/products/1491728890?itemId=2560769734&vendorItemId=81960834288&isAddedCart=",            
    #         "cookie": "PCID=17418002963470725662093; MARKETID=17418002963470725662093; x-coupang-accept-language=ko_KR;",
    #     }

    # url = 'https://www.coupang.com/vp/product/reviews?productId=1491728890&page=1&size=5&sortBy=ORDER_SCORE_ASC&ratings=&q=&viRoleCode=2&ratingSummary=true'

    