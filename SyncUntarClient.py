#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import exceptions
import socket
import subprocess
import GetConfig
import StringIO
import threading
import stat
import Queue
import time
import getpass
import datetime
import select
import hashlib
import urllib
import posixpath
import LogRecord
import GlobalConfigHandleKernel
import SpecialOperationThread

usleep = lambda x: time.sleep(x/100000.0000)

def send_common_result_to_client(connns,con_str):
    try:
        connns.send(con_str)
    except:
        return "error"
    return "ok"

def create_connect_socket(untar_log_fd,global_config_hash,t_ip):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if(clientsocket < 0):
        SpecialOperationThread.unversal_write_log(untar_log_fd,"Create clientsocket failed in client_sync_server thread\n") 
        return "error"
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    clientsocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        clientsocket.settimeout(10)
        clientsocket.connect((t_ip,int(global_config_hash['SERVER_PORT'])))
        clientsocket.settimeout(None)
    except:
        clientsocket.close()
        SpecialOperationThread.unversal_write_log(untar_log_fd,"Connect failed to universal remote ip:port %s:%s in client_sync_server thread\n" % (t_ip,global_config_hash['SERVER_PORT'])) 
        return "error"
    return clientsocket

    
class SyncHashList(threading.Thread):
    def __init__(self,global_config_hash,untar_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.untar_log_fd=untar_log_fd

    def run(self):
        while(1==1):
            [task_pre,task_addr]=GlobalConfigHandleKernel.global_untar_iptask.get()
            if(task_pre is None or task_addr is None):
                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here gets the setuntar error : None\n")
                continue
            task_line=task_pre.split()
            if(task_line is None or (len(task_line)!=5) or task_line[0].strip()!="setuntar"):
                #here send alarms
                GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Here gets the setuntar error")
                SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Here gets the setuntar error : %s\n" % task_pre)
                continue
            for dip in task_line[2].strip().split(","):
                clientsocket=None
                client_try_time=0
                while(1==1):
                    clientsocket=create_connect_socket(self.untar_log_fd,self.global_config_hash,dip)
                    if(str(clientsocket) == "error"):
                        time.sleep(1)
                        client_try_time=client_try_time + 1
                        if(client_try_time >=3):
                            break
                        continue
                    else:
                        break
                if(client_try_time >=3):
                    GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Here cannot connect to " + dip)
                    #here send alarms
                    continue
                try:
                    if("/" not in task_line[1].strip()):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Wrong filename failed to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Wrong filename of setuntar " + task_line[1].strip())
                        continue
                    r_filename=(task_line[1].strip())[task_line[1].strip().rindex("/"):]
                    infds,outfds,errfds=select.select([],[clientsocket.fileno()],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(outfds) !=0):
                        ten_access=int(stat.S_IMODE(os.stat(task_line[1].strip()).st_mode))
                        eight_1=ten_access/64
                        eight_2=(ten_access-64*eight_1)/8
                        eight_3=(ten_access-64*eight_1-8*eight_2)
                        eight_access=str(eight_1) + str(eight_2) + str(eight_3)
                        if(task_line[3].strip() == "0"):
                            clientsocket.send("kernel " +getpass.getuser() + " /" +r_filename + " " +str(os.stat(task_line[1].strip())[6]) + " stand " +task_line[4].strip()+ " "+eight_access+"\r\n")
                        else:
                            clientsocket.send("kernel " +getpass.getuser() + " /" +r_filename + " " +str(os.stat(task_line[1].strip())[6]) + " standu " +task_line[4].strip()+ " "+eight_access+"\r\n")
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send sync failed to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Send sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    infds,outfds,errfds=select.select([clientsocket.fileno()],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    recv_tmp_data=None
                    if(len(infds) !=0):
                        recv_tmp_data=clientsocket.recv(1024)
                    else:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv1 failed from ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Recv sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    if(recv_tmp_data.strip() != "ok"):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv1 ok failed from ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Recv sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    infds,outfds,errfds=select.select([],[clientsocket.fileno()],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    if(len(outfds) ==0):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send check failed to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Send sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    file_tmp_handle=None
                    try:
                        file_tmp_handle=open(task_line[1].strip(),"rb")
                    except:
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Open file failed to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Open sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    full_tok=0
                    while(True):
                        kk_tmp_read=file_tmp_handle.read(4096)
                        if(not kk_tmp_read):
                            full_tok=1
                            break
                        try:
                            clientsocket.send(kk_tmp_read)
                        except:
                            clientsocket.close()
                            SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send file failed to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                            #here send alarms
                            GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Send file sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                            break
                    file_tmp_handle.close()
                    if(full_tok ==0):
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Send full_tok==0 to ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                        continue
                    infds,outfds,errfds=select.select([clientsocket.fileno()],[],[],int(self.global_config_hash['CONNECT_TIMEOUT']))
                    recv_tmp_data=None
                    if(len(infds) ==0):
                        clientsocket.close()
                        SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv2 failed from ip %s %s in client_sync_server thread\n" % (dip,(task_line[1].strip())))
                        #here send alarms
                        GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Recv2 sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                        continue
                    if(task_line[3].strip() == "0"):
                        try:
                            clientsocket.recv(1024)
                        except:
                            pass
                    else:
                        file_tmp_open_md5=hashlib.md5(task_line[1].strip() + dip).hexdigest()
                        try:
                            result_tmp_open=open(self.global_config_hash['UNTAR_EXEC_RESULT'] + "/" + file_tmp_open_md5 + ".res","wb")
                        except:
                            clientsocket.close()
                            SpecialOperationThread.unversal_write_log(self.untar_log_fd,"Recv3 failed from ip %s:%s in client_sync_server thread\n" % (dip,task_line[1].strip()))
                            #here send alarms
                            GlobalConfigHandleKernel.local_sms_queue.put("lsms " + str(GlobalConfigHandleKernel.global_my_ip) + " Recv3 sync untar from %s:%s failed " % (dip,task_line[1].strip()))
                            continue
                        try:
                            abc_tmp=clientsocket.recv(4096)
                            while(abc_tmp and len(abc_tmp)!=0):
                                result_tmp_open.write(abc_tmp)
                                result_tmp_open.flush()
                                abc_tmp=clientsocket.recv(4096)
                        except:
                            clientsocket.close()
                            continue
                        finally:
                            result_tmp_open.close()
                    clientsocket.close()
                except:
                    pass
                continue
