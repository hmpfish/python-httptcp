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
import select
import hashlib
import LogRecord
import GlobalConfigHandleKernel
import SpecialOperationThread

usleep = lambda x: time.sleep(x/100000.0000)
today_time_date=str(datetime.datetime.now()).split()[0]

def need_close_conns(get_con,task_option):
    #if(str(task_option).strip() == "alive"):
    #    return "ALIVE"
    try:
        get_con.close()
    except:
        return None

def send_common_result_to_client(connns,con_str):
    try:
        connns.send(con_str)
    except:
        return "error"
    return "ok"
    
class TaskHashList(threading.Thread):
    def __init__(self,global_config_hash,untar_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.untar_log_fd=untar_log_fd

    def run(self):
        while(1==1):
            [task_pre,task_con,task_id]=GlobalConfigHandleKernel.global_autountar_iptask.get()
            if(task_pre is None or task_con is None or task_id is None):
                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here gets the autotar error : None\n")
                continue
            task_line=task_pre.split()
            if(task_line is None or (len(task_line)!=5 and len(task_line)!=2)):
                send_common_result_to_client(task_con,"Error\r\n")
                need_close_conns(task_con,"close")
                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here gets the autotar error : %s\n" % task_pre)
                continue
            if(len(task_line)==2 and task_line[0].strip()=="delcoming"):
                for d_ip in task_line[1].strip().split(","):
                    if(d_ip in GlobalConfigHandleKernel.global_tar_all_hash):
                        if(len(GlobalConfigHandleKernel.global_tar_all_hash[d_ip])!=0):
                            del(GlobalConfigHandleKernel.global_tar_all_hash[d_ip][0])
                send_common_result_to_client(task_con,"OK\r\n")
                need_close_conns(task_con,"close")
            elif(len(task_line)==2 and task_line[0].strip()=="cleancoming"):
                for d_ip in task_line[1].strip().split(","):
                    if(d_ip in GlobalConfigHandleKernel.global_tar_all_hash):
                        GlobalConfigHandleKernel.global_tar_all_hash[d_ip]=[]
                send_common_result_to_client(task_con,"OK\r\n")
                need_close_conns(task_con,"close")
            elif(len(task_line)==2 and task_line[0].strip()=="removecoming"):
                for d_ip in task_line[1].strip().split(","):
                    if(d_ip in GlobalConfigHandleKernel.global_tar_all_hash):
                        del(GlobalConfigHandleKernel.global_tar_all_hash[d_ip])
                send_common_result_to_client(task_con,"OK\r\n")
                need_close_conns(task_con,"close")
            elif(len(task_line)==2 and task_line[0].strip()=="autocoming"):
                if(task_line[1].strip() in GlobalConfigHandleKernel.global_tar_all_hash and len(GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()])!=0):
                    send_rs=send_common_result_to_client(task_con,(GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0]).replace("$"," ") + "\r\n")
                    if(send_rs=="error"):
                        need_close_conns(task_con,"close")
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here sends name and size of the autotar step 2 error : %s\n" % GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0])
                        continue
                    try:
                        recv_len=None
                        infds,outfds,errfds=select.select([task_id],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                        if(len(infds) !=0):
                            recv_len=task_con.recv(1024)
                    except:
                        need_close_conns(task_con,"close")
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here recv ok of the autotar step 3 except : %s\n" % GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0])
                        continue
                    if(recv_len is None or recv_len.strip() != "ok" or len(recv_len)>=1023 or len(recv_len)<=0):
                        need_close_conns(task_con,"close")
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here recv ok of the autotar step 3 error : %s\n" % GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0])
                        continue
                    #here open files
                    try:
                        file_tmp_open_name=(GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0]).split("$")[0]
                        file_tmp_open_md5=hashlib.md5(file_tmp_open_name + task_line[1].strip()).hexdigest()
                        file_tmp_open=open(file_tmp_open_name,"rb")
                        result_tmp_open=open(self.global_config_hash['UNTAR_EXEC_RESULT'] + "/" + file_tmp_open_md5 + ".res","wb")
                    except:
                        need_close_conns(task_con,"close")
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here open file of the autotar step 4 failed  : %s\n" % GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0])
                        continue
                    try:
                        task_con.setblocking(0)
                    except:
                        pass
                    del(GlobalConfigHandleKernel.global_tar_all_hash[task_line[1].strip()][0])
                    GlobalConfigHandleKernel.global_autountar_epoll_handle_openfile[task_id]=file_tmp_open
                    GlobalConfigHandleKernel.global_autountar_epoll_handle_openresult[task_id]=result_tmp_open
                    GlobalConfigHandleKernel.global_autountar_epoll_handle_conn[task_id]=task_con
                    GlobalConfigHandleKernel.global_autountar_epollfd.register(task_id,select.EPOLLIN|select.EPOLLOUT)
                    #here need to delete hash for ip
                    continue
                else:
                    send_common_result_to_client(task_con,"No\r\n")
                    need_close_conns(task_con,"close")
            elif(len(task_line)==5 and task_line[0].strip()=="autountar"):
                if(not os.path.isfile(task_line[1].strip())):
                    send_common_result_to_client(task_con,"Error\r\n")
                    need_close_conns(task_con,"close")
                    continue
                for d_ip in task_line[2].strip().split(","):
                    if(d_ip.strip() in GlobalConfigHandleKernel.global_tar_all_hash):
                        GlobalConfigHandleKernel.global_tar_all_hash[d_ip].append(task_line[1].strip() + "$" + str(os.stat(task_line[1].strip())[6])+ "$" + task_line[3].strip() + "$" + task_line[4].strip())
                    else:
                        GlobalConfigHandleKernel.global_tar_all_hash[d_ip]=[task_line[1].strip() + "$" + str(os.stat(task_line[1].strip())[6])+ "$" + task_line[3].strip()+ "$" + task_line[4].strip()]
                send_common_result_to_client(task_con,"OK\r\n")
                need_close_conns(task_con,"close")
            else:
                send_common_result_to_client(task_con,"Error\r\n")
                need_close_conns(task_con,"close")
            continue
