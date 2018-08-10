# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import json
import socket
import pymongo
from snownlp import SnowNLP
from datetime import datetime
from pyltp import Segmentor,Postagger
from Lyricalspider.utils import stop_word
from Lyricalspider.settings import MONGO_CONF,FLUME_CONF,LTP_MODELS_PATH


class LyricalspiderPipeline(object):
    def process_item(self, item, spider):
        return item

class JsonTest(object):
    """docstring for JsonTest"""
    def open_spider(self, spider):
        filedir = './%sdata'%str(datetime.now().date())
        if os.path.exists(filedir)==False:
            os.makedirs(filedir)
        filename = 'Slave-%s-wangyi-%s.json'%(str(socket.gethostname()).split('-')[-1],str(datetime.now().date()))
        filepath = os.path.join(filedir,filename)
        self.fp = open(filepath, 'a', encoding='utf-8')
    def _load(self,items):
        dict(items)
        for k in list(items.keys()):
            if type(items[k])==str:
                # 去除转义字符
                items[k] = re.sub(r'[\r|\n|\t]', '', items[k])
                # 去除长空格
                items[k] = re.sub(r'\s{2,}', '', items[k])
                # # 替换|为-
                items[k] = re.sub(r'\|', '-', items[k])
        return items

    def process_item(self, item, spider):
        obj = dict(self._load(item))
        obj.pop('context')
        string = json.dumps(obj, ensure_ascii=False)
        self.fp.write(string + '\n')
        return item

    def close_spider(self, spider):
        self.fp.close()

class MongodbPiplines(object):
    def open_spider(self,spider):
        host = MONGO_CONF['MONGODB_HOST']
        port = MONGO_CONF['MONGODB_PORT']
        dbName = MONGO_CONF['MONGODB_DBNAME']
        self.client = pymongo.MongoClient(host=host, port=port)
        tdb = self.client[dbName]
        post_name = spider.name+'_data'
        self.post = tdb[post_name]

    def process_item(self, item, spider):
        data = dict(item)
        data['source'] = spider.name
        data['crawl_date'] = str(datetime.now().date())
        self.post.insert(data)
        return item

    def close_spider(self, spider):
        self.client.close()

class process_transful(object):
    def open_spider(self,spider):
        self.models_path = LTP_MODELS_PATH
        self.segmentor =self._init_segmentor()
        self.postagger = self._init_postagger()
        self.conn = self._init_conn()

    def _init_conn(self):
        conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        conn.connect((FLUME_CONF['FLUME_HOST'],FLUME_CONF['FLUME_PORT']))
        return conn

    def _init_segmentor(self):
        cws_model_path = os.path.join(self.models_path, 'cws.model')
        segmentor = Segmentor()
        segmentor.load(cws_model_path)
        return segmentor

    def _init_postagger(self):
        pos_model_path = os.path.join(self.models_path, 'pos.model')
        postagger = Postagger()
        postagger.load(pos_model_path)
        return postagger

    def _key_word(self,comment):
        words = [word for word in self.segmentor.segment(comment) if word not in stop_word]
        postags = self.postagger.postag(words)
        dics = [{'word':words[i],'pos':postags[i]} for i in range(len(words))]
        return list(set([dic['word'] for dic in dics if dic['pos'] in ['n','v','a']]))

    def _viewpoint(self,comment):
        sts = SnowNLP(comment).sentiments
        if sts >= 0.6:
            return 'T'
        elif sts <0.6 and sts >=0.4:
            return 'M'
        else:
            return 'B'

    def process_item(self, item, spider):
        data = dict(item)
        data['source'] = spider.name
        data['crawl_date'] = str(datetime.now().date())
        data['key_word'] = self._key_word(data['comment'])
        date['viewpoint'] = self._viewpoint(data['comment'])
        result = json.dumps(json_context,ensure_ascii=False)
        send_data = str(result + '\n')
        self.conn.sendall(bytes(send_data, encoding="utf8"))
        self.conn.recv(1024*1024)
        return item

    def close_spider(self, spider):
        self.postagger.release()
        self.segmentor.release()
        self.conn.close()
