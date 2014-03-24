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


def clear_autotar_tok(fileno):
    try:
        GlobalConfigHandleKernel.global_autountar_epollfd.unregister(fileno)
        sas=GlobalConfigHandleKernel.global_autountar_epoll_handle_conn[fileno]
        sbs=GlobalConfigHandleKernel.global_autountar_epoll_handle_openfile[fileno]
        scs=GlobalConfigHandleKernel.global_autountar_epoll_handle_openresult[fileno]
        GlobalConfigHandleKernel.global_autountar_epoll_handle_conn[fileno]=None
        GlobalConfigHandleKernel.global_autountar_epoll_handle_openfile[fileno]=None
        GlobalConfigHandleKernel.global_autountar_epoll_handle_openresult[fileno]=None
        GlobalConfigHandleKernel.global_autountar_epoll_handle_full[fileno]=None
        sas.close()
        sbs.close()
        scs.close()
    except:
        pass
    return None

class TaskServerAuto(threading.Thread):
    def __init__(self,global_config_hash,untar_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.untar_log_fd=untar_log_fd

    def run(self):
        connections={}
        addressall={}
        while True:
            try:
                while True:
                    events = GlobalConfigHandleKernel.global_autountar_epollfd.poll(int(self.global_config_hash['LISTEN_FD']))
                    for fileno, event in events:
                        if(event & select.EPOLLIN):
                            if(fileno >= int(self.global_config_hash['LISTEN_FD'])-2):
                                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Auto server fd mounted to maximum,exit\n")
                                clear_autotar_tok(fileno)
                                #exit(1) modified as following:
                                continue
                            data_tmp=""
                            while True:
                                try:
                                    data_tmp=GlobalConfigHandleKernel.global_autountar_epoll_handle_conn[fileno].recv(int(self.global_config_hash['BUF_SIZE']))
                                    if(data_tmp is not None and len(data_tmp) >0 and len(data_tmp) <= int(self.global_config_hash['BUF_SIZE'])):
                                        if(data_tmp.strip() == "TaskServerAuto exit"):
                                            clear_autotar_tok(fileno)
                                            break
                                        GlobalConfigHandleKernel.global_autountar_epoll_handle_openresult[fileno].write(data_tmp)
                                        GlobalConfigHandleKernel.global_autountar_epoll_handle_openresult[fileno].flush()
                                        break
                                    elif(len(data_tmp) <= 0 or len(data_tmp) > int(self.global_config_hash['BUF_SIZE'])):
                                        clear_autotar_tok(fileno)
                                        break
                                except socket.error,msg:
                                    if(msg.errno == errno.EAGAIN or msg.errno == errno.EWOULDBLOCK or msg.errno==errno.EINTR):
                                        continue
                                    else:
                                        clear_autotar_tok(fileno)
                                        break
                                except:
                                    if(1<0):
                                        pass
                                    else:
                                        clear_autotar_tok(fileno)
                                        break
                        elif(event & select.EPOLLOUT):
                            if(fileno >= int(self.global_config_hash['LISTEN_FD'])-2):
                                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Auto server fd mounted to maximum,exit\n")
                                exit(1)
                            if(GlobalConfigHandleKernel.global_autountar_epoll_handle_full.get(fileno) is not None):
                                continue
                            data_tmp=""
                            data_tmp=GlobalConfigHandleKernel.global_autountar_epoll_handle_openfile[fileno].read(int(self.global_config_hash['BUF_SIZE']))
                            #if(data_tmp is None):
                            if(data_tmp is None or data_tmp ==""):
                                GlobalConfigHandleKernel.global_autountar_epoll_handle_full[fileno]="full"
                                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Auto server openfile read fully\n")
                                continue
                            while True:
                                try:
                                    send_size=0
                                    while(send_size < len(data_tmp)):
                                        data_tmp=data_tmp[send_size:]
                                        send_size=GlobalConfigHandleKernel.global_autountar_epoll_handle_conn[fileno].send(data_tmp)
                                    break
                                except socket.error,msg:
                                    if(msg.errno == errno.EAGAIN or msg.errno == errno.EWOULDBLOCK or msg.errno==errno.EINTR):
                                        continue
                                    else:
                                        clear_autotar_tok(fileno)
                                        break
                                except:
                                    if(1<0):
                                        pass
                                    else:
                                        clear_autotar_tok(fileno)
                                        break
                        else:
                            #elif(event & select.EPOLLHUP):
                            try:
                                clear_autotar_tok(fileno)
                            except:
                                pass
                        continue
            except:
                #here deleted for some exceptions
                #GlobalConfigHandleKernel.global_autountar_epollfd.close()
                continue
        return
