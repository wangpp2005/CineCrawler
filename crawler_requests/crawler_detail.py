# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time

# 伪装成浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ==========================
# 1. 爬取详情（年份、片长、类型、IMDb）
# ==========================
def get_detail(url):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    info = soup.find("div", id="info")

    year = soup.find("span", property="v:initialReleaseDate").text[:4]
    runtime = soup.find("span", property="v:runtime").text
    genre = soup.find("span", property="v:genre").text

    imdb = ""
    for span in soup.find_all("span"):
        if "IMDb:" in span.text:
            imdb = span.next_sibling.strip()

    return {
        "上映年份": year,
        "片长": runtime,
        "类型": genre,
        "IMDb评分": imdb
    }


# ==========================
# 2. 爬取15条短评（用户、评分、内容、时间）
# ==========================
def get_comments(url):
    res = requests.get(url + "comments?status=P", headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find_all("div", class_="comment-item")[:15]

    comments = []
    for item in items:
        user = item.find("span", class_="comment-info").a.text
        c_time = item.find("span", class_="comment-time").text.strip()
        content = item.find("span", class_="short").text

        try:
            score = item.find("span", class_="rating")["title"]
        except:
            score = "无评分"

        comments.append({
            "用户": user,
            "评分": score,
            "时间": c_time,
            "内容": content
        })
    return comments


# ==========================
# 3. 下载海报（保存到桌面，绝对能找到）
# ==========================
def download_poster(url, name):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    img_url = soup.find("div", id="mainpic").find("img")["src"]

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    folder = os.path.join(desktop, "posters")
    os.makedirs(folder, exist_ok=True)

    img_data = requests.get(img_url, headers=headers).content
    path = os.path.join(folder, f"{name}.jpg")

    with open(path, "wb") as f:
        f.write(img_data)

    print("海报已保存到桌面！")


# ==========================
# 运行（满足作业所有要求）
# ==========================
if __name__ == "__main__":
    test_url = "https://movie.douban.com/subject/1292064/"

    print("=== 电影详情 ===")
    print(get_detail(test_url))

    print("\n=== 短评 ===")
    for c in get_comments(test_url):
        print(c)

    print("\n=== 下载海报 ===")
    download_poster(test_url, "肖申克的救赎")