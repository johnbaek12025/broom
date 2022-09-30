from email import header
import re
import sys
import numpy
import requests
from bs4 import BeautifulSoup as bf
import random
import time
from requests.exceptions import ChunkedEncodingError
wtime = numpy.arange(2, 4, 0.5)
url = 'https://www.auction.co.kr/category/category{num}.html'
# sys.stdout = open('consequence.txt', 'w', encoding='utf-8')
headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36",            
            "refer": "https://auction.co.kr"
          }

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
        for d in data:
            a_tag = d.find_previous('a')
            link = a_tag['href']
            if 'http://through.auction.co.kr/common/SafeRedirect.' in link:
                continue            
            # link = re.sub('[^0-9]', '', a_tag['href'])
            # print(link)
            sub_links.add(link)
        i += 1
    print(i)
    return sub_links

def bring_seller_links(link: str):
    links = set()        
    for i in range(1, 51):
        url = f'https://browse.auction.co.kr/list?category={link}&s=8&p={i}'
        time.sleep(random.choice(wtime))
        try:
            res = requests.get(url, headers=headers)
        except:                
            time.sleep(5)
            res = requests.get(url, headers=headers)   
        try:
            info = res.content.decode('cp949')
        except:
            info = res.text
        if '소비자보호를 위한 오픈마켓 자율준수 규약' in info:
            print('-----------------------------------')
            return False
        data = bf(info, 'html.parser')
        cate_a = data.find_all('a', {'class': 'link--shop'}, href=True)        
        for a in cate_a:
            links.add(a['href'])
    return links


def get_deepest_cate(link):    
    links = set()
    time.sleep(random.choice(wtime))
    try:
        res = requests.get(link, headers=headers)
    except:
        time.sleep(5)
        res = requests.get(link, headers=headers)
    try:
        info = res.content.decode('cp949')
    except:
        info = res.text
    if '소비자보호를 위한 오픈마켓 자율준수 규약' in info:        
        return False
    data = bf(info, 'html.parser') 
    cates = data.find_all('li', {"class": "item depth3"})
    for c in cates:
        l = c.find('a', {"data-montelena-categoryno": True})
        links.add(l['data-montelena-categoryno'])
    return links

def collect_deepest_cates(links):
    contents = set()
    for l in links: # deeper cateory_numbers
        link = get_deepest_cate(l)
        print(link)
        if not link:
            continue        
        contents = contents|link        
        print(len(contents))
        save_file(contents, 'deeper_cate')

if __name__ == '__main__':
    # links = save_sub_links()
    # save_file(links, "last_cate")

    with open('./deeper_cate') as f:
        cates = eval(f.read())
    
    used_cates = list()
    with open('./used_cates') as f:
        used_cates = eval(f.read())

    seller_links = set()
    with open('./a_seller_links') as f:
        seller_links = eval(f.read())

    for c in cates:
        print(c)
        try:
            link = bring_seller_links(c)
        except ChunkedEncodingError:
            link = bring_seller_links(c)
        if not link:
            continue
        seller_links = seller_links | link
        used_cates.append(c)        
        save_file(used_cates, "used_cates")
        save_file(seller_links, "a_seller_links")
