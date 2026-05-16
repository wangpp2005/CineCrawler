# -*- coding: utf-8 -*-
"""
数据分析与可视化模块（完整版）
- 输出所有图表到 analysis_results/ 文件夹
- 输出统计分析结果到 analysis_results/ 下的多个 CSV 文件
- 不生成 cleaned_movies.csv 等中间数据文件
"""

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import os
import glob

# 创建输出文件夹
output_dir = "analysis_results"
os.makedirs(output_dir, exist_ok=True)

# 可选：情感分析
try:
    from snownlp import SnowNLP

    SNOWNLP_AVAILABLE = True
except ImportError:
    SNOWNLP_AVAILABLE = False
    print("提示：未安装 snownlp，将跳过情感分析。如需使用请执行：pip install snownlp")

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ===================== 1. 加载数据 =====================
print("正在加载数据...")

base_df = pd.read_csv("豆瓣TOP250完整数据.csv", encoding="utf-8-sig")
print(f"Base CSV 加载完成，共 {len(base_df)} 条")

detail_path = "douban_top250/movie_detail.csv"
if os.path.exists(detail_path):
    detail_df = pd.read_csv(detail_path, encoding="utf-8-sig")
    print(f"详情文件加载完成，共 {len(detail_df)} 条")
    title_col = None
    for col in detail_df.columns:
        if "标题" in col or "title" in col.lower():
            title_col = col
            break
    if title_col is None:
        title_col = detail_df.columns[0]
    merged_df = pd.merge(base_df, detail_df, left_on="中文标题", right_on=title_col, how="left")
    print(f"合并后数据量：{len(merged_df)}")
else:
    merged_df = base_df.copy()
    print("未找到 movie_detail.csv，仅使用 base 数据")

comments_dir = "douban_top250/comments_csv/"
comment_texts = []
if os.path.exists(comments_dir):
    csv_files = glob.glob(os.path.join(comments_dir, "*.csv"))
    print(f"找到 {len(csv_files)} 个评论文件")
    for file in csv_files:
        try:
            comment_df = pd.read_csv(file, encoding="utf-8-sig")
            content_col = None
            for col in comment_df.columns:
                if "内容" in col or "content" in col.lower():
                    content_col = col
                    break
            if content_col:
                texts = comment_df[content_col].dropna().astype(str).tolist()
                comment_texts.extend(texts)
        except Exception as e:
            print(f"读取 {file} 失败：{e}")
    print(f"共加载 {len(comment_texts)} 条短评")
else:
    print("未找到 comments_csv 文件夹，跳过评论相关分析")

# ===================== 2. 数据清洗 =====================
print("\n正在进行数据清洗...")
merged_df["评分"] = pd.to_numeric(merged_df["评分"], errors="coerce")
if "评价人数" in merged_df.columns:
    merged_df["评价人数"] = merged_df["评价人数"].astype(str).str.replace("人评价", "").str.strip()
    merged_df["评价人数"] = pd.to_numeric(merged_df["评价人数"], errors="coerce")
if "上映年份" in merged_df.columns:
    merged_df["上映年份"] = pd.to_numeric(merged_df["上映年份"], errors="coerce")
else:
    merged_df["上映年份"] = 0
if "类型" not in merged_df.columns:
    merged_df["类型"] = "未知"
merged_df.drop_duplicates(subset=["中文标题"], keep="first", inplace=True)
merged_df.dropna(subset=["评分"], inplace=True)
print(f"清洗后有效数据：{len(merged_df)} 条")

# 注意：这里不保存 cleaned_movies.csv（按你的要求去掉）

# ===================== 3. 统计分析并保存到 CSV =====================
print("\n=== 统计分析 ===")

# 3.1 高分电影 TOP10
top10 = merged_df.nlargest(10, "评分")[["中文标题", "评分"]]
top10.to_csv(os.path.join(output_dir, "top10_movies.csv"), index=False, encoding="utf-8-sig")
print("评分 TOP10 电影：")
print(top10.to_string(index=False))

# 3.2 导演分布（如果有）
if "导演" in merged_df.columns:
    director_series = merged_df["导演"].dropna().str.split("/").explode().str.strip()
    top_directors = director_series.value_counts().head(10).reset_index()
    top_directors.columns = ["导演", "作品数量"]
    top_directors.to_csv(os.path.join(output_dir, "top_directors.csv"), index=False, encoding="utf-8-sig")
    print("\n作品数量最多的导演 TOP10：")
    print(top_directors)

# 3.3 类型分布
if "类型" in merged_df.columns and merged_df["类型"].iloc[0] != "未知":
    type_series = merged_df["类型"].dropna().str.split("/").explode().str.strip()
    type_counts = type_series.value_counts().reset_index()
    type_counts.columns = ["类型", "电影数量"]
    type_counts.to_csv(os.path.join(output_dir, "genre_distribution.csv"), index=False, encoding="utf-8-sig")
    print("\n类型分布 TOP10：")
    print(type_counts.head(10))
else:
    print("\n缺少类型数据，跳过类型分布保存")

# 3.4 评分与评价人数的相关性
if "评价人数" in merged_df.columns and merged_df["评价人数"].notna().any():
    corr_value = merged_df[["评分", "评价人数"]].corr().iloc[0, 1]
    corr_df = pd.DataFrame({"指标": ["评分与评价人数的相关系数"], "数值": [corr_value]})
    corr_df.to_csv(os.path.join(output_dir, "correlation.csv"), index=False, encoding="utf-8-sig")
    print(f"\n评分与评价人数的相关系数：{corr_value:.3f}")

