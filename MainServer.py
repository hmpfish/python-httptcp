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
import select
import re
import GeneralOperationThread
import getpass
import LogRecord
import ListenServer
import signal
import socket
import GlobalConfigHandleKernel
import QueueLog
import KernelTaskQueue
import LocalSMSQUEUE
import RrSmsSend
import TarQueueHash
import AutoTarServer
import AsyncSendToClient
import ClientTarServer
import SyncUntarClient
import OsCount
import ProcessShell
import EventThread

def print_usage(help_string):
    print "Usage like following:"
    print "\t %s port >/dev/null 2>&1" % help_string
    print "\t %s port listenip >/dev/null 2>&1" % help_string
    exit(1)

if(len(sys.argv)!=2 and len(sys.argv)!=3):
    print_usage(sys.argv[0])

#server global variables
global_config_hashtable={}
log_handle_fd=None
untarlog_handle_fd=None
writelog_handle_fd=None
smslog_handle_fd=None
general_process_queue=Queue.Queue()
write_log_queue=Queue.Queue()
sms_log_queue=Queue.Queue()
mail_log_queue=Queue.Queue()
memcached_process_queue=Queue.Queue()
redis_process_queue=Queue.Queue()
logic_queue=Queue.Queue()
general_thread_pool=[]
serversocket=0
epoll_fd=0
GlobalConfigHandleKernel.task_data_queue=Queue.Queue()
GlobalConfigHandleKernel.local_sms_queue=Queue.Queue()
GlobalConfigHandleKernel.global_ksms_temp_queue=Queue.Queue()
GlobalConfigHandleKernel.global_rrsms_queue=Queue.Queue()
GlobalConfigHandleKernel.global_autountar_iptask=Queue.Queue()
GlobalConfigHandleKernel.global_untar_iptask=Queue.Queue()
GlobalConfigHandleKernel.global_autountar_epollfd=select.epoll()
GlobalConfigHandleKernel.global_asyncclient_epollfd=select.epoll()
GlobalConfigHandleKernel.global_eventio_queue=Queue.Queue()
GlobalConfigHandleKernel.global_cgi_process_pid=Queue.Queue()

os.environ['PATH']="/home/" + getpass.getuser() + "/bin:/usr/local/sbin:/usr/sbin:/sbin:/home/user_00/bin:/usr/local/bin:/usr/bin:/usr/X11R6/bin:/bin:/usr/games:/opt/gnome/bin:/usr/lib/mit/bin:/usr/lib/mit/sbin"

def get_remote_un_ip():
    r_config_file=global_config_hashtable['BACKEND_monitor_config']
    if(r_config_file is None):
        print("Error config file")
        return "error"
    r_handle=None
    r_counter=0
    r_tmp_ip=None
    r_tmp_bus=None
    try:
        r_handle=open(r_config_file,"r")
    except:
        return "error"
    try:
        r_line_get=None
        for r_line_get in r_handle:
            if(r_line_get is None or len(r_line_get) < 20):
                continue
            if("REMOTE_UNIVERSAL_IP=" in r_line_get):
                r_counter=r_counter+1
                r_tmp_ip=(r_line_get.split("=")[1]).strip()
            if("REMOTE_UNIVERSAL_YEWU=" in r_line_get):
                r_counter=r_counter+1
                r_tmp_bus=(r_line_get.split("=")[1]).strip()
        if(r_counter !=2):
            print("Error config file: %S" % r_config_file)
            return "error"
        GlobalConfigHandleKernel.remote_universal_ip=r_tmp_ip
        GlobalConfigHandleKernel.remote_universal_bus=r_tmp_bus
    except:
        print("Error get remote_universal_ip")
        return "error"
    finally:
        r_handle.close()
    return "ok"

def get_localhost_ip():
    try:
        GlobalConfigHandleKernel.LocalIpList=socket.gethostbyname_ex(socket.gethostname())[2]
        GlobalConfigHandleKernel.global_hostname=os.uname()[1]
    except:
        pass

