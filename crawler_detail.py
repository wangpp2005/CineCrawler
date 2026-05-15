# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv
import os
import pymysql
import re
import requests

# ====================== 配置 ======================
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
BASE_FOLDER = "douban_top250"
CSV_FOLDER = os.path.join(BASE_FOLDER, "comments_csv")
POSTER_FOLDER = os.path.join(BASE_FOLDER, "posters")
os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(POSTER_FOLDER, exist_ok=True)
CSV_FILE = os.path.join(BASE_FOLDER, "movie_detail.csv")

# ====================== 清空海报文件夹 ======================
def clear_posters():
    for f in os.listdir(POSTER_FOLDER):
        try:
            os.remove(os.path.join(POSTER_FOLDER, f))
        except:
            pass

# ====================== 主电影数据库：修复 runtime 加宽 ======================
def init_main_db():
    db = pymysql.connect(host="127.0.0.1", user=MYSQL_USER, password=MYSQL_PASSWORD, charset="utf8mb4")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS douban_movie")
    cursor.execute("USE douban_movie")
    cursor.execute("DROP TABLE IF EXISTS top250_detail")
    cursor.execute("""
    CREATE TABLE top250_detail (
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
    db.commit()
    cursor.close()
    db.close()

def clear_main_table():
    db = pymysql.connect(host="127.0.0.1", user=MYSQL_USER, password=MYSQL_PASSWORD, database="douban_movie", charset="utf8mb4")
    cursor = db.cursor()
    cursor.execute("TRUNCATE TABLE top250_detail")
    db.commit()
    cursor.close()
    db.close()

def save_main_to_db(item):
    db = pymysql.connect(host="127.0.0.1", user=MYSQL_USER, password=MYSQL_PASSWORD, database="douban_movie", charset="utf8mb4")
    cursor = db.cursor()
    sql = """INSERT INTO top250_detail (movie_rank, title_cn, title_en, year, runtime, genre, imdb, link)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    cursor.execute(sql, (
        item["排名"], item["中文标题"], item["外文标题"],
        item["上映年份"], item["片长"], item["类型"], item["IMDb"], item["详情链接"]
    ))
    db.commit()
    cursor.close()
    db.close()

# ====================== 短评数据库 ======================
def create_comment_table(table_name):
    db = pymysql.connect(host="127.0.0.1", user=MYSQL_USER, password=MYSQL_PASSWORD, database="douban_movie", charset="utf8mb4")
    cursor = db.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
    cursor.execute(f"""
    CREATE TABLE `{table_name}` (
        comment_index INT PRIMARY KEY,
        username VARCHAR(255),
        score VARCHAR(50),
        content TEXT,
        c_time VARCHAR(100)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    db.commit()
    cursor.close()
    db.close()

def save_comments_to_db(table_name, comments):
    db = pymysql.connect(host="127.0.0.1", user=MYSQL_USER, password=MYSQL_PASSWORD, database="douban_movie", charset="utf8mb4")
    cursor = db.cursor()
    for idx, c in enumerate(comments, start=1):
        sql = f"""INSERT INTO `{table_name}` (comment_index, username, score, content, c_time)
                  VALUES (%s,%s,%s,%s,%s)"""
        cursor.execute(sql, (idx, c["用户"], c["评分"], c["内容"], c["时间"]))
    db.commit()
    cursor.close()
    db.close()

# ====================== CSV保存 ======================
def init_main_csv():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    fieldnames = ["排名","中文标题","外文标题","上映年份","片长","类型","IMDb","详情链接"]
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=fieldnames).writeheader()

def save_main_to_csv(item):
    fieldnames = ["排名","中文标题","外文标题","上映年份","片长","类型","IMDb","详情链接"]
    row = {key: item[key] for key in fieldnames}
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=fieldnames).writerow(row)

def save_comments_to_csv(title_cn, comments):
    clean_title = re.sub(r'[\\/*?:"<>|]', "_", title_cn)
    csv_path = os.path.join(CSV_FOLDER, f"{clean_title}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["序号","评论者","评分","内容","时间"])
        writer.writeheader()
        for idx, c in enumerate(comments, 1):
            writer.writerow({
                "序号": idx,
                "评论者": c["用户"],
                "评分": c["评分"],
                "内容": c["内容"],
                "时间": c["时间"]
            })

# ====================== 下载海报 ======================
def save_poster(img_url, title_cn):
    if not img_url:
        return
    try:
        clean_name = re.sub(r'[\\/*?:"<>|]', "_", title_cn)
        img_path = os.path.join(POSTER_FOLDER, f"{clean_name}.jpg")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://movie.douban.com/"
        }
        res = requests.get(img_url, headers=headers, timeout=8)
        with open(img_path, "wb") as f:
            f.write(res.content)
    except Exception as e:
        pass

# ====================== 爬取信息 ======================
def get_movie_info(driver, url):
    driver.get(url)
    time.sleep(random.uniform(1.5, 2))
    info = driver.find_element(By.ID, "info").text

    img_url = ""
    try:
        img_url = driver.find_element(By.XPATH, '//div[@id="mainpic"]/a/img').get_attribute("src")
    except:
        pass

    year = runtime = genre = imdb = ""
    try:
        if "上映日期:" in info:
            year = info.split("上映日期:")[-1].split("\n")[0].strip()[:4]
    except:
        pass
    try:
        if "片长:" in info:
            runtime = info.split("片长:")[-1].split("\n")[0].strip()
    except:
        pass
    try:
        if "类型:" in info:
            genre = info.split("类型:")[-1].split("\n")[0].strip()
    except:
        pass
    try:
        if "IMDb:" in info:
            imdb = info.split("IMDb:")[-1].split("\n")[0].strip()
    except:
        pass

    comments = []
    try:
        driver.get(url + "comments?status=P")
        time.sleep(random.uniform(1, 1.5))
        items = driver.find_elements(By.CLASS_NAME, "comment-item")[:15]
        for item in items:
            try:
                user = item.find_element(By.CSS_SELECTOR, ".comment-info a").text.strip()
                score_tag = item.find_elements(By.CSS_SELECTOR, ".rating")
                score = score_tag[0].get_attribute("title") if score_tag else "无评分"
                c_time = item.find_element(By.CLASS_NAME, "comment-time").text.strip()
                content = item.find_element(By.CLASS_NAME, "short").text.strip()
                comments.append({"用户": user, "评分": score, "时间": c_time, "内容": content})
            except:
                continue
    except:
        pass

    return {"上映年份": year, "片长": runtime, "类型": genre, "IMDb": imdb, "短评": comments, "海报": img_url}

# ====================== 主程序 ======================
def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)

    init_main_db()
    clear_main_table()
    init_main_csv()
    clear_posters()
    print("初始化完成，开始爬取")

    for page in range(10):
        url = f"https://movie.douban.com/top250?start={page * 25}"
        print(f"\n第 {page + 1} 页")
        driver.get(url)
        time.sleep(random.uniform(2, 2.5))

        movie_list = []
        items = driver.find_elements(By.CLASS_NAME, "item")

        for item in items:
            rank = item.find_element(By.CLASS_NAME, "pic").text.strip()

            title_text = item.find_element(By.XPATH, ".//div[@class='hd']/a").text.strip()
            title_text = title_text.split("可播放")[0].split("不可播放")[0].split("预告片")[0].strip()
            title_cn = title_text
            title_en = ""
            if " / " in title_text:
                parts = title_text.split(" / ")
                title_cn = parts[0].strip()
                title_en = " / ".join(parts[1:]).strip()

            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
            movie_list.append({
                "排名": rank,
                "中文标题": title_cn,
                "外文标题": title_en,
                "详情链接": link
            })

        for movie in movie_list:
            cn_title = movie["中文标题"]
            print(f"正在处理：{cn_title}")

            info = get_movie_info(driver, movie["详情链接"])
            full_data = {**movie, **info}

            save_main_to_csv(full_data)
            save_main_to_db(full_data)
            save_poster(full_data["海报"], cn_title)

            comment_table_name = re.sub(r'[^0-9a-zA-Z\u4e00-\u9fa5]', "_", cn_title)
            create_comment_table(comment_table_name)
            save_comments_to_db(comment_table_name, info["短评"])
            save_comments_to_csv(cn_title, info["短评"])

        time.sleep(random.uniform(1.5, 2))

    driver.quit()
    print("\n全部爬取完成")

if __name__ == "__main__":
    main()