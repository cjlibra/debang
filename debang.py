#!/usr/bin/env python
# -*- coding: utf-8 -*-

'a server example which send hello to client.'

import time, socket, threading
import random
import binascii
import hashlib
import time
import string
import MySQLdb as mdb
import threading
import sys
import signal
import os


def make_auth_req():
    b = [] 
    b.append('\xAA')
    b.append('\x00')
    b.append('\x15')
    b.append('\x46')
    for x in range(0,16):
       a = random.randint(0,255)
       b.append("%c"%(a))

    b.append('\xEE')
    c = ''.join(b)
    return c

def make_auth_succ():
    b = [] 
    b.append('\xAA')
    b.append('\x00')
    b.append('\x06')
    b.append('\x48')
    b.append('\x01')
    b.append('\xEE')
    c = ''.join(b)
    return c
    

def makemd5(s):
    m2 = hashlib.md5()
    m2.update(s)
    ret = m2.hexdigest()
    ret = binascii.unhexlify(ret)
    return ret
     
    
def tcplink(sock, addr,con):
    auth_req = make_auth_req()
    sock.send(auth_req)
    starttime = time.time()
    while True :
        data = sock.recv(1024)
        if len(data) != 21 :
            if time.time()-starttime >= 10 :
                 print "timeout no auth_res\n"
                 sock.close()
                 return
            continue
        if data[3] != '\x47' :
            if time.time()-starttime >= 10 :
                 print "timeout no auth_res\n"
                 sock.close()
                 return
            continue
        break
        md5str = makemd5(data[4:20])
    if auth_req[4:20] != md5str[0:16] :
        print "md5 wrong\n"
        sock.close()
        return
    succ = make_auth_succ()
    sock.send(succ)   
    ptime = time.time()
    while True :
       if time.time()-ptime > 300 :
            print "timeout no heart"
            return
       data = sock.recv(1024)
       if data[3]=='5A' :
           jqid = string(data[6:14])
           eids,eidstime = takeeids(data) 
           dealwithdb(jqid,eids,eidstime,con)

       if data[3]=='50' :
           ptime = time.time()
           b = b"\xAA\x00\x06\x50\x01\xEE"
           sock.send(b)

def checkdb(con) :
    while True :
        cur = con.cursor()
        cur.execute("select id,jqid,eid,time from info where unix_timestamp(time) < UNIX_TIMESTAMP(Now())-300")
        results = cur.fetchall()
        for row in results:
            rowid = row[0]
            jqid = row[1]
            eid = row[2]
            ttime = row[3]
            cur.execute("insert into io(jqid,eid,time,status) values('%s','%s','%s',%d)" % (jqid,eid, ttime,0))
        con.commit()
        time.sleep(10)

def dealwithdb(jqid,eids,eidstime,con) :
    cur = con.cursor()
    for i in range(0,len(eids)) :
        cur.execute("select * from info where jqid='%s' and eid='%s' " % (jqid,eids[i]))
        numrows = int(cur.rowcount)
        if numrows<=0 :
            cur.execute("insert into info(jqid,eid,time) values('%s','%s','%s',%d)" % (jqid,eids[i], time.strftime("%Y-%m-%d %X", time.localtime(eidstime[i]))))
            cur.execute("insert into io(jqid,eid,time,status) values('%s','%s','%s',%d)" % (jqid,eids[i], time.strftime("%Y-%m-%d %X", time.localtime(eidstime[i])),1))
        else :
            cur.execute("update info set time='%s' where jqid='%s' and eid='%s' " % (time.localtime(eidstime[i]),jqid,eids[i])) 
    con.commit()

def takeeids(data) :
    num = ord(data[4])*256+ord(data[5])
    eids = []
    eidstime = []
    for i in range(0,num) :
        eids.append(string(data[14+12*i:14+12*i+8*(i+1)]))
        eidstime.append(makebyte4toint(data[14+12*i+8*(i+1):14+12*i+8*(i+1)+4]))
    return eids ,eidstime

def makebyte4toint(b) :
    numint = ord(b[0])*256*3+ord(b[1])*256*2+ord(b[2])*256+ord(b[3])
    return numint



def myhandle(n=0,e=0) :
    print "catch ctrl+c ,exit!"
    #sys.exit()
    os._exit(-1)

if __name__ == "__main__" :
    signal.signal(signal.SIGINT,myhandle)
    try :
        con = mdb.connect("localhost","root","root123root","debang")
    except Exception,e:  
            print Exception,":",e

    t1 = threading.Thread(target=checkdb,args=(con,))
    t1.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 监听端口:
    s.bind(('127.0.0.1', 9999))
    s.listen(5)
    print 'Waiting for connection...'
    while True:
        # 接受一个新连接:
        sock, addr = s.accept()
        # 创建新线程来处理TCP连接:
        t = threading.Thread(target=tcplink, args=(sock, addr,con))
        t.start()
