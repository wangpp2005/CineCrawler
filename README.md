# 豆瓣电影Top250 数据采集与分析系统

## 项目简介
本项目实现对豆瓣电影Top250榜单的全方位数据采集与深度分析。支持三种爬虫方案（Requests+BeautifulSoup、Selenium、Scrapy），获取电影详细信息（排名、标题、评分、评价人数、导演、主演、简介、上映年份、片长、类型、IMDb、前15条短评）并下载海报。基于Pandas进行数据清洗，Matplotlib和WordCloud生成6张可视化图表，SnowNLP完成短评情感分析。

## 技术栈
- **爬虫**：requests, beautifulsoup4, selenium, scrapy
- **数据分析**：pandas, numpy
- **可视化**：matplotlib, wordcloud
- **情感分析**：snownlp, jieba
- **存储**：pymysql (MySQL), csv

## 项目结构
```
douban-movie-analyzer/
├── main.py                 # 一键运行入口
├── crawler_base.py         # Requests+BS4 基础爬虫
├── crawler_detail.py       # Selenium 详情/短评/海报爬虫
├── analysis.py             # 数据清洗、统计、可视化
├── douban_scrapy/          # Scrapy 重构项目
├── requirements.txt        # 依赖列表
├── analysis_results/       # 输出图表和统计CSV
└── douban_top250/          # 爬取数据（详情CSV、短评、海报）
```

## 安装与运行
```bash
# 克隆项目
git clone https://github.com/your-team/douban-movie-analyzer.git
cd douban-movie-analyzer

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 一键运行（自动执行爬取+分析）
python main.py
```

> **注意**：如需使用MySQL，请先修改 `crawler_base.py` 和 `crawler_detail.py` 中的数据库密码。

## 输出结果
| 类型 | 路径 | 说明 |
|------|------|------|
| 图表 | `analysis_results/*.png` | 评分分布、类型饼图、散点图、词云、年份趋势、情感饼图 |
| 统计CSV | `analysis_results/*.csv` | TOP10电影、导演排行、类型分布、相关系数、情感分布 |
| 详情数据 | `douban_top250/movie_detail.csv` | 年份、片长、类型、IMDb等 |
| 短评 | `douban_top250/comments_csv/` | 每部电影前15条短评（CSV） |
| 海报 | `douban_top250/posters/` | 电影海报图片 |

## 部分结果示例
- **评分分布**：主要集中在8.5-9.0分
- **类型占比**：剧情片44.8%，喜剧19.2%
- **情感分析**：正面68%，中性22%，负面10%
- **性能对比**：Scrapy耗时约3.5分钟，Requests+Selenium约9分钟

## 团队分工
| 成员 | 任务 |
|------|------|
| 许禄苗 | 基础爬虫、Selenium动态处理、MySQL存储、海报下载 |
| 高钦| Scrapy重构、反爬策略、日志与异常处理 |
| 王奕涵 | 数据清洗、统计分析、可视化、情感分析、报告、PPT |

## 注意事项
- 请遵守豆瓣 `robots.txt`，本项目仅用于学习研究。
- 爬虫已设置随机延时（1-4秒），请勿过度请求。
- 如遇到反爬封禁，可尝试增加延时或使用代理。

## 许可证
MIT License。数据版权归豆瓣所有，请勿用于商业用途。
