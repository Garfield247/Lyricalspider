# -*- coding: utf-8 -*-
import re
import json
import math
import scrapy
import random
import urllib.parse
from Lyricalspider.items import LyricalspiderItem

class Wy163Spider(scrapy.Spider):
    name = 'wy163'
    # allowed_domains = ['tie.163.com']
    def start_requests(self):
        for page in range(1,4):
            url = 'http://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/heatedList/allSite?page=%d'%page
            yield scrapy.Request(url=url,callback = self.parse)

    def parse(self,response):
        # print(response.text)
        json_obj = json.loads(response.text)
        for i in json_obj:
            item = LyricalspiderItem()
            thread =  i["thread"]
            item['title'] = thread['title']
            item['url'] = thread['url']
            docId = thread['docId']
            yield scrapy.Request(url = thread['url'],callback = self.parse_context,meta = {'item':item,'docId':docId})

    def parse_context(self,response):
        item = response.meta['item']
        docId = response.meta['docId']
        url_local = urllib.parse.urlsplit(response.url).netloc
        print(url_local)
        if url_local == '2018.163.com':
            item['context'] = None
        else:
            item['context'] = ''.join(response.xpath('.//div[@id="endText"]/p/text()').extract())
        comment_first_url = 'http://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/%s/comments/newList?ibc=newspc&limit=30&showLevelThreshold=72&headLimit=1&tailLimit=2&offset=30'%docId
        yield scrapy.Request(url = comment_first_url,callback = self.parse_comment_scheduler,meta = {'item':item,'docId':docId})

    def comment_json(self,old_comment_json):
        new_comment_json = json.loads(re.sub(r'"label":"\[.*?\]",','',old_comment_json))
        return new_comment_json


    def parse_comment_scheduler(self,response):
        comment_json = self.comment_json(response.text)
        comment_limit = comment_json['newListSize']
        # print(comment_limit)
        page_num = math.ceil(comment_limit/30)
        docId = response.meta['docId']
        for i in range(1,page_num+1):
            offset = 30*i
            item = response.meta['item']
            comment_url = 'http://comment.api.163.com/api/v1/products/a2869674571f77b5a0867c3d71db5856/threads/%s/comments/newList?ibc=newspc&limit=30&showLevelThreshold=72&headLimit=1&tailLimit=2&offset=%d'%(docId,offset)
            yield scrapy.Request(url = comment_url,callback = self.parse_comment,meta = {'item':item})

    def parse_comment(self,response):
        comment_json = self.comment_json(response.text)
        comments = comment_json['comments']
        for comment_item in comments.values():
            item = response.meta['item']
            item['comment'] = comment_item['content']
            item['comment_user'] = comment_item['user'].get('nickname','游客用户')
            item['support'] = comment_item['vote']
            item['user_location'] = comment_item['user'].get('location')
            item['hits'] = random.choice(range(10,1000))
            yield item
