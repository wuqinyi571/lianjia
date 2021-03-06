#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author;Tsukasa

import json
import os
from multiprocessing import Pool
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import pymongo
from openpyxl import load_workbook

g_index = 0

def generate_allurl(user_in_nub, user_in_city):  # 生成url
    url = 'http://' + user_in_city + '.lianjia.com/ershoufang/pg{}/'
    for url_next in range(0, int(user_in_nub)):
        yield url.format(url_next+1)


def get_allurl(generate_allurl):  # 分析url解析出每一页的详细url
    send_headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
              "Connection":"keep-alive",
              "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
              "Accept-Language":"en-US,en;q=0.9"}
    #get_url = requests.get(generate_allurl, 'lxml')
    get_url = requests.get(generate_allurl, headers=send_headers)
    if get_url.status_code == 200:
        re_set = re.compile('<li class="clear LOGCLICKDATA" ><a class="noresultRecommend img ".*?href="(.*?)"')
        re_get = re.findall(re_set, get_url.text)
        return re_get


def open_url(re_get):  # 分析详细url获取所需信息
    send_headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
          "Connection":"keep-alive",
          "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
          "Accept-Language":"en-US,en;q=0.9"}
    res = requests.get(re_get, headers=send_headers)
    if res.status_code == 200:
        info = {}
        soup = BeautifulSoup(res.text, 'lxml')
        info['标题'] = soup.select('.main')[0].text
        info['总价'] = soup.select('.total')[0].text + '万'
        info['每平方售价'] = soup.select('.unitPriceValue')[0].text
        if soup.select('.taxtext') :
            info['参考总价'] = soup.select('.taxtext')[0].text
        else:
            info['参考总价'] = "暂无数据"
        info['建造时间'] = soup.select('.subInfo')[2].text
        info['小区名称'] = soup.select('.info')[0].text
        info['所在区域'] = soup.select('.info a')[0].text + ':' + soup.select('.info a')[1].text
        info['链家编号'] = str(re_get)[34:].rsplit('.html')[0]
        for i in soup.select('.base li'):
            i = str(i)
            if '</span>' in i or len(i) > 0:
                key, value = (i.split('</span>'))
                info[key[24:]] = value.rsplit('</li>')[0]
        for i in soup.select('.transaction li'):
            i = str(i)
            if '</span>' in i and len(i) > 0 and '抵押信息' not in i:
                key, value, tmp = (i.split('</span>'))
                info[key[25:]] = value.rsplit('</li>')[0][7:]
        return info


def update_to_MongoDB(one_page):  # update储存到MongoDB
    if db[Mongo_TABLE].update({'链家编号': one_page['链家编号']}, {'$set': one_page}, True): #去重复
        print('储存MongoDB 成功!')
        return True
    return False


def _excelAddSheet(dataframe, excelWriter, sheet_name):
    book = load_workbook(excelWriter.path)
    excelWriter.book = book
    dataframe.to_excel(excel_writer=excelWriter, sheet_name=sheet_name, index=None)
    excelWriter.close()

def pandas_to_xlsx(info):  # 储存到xlsx
    global g_index
    pd_look = pd.DataFrame(info, index=[g_index])
    g_index = g_index+1;
    #pd_look.to_excel('链家二手房.xlsx', sheet_name='链家二手房',mode='a')
    pd_look.to_csv('链家二手房.csv', mode='a',encoding='utf_8_sig')
    #with open('链家二手房.text', 'r', encoding='utf-8')as f:
        #f_info=f.read()
        #print("---------------------------------------------------------")
        #print(f_info)
        #pd_look = pd.DataFrame(f_info)
        #pd_look.to_excel('链家二手房.xlsx', sheet_name='链家二手房')
        #f.close()
    #pd_look = pd.DataFrame(info, index=[0])
    #print("pd_look")
    #print(pd_look)
    #if os.path.exists('链家二手房.xlsx'):
        #pd_look1 = pd.read_excel('链家二手房.xlsx',sheet_name='链家二手房',skiprows=[0])
        #print("pd_look1")
        #print(pd_look1)
        #pd.concat([pd_look, pd_look]).to_excel('链家二手房.xlsx', sheet_name='链家二手房')
    #else:
        #pd_look.to_excel('链家二手房.xlsx', sheet_name='链家二手房')


def writer_to_text(list):  # 储存到text
    with open('链家二手房.text', 'a', encoding='utf-8')as f:
        f.write(json.dumps(list, ensure_ascii=False) + '\n')
        f.close()


def main(url):
    f_info = open_url(url)
    print (f_info)
    writer_to_text(f_info)    #储存到text文件
    pandas_to_xlsx(f_info)
    # update_to_MongoDB(list)   #储存到Mongodb


if __name__ == '__main__':
    user_in_city = input('输入爬取城市：')
    user_in_nub = input('输入爬取页数：')

    Mongo_Url = 'localhost'
    Mongo_DB = 'Lianjia'
    Mongo_TABLE = 'Lianjia' + '\n' + str(user_in_city)
    client = pymongo.MongoClient(Mongo_Url)
    db = client[Mongo_DB]
    pool = Pool()
    #main("https://zs.lianjia.com/ershoufang/105101502402.html")
    for i in generate_allurl(user_in_nub, user_in_city):
        pool.map(main, [url for url in get_allurl(i)])