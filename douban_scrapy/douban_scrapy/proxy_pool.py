# -*- coding: utf-8 -*-
import random
import requests
import time
import logging

logger = logging.getLogger(__name__)


class ProxyPool:
    """免费代理IP池（从多个来源获取）"""

    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.failed_proxies = set()  # 记录失败的代理

    def fetch_free_proxies(self):
        """从免费代理网站获取代理IP"""
        proxies_list = []

        # 方案1: 从快代理获取免费代理
        try:
            url = "https://www.kuaidaili.com/free/inha/1/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # 注意：这里需要解析HTML，简单起见先用手动添加的代理
            pass
        except:
            pass

        # 方案2: 使用预设的免费代理（需要定期更新）
        # 这些代理从 https://free-proxy-list.net/ 获取
        default_proxies = [
            {'http': 'http://47.98.141.167:80', 'https': 'http://47.98.141.167:80'},
            {'http': 'http://47.104.27.43:80', 'https': 'http://47.104.27.43:80'},
            {'http': 'http://120.26.68.50:80', 'https': 'http://120.26.68.50:80'},
            {'http': 'http://47.105.125.100:80', 'https': 'http://47.105.125.100:80'},
            {'http': 'http://124.70.16.20:80', 'https': 'http://124.70.16.20:80'},
            {'http': 'http://47.111.6.202:80', 'https': 'http://47.111.6.202:80'},
            {'http': 'http://47.101.139.79:80', 'https': 'http://47.101.139.79:80'},
        ]

        self.proxies = default_proxies
        logger.info(f"已加载 {len(self.proxies)} 个代理IP")
        return self.proxies

    def get_random_proxy(self):
        """随机获取一个代理"""
        if not self.proxies:
            self.fetch_free_proxies()

        available = [p for p in self.proxies if str(p) not in self.failed_proxies]
        if available:
            self.current_proxy = random.choice(available)
            logger.info(f"使用代理: {self.current_proxy}")
            return self.current_proxy
        else:
            logger.warning("没有可用代理，将不使用代理")
            return None

    def mark_proxy_failed(self, proxy):
        """标记代理失败"""
        if proxy:
            self.failed_proxies.add(str(proxy))
            logger.warning(f"代理 {proxy} 已失效，剩余可用代理: {len(self.proxies) - len(self.failed_proxies)}")


# 全局代理池实例
proxy_pool = ProxyPool()


class ProxyMiddleware:
    """代理中间件"""

    def __init__(self):
        self.proxy_pool = proxy_pool
        self.proxy_pool.fetch_free_proxies()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        """为每个请求分配代理"""
        # 只对豆瓣请求使用代理
        if 'douban.com' in request.url:
            proxy = self.proxy_pool.get_random_proxy()
            if proxy:
                request.meta['proxy'] = proxy['http']
                # 保存代理信息，以便失败时标记
                request.meta['current_proxy'] = proxy

    def process_response(self, request, response, spider):
        """处理响应，检测代理是否有效"""
        if response.status in [403, 429, 500, 502, 503]:
            # 代理可能失效
            if 'current_proxy' in request.meta:
                self.proxy_pool.mark_proxy_failed(request.meta['current_proxy'])
        return response

    def process_exception(self, request, exception, spider):
        """处理请求异常"""
        if 'current_proxy' in request.meta:
            self.proxy_pool.mark_proxy_failed(request.meta['current_proxy'])
        return None