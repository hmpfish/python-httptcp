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
import SpecialOperationThread

usleep = lambda x: time.sleep(x/100000.0000)
today_time_date=str(datetime.datetime.now()).split()[0]

def need_close_conns(get_con,task_option):
    #deleted on 2012 09 12
    #if(str(task_option).strip() == "alive"):
    #    return "ALIVE"
    try:
        get_con.close()
    except:
        return None
    
class TaskKernel(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd

    def run(self):
        while(1==1):
            [task_tok,task_filename,task_id,task_conns,task_option]=GlobalConfigHandleKernel.task_data_queue.get()
            #print(task_tok + task_filename)
            try:
                task_conns.setblocking(0)
            except:
                pass
            if(task_option is None or len(task_option)==0):
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the error task line from task_data_queue: %s,%s\n" % (task_tok,task_filename))
                GlobalConfigHandleKernel.task_data_queue.task_done()
                need_close_conns(task_conns,task_option)
                continue
            if(task_filename is None or len(task_filename)==0):
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the error task line from task_data_queue: %s,%s\n" % (task_tok,task_filename))
                GlobalConfigHandleKernel.task_data_queue.task_done()
                need_close_conns(task_conns,task_option)
                continue
            if(task_id is None or len(str(task_id))==0):
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the error task line from task_data_queue: %s,%s\n" % (task_tok,task_filename))
                GlobalConfigHandleKernel.task_data_queue.task_done()
                need_close_conns(task_conns,task_option)
                continue
            task_data_hash=self.global_config_hash['TASK_QUEUE_SH']
            task_data_hash_real=eval(task_data_hash)
            tmp_task_get=None
            if((task_tok is not None) and (task_tok in task_data_hash_real)):
                tmp_task_get=task_data_hash_real[task_tok]
            else:
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the error task line from task_data_queue not in the config hash : %s,%s\n" % (task_tok,task_filename))
                GlobalConfigHandleKernel.task_data_queue.task_done()
                need_close_conns(task_conns,task_option)
                continue
            p=None
            sh_toks=0
            if(len(str(task_filename)) >=4):
                file_suffix_name=""
                if("." in str(task_filename)):
                    file_suffix_name=str(task_filename)[str(task_filename).rindex("."):]
                support_suffix=eval(self.global_config_hash['UNTAR_SUPPORT_EXEC'])
                if(file_suffix_name in support_suffix):
                    sh_toks=1
                    mode=(7*8*8)+(5 *8)+ 5
                    os.chmod(str(task_filename),mode)
                    if(file_suffix_name != ".exe"):
                        try:
                            os.system("sed -i 's/\r//g' %s ;" % str(task_filename))
                        except:
                            pass
                    p = subprocess.Popen("%s" % str(task_filename),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=task_id,
                                                stderr=subprocess.STDOUT)
                else:
                    p = subprocess.Popen("%s %s" % (str(tmp_task_get),str(task_filename)),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=task_id,
                                                stderr=subprocess.STDOUT)
            else:
                p = subprocess.Popen("%s %s" % (str(tmp_task_get),str(task_filename)),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                stdout=task_id,
                                                stderr=subprocess.STDOUT)
            wait_time=0
            while(wait_time < int(self.global_config_hash['TASK_TIMEOUT'])):
                poll_status=p.poll()
                if(poll_status is not None):
                    break
                else:
                    time.sleep(1)
                    wait_time=wait_time + 1
                    continue
            poll_status=p.poll()
            if(poll_status is None):
                p.kill()
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the task not finished for : %s,%s\n" % (task_tok,task_filename))
                GlobalConfigHandleKernel.task_data_queue.task_done()
                need_close_conns(task_conns,task_option)
                continue
            if(p.returncode !=0):
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the task returncode !=0 maybe failed : %s,%s\n" % (task_tok,task_filename))
            else:
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the task successfully : %s,%s\n" % (task_tok,task_filename))
                try:
                    if(os_toks == 0):
                        os.unlink(task_filename)
                except:
                    pass
            GlobalConfigHandleKernel.task_data_queue.task_done()
            need_close_conns(task_conns,task_option)
            continue
