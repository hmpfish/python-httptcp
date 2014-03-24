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
import select
import socket
#import gevent
import shutil

def me_greenlet_gevent(source,dstfdstream,sleep):
    try:
        source_open=open(source,"rb")
    except:
        dstfdstream.close()
        return None
    try:
        dst_fileobj=dstfdstream.makefile()
    except:
        source_open.close()
        dstfdstream.close()
        return None
    try:
        shutil.copyfileobj(source_open,dst_fileobj)
        dst_fileobj.flush()
    except:
        pass
    try:
        source_open.close()
        dstfdstream.close()
        return None
    except:
        pass
    return None

class EventIOThread(threading.Thread):
    def __init__(self,g_config_h):
        threading.Thread.__init__(self)
        self.g_config_h=g_config_h
    def run(self):
        if(self.g_config_h['ASYNC_CLIENT_ENABLE'].strip() == "2"):
            import gevent
        while(1==1):
            [source_file,dst_conn,tok_resign]=GlobalConfigHandleKernel.global_eventio_queue.get() 
            if(source_file is None or dst_conn is None or tok_resign is None):
                continue
            if(str(tok_resign).strip() == "2"):
                try:
                    gevent.spawn(me_greenlet_gevent,str(source_file).strip(),dst_conn,gevent.sleep) 
                    gevent.sleep(0)
                except:
                    pass
            elif(str(tok_resign).strip() == "1"):
                try:
                    tmp_source_open=open(str(source_file).strip(),"rb")
                    GlobalConfigHandleKernel.global_asyncclient_epoll_handle_openfile[dst_conn.fileno()]=tmp_source_open
                    GlobalConfigHandleKernel.global_asyncclient_epoll_handle_conn[dst_conn.fileno()]=dst_conn
                    GlobalConfigHandleKernel.global_asyncclient_epollfd.register(dst_conn.fileno(),select.EPOLLOUT|select.EPOLLIN)
                except:
                    dst_conn.close()
            else:
                try:
                    dst_conn.close()
                except:
                    pass
            continue
