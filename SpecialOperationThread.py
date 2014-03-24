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
import LogRecord
import SpecialOperationProcess
import GlobalConfigHandleKernel
import getpass
import select

usleep = lambda x: time.sleep(x/100000.0000)

def unversal_write_log(log_fd_un,log_string):
    rlw=LogRecord.RecordLogWriter(log_fd_un)
    rlw_result=rlw.write_log(log_string)
    if(rlw_result is None or rlw_result !=0):
        print "Error to write log file on %s\n" % log_string
        return "error"
    return "ok"


def special_send_to_client(connnnnn,connnnnn_fd,send_string,c_log_fd,addr,udata,tok=0):
    data_send_result=None
    try:
        #data_send_result=connnnnn.send(send_string + getpass.getuser() + "@>")
        data_send_result=connnnnn.send(send_string)
    except:
        print "Send to client erroron %s(%s)\n" % (addr,udata)
    
    if(data_send_result is None or data_send_result<=0):
        rlw=LogRecord.RecordLogWriter(c_log_fd)
        rlw_result=rlw.write_log("Failed send error result to client through fd %s on %s(%s)\n" % (send_string,addr,udata))
        if(rlw_result is None or rlw_result !=0):
            print "Error to write log file on %s(%s)\n" % (addr,udata)
        connnnnn.close()
        return "error"
    return "ok"

#MEMCACHED list all
#MEMCACHED start servicename port memsize user
#MEMCACHED remove servicename port
#MEMCACHED show servicename port
#MEMCACHED restart servicename port memsize user
#MEMCACHED status servicename port
#REDIS list all
#REDIS start servicename port slave mip mport user
#REDIS start servicename port master user
#REDIS remove servicename port
#REDIS show servicename port
#REDIS restart servicename port slave mip mport user
#REDIS restart servicename port master user
#REDIS status servicename port

def generate_special_process(global_config_hash,config_log_fd,conns,p_id,sock_address,user_data_all):
    p_gop=SpecialOperationProcess.ProcessBashSpecial(p_id,global_config_hash,config_log_fd,conns,sock_address,user_data_all)
    gop_exec_result=p_gop.exe_spe_process()
    if(gop_exec_result != "ok"):
        unversal_write_log(config_log_fd,["Error to exec spe process: %s" % sock_address,user_data_all])
        return "error"
    return "ok"

class OperationThreadSpecial(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd,epollhandle,conns,p_id,sock_address,user_data_all):
        threading.Thread.__init__(self)
#        self.thread_queue=thread_queue
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd
        self.epollhandle=epollhandle
        self.conns=conns
        self.p_id=p_id
        self.sock_address=sock_address
        self.user_data_all=user_data_all
        self.first_tok=1

    def run(self):
        #set blocking true because some will happen unpredicted
        self.conns.setblocking(1)
        while True:
            if(self.first_tok==1):
                self.first_tok=0
                user_data_all_split=self.user_data_all.strip().split()
                if(len(user_data_all_split)==3 and user_data_all_split[1] == "list" and user_data_all_split[2] == "all"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)==3 and user_data_all_split[1] == "showall" and user_data_all_split[2] == "all"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)==8 and (user_data_all_split[1] == "start" or user_data_all_split[1] == "restart") and user_data_all_split[4] == "slave"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)==6 and (user_data_all_split[1] == "start" or user_data_all_split[1] == "restart") and (user_data_all_split[4] == "master" or True)):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)==4 and (user_data_all_split[1] == "remove" or user_data_all_split[1] == "show" or user_data_all_split[1] == "status")):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)>=2 and user_data_all_split[0] == "shell"):
                    shell=1
                    try:
                        self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
                    except:
                        self.conns.close()
                        return "error"
                    #generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                elif(len(user_data_all_split)>=2 and user_data_all_split[0] == "script"):
                    script=1
                    try:
                        self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
                    except:
                        self.conns.close()
                        return "error"
                    #generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,self.user_data_all)
                else:
                    #def special_send_to_client(connnnnn,connnnnn_fd,send_string,c_log_fd,addr,udata,tok=0):
                    special_send_to_client(self.conns,self.p_id,"Error command,try again\n" +  getpass.getuser() +"@" + str(GlobalConfigHandleKernel.global_my_ip) +">",self.config_log_fd,self.sock_address,self.user_data_all.strip())
                    
            data_tmp=self.conns.recv(int(self.global_config_hash['BUF_SIZE']))
            if(data_tmp is not None and len(data_tmp) >0 and len(data_tmp)<int(self.global_config_hash['BUF_SIZE'])-1):
                #process the data
                tmp_data_all_split=data_tmp.strip().split()
                if(len(tmp_data_all_split)==1 and tmp_data_all_split[0] == "exit"):
                    #here deleted for return to main console shell in 2013-01-22
                    #special_send_to_client(self.conns,self.p_id,"Good luck,welcome back\n",self.config_log_fd,self.sock_address,self.user_data_all.strip())
                    #self.conns.close()
                    #end deleted
                    self.epollhandle.register(self.p_id,select.EPOLLIN)
                    return
                if(len(tmp_data_all_split)==3 and tmp_data_all_split[1] == "list" and tmp_data_all_split[2] == "all"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip())
                elif(len(tmp_data_all_split)==3 and tmp_data_all_split[1] == "showall" and tmp_data_all_split[2] == "all"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip())
                elif(len(tmp_data_all_split)==8 and (tmp_data_all_split[1] == "start" or tmp_data_all_split[1] == "restart") and tmp_data_all_split[4] == "slave"):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip());
                elif(len(tmp_data_all_split)==6 and (tmp_data_all_split[1] == "start" or tmp_data_all_split[1] == "restart") and (tmp_data_all_split[4] == "master" or True)):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip());
                elif(len(tmp_data_all_split)==4 and (tmp_data_all_split[1] == "remove" or tmp_data_all_split[1] == "show" or tmp_data_all_split[1] == "status")):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip());
                elif(len(tmp_data_all_split) >=1):
                    generate_special_process(self.global_config_hash,self.config_log_fd,self.conns,self.p_id,self.sock_address,data_tmp.strip());
                else:
                    #def special_send_to_client(connnnnn,connnnnn_fd,send_string,c_log_fd,addr,udata,tok=0):
                    #special_send_to_client(self.conns,self.p_id,"Error command,try again\n" + getpass.getuser() +"@" + str(GlobalConfigHandleKernel.global_my_ip) +">",self.config_log_fd,self.sock_address,data_tmp.strip())
                    special_send_to_client(self.conns,self.p_id,"Error command,try again\n",self.config_log_fd,self.sock_address,data_tmp.strip())
                special_send_to_client(self.conns,self.p_id,getpass.getuser() +"@" + str(GlobalConfigHandleKernel.global_my_ip) +">",self.config_log_fd,self.sock_address,data_tmp.strip())
            else:
                unversal_write_log(self.config_log_fd,str(["Error data received",self.sock_address]))
                self.conns.close()
                return