def update_global_master_iptok():
    get_remote_un_ip()
    get_localhost_ip()
    if(GlobalConfigHandleKernel.remote_universal_ip is None):
        return "error"
    if(GlobalConfigHandleKernel.LocalIpList is None or len(GlobalConfigHandleKernel.LocalIpList) ==0):
        return "error"
    if(GlobalConfigHandleKernel.remote_universal_ip in GlobalConfigHandleKernel.LocalIpList):
        GlobalConfigHandleKernel.global_master_iptok=1
    return "ok"

def open_log_file():
    global log_handle_fd
    global untarlog_handle_fd
    global writelog_handle_fd
    global smslog_handle_fd
    log_handle_fd=open(global_config_hashtable['SERVER_LOG_FILE'],"a")
    if(log_handle_fd is None):
        print "Error to open log file %s." % global_config_hashtable['SERVER_LOG_FILE']
        exit(1)
    writelog_handle_fd=open(global_config_hashtable['ANA_FAIL_LOG'],"a")
    if(writelog_handle_fd is None):
        print "Error to open write log file %s." % global_config_hashtable['ANA_FAIL_LOG']
        exit(1)
    smslog_handle_fd=open(global_config_hashtable['SMS_LOG_FILE'],"a")
    if(smslog_handle_fd is None):
        print "Error to open log file %s." % global_config_hashtable['SMS_LOG_FILE']
        exit(1)
    untarlog_handle_fd=open(global_config_hashtable['UNTAR_ALL_LOG'],"a")
    if(untarlog_handle_fd is None):
        print "Error to open log file %s." % global_config_hashtable['UNTAR_ALL_LOG']
        exit(1)

