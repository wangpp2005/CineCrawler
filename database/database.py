# -*- coding: utf-8 -*-
import pymysql
import csv
import pandas as pd

def create_db():
    conn = pymysql.connect(host="localhost", user="root", password="你的密码", charset="utf8mb4")
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS douban_movie DEFAULT CHARACTER SET utf8mb4")
    conn.close()

def create_table():
    conn = pymysql.connect(host="localhost", user="root", password="你的密码", db="douban_movie", charset="utf8mb4")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INT PRIMARY KEY AUTO_INCREMENT,
        ranking INT,
        title VARCHAR(200),
        score FLOAT,
        votes INT,
        year INT,
        genre VARCHAR(100),
        runtime VARCHAR(50),
        url VARCHAR(300)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INT PRIMARY KEY AUTO_INCREMENT,
        movie_id INT,
        username VARCHAR(100),
        content TEXT,
        ctime VARCHAR(100),
        FOREIGN KEY (movie_id) REFERENCES movies(id)
    )
    ''')
    conn.commit()
    conn.close()

def save_movie(data):
    conn = pymysql.connect(host="localhost", user="root", password="你的密码", db="douban_movie", charset="utf8mb4")
    cursor = conn.cursor()
    sql = "INSERT INTO movies(ranking,title,score,votes,year,genre,runtime,url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, data)
    conn.commit()
    conn.close()

def export_csv():
    conn = pymysql.connect(host="localhost", user="root", password="你的密码", db="douban_movie", charset="utf8mb4")
    df = pd.read_sql("SELECT * FROM movies", conn)
    df.to_csv("movies_backup.csv", index=False, encoding="utf-8-sig")
    conn.close()
    print("已导出CSV备份")

if __name__ == "__main__":
    create_db()
    create_table()
    print("数据库初始化完成")