#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import io
import exceptions
import time
import datetime
import GlobalConfigHandleKernel

#file_handle is a fd for writing log string to log file to record exactly logs
class RecordLogWriter(object):
    def __init__(self,file_handle):
        self.file_handle=file_handle


    def write_log(self,log_string):
        try:
            self.file_handle.write(str(datetime.datetime.now()) + " " + log_string)
            self.file_handle.flush()
        except IOError,ioe:
            print "Write log string error %s and exactly error %s ..\n" % (log_string,ioe.args)
            GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write python server[%s] log failed" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
            return None
        except Exception,ioe:
            print "Write log string error %s and exactly error %s ..\n" % (log_string,ioe.args)
            GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write python server[%s] log failed" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
            return None
        except:
            print "Write log string error %s and maybe some error ..\n" % (log_string)
            GlobalConfigHandleKernel.global_ksms_temp_queue.put(["ksms Write python server[%s] log failed" % GlobalConfigHandleKernel.global_hostname,"127.0.0.1"])
            return None
        return 0
