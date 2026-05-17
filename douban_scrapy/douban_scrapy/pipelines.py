# -*- coding: utf-8 -*-
import csv
import os
import pymysql
import logging
import re
import requests
from datetime import datetime

logger = logging.getLogger(__name__)
from douban_scrapy.items import MovieItem, CommentItem


class CsvExportPipeline:
    """批量保存到CSV"""

    def __init__(self, csv_path='output', batch_size=25):
        self.csv_path = csv_path
        self.batch_size = batch_size
        self.movie_buffer = []
        self.detail_buffer = []
        self.saved_ranks = set()
        self.movie_file = None
        self.movie_writer = None
        self.detail_file = None
        self.detail_writer = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            csv_path=crawler.settings.get('CSV_EXPORT_PATH', 'output'),
            batch_size=crawler.settings.get('BATCH_SIZE', 25)
        )

    def open_spider(self, spider):
        os.makedirs(self.csv_path, exist_ok=True)

        # 覆盖写入（每次运行重新生成）
        movie_csv = os.path.join(self.csv_path, '豆瓣TOP250完整数据.csv')
        self.movie_file = open(movie_csv, 'w', newline='', encoding='utf-8-sig')
        movie_fields = ['排名', '中文标题', '外文标题', '评分', '评价人数', '导演', '主演', '简介', '详情链接']
        self.movie_writer = csv.DictWriter(self.movie_file, fieldnames=movie_fields)
        self.movie_writer.writeheader()

        detail_csv = os.path.join(self.csv_path, 'movie_detail.csv')
        self.detail_file = open(detail_csv, 'w', newline='', encoding='utf-8-sig')
        detail_fields = ['排名', '中文标题', '外文标题', '上映年份', '片长', '类型', 'IMDb', '详情链接']
        self.detail_writer = csv.DictWriter(self.detail_file, fieldnames=detail_fields)
        self.detail_writer.writeheader()

        self.comment_folder = os.path.join(self.csv_path, 'comments_csv')
        os.makedirs(self.comment_folder, exist_ok=True)

        spider.logger.info(f"CSV批量保存已启动，批量大小: {self.batch_size}")

    def process_item(self, item, spider):
        if isinstance(item, MovieItem):
            rank = item.get('rank')
            if rank in self.saved_ranks:
                return item
            self.saved_ranks.add(rank)

            # 构建电影数据行
            movie_row = {
                '排名': rank,
                '中文标题': item.get('title_cn', ''),
                '外文标题': item.get('title_en', ''),
                '评分': item.get('score', ''),
                '评价人数': item.get('vote_num', ''),
                '导演': item.get('director', ''),
                '主演': item.get('actor', ''),
                '简介': item.get('intro', ''),
                '详情链接': item.get('link', '')
            }
            self.movie_buffer.append(movie_row)

            # 构建详情数据行
            detail_row = {
                '排名': rank,
                '中文标题': item.get('title_cn', ''),
                '外文标题': item.get('title_en', ''),
                '上映年份': item.get('year', ''),
                '片长': item.get('runtime', ''),
                '类型': item.get('genre', ''),
                'IMDb': item.get('imdb', ''),
                '详情链接': item.get('link', '')
            }
            self.detail_buffer.append(detail_row)

            # 达到批量大小时写入
            if len(self.movie_buffer) >= self.batch_size:
                self._flush_csv()

        elif isinstance(item, CommentItem):
            # 短评立即保存（不批量）
            self._save_comment_csv(item)

        return item

    def _flush_csv(self):
        """批量写入CSV"""
        if self.movie_buffer:
            for row in self.movie_buffer:
                self.movie_writer.writerow(row)
            self.movie_file.flush()
            logger.info(f"批量写入 {len(self.movie_buffer)} 条电影数据到CSV")
            self.movie_buffer.clear()

        if self.detail_buffer:
            for row in self.detail_buffer:
                self.detail_writer.writerow(row)
            self.detail_file.flush()
            logger.info(f"批量写入 {len(self.detail_buffer)} 条详情数据到CSV")
            self.detail_buffer.clear()

    def _save_comment_csv(self, item):
        """保存短评到CSV"""
        clean_title = re.sub(r'[\\/*?:"<>|]', '_', item.get('movie_title', '未知'))
        comment_csv = os.path.join(self.comment_folder, f'{clean_title}.csv')
        file_exists = os.path.exists(comment_csv)
        with open(comment_csv, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['序号', '评论者', '评分', '内容', '时间'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                '序号': item.get('comment_index', ''),
                '评论者': item.get('username', ''),
                '评分': item.get('score', ''),
                '内容': item.get('content', ''),
                '时间': item.get('comment_time', '')
            })

    def _sort_csv_by_rank(self):
        """按排名排序CSV文件"""
        movie_csv = os.path.join(self.csv_path, '豆瓣TOP250完整数据.csv')
        if os.path.exists(movie_csv):
            with open(movie_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                rows.sort(key=lambda x: int(x['排名']))

            with open(movie_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            logger.info(f"已按排名排序: {movie_csv}")

        detail_csv = os.path.join(self.csv_path, 'movie_detail.csv')
        if os.path.exists(detail_csv):
            with open(detail_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                rows.sort(key=lambda x: int(x['排名']))

            with open(detail_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            logger.info(f"已按排名排序: {detail_csv}")

    def close_spider(self, spider):
        # 写入剩余数据
        self._flush_csv()

        # 对CSV文件按排名排序
        self._sort_csv_by_rank()

        if self.movie_file:
            self.movie_file.close()
        if self.detail_file:
            self.detail_file.close()
        spider.logger.info(f"CSV导出完成，共保存 {len(self.saved_ranks)} 部电影")


class MySQLPipeline:
    """批量保存到MySQL"""

    def __init__(self, host, user, password, database, batch_size=25):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.batch_size = batch_size
        self.connection = None
        self.cursor = None
        self.saved_ranks = set()
        self.movie_buffer = []
        self.detail_buffer = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST', '127.0.0.1'),
            user=crawler.settings.get('MYSQL_USER', 'root'),
            password=crawler.settings.get('MYSQL_PASSWORD', '123456'),
            database=crawler.settings.get('MYSQL_DATABASE', 'douban_movie1'),
            batch_size=crawler.settings.get('BATCH_SIZE', 25)
        )

    def open_spider(self, spider):
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            charset='utf8mb4'
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4")
        self.cursor.execute(f"USE `{self.database}`")

        # TRUNCATE 不支持 IF EXISTS，需要先检查表是否存在
        self.cursor.execute("SHOW TABLES LIKE 'top250'")
        if self.cursor.fetchone():
            self.cursor.execute("TRUNCATE TABLE top250")

        self.cursor.execute("SHOW TABLES LIKE 'top250_detail'")
        if self.cursor.fetchone():
            self.cursor.execute("TRUNCATE TABLE top250_detail")

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS top250 (
            id INT PRIMARY KEY AUTO_INCREMENT,
            movie_rank INT,
            title_cn VARCHAR(255),
            title_en VARCHAR(500),
            score VARCHAR(50),
            vote_num VARCHAR(50),
            director TEXT,
            actor TEXT,
            intro TEXT,
            link TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS top250_detail (
            movie_rank INT PRIMARY KEY,
            title_cn VARCHAR(255),
            title_en VARCHAR(500),
            year VARCHAR(20),
            runtime VARCHAR(255),
            genre VARCHAR(255),
            imdb VARCHAR(50),
            link TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        self.connection.commit()
        spider.logger.info(f"MySQL批量保存已启动，批量大小: {self.batch_size}")

    def process_item(self, item, spider):
        if isinstance(item, MovieItem):
            rank = item.get('rank')
            if rank in self.saved_ranks:
                return item
            self.saved_ranks.add(rank)

            # 添加到批量缓冲区
            self.movie_buffer.append((
                rank,
                item.get('title_cn', ''),
                item.get('title_en', ''),
                item.get('score', ''),
                item.get('vote_num', ''),
                item.get('director', ''),
                item.get('actor', ''),
                item.get('intro', ''),
                item.get('link', '')
            ))

            self.detail_buffer.append((
                rank,
                item.get('title_cn', ''),
                item.get('title_en', ''),
                item.get('year', ''),
                item.get('runtime', ''),
                item.get('genre', ''),
                item.get('imdb', ''),
                item.get('link', '')
            ))

            # 达到批量大小时提交
            if len(self.movie_buffer) >= self.batch_size:
                self._flush_db()

        elif isinstance(item, CommentItem):
            # 短评立即保存到独立表
            self._save_comment_db(item)

        return item

    def _flush_db(self):
        """批量提交到数据库"""
        try:
            if self.movie_buffer:
                self.cursor.executemany("""
                INSERT INTO top250 (movie_rank, title_cn, title_en, score, vote_num, director, actor, intro, link)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, self.movie_buffer)
                logger.info(f"批量插入 {len(self.movie_buffer)} 条电影数据到MySQL")
                self.movie_buffer.clear()

            if self.detail_buffer:
                self.cursor.executemany("""
                INSERT INTO top250_detail (movie_rank, title_cn, title_en, year, runtime, genre, imdb, link)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                title_cn=VALUES(title_cn), title_en=VALUES(title_en),
                year=VALUES(year), runtime=VALUES(runtime), genre=VALUES(genre), imdb=VALUES(imdb)
                """, self.detail_buffer)
                logger.info(f"批量插入 {len(self.detail_buffer)} 条详情数据到MySQL")
                self.detail_buffer.clear()

            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"MySQL批量插入失败: {e}")

    def _save_comment_db(self, item):
        """保存短评到MySQL（每个电影独立表）"""
        movie_title = item.get('movie_title', '未知')
        safe_table_name = re.sub(r'[^0-9a-zA-Z\u4e00-\u9fa5]', '_', movie_title)
        safe_table_name = f"comments_{safe_table_name}"

        try:
            self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{safe_table_name}` (
                id INT PRIMARY KEY AUTO_INCREMENT,
                comment_index INT,
                username VARCHAR(255),
                score VARCHAR(50),
                content TEXT,
                comment_time VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            self.cursor.execute(f"""
            INSERT INTO `{safe_table_name}` 
            (comment_index, username, score, content, comment_time)
            VALUES (%s, %s, %s, %s, %s)
            """, (
                item.get('comment_index'),
                item.get('username'),
                item.get('score'),
                item.get('content'),
                item.get('comment_time')
            ))
            self.connection.commit()
        except Exception as e:
            logger.error(f"短评MySQL保存失败: {e}")

    def close_spider(self, spider):
        # 提交剩余数据
        self._flush_db()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        spider.logger.info(f"MySQL保存完成，共保存 {len(self.saved_ranks)} 部电影")


class PosterDownloadPipeline:
    """海报下载管道（批量下载）"""

    def __init__(self, poster_path='posters'):
        self.poster_path = poster_path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(poster_path=crawler.settings.get('POSTER_PATH', 'posters'))

    def open_spider(self, spider):
        os.makedirs(self.poster_path, exist_ok=True)

    def process_item(self, item, spider):
        if isinstance(item, MovieItem):
            url = item.get('poster_url')
            title = item.get('title_cn')
            if url and title:
                try:
                    clean = re.sub(r'[\\/*?:"<>|]', '_', title)
                    path = os.path.join(self.poster_path, f"{clean}.jpg")
                    if not os.path.exists(path):
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Referer': 'https://movie.douban.com/'
                        }
                        resp = requests.get(url, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            with open(path, 'wb') as f:
                                f.write(resp.content)
                            spider.logger.info(f"海报下载成功: {clean}.jpg")
                except Exception as e:
                    spider.logger.error(f"海报下载失败: {e}")
        return item