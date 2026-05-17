# -*- coding: utf-8 -*-

BOT_NAME = 'douban_scrapy'
SPIDER_MODULES = ['douban_scrapy.spiders']
NEWSPIDER_MODULE = 'douban_scrapy.spiders'

ROBOTSTXT_OBEY = False

# 反爬虫优化配置
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# 下载延迟
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# 自动限速扩展
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

COOKIES_ENABLED = False

DOWNLOAD_TIMEOUT = 30

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 403, 408]

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 下载器中间件
DOWNLOADER_MIDDLEWARES = {
    'douban_scrapy.middlewares.SeleniumMiddleware': 1,
    'douban_scrapy.middlewares.RandomDelayMiddleware': 2,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
}

ITEM_PIPELINES = {
    'douban_scrapy.pipelines.CsvExportPipeline': 100,
    'douban_scrapy.pipelines.PosterDownloadPipeline': 200,
    'douban_scrapy.pipelines.MySQLPipeline': 300,
}

RETRY_ENABLED = False
DOWNLOAD_TIMEOUT = 60
LOG_LEVEL = 'INFO'

# MySQL配置
MYSQL_HOST = '127.0.0.1'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123456'
MYSQL_DATABASE = 'douban_movie1'

CSV_EXPORT_PATH = 'output'
POSTER_PATH = 'posters'

# 在文件末尾添加
BATCH_SIZE = 25  # 每25部电影批量保存一次