# -*- coding: utf-8 -*-
import scrapy

class MovieItem(scrapy.Item):
    rank = scrapy.Field()
    title = scrapy.Field()
    score = scrapy.Field()
    votes = scrapy.Field()
    url = scrapy.Field()

class DoubanSpider(scrapy.Spider):
    name = "douban"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://movie.douban.com/top250"]

    def parse(self, response):
        items = response.css("div.item")
        for item in items:
            mi = MovieItem()
            mi["rank"] = item.css("em::text").get()
            mi["title"] = item.css("span.title::text").get()
            mi["score"] = item.css("span.rating_num::text").get()
            mi["votes"] = item.css("div.star span:nth-child(4)::text").get().replace("人评价", "")
            mi["url"] = item.css("a::attr(href)").get()
            yield mi

        # 分页
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)