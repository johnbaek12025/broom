import json
import time
import requests
from bs4 import BeautifulSoup as bf
import re
import asyncio
import cloudscraper

header = {            
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            "referer": "https://www.coupang.com/vp/products/1491728890?itemId=2560769734&vendorItemId=81960834288&isAddedCart=",            
            "cookie": "PCID=17418002963470725662093; MARKETID=17418002963470725662093; x-coupang-accept-language=ko_KR;",
        }

url = 'https://www.coupang.com/vp/product/reviews?productId=1491728890&page=1&size=5&sortBy=ORDER_SCORE_ASC&ratings=&q=&viRoleCode=2&ratingSummary=true'

s = requests.session()
res = s.get(url, headers=header)
print(res.text)
