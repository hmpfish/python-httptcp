#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import time
import sys
import io
import select
import socket
import Queue
import exceptions
import subprocess
import threading
import errno
import StringIO
import signal
import hashlib
import LogRecord
import GlobalConfigHandleKernel
import SpecialOperationThread
import posixpath
import urllib
import datetime

def tar_client_translate_path(path):
    path=path.replace("\\","/")
    path=path.replace("//","/")
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = "/"
    pdir="/"
    if(len(words)<2):
        return None
    new_words=words[:len(words)-1]
    for word in words:
        path = os.path.join(path, word)
    for word_2 in new_words:
        pdir = os.path.join(pdir, word_2)
    return [path,pdir]

def create_connect_socket(untar_log_fd,global_config_hash):
    if(GlobalConfigHandleKernel.remote_universal_ip is None):
        time.sleep(1)
        return "error"
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if(clientsocket < 0):
        SpecialOperationThread.unversal_write_log(untar_log_fd,"Create clientsocket failed in client_tar_server thread\n") 
        return "error"
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    clientsocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        clientsocket.settimeout(10)
        clientsocket.connect((GlobalConfigHandleKernel.remote_universal_ip,int(global_config_hash['SERVER_PORT'])))
        clientsocket.settimeout(None)
    except:
        clientsocket.close()
        SpecialOperationThread.unversal_write_log(untar_log_fd,"Connect failed to universal remote ip:port %s:%s in client_tar_server thread\n" % (GlobalConfigHandleKernel.remote_universal_ip,global_config_hash['SERVER_PORT'])) 
        return "error"
    return clientsocket

class ClientServerAuto(threading.Thread):
    def __init__(self,global_config_hash,untar_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.untar_log_fd=untar_log_fd

    def run(self):
        clientsocket=None
        while(1==1):
            clientsocket=create_connect_socket(self.untar_log_fd,self.global_config_hash)
            if(str(clientsocket) == "error"):
                time.sleep(1)
                continue
            else:
                break
        create_tok=0
        while(1==1):
            while(1==1):
                time.sleep(int(self.global_config_hash['CLIENT_UNTAR_SLEEP'])) 
                if(create_tok==1):
                    create_tok=0
                    while(1==1):
                        clientsocket=create_connect_socket(self.untar_log_fd,self.global_config_hash)
                        if(str(clientsocket) == "error"):
                            time.sleep(1)
                            continue
                        else:
                            break
                try:
                    infds,outfds,errfds=select.select([],[clientsocket.fileno()],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(outfds) !=0):
                        GlobalConfigHandleKernel.global_my_ip=clientsocket.getsockname()[0]
                        clientsocket.send("autocoming " + clientsocket.getsockname()[0] +"\r\n")
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send auto failed to universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    infds,outfds,errfds=select.select([clientsocket.fileno()],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    recv_tmp_data=None
                    if(len(infds) !=0):
                        recv_tmp_data=clientsocket.recv(1024)
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv1 failed from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    if(recv_tmp_data.strip() == "No"):
                        clientsocket.close()
                        create_tok=1
                        continue
                    recv_2_all=recv_tmp_data.strip().split()
                    if(len(recv_2_all)!=4 or ("/" not in recv_2_all[0]) or ("/" not in recv_2_all[3]) or (".." in recv_2_all[0]) or (".." in recv_2_all[3])):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Not3 failed from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    infds,outfds,errfds=select.select([],[clientsocket.fileno()],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(outfds) !=0):
                        clientsocket.send("ok\r\n")
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send ok failed to universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    #here recv data
                    tmp_recv_size=0
                    tmp_recv_tmpdata=None
                    file_suf=(recv_2_all[0].strip())[recv_2_all[0].strip().rindex("/"):]
                    file_suf=recv_2_all[3].strip() + file_suf
                    trans_result=tar_client_translate_path(file_suf)
                    if(trans_result is None):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv file path None to universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    [file_suf_new,file_suf_dir]=trans_result
                    if(file_suf_new is None or file_suf_dir is None):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv file path None to universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    try:
                        if(not os.path.isdir(file_suf_dir)):
                            os.makedirs(file_suf_dir,0755)
                        f_recv_file=open(file_suf_new,"wb")
                    except:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv open file None to universal remote ip %s:%s in client_tar_server thread\n" % (GlobalConfigHandleKernel.remote_universal_ip,file_suf_new))
                        create_tok=1
                        continue
                    infds,outfds,errfds=select.select([clientsocket.fileno()],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(infds)==0):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv2 timeout from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                        create_tok=1
                        continue
                    recv_full_tok=0
                    while(long(tmp_recv_size) < long(recv_2_all[1])):
                        try:
                            tmp_recv_tmpdata=clientsocket.recv(int(self.global_config_hash['BUF_SIZE']))
                            tmp_recv_size=long(tmp_recv_size) + long(len(tmp_recv_tmpdata))
                            f_recv_file.write(tmp_recv_tmpdata)
                            f_recv_file.flush()
                            if(long(tmp_recv_size) == long(recv_2_all[1])):
                                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv3 full from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                                recv_full_tok=1
                                break
                        except:
                            clientsocket.close()
                            SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv data failed from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                            create_tok=1
                            break
                    f_recv_file.close()
                    if(recv_full_tok !=1):
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv3 empty from universal remote ip %s in client_tar_server thread\n" % GlobalConfigHandleKernel.remote_universal_ip) 
                    if(recv_2_all[2].strip()=="1" and recv_full_tok==1):
                        GlobalConfigHandleKernel.task_data_queue.put(["utar",file_suf_new,clientsocket.fileno(),clientsocket,"close"])
                        clientsocket=None
                    else:
                        try:
                            clientsocket.send("Finished\r\n")
                        except:
                            pass
                        clientsocket.close()
                    create_tok=1
                    continue
                except:
                    clientsocket.close()
                    create_tok=1
                    continue
                continue
            continue
        clientsocket.close()
