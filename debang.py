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
    data = ""
    while 1 :
        try :
            data = sock.recv(1024)
        except Exception , e :
            print "error sock", e
            return
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
    #print binascii.hexlify(auth_req)
    md5str = makemd5(auth_req[4:20])
    if data[4:20] != md5str[0:16] :
        print "md5 wrong\no"
        print binascii.hexlify(auth_req)
        print "\n"
        print binascii.hexlify(md5str)
        sock.close()
        return
    succ = make_auth_succ()
    sock.send(succ)   
    ptime = time.time()
    while 1 :
       if time.time()-ptime > 300 :
            print "timeout no heart"
            return
       try:
           data = sock.recv(1024)
           print binascii.hexlify(data)

       except Exception ,e :
           print "error sock1" , e
           return
       if data[3]=='\x5A' :
           jqid = (data[6:14])
           eids,eidstime = takeeids(data) 
           try :
               dealwithdb(jqid,eids,eidstime,con)
           except Exception , e:
               print e
               con.close()
               con = mdb.connect(host = "127.0.0.1",port = 3306,user = "root",passwd = "root123root",db = "debang")

       if data[3]=='\x50' :
           #print "50:"
           #print binascii.hexlify(data)
           ptime = time.time()
           b = b"\xAA\x00\x06\x51\x01\xEE"
           sock.send(b)

def checkdb(con) :
    while True :
        print "checkdbing..."
        con.ping(True)
        cur = con.cursor()
        cur.execute("select id,jqid,eid,time from info where unix_timestamp(time) < UNIX_TIMESTAMP(Now())-60")
        results = cur.fetchall()
        for row in results:
            rowid = row[0]
            jqid = row[1]
            eid = row[2]
            ttime =  time.strftime("%Y-%m-%d %X", time.localtime()) 
            cur.execute("insert into io(jqid,eid,time,status) values('%s','%s','%s',%d)" % (jqid,eid, ttime,0))
            cur.execute("delete from info where jqid = '%s' and eid = '%s' " % (jqid,eid))
            print eid
        con.commit()
        time.sleep(6)

def dealwithdb(jqid,eids,eidstime,con) :
    cur = con.cursor()
    for i in range(0,len(eids)) :
        cur.execute("select * from info where jqid='%s' and eid='%s' " % (jqid,eids[i]))
        numrows = int(cur.rowcount)
        if numrows<=0 :
            cur.execute("insert into info(jqid,eid,time) values('%s','%s','%s')" % (jqid,eids[i], time.strftime("%Y-%m-%d %X", time.localtime())))
            cur.execute("insert into io(jqid,eid,time,status) values('%s','%s','%s',%d)" % (jqid,eids[i], time.strftime("%Y-%m-%d %X", time.localtime()),1))
        else :
            cur.execute("update info set time='%s' where jqid='%s' and eid='%s' " % (time.strftime("%Y-%m-%d %X",time.localtime()),jqid,eids[i])) 
    con.commit()

def takeeids(data) :
    num = ord(data[4])*256+ord(data[5])
    eids = []
    eidstime = []
    for i in range(0,num) :
        eids.append((data[14+12*i:14+12*i+8*(i+1)]))
        eidstime.append(makebyte4toint(data[14+12*i+8*(i+1):14+12*i+8*(i+1)+4]))
    return eids ,eidstime

def makebyte4toint(b) :
    numint = ord(b[0])*256*256*256+ord(b[1])*256*256+ord(b[2])*256+ord(b[3])
    return numint



def myhandle(n=0,e=0) :
    print "catch ctrl+c ,exit!"
    #sys.exit()
    os._exit(-1)


def modify_buff_size():
        SEND_BUF_SIZE = 4096
        RECV_BUF_SIZE = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

        print "Buffer size [Before] :%d" %bufsize

        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_SNDBUF,
            SEND_BUF_SIZE
            )
        sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                RECV_BUF_SIZE
             )

        bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        print "Buffer size [After] :%d" %bufsize
        return sock

if __name__ == "__main__" :
    signal.signal(signal.SIGINT,myhandle)
    try :
        con = mdb.connect(host = "127.0.0.1",port = 3306,user = "root",passwd = "root123root",db = "debang")
    except Exception,e:  
            print Exception,":",e

    t1 = threading.Thread(target=checkdb,args=(con,))
    t1.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # s =  modify_buff_size()
    # 监听端口:
    s.bind(('0.0.0.0', 9999))
    s.listen(5)
    print 'Waiting for connection...,port:9999'
    while True:
        # 接受一个新连接:
        sock, addr = s.accept()
        # 创建新线程来处理TCP连接:
        t = threading.Thread(target=tcplink, args=(sock, addr,con))
        t.start()
