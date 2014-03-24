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
import GlobalConfigHandleKernel
import StringIO
import LogRecord
import signal

#chmod the last step

def unversal_write_log_3(log_fd_un,log_string):
    rlw=LogRecord.RecordLogWriter(log_fd_un)
    rlw_result=rlw.write_log(log_string)
    if(rlw_result is None or rlw_result !=0):
        print "Error to write log file on %s\n" % log_string
        return "error"
    return "ok"

class PortServer(object):
    def __init__(self,serversocket,global_config_hash,epoll,thread_queue,log_fd_log):
        self.serversocket=serversocket
        self.global_config_hash=global_config_hash
        self.epoll=epoll
        self.thread_queue=thread_queue
        self.log_fd_log=log_fd_log

    def op_create(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if(self.serversocket < 0):
            print "Error to create socket handle fd"
            exit(1)

        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) 
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        #here socket opt linger is a useful option for setsocketopt but conflicts with TCP_NODELAY
        bind_result=self.serversocket.bind((self.global_config_hash['SERVER_IP'],int(self.global_config_hash['SERVER_PORT'])))
        #if(bind_result is None or bind_result < 0):
        #    print "Error to bind to socket server"
        #    exit(1)
    
        self.serversocket.listen(int(self.global_config_hash['LISTEN_FD'])) 
        self.serversocket.setblocking(0)
        self.epoll = select.epoll() 
        self.epoll.register(self.serversocket.fileno(), select.EPOLLIN)
        #select.EPOLLHUP|select.EPOLLERR is automated added for epoll registering by os kernel
        #connections={}
        connections=GlobalConfigHandleKernel.global_connections_all
        addressall={}
        while True:
            try:
                while True:
                    events = self.epoll.poll(int(self.global_config_hash['LISTEN_FD']))
                    for fileno, event in events:
                        if(fileno == self.serversocket.fileno()):
                            connection, address = self.serversocket.accept()
                            #if((connection.fileno() >= int(self.global_config_hash['LISTEN_FD']) -3) or (long(GlobalConfigHandleKernel.global_queue_length) > long(self.global_config_hash['QUEUE_LENGTH']))):
                            if((connection.fileno() >= int(self.global_config_hash['LISTEN_FD']) -3)):
                                print "FD too many not closed,perhaps the clients requests are coming in a rush dead time"
                                connection.close()
                                continue
                            #GlobalConfigHandleKernel.global_queue_length = GlobalConfigHandleKernel.global_queue_length +1
                            connection.setblocking(0)
                            connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) 
                            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                            self.epoll.register(connection.fileno(), select.EPOLLIN)
                            connections[connection.fileno()]=connection
                            addressall[connection.fileno()]=address
                        elif(event & select.EPOLLIN):
                            data_tmp=""
                            while True:
                                try:
                                    data_tmp=connections[fileno].recv(int(self.global_config_hash['BUF_SIZE']))
                                    if(data_tmp is not None and len(data_tmp) >0 and len(data_tmp) <= int(self.global_config_hash['BUF_SIZE'])):
                                        #here insert data to thread_process_queue handled by thread pool
                                        exist_fd=GlobalConfigHandleKernel.global_epoll_handle_openfile.get(fileno)
                                        exist_httpgettok=GlobalConfigHandleKernel.global_epoll_handle_httpgettok.get(fileno)
                                        if(not(exist_httpgettok is None)):
                                            break
                                        if(not(exist_fd is None)):
                                            try:
                                                GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno].write(data_tmp)
                                                GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno].flush()
                                                GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno] = GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno] + len(data_tmp)
                                                #beginsssss
                                                if(long(GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]) == long(GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno])):
                                                    exist_fd.close()
                                                    self.epoll.unregister(fileno)
                                                    del addressall[fileno]
                                                    standu_tok="close"
                                                    mode=int(GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno])
                                                    mode_u=mode/100
                                                    mode_g=(mode-(mode_u*100))/10
                                                    mode_o= mode-(mode_u*100)-(mode_g*10)
                                                    mode=(mode_u*8*8)+(mode_g *8)+mode_o
                                                    os.chmod(GlobalConfigHandleKernel.global_epoll_handle_filename[fileno],mode)
                                                    unversal_write_log_3(self.log_fd_log,"Upload file write successed in event & select.EPOLLIN\n")
                                                    except_tok=0
                                                    try:
                                                        connections[fileno].send("ok\r\n")
                                                    except:
                                                        except_tok=1
                                                    if(str(GlobalConfigHandleKernel.global_epoll_handle_fileexec.get(fileno)) == "standu" and (except_tok == 0)):
                                                        GlobalConfigHandleKernel.task_data_queue.put(["utar",str(GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]).strip(),fileno,connections[fileno],"alive"])
                                                        standu_tok="alive"
                                                    GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                                    if(standu_tok == "close"):
                                                        connections[fileno].close()
                                                    del connections[fileno]
                                                    break
                                                elif(long(GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]) > long(GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno])):
                                                    self.epoll.unregister(fileno)
                                                    del addressall[fileno]
                                                    exist_fd.close()
                                                    GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                                    connections[fileno].close()
                                                    del connections[fileno]
                                                    break
                                                #endssss
                                            except:
                                                try:
                                                    connections[fileno].send("Error occured\r\n")
                                                except:
                                                    pass
                                                self.epoll.unregister(fileno)
                                                del addressall[fileno]
                                                exist_fd.close()
                                                GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                                connections[fileno].close()
                                                del connections[fileno]
                                                unversal_write_log_3(self.log_fd_log,"Upload file write failed event & select.EPOLLIN except\n")
                                                break
                                        else:
                                            exist_proxyfd=GlobalConfigHandleKernel.global_proxy_web_fd.get(fileno)
                                            exist_proxycons=GlobalConfigHandleKernel.global_proxy_web_cons.get(fileno)
                                            if(not(exist_proxyfd is None)):
                                                while True:
                                                    try:
                                                        send_size=0
                                                        while(send_size < len(data_tmp)):
                                                            data_tmp=data_tmp[send_size:]
                                                            send_size=exist_proxyfd.send(data_tmp)
                                                        break
                                                    except socket.error,msg:
                                                        if(msg.errno==errno.EAGAIN or msg.errno == errno.EWOULDBLOCK or msg.errno==errno.EINTR):
                                                            continue
                                                        else:
                                                            self.epoll.unregister(fileno)
                                                            GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                                            GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                                            exist_proxyfd.close()
                                                            exist_proxycons.close()
                                                            break
                                                    except:
                                                        self.epoll.unregister(fileno)
                                                        GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                                        GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                                        exist_proxyfd.close()
                                                        exist_proxycons.close()
                                                        break
                                                break
                                            ####################################################################################
                                            abc_tmp=[self.epoll,connections[fileno],fileno,addressall[fileno],data_tmp]
                                            self.epoll.unregister(fileno)
                                            self.thread_queue.put(abc_tmp)
                                            GlobalConfigHandleKernel.global_queue_length = GlobalConfigHandleKernel.global_queue_length +1
                                            break
                                            ###################################################################################
                                    elif(len(data_tmp) <= 0 or len(data_tmp) > int(self.global_config_hash['BUF_SIZE'])):
                                        standu_tok="close"
                                        #[task_tok,task_filename,task_id,task_conns,task_option]
                                        self.epoll.unregister(fileno)
                                        #deleted connections[fileno].close()
                                        #deleted del connections[fileno]
                                        exist_proxyfd=GlobalConfigHandleKernel.global_proxy_web_fd.get(fileno)
                                        exist_proxycons=GlobalConfigHandleKernel.global_proxy_web_cons.get(fileno)
                                        if(not(exist_proxyfd is None)):
                                            try:
                                                GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                                GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                                exist_proxyfd.close()
                                                exist_proxycons.close()
                                            except:
                                                pass
                                            break
                                        del addressall[fileno]
                                        exist_fd=GlobalConfigHandleKernel.global_epoll_handle_openfile.get(fileno)
                                        exist_httpgettok=GlobalConfigHandleKernel.global_epoll_handle_httpgettok.get(fileno)
                                        if(not(exist_httpgettok is None)):
                                            GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                        if(not(exist_fd is None)):
                                            try:
                                                exist_fd.close()
                                                if(long(GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]) == long(GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]) and len(data_tmp)==0):
                                                    mode=int(GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno])
                                                    mode_u=mode/100
                                                    mode_g=(mode-(mode_u*100))/10
                                                    mode_o= mode-(mode_u*100)-(mode_g*10)
                                                    mode=(mode_u*8*8)+(mode_g *8)+mode_o
                                                    os.chmod(GlobalConfigHandleKernel.global_epoll_handle_filename[fileno],mode)
                                                    unversal_write_log_3(self.log_fd_log,"Upload file write successed in event & select.EPOLLIN\n")
                                                    except_tok=0
                                                    try:
                                                        connections[fileno].send("ok\r\n")
                                                    except:
                                                        except_tok=1
                                                    #print "ssss " + GlobalConfigHandleKernel.global_epoll_handle_fileexec.get(fileno) + " ssssss"
                                                    if(str(GlobalConfigHandleKernel.global_epoll_handle_fileexec.get(fileno)) == "standu" and (except_tok == 0)):
                                                        GlobalConfigHandleKernel.task_data_queue.put(["utar",str(GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]).strip(),fileno,connections[fileno],"alive"])
                                                        standu_tok="alive"
                                                    GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                else:
                                                    unversal_write_log_3(self.log_fd_log,"Upload file write failed in event & select.EPOLLIN for len==0\n")
                                                    print("Here size tok: %s tok %d data_tmp" % (GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno],len(data_tmp)))
                                                    GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                    GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                            except:
                                                print "Error while close file handle fd"
                                        if(standu_tok == "close"):
                                            connections[fileno].close()
                                        del connections[fileno]
                                        break
                                except socket.error,msg:
                                    #if(msg.errno == errno.EAGAIN):
                                    if(msg.errno == errno.EAGAIN or msg.errno == errno.EWOULDBLOCK or msg.errno==errno.EINTR):
                                        continue
                                    else:
                                        self.epoll.unregister(fileno)
                                        #connections[fileno].send("Error occured")
                                        exist_proxyfd=GlobalConfigHandleKernel.global_proxy_web_fd.get(fileno)
                                        exist_proxycons=GlobalConfigHandleKernel.global_proxy_web_cons.get(fileno)
                                        if(not(exist_proxyfd is None)):
                                            try:
                                                GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                                GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                                exist_proxyfd.close()
                                                exist_proxycons.close()
                                            except:
                                                pass
                                            break
                                        del addressall[fileno]
                                        exist_fd=GlobalConfigHandleKernel.global_epoll_handle_openfile.get(fileno)
                                        exist_httpgettok=GlobalConfigHandleKernel.global_epoll_handle_httpgettok.get(fileno)
                                        if(not(exist_httpgettok is None)):
                                            GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                        if(not(exist_fd is None)):
                                            try:
                                                exist_fd.close()
                                                GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                unversal_write_log_3(self.log_fd_log,"Upload file write failed in error,msg\n")
                                            except:
                                                print "Error while close file handle fd"
                                        connections[fileno].close()
                                        del connections[fileno]
                                        break
                                except:
                                    if(1<0):
                                        pass
                                    else:
                                        self.epoll.unregister(fileno)
                                        exist_proxyfd=GlobalConfigHandleKernel.global_proxy_web_fd.get(fileno)
                                        exist_proxycons=GlobalConfigHandleKernel.global_proxy_web_cons.get(fileno)
                                        if(not(exist_proxyfd is None)):
                                            try:
                                                GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                                GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                                exist_proxyfd.close()
                                                exist_proxycons.close()
                                            except:
                                                pass
                                            break
                                        del addressall[fileno]
                                        exist_fd=GlobalConfigHandleKernel.global_epoll_handle_openfile.get(fileno)
                                        exist_httpgettok=GlobalConfigHandleKernel.global_epoll_handle_httpgettok.get(fileno)
                                        if(not(exist_httpgettok is None)):
                                            GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                            GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                                        if(not(exist_fd is None)):
                                            try:
                                                exist_fd.close()
                                                GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                                GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                                unversal_write_log_3(self.log_fd_log,"Upload file write failed in error,msg\n")
                                            except:
                                                print "Error while close file handle fd"
                                        connections[fileno].close()
                                        del connections[fileno]
                                        break
                        else:
                            #Maybe some errors occured here
                            #1.EPOLLHUP/EPOLLERR coming or any other errors ,but all the same treasures
                            #elif(event & select.EPOLLHUP):
                            self.epoll.unregister(fileno)
                            exist_proxyfd=GlobalConfigHandleKernel.global_proxy_web_fd.get(fileno)
                            exist_proxycons=GlobalConfigHandleKernel.global_proxy_web_cons.get(fileno)
                            if(not(exist_proxyfd is None)):
                                try:
                                    GlobalConfigHandleKernel.global_proxy_web_fd[fileno]=None
                                    GlobalConfigHandleKernel.global_proxy_web_cons[fileno]=None
                                    exist_proxyfd.close()
                                    exist_proxycons.close()
                                except:
                                    pass
                                continue
                            del addressall[fileno]
                            exist_fd=GlobalConfigHandleKernel.global_epoll_handle_openfile.get(fileno)
                            exist_httpgettok=GlobalConfigHandleKernel.global_epoll_handle_httpgettok.get(fileno)
                            if(not(exist_httpgettok is None)):
                                GlobalConfigHandleKernel.global_epoll_handle_httpgettok[fileno]=None
                                GlobalConfigHandleKernel.global_epoll_handle_httpposttok[fileno]=None
                                GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[fileno]=None
                            if(not(exist_fd is None)):
                                try:
                                    exist_fd.close()
                                    GlobalConfigHandleKernel.global_epoll_handle_openfile[fileno]=None
                                    GlobalConfigHandleKernel.global_epoll_handle_filesize[fileno]=None
                                    GlobalConfigHandleKernel.global_epoll_handle_filefsize[fileno]=None
                                    GlobalConfigHandleKernel.global_epoll_handle_filemode[fileno]=None
                                    GlobalConfigHandleKernel.global_epoll_handle_filename[fileno]=None
                                    GlobalConfigHandleKernel.global_epoll_handle_fileexec[fileno]=None
                                    unversal_write_log_3(self.log_fd_log,"Upload file write failed in event & select.EPOLLHUP\n")
                                except:
                                    print "Error while close file handle fd"
                            connections[fileno].close()
                            del connections[fileno]
            except:
                #here for following exceptions:
                #1.strace the program
                #2.EPOLLIN EAGAIN error while select.epoll.poll in multiprocess 
                #3.any other exceptions
                continue
        self.epoll.unregister(self.serversocket.fileno())
        self.epoll.close()
        self.serversocket.close()
        return 0
