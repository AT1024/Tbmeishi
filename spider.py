#！usr/bin/env python3
# -*-coding:UTF-8 -*-
import re
import pyquery as pq
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *
import pymongo

# 配置MongoDB数据库
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
# 用来配置谷歌无界面浏览器
__browser_url=r'C:\Users\Administrator\AppData\Roaming\360se6\Application\360se.exe'
chrome_options = Options()
chrome_options.binary_location=__browser_url
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--disable-gpu')
browser = webdriver.Chrome(chrome_options=chrome_options)

wait =WebDriverWait(browser,10)

def search():
    print('正在搜索')
    browser.get('https://www.taobao.com/')
    try:
        # 获取首页输入端
        input=wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#q'))
        )
        # 获取提交按钮
        submit=wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button'))
        )
        input.send_keys('美食')
        submit.click()

        # 获取总页数
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total'))
        )
        return total.text
    except TimeoutException:
            # n+=1
            # print("超出时间%s次"%n)
        return search()

def next_page(page_number):
    print("正在翻页 ",page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'))
        )
    except TimeoutException:
        next_page(page_number)

def get_products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item'))
    )
    html = browser.page_source
    doc = pq(html)
    items=doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MongoDB成功\n',result)
    except Exception:
        print("存储到MongoDB失败\n",result)

def main():
    try:
        total = search()
        total= int(re.compile('(\d+)').search(total).group(1))
        for i in range(2,total+1):
            next_page(i)
    except Exception:
        print('主函数出错，关闭浏览器')
    finally:
        browser.close()

if __name__=='__main__':
    main()