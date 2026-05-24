#  CineCrawler – 电影数据爬取与分析系统


##  项目简介

**CineCrawler** 是一个自动化电影数据爬取系统，旨在从主流电影网站（如豆瓣、IMDb）采集电影信息（包括片名、评分、上映时间、简介、导演、演员等），并进行简单的数据分析与展示。本项目为《爬虫与信息提取》课程大作业，完整实现了数据采集、清洗、存储及可视化功能。

---

##  功能特性

-  多页面并发爬取，效率高  
-  支持增量更新（避免重复爬取）  
-  数据自动清洗并存储至 SQLite / MySQL 数据库  
-  提供数据导出为 CSV / JSON 功能  
-  基础统计分析（评分分布、年份趋势等）  
-  命令行交互式查询（按电影名、导演搜索）

---

##  依赖库

本项目使用以下 Python 库（完整列表见 `requirements.txt`）：

| 库名 | 版本示例 | 用途说明 |
|------|----------|----------|
| `requests` | 2.31.0 | 发送 HTTP 请求，获取网页内容 |
| `beautifulsoup4` | 4.12.2 | 解析 HTML，提取电影信息 |
| `lxml` | 4.9.3 | 解析器引擎，配合 BeautifulSoup 使用 |
| `pandas` | 2.0.3 | 数据清洗、分析及导出 CSV/JSON |
| `matplotlib` | 3.7.2 | 生成统计图表（评分分布、年份趋势） |
| `numpy` | 1.24.3 | 数值计算，辅助统计分析 |
| `sqlalchemy` | 2.0.19 | 数据库 ORM，简化数据库操作 |
| `pymysql` | 1.1.0 | 连接 MySQL 数据库（若使用 MySQL） |
| `fake-useragent` | 1.4.0 | 随机生成 User-Agent，防止被封 |
| `retrying` | 1.3.4 | 自动重试失败的请求 |
| `python-dotenv` | 1.0.0 | 管理环境变量（如数据库密码） |
| `tqdm` | 4.66.1 | 显示爬取进度条 |
| `chardet` | 5.1.0 | 自动检测网页编码 |
| `urllib3` | 2.0.4 | `requests` 的底层依赖，处理连接池 |


---

##  技术栈

| 类别          | 技术                                 |
| ------------- | ------------------------------------ |
| 编程语言      | Python 3.9+                          |
| 爬虫框架      | Requests, BeautifulSoup4, Scrapy (可选) |
| 数据解析      | lxml, re, json                       |
| 数据库        | SQLite3（默认）/ MySQL（可选）       |
| 数据分析      | Pandas, Matplotlib                   |
| 版本控制      | Git + GitHub                         |
| 协作流程      | Git Flow（`main`, `dev`, `feature/*`） |

---

##  项目结构

```
CineCrawler/
├── .gitignore              # Git 忽略文件配置
├── README.md               # 项目说明文档
├── requirements.txt        # Python 依赖包列表
├── db_dump.sql             # 数据库初始数据 dump 文件（SQLite 或 MySQL）
├── config.py               # 配置文件（数据库连接、爬虫参数等）
├── main.py                 # 程序入口
├── crawler/                # 爬虫模块
│   ├── __init__.py
│   ├── douban.py           # 豆瓣爬虫
│   ├── imdb.py             # IMDb 爬虫（示例）
│   └── utils.py            # 通用工具函数（请求头、代理、重试）
├── data/                   # 数据存储目录（CSV/JSON 导出文件）
├── database/               # 数据库操作模块
│   ├── __init__.py
│   ├── models.py           # 数据表定义（ORM 或 SQL 语句）
│   └── db_manager.py       # 数据库增删改查封装
├── analysis/               # 数据分析模块
│   └── stats.py            # 统计与可视化
└── tests/                  # 单元测试
    └── test_crawler.py
```

---

##  安装与配置

### 1. 环境要求

- Python 3.9 或更高版本
- pip 包管理工具
- MySQL 5.7+（若使用 MySQL 作为后端数据库）

### 2. 克隆仓库

```bash
git clone https://github.com/your-username/CineCrawler.git
cd CineCrawler
```

### 3. 创建并激活虚拟环境

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```


### 5. 数据库配置

- **默认 SQLite**：无需额外配置，程序会自动在当前目录创建 `cinecrawler.db` 文件。  
- **使用 MySQL**：修改 `config.py` 中的数据库连接信息（主机、用户、密码、数据库名），并导入 `db_dump.sql`：
  ```bash
  mysql -u root -p your_database < db_dump.sql
  ```


### 6. 配置文件说明

编辑 `config.py`，可以调整以下参数：

```python
# 爬虫设置
CRAWL_DELAY = 1          # 请求间隔（秒），避免被封IP
USER_AGENT = "Mozilla/5.0 ..."
USE_PROXY = False        # 是否启用代理

# 数据库设置
DB_TYPE = "sqlite"       # "sqlite" 或 "mysql"
SQLITE_PATH = "cinecrawler.db"
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "cinecrawler"
}
```

---

##  使用方法

### 运行爬虫

```bash
python main.py
```

### 数据查询

```bash
python main.py -s "肖申克的救赎"
```

### 生成统计图表

会自动生成评分分布柱状图并保存为 `rating_hist.png`。

---

##  团队成员及分工

| 姓名   | 学号/工号 | 主要贡献                                                               |
| ------ | --------- | --------------------------------------------------------------------- |
| 许禄苗   | 2304300224  | 基础爬取模块、Selenium动态处理、海报下载、MySQL数据库设计与存储        |
| 高钦   | 2304300214  | Scrapy框架重构、反爬策略实现、日志与异常处理                            |
| 王奕涵   | 2304300213  | 数据分析与清洗、可视化图表、情感分析、报告撰写、Git仓库管理、演示PPT整合|

>  团队采用 **Git Flow** 协作：`main` 分支为稳定版本，`dev` 分支为日常集成，每位成员从 `dev` 拉取 `feature/xxx` 分支开发，完成后通过 Pull Request 合并，并保留合并记录。

---

##  分支协作痕迹说明

- 所有功能开发均在独立分支进行（如 `feature/douban_spider`、`feature/database`）。  
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范（如 `feat: add douban spider`、`fix: correct user-agent`）。  
- 合并前必须通过代码审查（Pull Request），且至少一位团队成员批准。  
- GitHub 仓库的 **Insights → Network** 可查看完整的分支历史与合并关系。

---

##  致谢

- 豆瓣电影、IMDb 提供公开数据  
- 课程老师与助教的指导  
- 开源社区提供的 Requests、BeautifulSoup 等优秀库
