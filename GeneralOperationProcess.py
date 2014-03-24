#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import subprocess
import LogRecord

class ProcessBashGeneral(object):
    def __init__(self,parameter_key,parameter_value,file_handle,global_config_transmit,log_writer_fd,client_conn,client_addr):
        self.parameter_key=parameter_key
        self.parameter_value=parameter_value
        self.file_handle=file_handle
        self.global_config_transmit=global_config_transmit
        self.proc_list=[]
        self.log_writer_fd=log_writer_fd
        self.client_conn=client_conn
        self.client_addr=client_addr


    def exe_process(self):
        rlw=LogRecord.RecordLogWriter(self.log_writer_fd)
        rlw_result=rlw.write_log("Execute shell of %s=%s on %s/%s\n" % (self.parameter_key,self.parameter_value,self.global_config_transmit['BACKEND_monitor_config'],self.client_addr))
        if(rlw_result is None or rlw_result !=0):
            return "Error write to log local file"
  
        p=None
 
        if(self.parameter_key != "sms"):
            p = subprocess.Popen("%s %s %s set" % (self.global_config_transmit['API_BASH'],self.parameter_key,self.parameter_value),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=self.file_handle,
                                                stderr=subprocess.STDOUT)
        else:
            p = subprocess.Popen("%s \"%s\"" % (self.global_config_transmit['MSG_API_BASH'],self.parameter_value),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=open("/dev/null", 'w',buffering=0),
                                                stderr=subprocess.STDOUT)
        #proc_list.append(self.parameter_key,p,self.parameter_value,file_handle)
        p.wait()

        if(p.returncode !=0):
            rlw_result=rlw.write_log("Execute shell of %s=%s on %s/%s failed\n" % (self.parameter_key,self.parameter_value,self.global_config_transmit['BACKEND_monitor_config'],self.client_addr))
        if(rlw_result is None or rlw_result !=0):
            return "Error write to log local file %s" % self.client_addr

    
        return "ok"
