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
import GlobalConfigHandleKernel
import StringIO
import LogRecord
import GeneralOperationThread


class FileDownload(threading.Thread):
    def __init__(self,log_fd,client_sock_fd,client_conn,epoll_fd,file_name,file_user,config_h):
        threading.Thread.__init__(self)
        self.log_fd=log_fd
        self.client_sock_fd=client_sock_fd
        self.client_conn=client_conn
        self.epoll_fd=epoll_fd
        self.file_name=file_name
        self.file_user=file_user
        self.global_config_hash=config_h
    def get_filename(self):
        return self.file_name
    def get_fileuser(self):
        return self.file_user
    def run(self):
        self.client_conn.setblocking(1)
        file_stat=os.stat(self.file_name)[6]
        #file_stat_s=file_stat[0:len(file_stat)-1]
        file_stat_s=str(file_stat)
        infds,outfds,errfds=select.select([],[self.client_sock_fd],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
        if(len(outfds)==0):
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Step1 check failed write to client" + self.file_name + self.file_user + "\n")
            self.client_conn.close()
            return "Error"
        try:
            self.client_conn.send(file_stat_s + "\r\n")
        except:
            print "Error to send file size to client"
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Error to send file size to client" + self.file_name + self.file_user + "\n")
            self.client_conn.close()
            return "Error"
        try:
            recv_len=None
            infds,outfds,errfds=select.select([self.client_sock_fd],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
            if(len(infds) !=0):
                recv_len=self.client_conn.recv(1024)
            if(recv_len is None or recv_len.strip() != "ok" or len(recv_len)>=1023 or len(recv_len)<=0):
                #self.epoll_fd.unregister(self.client_sock_fd)
                GeneralOperationThread.unversal_write_log_2(self.log_fd,"Error to recv file size ok from client" + self.file_name + self.file_user + "\n")
                self.client_conn.close()
                return "Error"
        except:
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Except to recv file size ok from client" + self.file_name + self.file_user + "\n")
            self.client_conn.close()
            return "Error"
        infds,outfds,errfds=select.select([],[self.client_sock_fd],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
        if(len(outfds)==0):
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Check write failed from client" + self.file_name + self.file_user + "\n")
            self.client_conn.close()
            return "Error"
        try:
            file_read_handle=open(self.file_name,"rb")
        except:
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Open file failed from client" + self.file_name + self.file_user + "\n")
            self.client_conn.close()
            return "Error"
        try:
            file_read_tmp=file_read_handle.read(4096)
            while file_read_tmp:
                self.client_conn.send(file_read_tmp)
                file_read_tmp=file_read_handle.read(4096)
        except:
            GeneralOperationThread.unversal_write_log_2(self.log_fd,"Error to read file for binary mode" + self.file_name + self.file_user + "\n")
            print "File binary read error"
        finally:
            file_read_handle.close()
        #here useful for new version
        #try:
        #    last_tok=self.client_conn.recv(1024)
        #except:
        #    pass
        self.client_conn.close()	
        GeneralOperationThread.unversal_write_log_2(self.log_fd,"Done to send file for binary mode" + self.file_name + self.file_user + "\n")
        return "ok"