class CleanZoobie(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global_cgi_process_pid_number=0
        while(1==1):
            try:
                if(global_cgi_process_pid_number==100):
                    global_cgi_process_pid_number=0
                    time.sleep(1)
                    continue
                #[pkid]=GlobalConfigHandleKernel.global_cgi_process_pid.get()
                #if(pkid is None):
                #    continue 
                try:
                    [pkid_wait_result,x_s]=os.waitpid(0,os.WNOHANG)
                    global_cgi_process_pid_number=global_cgi_process_pid_number+1
                    continue
                    ####if(pkid_wait_result != pkid):
                except:
                    time.sleep(1)
                    #print 1111111111111
                    continue
            except:
                #print 00000000000000
                time.sleep(1)
               	continue 
            continue

class RIUT(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        update_sleep_counter=0
        global_cgi_process_pid_number=0
        while(1==1):
            if(global_config_hashtable['ALARM_LEAST_ENABLE'].strip() != "1"):
                time.sleep(1)
                update_sleep_counter=update_sleep_counter+1
                if(update_sleep_counter >=600):
                    update_global_master_iptok()
                    update_sleep_counter=0
                continue
            try:
                [g_get_data,g_get_a]=GlobalConfigHandleKernel.global_ksms_temp_queue.get_nowait()
            except:
                time.sleep(1)
                update_sleep_counter=update_sleep_counter+1
                if(update_sleep_counter >=600):
                    update_global_master_iptok()
                    update_sleep_counter=0
                continue
            if(g_get_data is None or g_get_a is None):
                time.sleep(1)
                update_sleep_counter=update_sleep_counter+1
                if(update_sleep_counter >=600):
                    update_global_master_iptok()
                    update_sleep_counter=0
                continue
            update_sleep_counter=update_sleep_counter+1
            if(update_sleep_counter >=600):
                update_global_master_iptok()
                update_sleep_counter=0
            real_read_data=g_get_data
            key_alarm=None
            current_second=long(str(time.time()).split(".")[0])
            rn=re.findall(r'ksms ([\w\d]+) attention:([\w\d]+) (.*)([^\d]+)([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(.*)',g_get_data)
            if(rn is None or len(rn) ==0 or len(rn[0])==0):
                rn=re.findall(r'ksms ([\w\d]+) attention:([\w\d]+) (.*)',g_get_data)
                if(rn is None or len(rn) ==0 or len(rn[0])==0):
                    key_alarm=str(g_get_a)
                else:
                    key_alarm=str(rn[0][1] + str(g_get_a))
            else:
                key_alarm=str(rn[0][1] + rn[0][4])
                #print key_alarm
            if(1==1):
                if(key_alarm in GlobalConfigHandleKernel.global_ksms_alarm_timer):
                    if(current_second - long(GlobalConfigHandleKernel.global_ksms_alarm_timer[key_alarm]) >=3600):
                        GlobalConfigHandleKernel.global_ksms_alarm_counter[key_alarm]=1
                        GlobalConfigHandleKernel.global_ksms_alarm_timer[key_alarm]=current_second
                        GlobalConfigHandleKernel.global_ksms_alarm_content[key_alarm]=real_read_data
                        sms_log_queue.put(real_read_data)
                    else:
                        if(int(GlobalConfigHandleKernel.global_ksms_alarm_counter[key_alarm]) < int(global_config_hashtable['ALARM_PER_HOUR'])):
                            sms_log_queue.put(real_read_data)
                        GlobalConfigHandleKernel.global_ksms_alarm_counter[key_alarm]=GlobalConfigHandleKernel.global_ksms_alarm_counter[key_alarm] + 1
                else:
                    GlobalConfigHandleKernel.global_ksms_alarm_counter[key_alarm]=1
                    GlobalConfigHandleKernel.global_ksms_alarm_timer[key_alarm]=current_second
                    GlobalConfigHandleKernel.global_ksms_alarm_content[key_alarm]=real_read_data
                    sms_log_queue.put(real_read_data)
            continue

def run_server():
    if(global_config_hashtable['UNTAR_SERVER_ENABLE'].strip() == "1"):
        tas=AutoTarServer.TaskServerAuto(global_config_hashtable,untarlog_handle_fd)
        tas.daemon=True
        tas.start()
        thl=TarQueueHash.TaskHashList(global_config_hashtable,untarlog_handle_fd)
        thl.daemon=True
        thl.start()
    if(global_config_hashtable['ASYNC_CLIENT_ENABLE'].strip() == "1" or global_config_hashtable['ASYNC_CLIENT_ENABLE'].strip() == "3"):
        scas=AsyncSendToClient.SendToClientAsync(global_config_hashtable)
        scas.daemon=True
        scas.start()
    if(global_config_hashtable['UNTAR_CLIENT_ENABLE'].strip() == "1"):
        csa=ClientTarServer.ClientServerAuto(global_config_hashtable,untarlog_handle_fd)
        csa.daemon=True
        csa.start()
    if(global_config_hashtable['UNTAR_SYNC_ENABLE'].strip() == "1"):
        suc=SyncUntarClient.SyncHashList(global_config_hashtable,untarlog_handle_fd)
        suc.daemon=True
        suc.start()
    if(global_config_hashtable['OSCOUNT_ENABLE'].strip() == "1"):
        osp=OsCount.GetOsCount(global_config_hashtable,log_handle_fd)
        osp.daemon=True
        osp.start()
    q_log_write=QueueLog.WriteQueueLog(global_config_hashtable,log_handle_fd,writelog_handle_fd,write_log_queue)
    q_log_write.daemon=True
    q_log_write.start()
    task_data_thread=KernelTaskQueue.TaskKernel(global_config_hashtable,log_handle_fd)
    task_data_thread.daemon=True
    task_data_thread.start()
    remote_ip_update_thread=RIUT()
    remote_ip_update_thread.daemon=True
    remote_ip_update_thread.start()
    zoobie_clean=CleanZoobie()
    zoobie_clean.daemon=True
    zoobie_clean.start()
    localsms_data_thread=LocalSMSQUEUE.MsgLocalOk(global_config_hashtable,log_handle_fd)
    localsms_data_thread.daemon=True
    localsms_data_thread.start()
    #print global_config_hashtable
    rrsms_data_thread=RrSmsSend.SendSmsReal(global_config_hashtable,log_handle_fd)
    rrsms_data_thread.daemon=True
    rrsms_data_thread.start()
    #here start thread
    thread_number=0
    while(thread_number < int(global_config_hashtable['APP_THREAD'])):
        thread_pool_handle=GeneralOperationThread.OperationThreadGeneral(general_process_queue,global_config_hashtable,log_handle_fd,writelog_handle_fd,write_log_queue,smslog_handle_fd,sms_log_queue,mail_log_queue)
        general_thread_pool.append(thread_pool_handle)
        thread_pool_handle.daemon=True
        thread_pool_handle.start()
        thread_number=thread_number+1

    GlobalConfigHandleKernel.extensions_map.update({
                    '': 'application/octet-stream',
                    '.py': 'text/plain',
                    '.sql': 'text/plain',
                    '.c': 'text/plain',
                    '.cpp': 'text/plain',
                    '.cc': 'text/plain',
                    '.txt':'text/plain',
                    '.html':'text/html',
                    '.htm':'text/html',
                    '.xml':'text/xml',
                    '.cf':'text/plain',
                    '.conf':'text/plain',
                    '.cnf':'text/plain',
                    '.ini':'text/plain',
                    '.sh':'text/plain',
                    '.pl':'text/plain',
                    '.log':'text/plain',
                    '.php':'text/plain',
                    '.rb':'text/plain',
                    '.jpg':'image/jpeg',
                    '.gif':'image/gif',
                    '.png':'image/png',
                    '.h': 'text/plain',}) 
    lpres=ListenServer.PortServer(serversocket,global_config_hashtable,epoll_fd,general_process_queue,log_handle_fd).op_create()
    if(lpres is not None and lpres == 0):
        lpres=ListenServer.PortServer(serversocket,global_config_hashtable,epoll_fd,general_process_queue,log_handle_fd).op_create()
   
def create_daemon():
    pid=os.fork() 
    if(pid>0):
        exit(1)
    if(pid==0):
        os.setsid()
        os.umask(0)
        pid=os.fork()
        if(pid>0):
            exit(1)
            os.setsid()
            os.umask(0)
        signal.signal(signal.SIGHUP,signal.SIG_IGN)
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        signal.signal(signal.SIGQUIT,signal.SIG_IGN)
        signal.signal(signal.SIGPIPE,signal.SIG_IGN)
        signal.signal(signal.SIGURG,signal.SIG_IGN)
        signal.signal(signal.SIGTSTP,signal.SIG_IGN)
        signal.signal(signal.SIGTTIN,signal.SIG_IGN)
        signal.signal(signal.SIGTTOU,signal.SIG_IGN)
        signal.signal(signal.SIGALRM,signal.SIG_IGN)
        signal.signal(signal.SIGIOT,signal.SIG_IGN)
        signal.signal(signal.SIGABRT,signal.SIG_IGN)
        signal.signal(signal.SIGPIPE,signal.SIG_IGN)
        signal.signal(signal.SIGCONT,signal.SIG_IGN) 

if __name__ == "__main__":
    create_daemon()
    gsc=GetConfig.GetServerConfig("./conf/server.conf")
    global_config_hashtable=gsc.do_read_config()
    if(global_config_hashtable is None or len(global_config_hashtable) == 0):
        print "Error config file of the tcp server..exit"
        exit(1)
    
    global_config_hashtable['SERVER_PORT']=sys.argv[1]
    if(len(sys.argv)==3):
        if(len(sys.argv[2]) <7):
            print_usage(sys.argv[0])
        global_config_hashtable['SERVER_IP']=sys.argv[2]
    open_log_file()
    if(global_config_hashtable['ASYNC_CLIENT_ENABLE'].strip() == "2" or global_config_hashtable['ASYNC_CLIENT_ENABLE'].strip() == "1"):
        eteio=EventThread.EventIOThread(global_config_hashtable)
        eteio.daemon=True
        eteio.start()
    update_global_master_iptok()
    run_server()
