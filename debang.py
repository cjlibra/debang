#!/usr/bin/env python
# -*- coding: utf-8 -*-

'a server example which send hello to client.'

import time, socket, threading
import random
import binascii
import hashlib
import time

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
     
    
def tcplink(sock, addr):
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
    while 1 :
       data = sock.recv(1024)





s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 监听端口:
s.bind(('127.0.0.1', 9999))
s.listen(5)
print 'Waiting for connection...'
while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()
