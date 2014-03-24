#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import exceptions
import subprocess
import GetConfig
import StringIO
import threading
import Queue
import time
import datetime
import LogRecord
import GlobalConfigHandleKernel
import SpecialOperationThread
import select
import socket

usleep = lambda x: time.sleep(x/100000.0000)

def create_connect_socket(config_log_fd,global_config_hash):
    if(GlobalConfigHandleKernel.remote_universal_ip is None):
        time.sleep(1)
        return "error"
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if(clientsocket < 0):
        SpecialOperationThread.unversal_write_log(config_log_fd,"Create clientsocket failed in local_sms_queue thread\n") 
        return "error"
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    clientsocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        clientsocket.settimeout(10)
        clientsocket.connect((GlobalConfigHandleKernel.remote_universal_ip,int(global_config_hash['SERVER_PORT'])))
        clientsocket.settimeout(None)
    except:
        clientsocket.close()
        SpecialOperationThread.unversal_write_log(config_log_fd,"Connect failed to universal remote ip:port %s:%s in local_sms_queue thread\n" % (GlobalConfigHandleKernel.remote_universal_ip,global_config_hash['SERVER_PORT'])) 
        return "error"
    return clientsocket

class MsgLocalOk(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd

    def run(self):
        clientsocket=None
        while(1==1):
            clientsocket=create_connect_socket(self.config_log_fd,self.global_config_hash)
            if(str(clientsocket) == "error"):
                time.sleep(1)
                continue
            else:
                break
        create_tok=0
        while(1==1):
            abc_sms=GlobalConfigHandleKernel.local_sms_queue.get()
            if(abc_sms is None or len(abc_sms.strip()) < 6):
                continue
            abc_sms=abc_sms.strip().replace("lsms","ksms")
            while(1==1):
                if(create_tok==1):
                    create_tok=0
                    while(1==1):
                        clientsocket=create_connect_socket(self.config_log_fd,self.global_config_hash)
                        if(str(clientsocket) == "error"):
                            time.sleep(1)
                            continue
                        else:
                            break
                try:
                    infds,outfds,errfds=select.select([],[clientsocket.fileno()],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(outfds) !=0):
                        clientsocket.send(abc_sms +"\r\n")
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.config_log_fd,"Send failed to universal remote ip %s in local_sms_queue thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        time.sleep(1)
                        create_tok=1
                        continue
                    infds,outfds,errfds=select.select([clientsocket.fileno()],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    recv_tmp_data=None
                    if(len(infds) !=0):
                        recv_tmp_data=clientsocket.recv(1024)
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.config_log_fd,"Recv failed to universal remote ip %s in local_sms_queue thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        time.sleep(1)
                        create_tok=1
                        continue
                    if(recv_tmp_data.strip() != "ok"):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.config_log_fd,"Notok failed to universal remote ip %s in local_sms_queue thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        time.sleep(1)
                        create_tok=1
                        continue
                except:
                    clientsocket.close()
                    time.sleep(1)
                    create_tok=1
                    continue
                break
            continue
        clientsocket.close()
