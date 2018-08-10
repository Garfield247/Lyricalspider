# -*- coding: utf-8 -*-
import re
import json
import math
import scrapy
from scrapy.selector import Selector
from Lyricalspider.items import LyricalspiderItem


class SinaSpider(scrapy.Spider):
    name = 'sina'
    # allowed_domains = ['s.sina.com']
    start_urls = ['http://s.weibo.com/top/summary?cate=realtimehot']

    def parse(self,response):
        # with open('sina.html','w',encoding='utf-8') as fp:
        #     fp.write(response.text)
        realtimehot = json.loads(re.findall(r'<script>STK\ &&\ STK\.pageletM\ &&\ STK\.pageletM\.view\((\{"pid":"pl_top_realtimehot".*?)\)</script>',response.text)[0])
        # print(realtimehot['html'])
        realtimehot_html = Selector(text = realtimehot['html'])
        for tr in realtimehot_html.xpath('.//tr[@action-type="hover"]'):
            item = LyricalspiderItem()
            item['title'] = tr.xpath('./td[@class="td_02"]/div/p/a/text()').extract_first()
            url = 'http://s.weibo.com' + tr.xpath('./td[@class="td_02"]/div/p/a/@href').extract_first()+'&xsort=hot&suball=1'
            item['url'] = url
            item['hits'] = tr.xpath('./td[@class="td_03"]/p/span/text()').extract_first()
            yield scrapy.Request(url = url,callback=self.parse_context_list,meta = {'item':item})
    def parse_context_list(self,response):
        # with open('sia.html','w',encoding='utf-8') as fp:
        #     fp.write(response.text)
        mids = list(set(re.findall(r'mid=(\d+)&',response.text)))
        for mid in mids:
            item = response.meta['item']
            index_url = 'https://m.weibo.cn/detail/%s'%str(mid)
            yield scrapy.Request(url=index_url,callback=self.parse_context,meta = {'item':item,'mid':mid})

    def parse_context(self,response):
        res = json.loads(re.findall(r'var\ \$render_data\ =\ \[(.*?)\]\[0\]\ \|\| \{\};',response.text)[0])
        for page_num in range(1,math.ceil(int(res['status'].get('comments_count'))/10)+1):
            item = response.meta['item']
            mid = response.meta['mid']
            item['context'] = res['status'].get('text')
            item['hits'] = int(res['status'].get('reposts_count')) + int(res['status'].get('comments_count')) + int(res['status'].get('attitudes_count'))
            comments_url = 'https://m.weibo.cn/api/comments/show?id=%s&page=%d'%(str(mid),int(page_num))
            yield scrapy.Request(url=comments_url,callback = self.parse_comments,meta = {'item':item})

    def parse_comments(self,response):
        res = josn.loads(response.text)
        comments = res['data'].get('data',[])
        if len(comments)>0:
            for comment in comments:
                item = response.meta['item']
                item['comment'] = comments.get('text')
                item['comment_user'] = comments.get('user').get('screen_name')
                item['support'] = comments.get('like_counts')
                user_id = comments.get('user').get('id')
                user_info_url = 'https://m.weibo.cn/api/container/getIndex?containerid=230283%d_-_INFO'%user_id
                yield scrapy.Request(url=user_info_url,callback = self.parse_user_info,meta = {'item':item})

    def parse_user_info(self,response):
        res = json.loads(re.findall(r'\{"card_type":41,"item_name":"\\\\u6240\\\\u5728\\\\u5730","item_content":".*?"\}', response.text)[0])
        item = response.meta['item']
        item['user_location'] = res.get('item_content','未知地区')
        yield item







