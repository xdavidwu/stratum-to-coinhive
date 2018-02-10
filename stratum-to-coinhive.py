#!/usr/bin/python

# Stratum to Coinhive proxy
# 
#  currently no multiple miners support

from websocket import create_connection
import json
import socket
import threading
import time
import uuid

site_key=""
ws_url="wss://ws001.coinhive.com/proxy"
user=""
bind_address=''
bind_port=3333
debug=False

def debugPrint(str):
    if debug:
        print(str)

def sendJob(mcsock,mws):
    while True:
        mes=mcsock.recv(1024)
        debugPrint("from miner "+mes+"\n")
        if "submit" in mes:
            djob=json.loads(mes)
            nid=djob['id']
            djob['params'].pop('id')
            cjob=json.dumps({"type":"submit","params":djob['params']})
            mws.send(cjob)
            debugPrint("upload "+cjob+"\n")
    
ws=create_connection(ws_url)
nid=1
uid=str(uuid.uuid4())

ssock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
ssock.bind((bind_address,bind_port))
ssock.listen(1)
(csock,addr)=ssock.accept()

debugPrint(csock.recv(1024)) #should be login
#auth
ws.send("{\"type\":\"auth\",\"params\":{\"site_key\":\""+site_key+"\",\"type\":\"user\",\"user\":\""+user+"\",\"goal\":0}}")
authmsg=ws.recv()
debugPrint("recieve "+authmsg+"\n")
inith=json.loads(authmsg)['params']['hashes']
prevh=inith

thr=threading.Thread(target=sendJob,args=(csock,ws))
thr.setDaemon(True)
thr.start()

job=ws.recv()
debugPrint("recieve "+job+"\n")
jjob=json.loads(job)
sjob=json.dumps({"id":1,"jsonrpc":"2.0","error":None,"result":{"id":uid,"job":jjob['params'],"status":"OK"}})
debugPrint("to miner "+sjob+"\n")
csock.send(sjob+"\n")
initt=time.time()
prevt=initt
while True:
    try:
        job=ws.recv()
        debugPrint("recieve "+job+"\n")
        if "job" in job:
            jjob=json.loads(job)
            jjob['params']['id']=uid
            sjob=json.dumps({"jsonrpc":"2.0","method":"job","params":jjob['params']})
            debugPrint("to miner "+sjob+"\n")
            csock.send(sjob+"\n")
        elif "accepted" in job:
            h=json.loads(job)['params']['hashes']
            t=time.time()
            print("accepted, current: %f h/s, avg %f h/s\n" % ((h-prevh)/(t-prevt),(h-inith)/(t-initt)))
            prevh=h
            prevt=t
            csock.send("{\"id\":"+str(nid)+",\"jsonrpc\":\"2.0\",\"error\":null,\"result\":{\"status\":\"OK\"}}\n")
    except KeyboardInterrupt:
        csock.close()
        ssock.close()
        ws.close()
        exit()
