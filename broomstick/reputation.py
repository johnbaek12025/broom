import json
import time
import requests
from bs4 import BeautifulSoup as bf
import re
import asyncio
import random
import numpy
from xlsxwriter import Workbook

class Reputation(object):
    def __init__(self, product_url, path) -> None:
        self.session = None
        self.header = header = {            
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            }
        self.referer = "https://www.coupang.com/vp/products/{product_id}"
        self.product_url = product_url
        self.wtime = numpy.arange(0.5, 2, 0.5)
        self._url = 'https://www.coupang.com/vp/product/reviews?productId={product_id}&page={page}&size=30&sortBy=ORDER_SCORE_ASC'
        self._ordered_list = ["판매자", "상품명", "작성자", "좋아요 갯수", "작성 날짜", "이미지", "작성 내용"]
        self.path = path

    def extract_product_id(self):
        product_id = re.search(r'/\d+\?', self.product_url)
        if product_id:
            product_id = re.sub('[^0-9]+', '', product_id.group())
        return product_id    

    def set_session(self):        
        s = requests.session()
        s.headers.update(self.header)
        s.cookies.set(**{"domain": ".coupang.com", 
                    "value": "17418002963470725662093", 
                    "path": "/",                 
                    "name": "PCID",
                    "rest": {"httpOnly": False, "sameSite": False},})
        s.cookies.set(**{ "name": "MARKETID",
                    "value": "17418002963470725662093",
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": True, "sameSite": None, "secure": True},})            
        s.cookies.set(**{"name": "x-coupang-accept-language",
                    "value": "ko_KR",            
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": False, "sameSite": '', "secure": False},})    
        return s

    def main(self):
        if not self.extract_product_id():
            return None
        product_id = self.extract_product_id()
        print(self.path)
        self.header['referer'] = self.referer.format(product_id=product_id)
        collect_parser = {}
        for page in range(1, 35):            
            url = self._url.format(product_id=product_id, page=page)
            info = self.status_validation(url)
            if not info:
                break
            data = bf(info, 'html.parser')
            if len(data.text) == 17:
                break
            collect_parser[page] = data

        reviews_lst = []
        for k, v in collect_parser.items():
            reviews = self.set_review_data(v)
            reviews_lst.extend(reviews)
        try:
            self.set_excel_file(reviews_lst)
        except Exception as e:
            return f"{e} generated"

    def set_excel_file(self, data):
        wb = Workbook(f"{self.path}.xlsx")
        ws = wb.add_worksheet()
        first_row = 0
        for header in self._ordered_list:
            col = self._ordered_list.index(header)
            ws.write(first_row,col,header)

        for i, review in enumerate(data):
            for k, v in review.items():
                print(v)
                ws.write(i+1, self._ordered_list.index(k), v)
        wb.close()
        return True

    def set_review_data(self, data:bf):
        review_lst = []
        each_review = data.find_all('article', {"class": 'sdp-review__article__list js_reviewArticleReviewList'})    
        product_name = data.find('div', {'class': 'sdp-review__article__list__info__product-info__name'}).text
        seller = data.find('div', {'class': 'sdp-review__article__list__info__product-info__seller_name'}).text
        seller = re.sub(r'\s+판매자:\s', '', seller)
        seller = re.sub(r'\s+', '', seller)
        for i, review in enumerate(each_review):
            reviewer = review.find('span', {'class': 'sdp-review__article__list__info__user__name js_reviewUserProfileImage'}).text        
            like = review.find('span', {'class': 'js_reviewArticleHelpfulCount'})        
            review_date = review.find('div', {'class': 'sdp-review__article__list__info__product-info__reg-date'}).text
            review_content = review.find('div', {'class': 'sdp-review__article__list__review__content js_reviewArticleContent'})
            img_links = [div.img['src'] for div in review.find_all('div', {'class': 'sdp-review__article__list__attachment__list'})]
            if review_content:
                review_content = review_content.text
                review_content = re.sub(r'^\s+', '', review_content)
                review_content = re.sub(r'\n', ' ', review_content)
            review = {
            "판매자": seller,
            "상품명": product_name,
            "작성자": reviewer,
            "좋아요 갯수": like.text if like else '0',
            "작성 날짜": review_date,
            "이미지": ', '.join(img_links),
            "작성 내용": review_content,
            }
            review_lst.append(review)    
        return review_lst

    def status_validation(self, url):
        time.sleep(random.choice(self.wtime))
        s = self.set_session()
        res = s.get(url)
        status = res.status_code
        if status == 200:            
            try:                
                return res.json()
            except json.JSONDecodeError:
                if "error" in res.text:
                    return None
                return res.text
        else:
            return None


if __name__ == '__main__':
    url = 'https://www.coupang.com/vp/products/17789203?itemId=71456726&vendorItemId=3115316866&sourceType=CATEGORY&categoryId=195166&isAddedCart='
    path = 'C:/Users/user1/Downloads/sample_data'
    b = Reputation(url, path)
    b.main()
