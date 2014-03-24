#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import GlobalConfigHandleKernel
import subprocess
import LogRecord
import socket
import getpass

class HandleShellProcess(object):
    def __init__(self,global_config_hash,conns,p_id):
        self.global_config_hash=global_config_hash
        self.conns=conns
        self.p_id=p_id

    def operate(self):
        for ids in range(3,64):
            if(ids != self.p_id):
                try:
                    os.close(ids)
                except:
                    pass
        os.dup2(self.p_id,1) 
        os.dup2(self.p_id,2) 
        os.chdir("/")
        data_tmp=""
        try:
            self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
        except:
            self.conns.close()
            exit(1)
        self.conns.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.conns.setblocking(1)
        while(1==1):
            try:
                data_tmp=self.conns.recv(int(self.global_config_hash['BUF_SIZE']))
            except:
                self.conns.close()
                exit(1)
            if(data_tmp is None or len(data_tmp) ==0):
                self.conns.close()
                exit(1)
            chdir_result=0
            if(len(data_tmp.strip()) >=4):
                if(data_tmp.strip()[0:2] == "cd"):
                    try:
                        chdir_result=os.chdir(data_tmp.strip()[3:])
                    except:
                        pass
                elif(data_tmp.strip()[0:4] == "exit"):
                    self.conns.close()
                    exit(1)
                else:
                    try:
                        os.system(data_tmp.strip())
                    except:
                        print "Some errors occured\n"
                try:
                    self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
                except:
                    self.conns.close()
                    exit(1)
            else:
                if(len(data_tmp.strip()) !=0):
                    try:
                        os.system(data_tmp.strip())
                    except:
                        print "Some errors occured\n"
                try:
                    self.conns.send(getpass.getuser()+ "@" + str(GlobalConfigHandleKernel.global_my_ip) +">")
                except:
                    self.conns.close()
                    exit(1)
            continue
