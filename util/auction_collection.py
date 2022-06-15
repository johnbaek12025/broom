import re
import sys
import numpy
import requests
from bs4 import BeautifulSoup as bf
import random
import time

wtime = numpy.arange(1, 3, 0.5)
url = 'https://www.auction.co.kr/category/category{num}.html'
# sys.stdout = open('consequence.txt', 'w', encoding='utf-8')
headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"}
def save_file(data, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(str(data))

def save_sub_links():
    links = {}
    i = 0
    skip = [35, 42,54, 53, 57, 74]
    sub_links = set()
    for n in range(1, 99):
        if n in skip:
            continue
        num = f"{str(n).zfill(2)}"
        time.sleep(random.choice(wtime))
        url = f'https://www.auction.co.kr/category/category{num}.html'    
        res = requests.get(url = url)
        status = res.status_code
        if status != 200:
            continue        
        res.encoding = 'euc-kr'
        info = res.text
        data = bf(info, 'html.parser')
        data = data.find_all('div', {'class': 'sub-cat'})
        if not data:
            continue    
        print(url)
        for d in data:
            a_tag = d.find_previous('a')
            link = a_tag['href']
            if 'http://through.auction.co.kr/common/SafeRedirect.' in link:
                continue
            print(link)
            # link = re.sub('[^0-9]', '', a_tag['href'])
            # print(link)
            sub_links.add(link)
        i += 1
    print(i)
    return sub_links

def bring_seller_links(link: str):
    links = set()    
    for i in range(1, 21):
        url = f'{link}&s=8&p={i}'
        time.sleep(random.choice(wtime))
        res = requests.get(url, headers=headers)
        try:
            info = res.content.decode('cp949')
        except:
            info = res.text
        if '소비자보호를 위한 오픈마켓 자율준수 규약' in info:
            print('-----------------------------------')
            return 'error'
        data = bf(info, 'html.parser')    
        
        
        cate_a = data.find_all('a', {'class': 'link--shop'}, href=True)        
        for a in cate_a:
            links.add(a['href'])
    return links

if __name__ == '__main__':
    # links = save_sub_links()
    seller_links = set()
    with open('current.txt', 'r') as file:
        f = file.read()
        skip = eval(f)

    with open('consequence.txt', 'r') as file:
        cate_set = file.read()
        links = eval(cate_set) 
    
    with open('seller_links.txt', 'r', encoding='utf-8') as file:
        cate_set = file.read()
        seller_links = eval(cate_set) 
    # links = ["https://browse.auction.co.kr/list?category=86220000",'https://browse.auction.co.kr/list?category=29610000', 'https://browse.auction.co.kr/list?category=01810000', 'https://browse.auction.co.kr/list?category=51410000', 'https://browse.auction.co.kr/list?category=46550000', 'https://browse.auction.co.kr/list?category=51530000']
    print(len(skip))
    for link in links:            
        if link in skip:
            continue
        print(link)
        s_links = bring_seller_links(link)      
        if not s_links:
            continue   
        elif s_links == 'error':
            print('ip_변경')
            break
        seller_links = seller_links|s_links        
        save_file(seller_links, f'seller_links.txt')
        skip.add(link)
        save_file(skip, 'current.txt')
    print(len(seller_links))
