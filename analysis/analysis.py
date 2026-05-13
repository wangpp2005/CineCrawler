# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 读取数据
df = pd.read_csv("douban_top250.csv")

# 清洗
df["评分"] = pd.to_numeric(df["评分"])
df = df.drop_duplicates(subset=["片名"])

# 1. 评分分布
plt.figure(figsize=(10,5))
plt.hist(df["评分"], bins=12, color="#4285F4", edgecolor="black")
plt.title("豆瓣Top250评分分布")
plt.xlabel("评分")
plt.ylabel("影片数量")
plt.savefig("score_dist.png", dpi=300)
plt.close()

# 2. 高分TOP10
top10 = df.sort_values("评分", ascending=False).head(10)
plt.figure(figsize=(12,6))
plt.barh(top10["片名"], top10["评分"], color="#34A853")
plt.title("评分TOP10电影")
plt.tight_layout()
plt.savefig("top10.png", dpi=300)
plt.close()

# 3. 词云
text = " ".join(df["片名"].astype(str))
words = jieba.lcut(text)
wc = WordCloud(font_path="simhei.ttf", width=1000, height=500, background_color="white").generate(" ".join(words))
wc.to_file("wordcloud.png")

print("图表与词云已生成完成！")