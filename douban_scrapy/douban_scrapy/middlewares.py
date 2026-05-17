# -*- coding: utf-8 -*-
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse
from scrapy import signals
import logging

logger = logging.getLogger(__name__)


class CookieManager:
    """Cookie管理器"""

    def __init__(self):
        # 你提供的完整Cookie字符串
        self.cookies_str = 'bid=SxqQ23FKsiY; ll="118254"; _pk_id.100001.4cf6=5a679397a627728f.1778655672.; __yadk_uid=k4Rd3VvlDg0mg4Y9VQeZTaGI78J7H86z; _vwo_uuid_v2=D1E782EA7C8F6ED85AA6030CA36BF6CC9|98e552d17e9069b4c9d741ed3b74a943; FCCDCF=%5Bnull%2Cnull%2Cnull%2C%5B%22CQkTQMAQkTQMAEsACBZHCfFgALAAAELAAARoF5wAQF5gXnABAXmAAA.IF5wAQF5gA%22%2C%222~~dv.%22%2C%220E26CCBB-CEC5-4B2A-B64B-CEB0D61D550B%22%5D%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%2255f8412a-04a8-456f-a5f9-0584f73ab4fa%5C%22%2C%5B1778922418%2C447000000%5D%5D%22%5D%5D%5D; ap_v=0,6.0; __utma=30149280.441685713.1745222703.1778995187.1779000805.14; __utmb=30149280.0.10.1779000805; __utmc=30149280; __utmz=30149280.1779000805.14.7.utmcsr=sec.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=223695111.890769463.1778655672.1778995187.1779000805.13; __utmb=223695111.0.10.1779000805; __utmc=223695111; __utmz=223695111.1779000805.13.7.utmcsr=sec.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1779000805%2C%22https%3A%2F%2Fsec.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1'

        self.cookies = self._parse_cookies()
        logger.info(f"已加载 {len(self.cookies)} 个Cookie")

    def _parse_cookies(self):
        """解析Cookie字符串为字典"""
        cookies = {}
        for item in self.cookies_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        return cookies

    def get_cookies(self):
        """获取Cookie字典"""
        return self.cookies


class RandomDelayMiddleware:
    """随机延迟中间件"""

    def __init__(self):
        self.delays = [5, 6, 7, 8, 9, 10, 12, 15]

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        delay = random.choice(self.delays)
        logger.info(f"随机延迟 {delay} 秒...")
        time.sleep(delay)


class SeleniumMiddleware:
    """使用Selenium处理所有请求，绕过反爬"""

    def __init__(self):
        self.driver = None
        self.cookie_manager = CookieManager()

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        """启动浏览器 - 增强反检测"""
        chrome_options = Options()

        # 无头模式
        chrome_options.add_argument('--headless=new')

        # 禁用自动化控制标志
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 随机用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')

        # 禁用GPU和沙箱
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # 设置窗口大小
        chrome_options.add_argument('--window-size=1920,1080')

        # 禁用图片加载（提高速度，但海报下载仍可进行）
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
                'css': 1,
                'javascript': 1
            }
        }
        chrome_options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(options=chrome_options)

        # 先访问豆瓣首页，设置Cookie
        self.driver.get('https://movie.douban.com')

        # 添加Cookie
        for key, value in self.cookie_manager.get_cookies().items():
            try:
                self.driver.add_cookie({'name': key, 'value': value, 'domain': '.douban.com'})
            except Exception as e:
                logger.debug(f"添加Cookie失败 {key}: {e}")

        # 刷新页面使Cookie生效
        self.driver.refresh()
        time.sleep(2)

        # 执行JavaScript隐藏webdriver特征
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            '''
        })

        spider.driver = self.driver
        logger.info("Selenium浏览器已启动并配置Cookie")

    def spider_closed(self, spider):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium浏览器已关闭")

    def process_request(self, request, spider):
        """用Selenium获取页面内容"""
        url = request.url
        logger.info(f'加载页面: {url}')

        try:
            self.driver.get(url)

            # 如果是详情页，尝试点击展开按钮获取完整简介和更多信息
            if '/subject/' in url:
                try:
                    # 等待页面加载
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "info"))
                    )
                    time.sleep(random.uniform(1, 2))

                    # 点击"展开全部"按钮获取完整简介
                    try:
                        expand_btn = self.driver.find_elements(By.XPATH, '//a[contains(text(),"展开全部")]')
                        if expand_btn:
                            self.driver.execute_script("arguments[0].click();", expand_btn[0])
                            time.sleep(random.uniform(1, 2))
                            spider.logger.info("已点击'(展开全部)'按钮")
                    except Exception as e:
                        spider.logger.debug(f"展开全部按钮点击失败: {e}")

                    # 点击"更多"按钮展开主演列表
                    try:
                        more_btn = self.driver.find_elements(By.XPATH, '//*[contains(text(),"更多")]')
                        if more_btn:
                            self.driver.execute_script("arguments[0].click();", more_btn[0])
                            time.sleep(random.uniform(1, 2))
                            spider.logger.info("已点击'更多'按钮")
                    except Exception as e:
                        spider.logger.debug(f"更多按钮点击失败: {e}")

                except Exception as e:
                    spider.logger.debug(f"详情页展开操作失败: {e}")

            # 随机等待 5-12 秒
            wait_time = random.uniform(5, 12)
            logger.info(f'等待 {wait_time:.1f} 秒...')
            time.sleep(wait_time)

            # 模拟人类滚动行为
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            time.sleep(random.uniform(1, 2))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
            time.sleep(random.uniform(1, 2))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))

            # 检查反爬
            page_text = self.driver.page_source
            if 'sec.douban.com' in self.driver.current_url or '验证' in page_text or '检测到' in page_text:
                spider.logger.warning('检测到反爬，等待20秒后重试...')
                time.sleep(20)
                self.driver.get(url)
                time.sleep(10)

            # 构建Scrapy Response
            body = self.driver.page_source
            return HtmlResponse(
                url=url,
                body=body.encode('utf-8'),
                encoding='utf-8',
                request=request
            )

        except Exception as e:
            logger.error(f'Selenium加载失败: {e}')
            return HtmlResponse(
                url=url,
                status=500,
                request=request
            )