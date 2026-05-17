# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy import Request
from douban_scrapy.items import MovieItem, CommentItem


class DoubanTop250Spider(scrapy.Spider):
    name = 'douban_top250'
    allowed_domains = ['movie.douban.com']

    def __init__(self, start=None, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start) if start is not None else 0
        self.limit = int(limit) if limit is not None else 10
        self.logger.info(f"爬取设置: 起始页={self.start_page}, 爬取页数={self.limit}")

    def start_requests(self):
        """开始爬取"""
        for page in range(self.limit):
            url = f'https://movie.douban.com/top250?start={self.start_page + page * 25}'
            self.logger.info(f"准备请求URL: {url}")
            yield Request(url, meta={'page': page + 1}, dont_filter=True)

    def parse(self, response):
        page = response.meta.get('page', 1)
        self.logger.info(f"正在爬取第 {page} 页")

        items = response.xpath('//div[@class="item"]')
        for item in items:
            rank = item.xpath('.//div[@class="pic"]/em/text()').get()
            if not rank:
                continue
            rank = rank.strip()

            # 提取中文标题
            title_cn = item.xpath('.//div[@class="hd"]/a/span[1]/text()').get()
            title_cn = title_cn.strip() if title_cn else ''

            # 提取外文标题
            title_en = item.xpath('.//div[@class="hd"]/a/span[2]/text()').get()
            if title_en:
                title_en = title_en.strip(' /').strip()
            else:
                title_en = ''

            score = item.xpath('.//span[@class="rating_num"]/text()').get()
            score = score.strip() if score else ''

            # 评价人数
            vote_num = item.xpath('.//div[@class="star"]/span[4]/text()').get()
            if vote_num:
                vote_num = vote_num.replace('人评价', '').strip()
            else:
                vote_text = item.xpath('.//span[contains(text(),"评价")]/text()').get()
                if vote_text:
                    match = re.search(r'(\d+)', vote_text)
                    vote_num = match.group(1) if match else '无'
                else:
                    vote_num = '无'

            detail_url = item.xpath('.//div[@class="hd"]/a/@href').get()

            yield Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    'rank': rank,
                    'title_cn': title_cn,
                    'title_en': title_en,
                    'score': score,
                    'vote_num': vote_num,
                    'link': detail_url
                },
                dont_filter=True
            )

    def parse_detail(self, response):
        rank = response.meta['rank']
        title_cn = response.meta['title_cn']
        title_en = response.meta['title_en']
        score = response.meta['score']
        vote_num = response.meta['vote_num']
        link = response.meta['link']

        # 导演
        director = response.xpath('//a[@rel="v:directedBy"]/text()').get()
        director = director.strip() if director else ''

        # 主演
        actor = ''
        info_text = response.xpath('//div[@id="info"]//text()').getall()
        info_full = ''.join(info_text)
        if '主演:' in info_full:
            m = re.search(r'主演:(.+?)(?:\n|$)', info_full)
            if m:
                actor = m.group(1).strip()
                actor = re.sub(r'\s+', ' ', actor)
                actor = re.sub(r'更多\.\.\.$', '', actor).strip()

        if not actor:
            actors = response.xpath('//a[@rel="v:starring"]/text()').getall()
            if actors:
                actor = '/'.join(actors)

        # 简介
        intro = '暂无简介'
        all_intro = response.xpath('//span[@class="all"]/text()').get()
        if all_intro:
            intro = all_intro.strip()
            if '©豆瓣' in intro:
                intro = intro.split('©豆瓣')[0].strip()
        else:
            summary = response.xpath('//span[@property="v:summary"]/text()').get()
            if summary:
                intro = summary.strip()

        # 年份、片长、类型、IMDb
        year = ''
        runtime = ''
        genre = ''
        imdb = ''

        if info_full:
            year_match = re.search(r'(\d{4})', info_full)
            if year_match:
                year = year_match.group(1)

            runtime_match = re.search(r'片长:\s*(\d+)', info_full)
            if runtime_match:
                runtime = runtime_match.group(1) + '分钟'

            genre_match = re.search(r'类型:\s*([^\n]+)', info_full)
            if genre_match:
                genre = genre_match.group(1).strip()

            imdb_match = re.search(r'IMDb:\s*([^\n]+)', info_full)
            if imdb_match:
                imdb = imdb_match.group(1).strip()

        if not year:
            year_elem = response.xpath('//span[@class="year"]/text()').get()
            if year_elem:
                m = re.search(r'\d{4}', year_elem)
                year = m.group() if m else ''

        if not runtime:
            runtime_elem = response.xpath('//span[@property="v:runtime"]/@content').get()
            runtime = runtime_elem.strip() if runtime_elem else ''
            if runtime and not runtime.endswith('分钟'):
                runtime = runtime + '分钟'

        if not genre:
            genres = response.xpath('//span[@property="v:genre"]/text()').getall()
            genre = '/'.join(genres) if genres else ''

        if not imdb:
            imdb_elem = response.xpath('//a[contains(@href,"imdb")]/text()').get()
            imdb = imdb_elem.strip() if imdb_elem else ''

        # 海报URL
        poster = response.xpath('//div[@id="mainpic"]/a/img/@src').get()

        # 产出电影Item
        yield MovieItem(
            rank=rank,
            title_cn=title_cn,
            title_en=title_en,
            score=score,
            vote_num=vote_num,
            director=director,
            actor=actor,
            intro=intro,
            link=link,
            year=year,
            runtime=runtime,
            genre=genre,
            imdb=imdb,
            poster_url=poster
        )

        # 请求短评
        comment_url = response.url + 'comments?status=P'
        yield Request(
            url=comment_url,
            callback=self.parse_comments,
            meta={'movie_rank': rank, 'movie_title': title_cn},
            dont_filter=True
        )

    def parse_comments(self, response):
        """解析短评 - 修复评分提取"""
        movie_rank = response.meta['movie_rank']
        movie_title = response.meta['movie_title']

        # 只取前15条短评
        comments = response.xpath('//div[@class="comment-item"]')[:15]

        for idx, comment in enumerate(comments, 1):
            # 用户名
            username = comment.xpath('.//span[@class="comment-info"]/a/text()').get()
            username = username.strip() if username else '匿名用户'

            # 修复评分：从rating标签的title属性获取（如"力荐"、"推荐"、"还行"等）
            rating = comment.xpath('.//span[@class="rating"]/@title').get()
            if rating:
                rating = rating.strip()
            else:
                # 如果没有rating，尝试获取class中的星星数
                rating_class = comment.xpath('.//span[@class="rating"]/@class').get()
                if rating_class:
                    # 例如 "rating star5" 表示5星
                    star_match = re.search(r'star(\d)', rating_class)
                    if star_match:
                        star_num = star_match.group(1)
                        rating_map = {'5': '力荐', '4': '推荐', '3': '还行', '2': '较差', '1': '很差'}
                        rating = rating_map.get(star_num, '未评分')
                    else:
                        rating = '未评分'
                else:
                    rating = '未评分'

            # 评论时间
            c_time = comment.xpath('.//span[@class="comment-time"]/text()').get()
            c_time = c_time.strip() if c_time else ''

            # 评论内容
            content = comment.xpath('.//span[@class="short"]/text()').get()
            content = content.strip() if content else ''

            yield CommentItem(
                movie_rank=movie_rank,
                movie_title=movie_title,
                comment_index=idx,
                username=username,
                score=rating,
                content=content,
                comment_time=c_time
            )