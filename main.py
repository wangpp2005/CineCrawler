# -*- coding: utf-8 -*-
"""
豆瓣电影Top250 爬虫+存储+分析 一键运行主程序
项目入口文件
"""
import time
import os
print("=" * 60)
print("🚀 豆瓣电影Top250 数据采集与分析系统 启动")
print("=" * 60)

# 1. 运行基础爬虫（requests）
print("\n【1/5】开始爬取 豆瓣Top250 列表页...")
import crawler_base
crawler_base.main()
time.sleep(2)

# 2. 初始化数据库
print("\n【2/5】初始化 MySQL 数据库与数据表...")
import database
database.create_db()
database.create_table()
time.sleep(1)

# 3. 爬取详情、短评、下载海报
print("\n【3/5】开始爬取详情页、短评、下载海报...")
import crawler_detail
print("✅ 详情页/短评/海报模块 加载完成")
time.sleep(1)

# 4. 数据清洗 + 可视化 + 词云
print("\n【4/5】开始数据分析与图表生成...")
import analysis
time.sleep(1)

# 5. 导出备份
print("\n【5/5】导出CSV备份文件...")
database.export_csv()

print("\n" + "=" * 60)
print("✅ 全部任务执行完成！")
print("📊 生成文件：")
print("   - douban_top250.csv")
print("   - movies_backup.csv")
print("   - posters/ 海报文件夹")
print("   - score_dist.png / top10.png / wordcloud.png")
print("=" * 60)