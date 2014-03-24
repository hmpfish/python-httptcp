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
import GlobalConfigHandleKernel
import re
import SpecialOperationThread
import socket
import urllib
import hashlib

usleep = lambda x: time.sleep(x/100000.0000)
#rrsms_data_thread=RrSmsSend.SendSmsReal(global_config_hashtable,log_handle_fd)

class SendSmsReal(threading.Thread):
    def __init__(self,config_hash,log_fd):
        threading.Thread.__init__(self)
        self.config_hash=config_hash
        self.log_fd=log_fd

    def run(self):
        while(1==1):
            [abc_sms,abc_client]=GlobalConfigHandleKernel.global_rrsms_queue.get()
            if(abc_sms is None or len(abc_sms.strip()) < 14 ):
                SpecialOperationThread.unversal_write_log(self.log_fd,"RRSMS wrong: %s [%s]\n" % (abc_sms,abc_client))
                continue
            abc_array=abc_sms.split()
            if(abc_array is None or len(abc_array) != 4):
                SpecialOperationThread.unversal_write_log(self.log_fd,"RRSMS wrong: %s [%s]\n" % (abc_sms,abc_client))
                continue
            abc_msg=abc_array[3].strip()
            abc_msg=abc_msg.replace("'","")
            abc_msg=abc_msg.replace("\"","")
            abc_msg=urllib.unquote(abc_msg)
            if(abc_msg is None or len(abc_msg) < 2):
                SpecialOperationThread.unversal_write_log(self.log_fd,"RRSMS wrong: %s [%s]\n" % (abc_sms,abc_client))
                continue
            #here congervency alarms
            ip_value=""
            ip_f=re.findall(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)",abc_msg)
            if(ip_f is None or len(ip_f) ==0):
                ip_value=""
            else:
                ip_value=":".join(ip_f)
            sub_rep=re.compile("([0-9]+|%)")
            sub_result=sub_rep.sub("",abc_msg)
            sub_md5=hashlib.md5(ip_value + sub_result).hexdigest()
            current_second=long(str(time.time()).split(".")[0])
            if(sub_md5 in GlobalConfigHandleKernel.global_congervency_timer):
                if(current_second - long(GlobalConfigHandleKernel.global_congervency_timer[sub_md5]) >= long(int(self.config_hash['CONGERVENCY_hour']) * 3600)):
                    GlobalConfigHandleKernel.global_congervency_alarm[sub_md5]=1
                    GlobalConfigHandleKernel.global_congervency_timer[sub_md5]=current_second
                    GlobalConfigHandleKernel.global_congervency_content[sub_md5]=abc_msg
                else:
                    if(int(GlobalConfigHandleKernel.global_congervency_alarm[sub_md5]) >= int(self.config_hash['CONGERVENCY_number'])):
                        GlobalConfigHandleKernel.global_congervency_alarm[sub_md5]=GlobalConfigHandleKernel.global_congervency_alarm[sub_md5] + 1
                        SpecialOperationThread.unversal_write_log(self.log_fd,"RRSMS congervency: %s [%s]\n" % (abc_sms,abc_client))
                        continue
                    GlobalConfigHandleKernel.global_congervency_alarm[sub_md5]=GlobalConfigHandleKernel.global_congervency_alarm[sub_md5] + 1
            else:
                GlobalConfigHandleKernel.global_congervency_alarm[sub_md5]=1
                GlobalConfigHandleKernel.global_congervency_timer[sub_md5]=current_second
                GlobalConfigHandleKernel.global_congervency_content[sub_md5]=abc_msg
            #ends
            p_sms = subprocess.Popen("/bin/bash -c \"%s '%s' '%s' '%s'\"" % (self.config_hash['RRSENDSMS_home'],abc_msg,abc_array[2],abc_array[1]),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=open("/dev/null", 'w'),
                                                stderr=subprocess.STDOUT)
            poll_counter=0
            poll_ok=0
            while(poll_counter < int(self.config_hash['RRSENDSMS_polltime'])):
                poll_result=p_sms.poll()
                if(poll_result is None):
                    poll_counter = poll_counter + 1
                    time.sleep(1)
                    continue
                else:
                    poll_ok=1
                    break
            if(poll_ok ==0):
                try:
                    p_sms.kill()
                    SpecialOperationThread.unversal_write_log(self.log_fd,"RRSMS send timeout: %s [%s]\n" % (abc_sms,abc_client))
                except:
                    pass
            continue
