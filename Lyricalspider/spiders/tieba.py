# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy
from urllib import parse
from Lyricalspider.items import LyricalspiderItem
# from scrapy.selector import Selector

class TiebaSpider(scrapy.Spider):
    name = 'tieba'
    # allowed_domains = ['tieba.baidu.com']
    start_urls = ['http://tieba.baidu.com/hottopic/browse/topicList']

    def parse(self,response):
        # print(json.loads(response.text))
        bang_topic_list = json.loads(response.text).get('data').get('bang_topic').get('topic_list')
        for topic in bang_topic_list:
            item = LyricalspiderItem()
            item['title'] = topic.get('topic_name')
            item['hits'] = topic.get('discuss_num')
            item['context'] = topic.get('topic_desc')
            topic_url = 'http://tieba.baidu.com/hottopic/browse/getTopicRelateThread?topic_name={tn}'.format(tn = topic.get('topic_name'))
            item['url'] = topic_url
            yield scrapy.Request(url = topic_url,callback = self.parse_topic,meta = {'item':item})

    def parse_topic(self,response):
        # print(response.text)
        print(re.findall(r'\"tid\":(\d+),',response.text))
        print('---------------------------------')
        for p in re.findall(r'\"tid\":(\d+),',response.text):
            item = response.meta['item']
            tie_url = 'https://tieba.baidu.com/p/{tie_p}'.format(tie_p = p)
            print(tie_url)
            yield scrapy.Request(url = tie_url,callback = self.parse_tie_pn,meta = {'item':item})

    def parse_tie_pn(self,response):
        page_num = re.findall(r'共<span class="red">(\d+)</span>页</li>',response.text)[0]
        print(page_num)
        t_id = response.url.split('/')[-1]
        for p_n in range(1,int(page_num)+1):
            item = response.meta['item']
            time_str = str(time.time())[0:-3].replace('.','')
            comment_url = 'https://tieba.baidu.com/p/totalComment?t={t}&tid={tid}&pn={pn}&see_lz=0'.format(t = time_str,tid = t_id,pn = p_n)
            yield scrapy.Request(url = comment_url,callback = self.parse_comments,meta = {'item':item})

    def parse_comments(self,response):
        comment_list = json.loads(response.text)['data'].get('comment_list',[])
        print(comment_list)
        for comments in comment_list.values():
            for comment in comments.get('comment_info',[]):
                item = response.meta['item']
                item['comment'] = re.sub(r'[回复 ]{0,1}<.*>[:]{0,1}','',comment.get('content')).lstrip('回复')
                item['comment_user'] = comment.get('username')
                item['support'] = comments.get('comment_num')
                yield item







