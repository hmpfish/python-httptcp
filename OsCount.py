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
import StringIO
import signal
import hashlib
import LogRecord
import GlobalConfigHandleKernel
import SpecialOperationThread
import posixpath
import urllib
import datetime

#hongyan   10.190.134.29       web0.hongyan.com    2%        87%       (/)72%              0.97      (/usr/local)20%     145            89.4%     1000 0.18/0.13         0/0

class GetOsCount(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd

    def run(self):
        while(1==1):
            #pipein,pipeout=os.pipe()
            p = subprocess.Popen("%s %s %s" % (self.global_config_hash['OSCOUNT_SCRIPT'],GlobalConfigHandleKernel.remote_universal_bus,GlobalConfigHandleKernel.remote_universal_ip),
                                                shell=True,
                                                close_fds=True,
                                                stdin=open("/dev/null", 'r'),
                                                #stdout=pipein,
                                                stdout=subprocess.PIPE,
                                                stderr=open("/dev/null", 'w'))
            #os.close(pipein)
            wait_time=0
            while(wait_time < 30):
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
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the oscount not finished\n")
                time.sleep(int(self.global_config_hash['OSCOUNT_SLEEP']))
                continue
            if(p.returncode !=0):
                SpecialOperationThread.unversal_write_log(self.config_log_fd,"Here gets the oscount returncode !=0 maybe failed\n")
            else:
                for count_data in p.stdout:
                    GlobalConfigHandleKernel.global_oscount_data['oscount']=count_data.strip()
                    break
                #os.close(pipeout)
            time.sleep(int(self.global_config_hash['OSCOUNT_SLEEP']))
