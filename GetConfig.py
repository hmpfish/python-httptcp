#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io


class GetServerConfig(object):
        def __init__(self,config_file_name):
                self.config_file_name=config_file_name

        def do_read_config(self):
                config_result_all={}
                try:
                        #file_fd_open=io.TextIOBase.open(self.config_file_name,"r")
                        file_fd_open=open(self.config_file_name,"r")
                except:
                        print("Error to open the config server list file %s .." % (self.config_file_name))
                        return None

                #while file_fd_open:
                for temp_read_line in file_fd_open:
                        #temp_read_line=file_fd_open.readline()
                        if(temp_read_line is None):
                                return None

                        if(len(temp_read_line) < 10):
                                continue

                        if(temp_read_line[0] == '#'):
                                continue

                        temp_split_array=()
                        temp_split_array=temp_read_line.strip().split('=')
                        if(len(temp_split_array) !=2):
                                print "Error line read from config server file because of the number is not equal 2"
                                os.exit(1)
                                #continue

                        #config_result_all.append(temp_split_array)
                        config_result_all[temp_split_array[0]]=temp_split_array[1]
                        continue

                file_fd_open.close()
                return config_result_all


        def print_file_name(self):
                print self.config_file_name
