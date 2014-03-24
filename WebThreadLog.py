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

usleep = lambda x: time.sleep(x/100000.0000)

class OperationThreadWeb(threading.Thread):
    #(connnnnn_fd,g_config_h,c_log_fd,connnnnn,addr,"mk_web=" + real_exec)
    def __init__(self,p_id,global_config_hash,config_log_fd,conns,sock_address,user_data_all):
        threading.Thread.__init__(self)
        self.p_id=p_id
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd
        self.conns=conns
        self.sock_address=sock_address
        self.user_data_all=user_data_all


    def run(self):
        user_data_all_split=self.user_data_all.strip().split("&")
        self.conns.setblocking(1)
        if(user_data_all_split is None or len(user_data_all_split) < 4):
            try:
                self.conns.send("Error,request,try again (web)\r\n")
            except:
                pass
            self.conns.close()
            return None
        user_data_script_name=str(user_data_all_split[0].split("=")[1])
        user_data_real_script=self.global_config_hash['ALL_WEB_SH']
        user_data_real_script_dict=eval(user_data_real_script)
        current_script=None
        if(user_data_script_name in user_data_real_script_dict):
            current_script=user_data_real_script_dict[user_data_script_name]
        if(current_script is None): 
            try:
                self.conns.send("Error,request,try again (web)\r\n")
            except:
                pass
            self.conns.close()
            return None
        del user_data_all_split[0]
        self.conns.setblocking(0)
        p = subprocess.Popen("%s \"%s\"" % (str(current_script),str("&".join(user_data_all_split))),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
        #proc_list.append(self.parameter_key,p,self.parameter_value,file_handle)
        p.wait()
        rlw_result="nonone" 
        if(p.returncode !=0):
            rlw=LogRecord.RecordLogWriter(self.config_log_fd)
            rlw_result=rlw.write_log("Execute web log shell of %s on %s/%s failed,code: %d\n" % (self.user_data_all.strip(),str(current_script),self.sock_address,p.returncode))
        if(rlw_result is None or rlw_result !=0):
            self.conns.close()
            return "Error write to log local file %s" % str(self.sock_address)
        self.conns.close()
        return "ok"
