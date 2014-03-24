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
import LogRecord
import SpecialOperationThread
import GlobalConfigHandleKernel

usleep = lambda x: time.sleep(x/100000.0000)
today_time_date=str(datetime.datetime.now()).split()[0]
combine_log_handle=None

def open_log_first(global_config_hash,config_log_fd):
    global combine_log_handle
    try:
        combine_log_handle=open(global_config_hash['WEB_LOG_DIR'] + "/" + today_time_date + "-act-combine.log","a")
        if(combine_log_handle is None):
            print "Error to open combine web log file %s:%s" % (global_config_hashtable['WEB_LOG_DIR'],today_time_date)
            SpecialOperationThread.unversal_write_log(config_log_fd,"Error to open combine web log file %s:%s\n" % (global_config_hashtable['WEB_LOG_DIR'],today_time_date))
            return -1
    except:
        return -2
    return 0

def check_logname_update(global_config_hash,config_log_fd,l_date):
    global combine_log_handle
    #new_time_date=str(datetime.datetime.now()).split()[0]
    new_time_date=l_date
    if(new_time_date!=today_time_date):
        try:
            combine_log_handle.close()
            combine_log_handle=open(global_config_hash['WEB_LOG_DIR'] + "/" + new_time_date + "-act-combine.log","a")
            if(combine_log_handle is None):
                SpecialOperationThread.unversal_write_log(config_log_fd,"Error to open combine web log file %s:%s\n" % (global_config_hashtable['WEB_LOG_DIR'],new_time_date))
                print "Error to open combine web log file %s:%s" % (global_config_hashtable['WEB_LOG_DIR'],new_time_date)
                return -1
        except:
            return -2
    return 0

class WriteQueueLog(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd,config_log_fd_web,web_queue):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd
        self.config_log_fd_web=config_log_fd_web
        self.web_queue=web_queue

    def run(self):
        first_o_result=open_log_first(self.global_config_hash,self.config_log_fd)
        if(first_o_result < 0):
            if(first_o_result == -2):
                SpecialOperationThread.unversal_write_log(config_log_fd,"Error to open combine web log file %s:%s\n" % (global_config_hashtable['WEB_LOG_DIR'],"onfirst"))
            return "error"
        while(1==1):
            #The following 3 lines is deleted on 2012-08-23
            #if(self.web_queue.empty()):
            #    usleep(10000)
            #    continue
            #logname_s_result=check_logname_update(self.global_config_hash,self.config_log_fd)
            #if(logname_s_result < 0):
            #    if(logname_s_result == -2):
            #        SpecialOperationThread.unversal_write_log(config_log_fd,"Error to open combine web log file %s:%s\n" % (global_config_hashtable['WEB_LOG_DIR'],"onfirst"))
            #    return "error"
            (log_string,l_date,l_code)=self.web_queue.get()
            logname_s_result=check_logname_update(self.global_config_hash,self.config_log_fd,l_date)
            if(logname_s_result < 0):
                if(logname_s_result == -2):
                    SpecialOperationThread.unversal_write_log(config_log_fd,"Error to open combine web log file %s:%s\n" % (global_config_hashtable['WEB_LOG_DIR'],"onfirst"))
                self.web_queue.task_done()
                return "error"
            if(combine_log_handle is None and log_string is not None):
                self.config_log_fd_web.write(l_code + " " + log_string + "\n")
                self.config_log_fd_web.flush()
                self.web_queue.task_done()
                continue
            if(log_string is not None):
                try:
                    combine_log_handle.write(l_code + " " + log_string + "\n")
                    combine_log_handle.flush()
                except IOError,ioe:
                    print "Write web log string error %s and exactly error %s ..\n" % (log_string,ioe.args)
                    self.config_log_fd_web.write(l_code + " " + log_string +"\n")
                    self.config_log_fd_web.flush()
                    self.web_queue.task_done()
                    GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write web action log failed,hostname:[%s]" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
                    continue
                except Exception,ioe:
                    print "Write web log string error %s and exactly error %s ..\n" % (log_string,ioe.args)
                    self.config_log_fd_web.write(l_code + " " + log_string +"\n")
                    self.config_log_fd_web.flush()
                    self.web_queue.task_done()
                    GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write web action log failed,hostname:[%s]" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
                    continue
                except:
                    self.config_log_fd_web.write(l_code + " " + log_string +"\n")
                    self.config_log_fd_web.flush()
                    self.web_queue.task_done()
                    GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write web action log failed,hostname:[%s]" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
                    continue
            self.web_queue.task_done()
            continue
        return "ok"
