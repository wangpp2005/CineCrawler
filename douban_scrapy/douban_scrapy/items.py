# -*- coding: utf-8 -*-
import scrapy


class MovieItem(scrapy.Item):
    """电影数据项"""
    rank = scrapy.Field()           # 排名
    title_cn = scrapy.Field()       # 中文标题
    title_en = scrapy.Field()       # 外文标题
    score = scrapy.Field()          # 评分
    vote_num = scrapy.Field()       # 评价人数
    director = scrapy.Field()       # 导演
    actor = scrapy.Field()          # 主演
    intro = scrapy.Field()          # 简介
    link = scrapy.Field()           # 详情链接
    year = scrapy.Field()           # 上映年份
    runtime = scrapy.Field()        # 片长
    genre = scrapy.Field()          # 类型
    imdb = scrapy.Field()           # IMDb
    poster_url = scrapy.Field()     # 海报URL


class CommentItem(scrapy.Item):
    """短评数据项"""
    movie_rank = scrapy.Field()     # 关联电影排名
    movie_title = scrapy.Field()    # 电影标题
    comment_index = scrapy.Field()  # 评论序号
    username = scrapy.Field()       # 评论者
    score = scrapy.Field()          # 评分
    content = scrapy.Field()        # 内容
    comment_time = scrapy.Field()   # 时间