# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LyricalspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    url = scrapy.Field()

    title = scrapy.Field()

    hits = scrapy.Field()

    context = scrapy.Field()

    comment = scrapy.Field()

    comment_user = scrapy.Field()

    support = scrapy.Field()

    user_location = scrapy.Field()


