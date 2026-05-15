# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import csv
import os
import pymysql

MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"          # 请修改为您的 MySQL 密码

def init_database():
    """创建数据库和表（如果不存在）"""
    db = pymysql.connect(
        host="127.0.0.1",
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4"
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS douban_movie CHARACTER SET utf8mb4")
    cursor.execute("USE douban_movie")
    cursor.execute("""
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
    db.commit()
    cursor.close()
    db.close()
    print("数据库/表初始化完成（已存在则跳过）")

def clear_table():
    """清空 top250 表，重置自增 ID"""
    db = pymysql.connect(
        host="127.0.0.1",
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database="douban_movie",
        charset="utf8mb4"
    )
    cursor = db.cursor()
    cursor.execute("TRUNCATE TABLE top250")   # 清空并重置 AUTO_INCREMENT
    db.commit()
    cursor.close()
    db.close()
    print("已清空 top250 表，本次爬取将存入全新数据。")

def save_to_db(item):
    """保存单条电影数据到 MySQL"""
    db = pymysql.connect(
        host="127.0.0.1",
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database="douban_movie",
        charset="utf8mb4"
    )
    cursor = db.cursor()
    sql = """
    INSERT INTO top250 (movie_rank, title_cn, title_en, score, vote_num, director, actor, intro, link)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        item["排名"], item["中文标题"], item["外文标题"], item["评分"],
        item["评价人数"], item["导演"], item["主演"], item["简介"], item["详情链接"]
    ))
    db.commit()
    cursor.close()
    db.close()

def save_to_csv(item):
    """追加写入 CSV（由于主函数已删除旧文件，每次运行都是全新文件）"""
    filename = "豆瓣TOP250完整数据.csv"
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["排名", "中文标题", "外文标题", "评分", "评价人数", "导演", "主演", "简介", "详情链接"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(item)

def main():
    # 1. 覆盖 CSV：删除旧文件
    csv_filename = "豆瓣TOP250完整数据.csv"
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        print(f"已删除旧的 {csv_filename}，本次运行将重新生成。")

    # 2. 初始化数据库（建库建表）
    init_database()
    # 3. 清空表数据（保证每次运行数据是干净的）
    clear_table()

    # 4. 配置 Selenium 无头浏览器
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # 5. 分页爬取 Top250 列表
    for page in range(10):
        url = f"https://movie.douban.com/top250?start={page * 25}"
        print(f"\n正在爬取第 {page + 1} 页")
        driver.get(url)
        time.sleep(random.uniform(4, 6))

        movie_list = []
        items = driver.find_elements(By.CLASS_NAME, "item")

        for item in items:
            # 排名
            rank = item.find_element(By.CLASS_NAME, "pic").text.strip()

            # 标题（处理中英文）
            title_text = item.find_element(By.XPATH, ".//div[@class='hd']/a").text.strip()
            title_text = title_text.split("可播放")[0].split("不可播放")[0].split("预告片")[0].strip()
            title_cn = title_text
            title_en = ""
            if " / " in title_text:
                parts = title_text.split(" / ")
                title_cn = parts[0].strip()
                title_en = " / ".join(parts[1:]).strip()

            # 评分
            score = item.find_element(By.CLASS_NAME, "rating_num").text.strip()

            # 评价人数
            try:
                vote_num = item.find_element(By.XPATH, ".//span[contains(text(),'评价')]").text.strip()
            except:
                vote_num = "无"

            # 详情链接
            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")

            movie_list.append({
                "排名": rank,
                "中文标题": title_cn,
                "外文标题": title_en,
                "评分": score,
                "评价人数": vote_num,
                "导演": "",
                "主演": "",
                "简介": "",
                "详情链接": link
            })

        # 6. 遍历每部电影，进入详情页抓取额外信息
        for movie in movie_list:
            title = movie["中文标题"]
            link = movie["详情链接"]
            print(f"正在打开详情页：{title}")

            driver.get(link)
            time.sleep(random.uniform(4, 6))

            # 点击“更多”展开主演列表（如果存在）
            try:
                more_btn = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"更多")]'))
                )
                driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(2)
            except:
                pass

            # 点击“展开全部”按钮获取完整简介（关键修复）
            try:
                expand_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(text(),"展开全部")]'))
                )
                driver.execute_script("arguments[0].click();", expand_btn)
                time.sleep(2)
                print("  → 已点击“(展开全部)”按钮")
            except:
                print("  → 没有找到“(展开全部)”按钮，使用默认简介")

            # 抓取导演
            director = ""
            try:
                director = driver.find_element(By.XPATH, '//a[@rel="v:directedBy"]').text.strip()
            except:
                pass

            # 抓取主演
            actor = ""
            try:
                info_text = driver.find_element(By.ID, "info").text
                if "主演:" in info_text:
                    actor_part = info_text.split("主演:")[-1].split("\n")[0].strip()
                    actor = actor_part
            except:
                pass

            # 抓取完整简介：优先从 .all 区域获取（展开后的内容）
            intro = "暂无简介"
            try:
                all_intro = driver.find_element(By.CSS_SELECTOR, "span.all")
                intro = all_intro.text.strip()
                if "©豆瓣" in intro:
                    intro = intro.split("©豆瓣")[0].strip()
                print(f"  → 获取到完整简介（长度 {len(intro)}）")
            except:
                try:
                    intro = driver.find_element(By.XPATH, '//span[@property="v:summary"]').text.strip()
                    print(f"  → 使用默认简介（长度 {len(intro)}）")
                except:
                    pass

            # 更新电影数据
            movie["导演"] = director
            movie["主演"] = actor
            movie["简介"] = intro

            # 保存到 CSV 和 MySQL
            save_to_csv(movie)
            save_to_db(movie)

        time.sleep(random.uniform(4, 6))

    driver.quit()
    print("\n✅ 全部爬取完成！数据已保存至 CSV 和 MySQL（已覆盖旧数据）。")

if __name__ == "__main__":
    main()