#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import GlobalConfigHandleKernel
import subprocess
import LogRecord
import getpass

class ProcessBashSpecial(object):
    def __init__(self,p_id,global_config_hash,config_log_fd,conns,sock_address,user_data_all):
        #SpecialOperationProcess.ProcessBashSpecial(p_id,global_config_hash,config_log_fd,conns,sock_address,user_data_all)
        self.p_id=p_id
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd
        self.conns=conns
        self.sock_address=sock_address
        self.user_data_all=user_data_all

    def exe_spe_process(self):
        rlw=LogRecord.RecordLogWriter(self.config_log_fd)
        tmp_values=(self.user_data_all.strip().split())[0]
        if(tmp_values == "shell" or (tmp_values != "MEMCACHE" and tmp_values != "REDIS" and tmp_values != "all")):
            rlw_result=rlw.write_log("Execute shell of %s on %s/%s\n" % (self.user_data_all.strip(),"/bin/bash",self.sock_address))
        elif( tmp_values == "MEMCACHE" or tmp_values == "REDIS"):
            rlw_result=rlw.write_log("Execute shell of %s on %s/%s\n" % (self.user_data_all.strip(),self.global_config_hash['SP_API_BASH'],self.sock_address))
        elif( tmp_values == "all"):
            rlw_result=rlw.write_log("Execute shell of %s on %s/%s\n" % (self.user_data_all.strip(),self.global_config_hash['API_BASH'],self.sock_address))
        else:
            #rlw_result=rlw.write_log("Execute shell of %s on %s/%s\n" % (self.user_data_all.strip(),self.global_config_hash['SP_API_BASH'],self.sock_address))
            return "Error parameters"
        if(rlw_result is None or rlw_result !=0):
            return "Error write to log local file %s" % str(self.sock_address)
  
        if(tmp_values == "shell" or (tmp_values != "MEMCACHE" and tmp_values != "REDIS" and tmp_values != "all")):
            p = subprocess.Popen("/bin/bash -c \"%s\"" % (self.user_data_all),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
        elif( tmp_values == "MEMCACHE" or tmp_values == "REDIS"):
            p = subprocess.Popen("%s %s" % (self.global_config_hash['SP_API_BASH'],self.user_data_all),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
        elif( tmp_values == "all"):
            p = subprocess.Popen("%s %s allm" % (self.global_config_hash['API_BASH'],self.user_data_all),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
        else:
	    """
            p = subprocess.Popen("%s %s" % (self.global_config_hash['SP_API_BASH'],self.user_data_all),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
	   """
            p = subprocess.Popen("/bin/bash -c \"%s\"" % (self.user_data_all),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.conns,
                                                stderr=subprocess.STDOUT)
        #proc_list.append(self.parameter_key,p,self.parameter_value,file_handle)
        p.wait()
        #here new add 
        if(tmp_values == "shell" or (tmp_values != "MEMCACHE" and tmp_values != "REDIS" and tmp_values != "all")):
            try:
                self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
            except:
                return "error"
        if(p.returncode !=0):
            rlw_result=rlw.write_log("Execute shell of %s on %s/%s failed\n" % (self.user_data_all.strip(),self.global_config_hash['SP_API_BASH'],self.sock_address))
        if(rlw_result is None or rlw_result !=0):
            return "Error write to log local file %s" % str(self.sock_address)
        return "ok"
