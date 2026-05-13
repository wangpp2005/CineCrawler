# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import random
import time
import csv
import os

# 请求头（防反爬）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win66; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]


# 获取页面
def get_page(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.text
        print(f"请求失败：{resp.status_code}")
        return None
    except Exception as e:
        print(f"异常：{e}")
        return None


# 解析一页（一次性爬取所有字段，导演、主演已拆分）
def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("div", class_="item")
    result = []

    for item in items:
        # 1. 排名
        rank = item.find("em").text.strip()

        # 2. 标题（中文 + 外文）
        title_tags = item.find_all("span", class_="title")
        title_cn = title_tags[0].text.strip()
        title_en = title_tags[1].text.strip().replace("/", "").strip() if len(title_tags) > 1 else ""

        # 3. 评分
        score = item.find("span", class_="rating_num").text.strip()

        # 4. 评价人数
        vote_elem = item.find(string=lambda x: x and "人评价" in x)
        vote_num = vote_elem.replace("人评价", "").strip() if vote_elem else "0"

        # 5. 导演 & 主演 拆分
        info_text = item.find("div", class_="bd").p.text.strip()
        director = ""
        actor = ""

        # 按换行分割，第一行是导演主演信息
        if "\n" in info_text:
            first_line = info_text.split("\n")[0].strip()
            # 按“主演:”拆分
            if "主演:" in first_line:
                director_part, actor_part = first_line.split("主演:", 1)
                director = director_part.replace("导演:", "").strip()
                actor = actor_part.strip()
            else:
                director = first_line.replace("导演:", "").strip()

        # 6. 简介
        quote_elem = item.find("span", class_="inq")
        intro = quote_elem.text.strip() if quote_elem else "暂无简介"

        # 7. 详情链接
        link = item.find("a")["href"]

        # 组装成一行数据（导演、主演分开）
        movie = {
            "排名": rank,
            "中文标题": title_cn,
            "外文标题": title_en,
            "评分": score,
            "评价人数": vote_num,
            "导演": director,
            "主演": actor,
            "简介": intro,
            "详情链接": link
        }
        result.append(movie)

    return result


# 保存CSV
def save_to_csv(data):
    filename = "豆瓣TOP250完整数据.csv"
    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)


# 主函数
def main():
    print("开始爬取 豆瓣电影Top250 完整数据...")

    # 删除旧文件，避免重复数据
    if os.path.exists("豆瓣TOP250完整数据.csv"):
        os.remove("豆瓣TOP250完整数据.csv")

    for i in range(10):
        url = f"https://movie.douban.com/top250?start={i * 25}&filter="
        html = get_page(url)
        if html:
            data = parse(html)
            save_to_csv(data)
            print(f"第 {i + 1} 页爬取完成")
        time.sleep(random.uniform(2, 4))

    print("\n全部爬取完成！文件：豆瓣TOP250完整数据.csv")


if __name__ == "__main__":
    main()