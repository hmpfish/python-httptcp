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


def clear_async_tok(fileno):
    try:
        GlobalConfigHandleKernel.global_asyncclient_epollfd.unregister(fileno)
        sas=GlobalConfigHandleKernel.global_asyncclient_epoll_handle_conn[fileno]
        sbs=GlobalConfigHandleKernel.global_asyncclient_epoll_handle_openfile[fileno]
        GlobalConfigHandleKernel.global_asyncclient_epoll_handle_conn[fileno]=None
        GlobalConfigHandleKernel.global_asyncclient_epoll_handle_openfile[fileno]=None
        GlobalConfigHandleKernel.global_asyncclient_epoll_handle_full[fileno]=None
        sas.close()
        sbs.close()
    except:
        pass
    return None

class SendToClientAsync(threading.Thread):
    def __init__(self,global_config_hash):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash

    def run(self):
        connections={}
        addressall={}
        while True:
            try:
                while True:
                    events = GlobalConfigHandleKernel.global_asyncclient_epollfd.poll(int(self.global_config_hash['LISTEN_FD']))
                    for fileno, event in events:
                        if(event & select.EPOLLIN):
                            if(1==1):
                                clear_async_tok(fileno)
                                continue
                        elif(event & select.EPOLLOUT):
                            if(fileno >= int(self.global_config_hash['LISTEN_FD'])-2):
                                clear_async_tok(fileno)
                                #exit(1) modified as following:
                                continue
                            if(GlobalConfigHandleKernel.global_asyncclient_epoll_handle_full.get(fileno) is not None):
                                continue
                            data_tmp=""
                            data_tmp=GlobalConfigHandleKernel.global_asyncclient_epoll_handle_openfile[fileno].read(int(self.global_config_hash['BUF_SIZE']))
                            if(data_tmp is None or data_tmp ==""):
                                GlobalConfigHandleKernel.global_asyncclient_epoll_handle_full[fileno]="full"
                                clear_async_tok(fileno)
                                continue
                            while True:
                                try:
                                    send_size=0
                                    while(send_size < len(data_tmp)):
                                        data_tmp=data_tmp[send_size:]
                                        send_size=GlobalConfigHandleKernel.global_asyncclient_epoll_handle_conn[fileno].send(data_tmp)
                                    break
                                except socket.error,msg:
                                    if(msg.errno == errno.EAGAIN or msg.errno == errno.EWOULDBLOCK or msg.errno==errno.EINTR):
                                        continue
                                    else:
                                        clear_async_tok(fileno)
                                        break
                                except:
                                    if(1<0):
                                        pass
                                    else:
                                        clear_async_tok(fileno)
                                        break
                        else:
                            #elif(event & select.EPOLLHUP):
                            try:
                                clear_async_tok(fileno)
                            except:
                                pass
                        continue
            except:
                #here deleted for some exceptions
                #GlobalConfigHandleKernel.global_asyncclient_epollfd.close()
                continue
        return