# ===================== 4. 可视化（所有图片保存到 output_dir） =====================
print("\n正在生成图表...")

# 图1：评分分布直方图
plt.figure(figsize=(10, 5))
plt.hist(merged_df["评分"], bins=20, color="#4285F4", edgecolor="black", alpha=0.7)
plt.title("豆瓣Top250电影评分分布")
plt.xlabel("评分")
plt.ylabel("电影数量")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.savefig(os.path.join(output_dir, "score_distribution.png"), dpi=300, bbox_inches="tight")
plt.close()
print(f"已保存：{output_dir}/score_distribution.png")

# 图2：类型饼图
if "类型" in merged_df.columns and merged_df["类型"].iloc[0] != "未知":
    type_counts_top = type_series.value_counts().head(8)
    if type_counts_top.sum() < type_series.value_counts().sum():
        other_sum = type_series.value_counts().sum() - type_counts_top.sum()
        type_counts_top["其他"] = other_sum
    plt.figure(figsize=(10, 8))
    plt.pie(type_counts_top, labels=type_counts_top.index, autopct="%1.1f%%", startangle=90)
    plt.title("电影类型分布（Top8+其他）")
    plt.savefig(os.path.join(output_dir, "genre_pie.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"已保存：{output_dir}/genre_pie.png")
else:
    print("跳过类型饼图（缺少类型数据）")

# 图3：散点图
if "评价人数" in merged_df.columns and merged_df["评价人数"].notna().any():
    plt.figure(figsize=(10, 6))
    plt.scatter(merged_df["评分"], merged_df["评价人数"], alpha=0.6, c="#34A853")
    plt.title("评分与评价人数的关系")
    plt.xlabel("评分")
    plt.ylabel("评价人数")
    plt.yscale("log")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, "score_vs_votes_scatter.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"已保存：{output_dir}/score_vs_votes_scatter.png")
else:
    print("跳过散点图（缺少评价人数）")

# 图4：短评词云
if comment_texts:
    all_text = " ".join(comment_texts)
    words = jieba.lcut(all_text)
    stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "也", "很", "到", "说", "要", "去", "你",
                 "会", "着", "没有", "看", "好", "很", "电影", "这部", "片子", "一部"}
    words = [w for w in words if len(w) > 1 and w not in stopwords]
    text_for_wc = " ".join(words)
    # 如果找不到 simhei.ttf，可以注释 font_path 或指定其他字体
    wc = WordCloud(font_path="simhei.ttf", width=1000, height=500, background_color="white").generate(text_for_wc)
    wc.to_file(os.path.join(output_dir, "comments_wordcloud.png"))
    print(f"已保存：{output_dir}/comments_wordcloud.png")
else:
    print("跳过短评词云（无评论数据）")

# 图5：年份趋势线图
if "上映年份" in merged_df.columns and merged_df["上映年份"].notna().any() and (merged_df["上映年份"] > 1900).any():
    year_score = merged_df.groupby("上映年份")["评分"].mean().reset_index()
    year_score = year_score.sort_values("上映年份")
    plt.figure(figsize=(12, 6))
    plt.plot(year_score["上映年份"], year_score["评分"], marker="o", linestyle="-", color="#EA4335")
    plt.title("不同年份上映电影的平均评分趋势")
    plt.xlabel("上映年份")
    plt.ylabel("平均评分")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, "year_trend.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"已保存：{output_dir}/year_trend.png")
else:
    print("跳过年份趋势图（缺少年份数据）")

# ===================== 5. 情感分析（结果保存到 CSV + 饼图） =====================
if comment_texts and SNOWNLP_AVAILABLE:
    print("\n正在进行短评情感分析...")
    sentiments = []
    for text in comment_texts[:500]:
        s = SnowNLP(text)
        score = s.sentiments
        if score >= 0.6:
            sentiments.append("正面")
        elif score <= 0.4:
            sentiments.append("负面")
        else:
            sentiments.append("中性")
    sentiment_counts = pd.Series(sentiments).value_counts().reset_index()
    sentiment_counts.columns = ["情感", "评论数量"]
    sentiment_counts.to_csv(os.path.join(output_dir, "sentiment_distribution.csv"), index=False, encoding="utf-8-sig")
    print("情感分布：")
    print(sentiment_counts)

    plt.figure(figsize=(8, 8))
    plt.pie(sentiment_counts["评论数量"], labels=sentiment_counts["情感"], autopct="%1.1f%%", startangle=90,
            colors=["#34A853", "#FBBC05", "#EA4335"])
    plt.title("短评情感分析（正面/中性/负面）")
    plt.savefig(os.path.join(output_dir, "sentiment_pie.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"已保存：{output_dir}/sentiment_pie.png")
elif comment_texts and not SNOWNLP_AVAILABLE:
    print("跳过情感分析（未安装 snownlp）")
else:
    print("跳过情感分析（无评论数据）")

print(f"\n===== 全部完成！结果已保存到文件夹：{output_dir}/ =====")
print("统计结果 CSV 文件：")
print("  - top10_movies.csv")
print("  - top_directors.csv (如果有导演数据)")
print("  - genre_distribution.csv (如果有类型数据)")
print("  - correlation.csv")
print("  - sentiment_distribution.csv (如果有情感分析)")