#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getpass
import io
import exceptions
import subprocess
import GetConfig
import StringIO
import threading
import Queue
import time
import random
import GeneralOperationProcess
import LogRecord
import SpecialOperationThread
import SpecialOperationProcess
import GlobalConfigHandleKernel
import WebThreadLog
import DownloadFile
import select
import posixpath
import urllib2
import urllib
import cgi
import shutil
import hashlib
import mimetypes
import re
import datetime
import ProcessShell
import signal
import socket
import KernelFCGI

usleep = lambda x: time.sleep(x/100000.0000)

from BaseHTTPServer import BaseHTTPRequestHandler
 
class HTTPMeRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO.StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.rfile.close()
    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

def h_date_time_string(timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
            self.weekdayname[wd],
            day, self.monthname[month], year,
            hh, mm, ss)
    return s

def client_translate_path(path):
    path=path.replace("\\","/")
    path=path.replace("//","/")
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = "/"
    if(len(words)<2):
        return None
    new_words=words[:len(words)-1]
    for word in new_words:
        path = os.path.join(path, word)
    return path

def do_some_thing_for_file_upload(client_fd,file_size,file_name,file_dir,file_mod,exec_toks="stand"):
    file_fd_tmp_open=None
    try:
        file_fd_filename=file_dir + "/" + file_name
        c_file_dir=client_translate_path(file_fd_filename) 
        if(c_file_dir is None or c_file_dir == ""):
            return -2
        if(not os.path.isdir(c_file_dir)):
            try:
                os.makedirs(c_file_dir,0755)
            except:
                pass
        #file_fd_tmp_open=open(file_dir + "/" + file_name ,"wb")
        file_fd_tmp_open=open(file_fd_filename,"wb")
    except:
        return -2
    GlobalConfigHandleKernel.global_epoll_handle_openfile[client_fd]=file_fd_tmp_open
    GlobalConfigHandleKernel.global_epoll_handle_filesize[client_fd]=file_size
    GlobalConfigHandleKernel.global_epoll_handle_filefsize[client_fd]=0
    GlobalConfigHandleKernel.global_epoll_handle_filemode[client_fd]=file_mod
    GlobalConfigHandleKernel.global_epoll_handle_filename[client_fd]=file_fd_filename
    GlobalConfigHandleKernel.global_epoll_handle_fileexec[client_fd]=exec_toks
    return 1

def clear_http_tok(client_fd):
    GlobalConfigHandleKernel.global_epoll_handle_httpgettok[client_fd]=None
    GlobalConfigHandleKernel.global_epoll_handle_httpposttok[client_fd]=None
    GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[client_fd]=None


def set_http_tok(client_fd,file_size,file_name,file_dir):
    GlobalConfigHandleKernel.global_epoll_handle_httpgettok[client_fd]="1"
    GlobalConfigHandleKernel.global_epoll_handle_httpposttok[client_fd]=None
    GlobalConfigHandleKernel.global_epoll_handle_httppostfiletok[client_fd]=None
    return 1

def unversal_write_log_2(log_fd_un,log_string):
    rlw=LogRecord.RecordLogWriter(log_fd_un)
    rlw_result=rlw.write_log(log_string)
    if(rlw_result is None or rlw_result !=0):
        print "Error to write log file on %s\n" % log_string
        return "error"
    return "ok"

def check_valid_file(log_c_fd,file_dir_name):
    if(len(file_dir_name.strip()) ==0):
        return -1
    file_dir_len=len(file_dir_name.strip())
    counter_i=0
    while(counter_i < file_dir_len-1):
        if(file_dir_name[counter_i:counter_i+1] == ".." or file_dir_name[counter_i:counter_i+1] == ".\\" or file_dir_name[counter_i:counter_i+1] == "./"):
             unversal_write_log_2(log_c_fd,"Error file name for upload %s \n" % file_dir_name)
             return -2
        counter_i=counter_i+1
    return 1

def check_valid_dir(log_c_fd,file_dir_name):
    if(len(file_dir_name.strip()) ==0):
        return -1
    if(file_dir_name == "/" or file_dir_name == "/." or file_dir_name == "./" or file_dir_name == "/etc/" or file_dir_name == "/etc" or file_dir_name == "/root/" or file_dir_name == "/root" or file_dir_name == "/proc/" or file_dir_name == "/proc" or (".." in file_dir_name)):
        unversal_write_log_2(log_c_fd,"Error file dir for upload %s \n" % file_dir_name)
        return -1
    return 1

def translate_path(path,g_config_h):
    save_path_p=path
    path=path.replace("\\","/")
    path=path.replace("//","/")
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    if((len(save_path_p) >= 10) and ("/kcgi-bin/" == save_path_p[0:10])):
        if(not os.path.isdir(g_config_h['LISTHOME'] + "/kcgi-bin")):
            path=os.getcwd()
        else:
            path = g_config_h['LISTHOME']
    else:
        path = g_config_h['LISTHOME']
    for word in words:
        path = os.path.join(path, word)
    return path


def guess_type(path):
    base, ext = posixpath.splitext(path)
    if ext in GlobalConfigHandleKernel.extensions_map:
        return GlobalConfigHandleKernel.extensions_map[ext]
    ext = ext.lower()
    if ext in GlobalConfigHandleKernel.extensions_map:
        return GlobalConfigHandleKernel.extensions_map[ext]
    else:
        return GlobalConfigHandleKernel.extensions_map['']

def post_directory_suc(r,connnnnn,p_id,ffiles,rrfn,h_prot):
    f = StringIO.StringIO()
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n')
    f.write("<html>\n<title>Results:</title>\n")
    f.write("<body>\n<h2>Result:</h2>\n")
    f.write("<hr>\n")
    suc_tok="200"
    if r:
        f.write("<strong>Success:</strong>\n")
    else:
        f.write("<strong>Failed:</strong>\n")
    f.write(ffiles)
    #f.write("<br><a href=\"http://%s\">back</a>\n" % rrfn)
    #f.write("<br><a href=javascript:history.back(-2);javascript:window.location.reload()>back</a>\n")
    f.write("<br><a href=javascript:history.back(-2)>back</a>\n")
    f.write("<hr><small>Contact: kernelhuang\n")
    f.write("</small></body>\n</html>\n")
    f.flush()
    length = f.tell()
    f.seek(0)
    data_send_result=None
    try:
        c_file_obj=connnnnn.makefile()
        ff=StringIO.StringIO()
        ff.write("%s 200 OK\r\n" % h_prot)
        ff.write("Server: kernelHTTP/1.0\r\n")
        ff.write("Content-Type: text/html\r\n")
        ff.write("Content-Length: %s\r\n\r\n" % str(length))
    	ff.flush()
        ff.seek(0)
    	shutil.copyfileobj(ff,c_file_obj)
        shutil.copyfileobj(f,c_file_obj)
    	c_file_obj.flush()
    except:
        print "Error to send to client on post_directory_suc function"
        suc_tok="000"
    finally:
        ff.close()
    f.close()
    return suc_tok

def common_send_http_error(connnnnn,ske):
    try:
        f=StringIO.StringIO()
    	c_file_obj=connnnnn.makefile()
        f.write("HTTP/1.1 200 OK\r\n")
        f.write("Server: kernelHTTP/1.0\r\n")
        f.write("Content-Type: text/html\r\n")
        f.write("Content-Length: %d\r\n\r\n" % len(ske))
        f.write(ske)
    	f.flush()
        f.seek(0)
    	shutil.copyfileobj(f,c_file_obj)
        c_file_obj.flush()
    except:
        pass
    finally:
        f.close()
    return None

def common_send_http(connnnnn):
    try:
    	f=StringIO.StringIO()
        c_file_obj=connnnnn.makefile()
    	f.write("HTTP/1.1 200 OK\r\n")
        f.write("Server: kernelHTTP/1.0\r\n")
        f.write("Content-Type: text/html\r\n\r\n")
    	f.flush()
        f.seek(0)
    	shutil.copyfileobj(f,c_file_obj)
    	c_file_obj.flush()
    except:
        pass
    finally:
        f.close()
    return None

def common_send_exec(connnnnn):
    try:
    	f=StringIO.StringIO()
        c_file_obj=connnnnn.makefile()
    	f.write("HTTP/1.1 200 OK\r\n")
        f.write("Server: kernelHTTP/1.0\r\n")
        #f.write("Content-Type: text/html\r\n\r\n")
        f.flush()
    	f.seek(0)
    	shutil.copyfileobj(f,c_file_obj)
    	c_file_obj.flush()
    except:
        pass
    finally:
        f.close()
    return None

def post_cgi_upload_file(connnnnn,connnnnn_fd,c_log_fd,addr,udata,noab_url,noab_uri,g_config_h,h_prot,http_cookie,content_len,u_tmpfile,p_boundary):
        file_script_name=str(udata)
        n_user_suffix=""
        if("." in udata):
            n_user_suffix=udata[udata.rindex("."):]
        if(not os.path.isfile(file_script_name)):
            common_send_http_error(connnnnn,"Error request cgi,not file")
            connnnnn.close()
            return "002"
        if((not os.access(file_script_name,os.X_OK)) and (n_user_suffix != ".php")):
            common_send_http_error(connnnnn,"Error request cgi,no executable")
            connnnnn.close()
            return "002"
        real_interpreter=None
        if(n_user_suffix in GlobalConfigHandleKernel.global_cgi_hash_lst):
            real_interpreter=GlobalConfigHandleKernel.global_cgi_hash_lst[n_user_suffix]
        else:
            real_interpreter="/bin/bash"
        if(not os.path.isfile(real_interpreter)):
            common_send_http_error(connnnnn,"Error request cgi,no interpreter")
            connnnnn.close()
            return "002"
        pipein,pipeout = os.pipe()
        child_pids=os.fork()
        if(child_pids==0):
            connnnnn.setblocking(1)
            os.environ['SERVER_NAME']="KernelWebserver.com"
            os.environ['SERVER_SOFTWARE']="KernelWebServer"
            os.environ['GATEWAY_INTERFACE']="CGI/1.1"
            os.environ['SERVER_PROTOCOL']=h_prot
            os.environ['SERVER_PORT']=g_config_h['SERVER_PORT']
            os.environ['REQUEST_METHOD']="POST"
            os.environ['REMOTE_ADDR']=str(addr[0])
            os.environ['HTTP_ACCEPT']="image/gif,image/jpeg,image/pjpeg,image/pjpeg,application/x-shockwave-flash,application/vnd.ms-excel,application/vnd.ms-powerpoint,application/msword,application/xaml+xml,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            os.environ['PATH_INFO']=""
            os.environ['HTTP_COOKIE']=http_cookie
            os.environ['HTTP_COOKIE_VARS']=http_cookie
            os.environ['PATH_TRANSLATED']=""
            #HTTP_POST_FILES
            os.environ['DOCUMENT_ROOT']=os.getcwd()
            os.environ['SCRIPT_NAME']=noab_url
            os.environ['REMOTE_USER']=getpass.getuser()
            os.environ['CONTENT_TYPE']="multipart/form-data; boundary=" + p_boundary
            #os.environ['REDIRECT_STATUS']="200"
            os.environ['REDIRECT_STATUS']="1"
            os.environ['SCRIPT_FILENAME']=file_script_name
            os.environ['REQUEST_URI']=noab_uri
            os.environ['CONTENT_LENGTH']=str(content_len)
            pfile_get=noab_uri.split("?")[1]
            os.environ['QUERY_STRING']=pfile_get
            try:
                os.close(pipeout)
                os.dup2(pipein,0)
                os.dup2(connnnnn_fd,1)
                os.dup2(connnnnn_fd,2)
            except:
                pass
            for fd in range(3,128):
                if(fd!=connnnnn_fd and fd!=pipeout and fd!=pipein):
                    try:
                        os.close(fd)
                    except:
                        pass
            try:
                connnnnn.send(h_prot + " 200 OK\r\nConnection: Close,cgi\r\n")
            except:
                exit(1)
            if(n_user_suffix == ".php"):
                os.execv(real_interpreter,("",))
            else:
                os.execv("." + file_script_name,("",))
            #never be here
            exit(1)
        connnnnn.close()
        os.close(pipein)
        try:
            tmp_write_php=open(u_tmpfile,"rb")
        except:
            os.kill(child_pids,9)
            os.close(pipeout)
            return "002"
        try:
            ktmp=tmp_write_php.read(4096)
            while(ktmp):
                split_k=ktmp
                split_k_i=0
                while(split_k_i < len(split_k)):
                    split_k_i=os.write(pipeout,split_k)
                    if(split_k_i == len(split_k)):
                        break
                    split_k=split_k[split_k_i:]
                    split_k_i=0
                    continue
                ktmp=tmp_write_php.read(4096)
        except:
            os.kill(child_pids,9)
            os.close(pipeout)
            return "002"
        finally:
            tmp_write_php.close()
        os.close(pipeout)
        try:
            os.unlink(u_tmpfile)
        except:
            pass
        GlobalConfigHandleKernel.global_cgi_process_pid.put([child_pids])
        return "002"

def encodeNetstring(s):
    return ''.join([str(len(s)), ':', s, ','])

def list_http_directory(connnnnn,connnnnn_fd,c_log_fd,epoll_f,addr,udata,uhttp_para,uhttp_all,g_config_h,h_prot,http_sms_log_queue,http_mail_log_queue,http_method_t="GET",http_cookie="",tok=0):
    n_user_dir=""
    udata_ok_exec=""
    upost_get=""
    if(http_method_t =="GET"):
        usplit_t=udata.split("?")
        if(len(usplit_t)==2):
            n_user_dir=usplit_t[0]
            udata_ok_exec=usplit_t[1]
            #udata_ok_exec=udata_ok_exec.replace("\r\n","\r")
        else:
            n_user_dir=usplit_t[0]
    else:
        usplit_t=udata.split("?")
        if(len(usplit_t)==2):
            n_user_dir=usplit_t[0]
            upost_get=usplit_t[1]
        else:
            n_user_dir=usplit_t[0]
        udata_ok_exec=uhttp_para
        #udata_ok_exec=udata_ok_exec.replace("\r\n","\r")
    n_user_cgitok=0
    n_user_suffix=""
    if(("." in n_user_dir) and (len(n_user_dir) >=10) and ("/kcgi-bin/" == n_user_dir[0:10])):
        n_user_suffix=n_user_dir[n_user_dir.rindex("."):]
        if(n_user_suffix in GlobalConfigHandleKernel.global_cgi_hash_lst):
            n_user_cgitok=1
    if(("." not in n_user_dir) and (len(n_user_dir) >=10) and ("/kcgi-bin/" == n_user_dir[0:10])):
        n_user_cgitok=1
    ##########################################################################################################################
    ##########simple FCGI implementation total length < 4096##################################################################
    if(("." in n_user_dir) and (len(n_user_dir) >=11) and ("/kfcgi-bin/" == n_user_dir[0:11]) and g_config_h['FCGI_ENABLE'] == "1"):
        k_scgi_con=None
        k_scgi_server=g_config_h['FCGI_SERVER'].split(":")[0]
        k_scgi_port=g_config_h['FCGI_SERVER'].split(":")[1]
        if((k_scgi_port is None) or (k_scgi_port =="") or (k_scgi_server is None) or (k_scgi_server =="")):
            common_send_http_error(connnnnn,"Error fcgi configurarion")
            return "002"
        headers_out={}
        headers_out['SERVER_NAME']="KernelWebserver.com"
        headers_out['SERVER_SOFTWARE']="KernelWebServer"
        headers_out['SERVER_PROTOCOL']=h_prot
        headers_out['SERVER_PORT']=g_config_h['SERVER_PORT']
        headers_out['HTTP_ACCEPT']="image/gif,image/jpeg,image/pjpeg,image/pjpeg,application/x-shockwave-flash,application/vnd.ms-excel,application/vnd.ms-powerpoint,application/msword,application/xaml+xml,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers_out['HTTP_COOKIE']=http_cookie
        headers_out['HTTP_COOKIE_VARS']=http_cookie
        headers_out['REQUEST_METHOD']=http_method_t
        headers_out['REQUEST_URI']=udata
        headers_out['REMOTE_ADDR']=str(addr[0])
        headers_out['REMOTE_USER']=getpass.getuser()
        headers_out['PATH_INFO']=""
        headers_out['PATH_TRANSLATED']=""
        headers_out['CONTENT_TYPE']="application/x-www-form-urlencoded"
        headers_out['REDIRECT_STATUS']="200"
        n_user_dir=n_user_dir.replace("//","/")
        #file_script_name=str(os.getcwd() + n_user_dir)
        file_script_name=str(g_config_h['FCGI_DOC_ROOT'] + n_user_dir)
        headers_out['SCRIPT_NAME']=n_user_dir
        headers_out['SCRIPT_FILENAME']=file_script_name
        headers_out['DOCUMENT_ROOT']=g_config_h['FCGI_DOC_ROOT']
        transfer_parameters=udata_ok_exec
        if(http_method_t == "GET"):
            headers_out['QUERY_STRING']=transfer_parameters
            headers_out['CONTENT_LENGTH']="0"
        else:
            headers_out['CONTENT_LENGTH']=str(len(transfer_parameters))
            headers_out['QUERY_STRING']=upost_get
        myfcgiapp = KernelFCGI.FCGIApp(connect=(k_scgi_server,int(k_scgi_port)))
        fcgi_result=""
        try:
            fcgi_result=myfcgiapp.mecall(headers_out,http_method_t,transfer_parameters)
        except:
            common_send_http_error(connnnnn,"Error occured during fcgi backend handle")
            return "002"
        if(fcgi_result is None or fcgi_result==""):
            common_send_http_error(connnnnn,"No results returned")
            return "002"
        c_file_obj=connnnnn.makefile()
        try:
            fs_2=StringIO.StringIO()
            fs_2.write("%s 200 OK\r\n" % h_prot)
            fs_2.write("Server: kernelHTTP/1.0\r\n")
            fs_2.write("Content-Type: text/html\r\n")
            fs_2.write("Content-Length: %d\r\n\r\n" % len(fcgi_result))
            fs_2.write(fcgi_result)
            fs_2.flush()
            fs_2.seek(0)
            shutil.copyfileobj(fs_2,c_file_obj)
        except:
            print "Error to send to client on scgi %s(%s)" % (addr,udata)
        finally:
            fs_2.close()
        return "002"
    ##########################################################################################################################
    ##########simple SCGI implementation total length < 4096##################################################################
    if(("." in n_user_dir) and (len(n_user_dir) >=11) and ("/kscgi-bin/" == n_user_dir[0:11]) and g_config_h['SCGI_ENABLE'] == "1"):
        k_scgi_con=None
        k_scgi_server=g_config_h['SCGI_SERVER'].split(":")[0]
        k_scgi_port=g_config_h['SCGI_SERVER'].split(":")[1]
        if((k_scgi_port is None) or (k_scgi_port =="") or (k_scgi_server is None) or (k_scgi_server =="")):
            common_send_http_error(connnnnn,"Error scgi configurarion")
            return "002"
        try:
            k_scgi_con=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            common_send_http_error(connnnnn,"Error create local socket")
            return "002"
        try:
            k_scgi_con.settimeout(10)
            k_scgi_con.connect((k_scgi_server,int(k_scgi_port)))
            k_scgi_con.settimeout(None)
        except:
            common_send_http_error(connnnnn,"Error scgi configurarion or error remote scgi server")
            k_scgi_con.close()
            return "002"
        headers_out={}
        headers_out['SERVER_NAME']="KernelWebserver.com"
        headers_out['SERVER_SOFTWARE']="KernelWebServer"
        headers_out['SERVER_PROTOCOL']=h_prot
        headers_out['SERVER_PORT']=g_config_h['SERVER_PORT']
        headers_out['HTTP_ACCEPT']="image/gif,image/jpeg,image/pjpeg,image/pjpeg,application/x-shockwave-flash,application/vnd.ms-excel,application/vnd.ms-powerpoint,application/msword,application/xaml+xml,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers_out['HTTP_COOKIE']=http_cookie
        headers_out['HTTP_COOKIE_VARS']=http_cookie
        headers_out['REQUEST_METHOD']=http_method_t
        headers_out['REQUEST_URI']=udata
        headers_out['REMOTE_ADDR']=str(addr[0])
        headers_out['REMOTE_USER']=getpass.getuser()
        headers_out['PATH_INFO']=""
        headers_out['PATH_TRANSLATED']=""
        headers_out['CONTENT_TYPE']="application/x-www-form-urlencoded"
        headers_out['REDIRECT_STATUS']="200"
        n_user_dir=n_user_dir.replace("//","/")
        #file_script_name=str(os.getcwd() + n_user_dir)
        file_script_name=str(g_config_h['SCGI_DOC_ROOT'] + n_user_dir)
        headers_out['SCRIPT_NAME']=n_user_dir
        headers_out['SCRIPT_FILENAME']=file_script_name
        headers_out['DOCUMENT_ROOT']=g_config_h['SCGI_DOC_ROOT']
        transfer_parameters=udata_ok_exec
        headers_real_out=[]
        if(http_method_t == "POST"):
            headers_real_out = ['CONTENT_LENGTH', str(transfer_parameters), 'SCGI', '1']
            #headers_real_out['QUERY_STRING']=upost_get
        else:
            headers_real_out = ['CONTENT_LENGTH', "0", 'SCGI', '1']
            headers_out['QUERY_STRING']=transfer_parameters
        for k,v in headers_out.items():
            #if(v is None or v ==""):
            #    continue
            headers_real_out.append(k)
            headers_real_out.append(v)
        headers_real_out.append('') # For trailing NUL
        try:
            k_scgi_con.send(encodeNetstring('\x00'.join(headers_real_out)))
        except:
            common_send_http_error(connnnnn,"Error to send request headers to remote scgi server")
            k_scgi_con.close()
            return "002"
        if(http_method_t == "POST" and len(transfer_parameters)!=0):
            try:
                trans_counter=0
                while True:
                    need_to_tran=transfer_parameters[trans_counter:4096]
                    if(need_to_tran != ""):
                        k_scgi_con.send(need_to_tran)
                    else:
                        break
                    trans_counter=trans_counter + 4096        
                    continue
            except:
                common_send_http_error(connnnnn,"Error to send request body to remocte scgi server")
                k_scgi_con.close()
                return "002"
        scgi_response_result=[]
        try:
            while True:
                s_tmp_read=k_scgi_con.recv(4096)
                if(s_tmp_read is None or s_tmp_read ==""):
                    break
                scgi_response_result.append(s_tmp_read)
        except:
            common_send_http_error(connnnnn,"Error to read scgi result from remote scgi server")
            k_scgi_con.close()
            return "002"
        k_scgi_con.close()
        scgi_response_result="".join(scgi_response_result)
        # Parse response headers
        s_status = '200 OK'
        s_headers = []
        pos = 0
        while True:
            eolpos =scgi_response_result.find('\n', pos)
            if(eolpos < 0):
                break
            line = scgi_response_result[pos:eolpos-1]
            pos = eolpos + 1
            line = line.strip()
            if(not line):
                break
            header, value = line.split(':', 1)
            header = header.strip().lower()
            value = value.strip()
            if header == 'status':
                s_status = value
                if(s_status.find(' ') < 0):
                    s_status += ' SCGIApp'
            else:
                s_headers.append((header, value))
        scgi_response_result = scgi_response_result[pos:]
        #start_response(s_status, s_headers)
        c_file_obj=connnnnn.makefile()
        try:
            fs_2=StringIO.StringIO()
            fs_2.write("%s 200 OK\r\n" % h_prot)
            fs_2.write("Server: kernelHTTP/1.0\r\n")
            fs_2.write("Content-Type: text/html\r\n")
            fs_2.write("Content-Length: %d\r\n\r\n" % len(scgi_response_result))
            fs_2.write(scgi_response_result)
            fs_2.flush()
            fs_2.seek(0)
            shutil.copyfileobj(fs_2,c_file_obj)
        except:
            print "Error to send to client on scgi %s(%s)" % (addr,udata)
        finally:
            fs_2.close()
        return "002"
    get_spe_tok=re.findall(r"^/kcgi-bin/(.*)$",udata)
    if(get_spe_tok is not None and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0 and n_user_cgitok==1):
        if(g_config_h['CGI_ENABLE'] != "1"):
            common_send_http_error(connnnnn,"Error request cgi")
            return "002"
        transfer_parameters=udata_ok_exec
        #if(".." in user_dir):
        if(".." in n_user_dir):
            common_send_http_error(connnnnn,"Error request cgi ,wrong path")
            return "002"
        #user_suffix=""
        #if(len(user_dir) > 4):
        #    user_suffix=user_dir[-4:]
        #user_dir=user_dir.replace("//","/")
        n_user_dir=n_user_dir.replace("//","/")
        #file_script_name=str(os.getcwd() + "/kcgi-bin/" + user_dir)
        file_script_name=str(os.getcwd() + n_user_dir)
        if(not os.path.isfile(file_script_name)):
            common_send_http_error(connnnnn,"Error request cgi,not file")
            return "002"
        #if((not os.access(file_script_name,os.X_OK)) and (user_suffix != ".php")):
        if((not os.access(file_script_name,os.X_OK)) and (n_user_suffix != ".php")):
            common_send_http_error(connnnnn,"Error request cgi,no executable")
            return "002"
        #cgi_hash_list=eval(g_config_h['CGI_SUPPORT'])
        real_interpreter=None
        #if(user_suffix in cgi_hash_list):
        if(n_user_suffix in GlobalConfigHandleKernel.global_cgi_hash_lst):
            #real_interpreter=cgi_hash_list[user_suffix]
            real_interpreter=GlobalConfigHandleKernel.global_cgi_hash_lst[n_user_suffix]
        else:
            real_interpreter="/bin/bash"
        if(not os.path.isfile(real_interpreter)):
            common_send_http_error(connnnnn,"Error request cgi,no interpreter")
            return "002"
        if(http_method_t == "POST"):
            pipein,pipeout = os.pipe()
        child_pids=os.fork()
        if(child_pids==0):
            connnnnn.setblocking(1)
            os.environ['SERVER_NAME']="KernelWebserver.com"
            os.environ['SERVER_SOFTWARE']="KernelWebServer"
            os.environ['GATEWAY_INTERFACE']="CGI/1.1"
            os.environ['SERVER_PROTOCOL']=h_prot
            os.environ['SERVER_PORT']=g_config_h['SERVER_PORT']
            os.environ['REQUEST_METHOD']=http_method_t
            os.environ['REMOTE_ADDR']=str(addr[0])
            #os.environ['HTTP_ACCEPT']="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            os.environ['HTTP_ACCEPT']="image/gif,image/jpeg,image/pjpeg,image/pjpeg,application/x-shockwave-flash,application/vnd.ms-excel,application/vnd.ms-powerpoint,application/msword,application/xaml+xml,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            os.environ['PATH_INFO']=""
            os.environ['HTTP_COOKIE']=http_cookie
            os.environ['HTTP_COOKIE_VARS']=http_cookie
            os.environ['PATH_TRANSLATED']=""
            #HTTP_POST_FILES
            os.environ['DOCUMENT_ROOT']=os.getcwd()
            #os.environ['SCRIPT_NAME']="/kcgi-bin/" + user_dir
            os.environ['SCRIPT_NAME']=n_user_dir
            if(http_method_t == "GET"):
                os.environ['QUERY_STRING']=transfer_parameters
            os.environ['REMOTE_USER']=getpass.getuser()
            os.environ['CONTENT_TYPE']="application/x-www-form-urlencoded"
            #os.environ['REDIRECT_STATUS']="200"
            os.environ['REDIRECT_STATUS']="1"
            os.environ['SCRIPT_FILENAME']=file_script_name
            os.environ['REQUEST_URI']=udata
            if(http_method_t == "POST"):
                #os.environ['CONTENT_LENGTH']=str(uhttp_all)
                os.environ['CONTENT_LENGTH']=str(len(transfer_parameters))
            	os.environ['QUERY_STRING']=upost_get
            try:
                if(http_method_t == "POST"):
                    os.close(pipeout)
                    os.dup2(pipein,0)
                else:
                    os.dup2(connnnnn_fd,0)
                os.dup2(connnnnn_fd,1)
                os.dup2(connnnnn_fd,2)
            except:
                pass
            for fd in range(3,128):
                if(http_method_t == "POST"):
                    if(fd!=connnnnn_fd and fd!=pipeout and fd!=pipein):
                        try:
                            os.close(fd)
                        except:
                            pass
                else:
                    if(fd!=connnnnn_fd):
                        try:
                            os.close(fd)
                        except:
                            pass
            #delete on 2012 09 14
            try:
                connnnnn.send(h_prot + " 200 OK\r\nConnection: Close,cgi\r\n")
            except:
                exit(1)
            #if(user_suffix == ".php"):
            if(n_user_suffix == ".php"):
                os.execv(real_interpreter,("",))
            else:
                #os.execv("./kcgi-bin/" + user_dir,("",))
                os.execv("." + n_user_dir,("",))
            #never be here
            exit(1)
        if(http_method_t == "POST"):
            os.close(pipein)
            try:
                os.write(pipeout,transfer_parameters)
                #ktmp=transfer_parameters[0:4096]
                #print len(transfer_parameters)
                #write_all_counter=0
                #while(ktmp and len(ktmp)>0):
                #    split_k=ktmp
                #    split_k_i=0
                #    while(split_k_i < len(split_k)):
                #        split_k_i=os.write(pipeout,split_k)
                #        if(split_k_i == len(split_k)):
                #            break
                #        split_k=split_k[split_k_i:]
                #        split_k_i=0
                #        continue
                #    if(len(ktmp)<4096):
                #        break
                #    write_all_counter=write_all_counter + 4096
                #    ktmp=transfer_parameters[write_all_counter:4096]
            except:
                os.kill(child_pids,9)
                os.close(pipeout)
                unversal_write_log_2(c_log_fd,"Close on exception for os.write data to pipeout: %d\n" % uhttp_all)
                return "002"
            os.close(pipeout)
        #common_send_http_error(connnnnn,"Successfully")
        GlobalConfigHandleKernel.global_cgi_process_pid.put([child_pids])
        return "002"
    if(n_user_dir == "/rstoreme" or n_user_dir == "/rstoreme/"):
        if(g_config_h['REDIS_CACHE_ENABLE'].strip() != "1"):
            return "001"
        array_file_iplist=udata_ok_exec.split("=")
        if(len(array_file_iplist)!=2):
            return "001"
        #########################################################################
        if(len(array_file_iplist[0].strip()) < 4):
            return "001"
        rstore_key=array_file_iplist[0].strip()[3:]
        rstore_value=array_file_iplist[1]
        rhostport=g_config_h['REDIS_CONN'].strip().split(":")
        if(len(rhostport)!=2):
            return "001"
        rstore_act=array_file_iplist[0].strip()[0:3]
        if(g_config_h['REDIS_CACHE_ENABLE'].strip() == "1"):
            import redis
        rstorehandle=redis.Redis(host=rhostport[0],port=int(rhostport[1]),db=0,password=None,socket_timeout=3)
        try:
            if(rstore_act == "get"):
                rvv=rstorehandle.get(rstore_key)
                if(rvv is None or rvv==""):
                    connnnnn.send("No DATA\r\n")
                else:
                    connnnnn.send(rvv + "\r\n")
            elif(rstore_act == "set"):
                rvv=rstorehandle.set(rstore_key,rstore_value)
                if(rvv is None or rvv is False or rvv==""):
                    connnnnn.send("RStored failed\r\n")
                else:
                    connnnnn.send("RStored ok\r\n")
            elif(rstore_act.strip() == "del"):
                rvv=rstorehandle.delete(rstore_key)
                connnnnn.send("RDelete ok\r\n")
            else:
                connnnnn.send("Error rstore command\r\n")
        except:
            pass
        return "002"
        #########################################################################
    if(n_user_dir == "/setuntarip" or n_user_dir == "/setuntarip/"):
        array_file_iplist=udata_ok_exec.split("=")
        if(len(array_file_iplist)!=2):
            return "001"
        if(".." in array_file_iplist[1] or ("/" not in array_file_iplist[1])):
            return "001"
        #unversal_write_log_2(sms_log_fd,str(udata_ok_exec.strip()) + "\n")
        if(g_config_h['UNTAR_SYNC_ENABLE'].strip() == "1"):
            GlobalConfigHandleKernel.global_untar_iptask.put(["setuntar " + array_file_iplist[1].replace(":"," "),str(addr[0])])
            return "008"
        else:
            common_send_http_error(connnnnn,"NotOpen")
            return "002"
    if(n_user_dir == "/autountarip" or n_user_dir == "/autountarip/"):
        array_file_iplist=udata_ok_exec.split("=")
        if(len(array_file_iplist)!=2):
            return "001"
        if(".." in array_file_iplist[1] or ("/" not in array_file_iplist[1])):
            return "001"
        if(g_config_h['UNTAR_SERVER_ENABLE'].strip() == "1"):
            GlobalConfigHandleKernel.global_autountar_iptask.put(["autountar " + array_file_iplist[1].replace(":"," "),connnnnn,connnnnn_fd])
            return "008"
        else:
            common_send_http_error(connnnnn,"NotOpen")
            return "002"
    if(n_user_dir == "/globals" or n_user_dir == "/globals/"):
        array_file_iplist=udata_ok_exec.split("=")
        if(len(array_file_iplist)!=2):
            return "001"
        if(".." in array_file_iplist[0]):
            return "001"
        g_config_h[array_file_iplist[0].strip()]=array_file_iplist[1].strip()
        return "008"
    udata=urllib.unquote(udata)
    webno_find=re.findall(r"/(webno[0-9]{2})",udata)
    webno_find_file=None
    if(webno_find is not None and len(webno_find)!=0):
        webno_find_file=str(webno_find[0])
        #if(udata_ok_exec=="/webno" or udata_ok_exec=="/webno/"):
        suc_tok="200"
        f = StringIO.StringIO()
        #f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        #f.write("<html>\n<title>Query log page</title>\n")
        #f.write("<body>\n<h2>Input: </h2>\n")
        #f.write("<form method=\"get\" action=\"web\">")
        #f.write("<input type=\"hidden\" name=\"mk_web\" value=\"log_prod\"/>\n")
        #f.write("Time:<input name=\"mk_time\" type=\"text\" length=32 value=\"2012-01-01 06:00:00\"/>")
        #f.write("&nbsp;&nbsp;&nbsp;&nbsp;")
        #f.write("RoleID:<input name=\"mk_role\" type=\"text\" length=64/>")
        #f.write("&nbsp;&nbsp;&nbsp;&nbsp;")
        #f.write("ActionID:<input name=\"mk_action\" type=\"text\" size=32/>")
        #f.write("&nbsp;&nbsp;&nbsp;&nbsp;<input type=\"submit\" value=\"Query\"/><input type=reset value=\"Clear\"></form>\n")
        #f.write("</ul>\n</body>\n</html>\n")
        tpl_dict=eval(g_config_h['ALL_WEB_TMP'])
        current_dict_webno=None
        if(webno_find_file in tpl_dict):
            current_dict_webno=tpl_dict[webno_find_file]
        if(current_dict_webno is None):
            common_send_http_error(connnnnn,"Some error occured,none exists in hash")
            return "000"
        try:
            find_file_tpl=open(str(current_dict_webno),"r")
        except:
            common_send_http_error(connnnnn,"Some error occured,open file failed")
            return "000"
        f.write(find_file_tpl.read())
        f.flush()
        try:
            find_file_tpl.close()
        except:
            pass
        length = f.tell()
        f.seek(0)
        c_file_obj=connnnnn.makefile()
        try:
            fs_2=StringIO.StringIO()
            fs_2.write("%s 200 OK\r\n" % h_prot)
            fs_2.write("Server: kernelHTTP/1.0\r\n")
            fs_2.write("Content-Type: text/html\r\n")
            fs_2.write("Content-Length: %s\r\n\r\n" % str(length))
            fs_2.flush()
            fs_2.seek(0)
            shutil.copyfileobj(fs_2,c_file_obj)
            shutil.copyfileobj(f,c_file_obj)
        except:
            print "Error to send to client on %s(%s)" % (addr,udata)
            suc_tok="002"
        finally:
            fs_2.close()
        f.close()
        return suc_tok

    get_spe_tok=re.findall(r"/ok\?mk_dir=([0-9a-zA-Z/_-]*)",udata)
    if(get_spe_tok is not None and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        user_dir=str(get_spe_tok[0])
        user_index=udata_ok_exec.find("/ok?mk_dir=")
        if(user_index == -1):
            common_send_http_error(connnnnn,"Error mkdir request")
            return "000"
    	user_first=udata[0:user_index]
        user_last_create_dir=g_config_h['LISTHOME'] + user_first + "/" + user_dir
    	user_last_create_dir=user_last_create_dir.replace("//","/")
        if(os.path.isdir(user_last_create_dir)):
            common_send_http_error(connnnnn,"Directory exists")
    	    return 200
        try:
            os.makedirs(user_last_create_dir,0755)
    	except:
            return "001" 
    	common_send_http_error(connnnnn,"Successfully")
        return "200"
    get_spe_tok=re.findall(r"/exec\?mk_exec=(.*)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
    	real_exec=str(get_spe_tok[0])
        real_exec=real_exec.replace("+"," ")
        #common_send_exec(connnnnn)
        connnnnn.setblocking(0)
        #p_gop=SpecialOperationProcess.ProcessBashSpecial(connnnnn_fd,g_config_h,c_log_fd,connnnnn,addr,real_exec + " | sed 's/$/<br>/g'")
        p_gop=SpecialOperationProcess.ProcessBashSpecial(connnnnn_fd,g_config_h,c_log_fd,connnnnn,addr,real_exec)
    	gop_exec_result=p_gop.exe_spe_process()
        if(gop_exec_result != "ok"):
            unversal_write_log_2(c_log_fd,"Error to exec mk_exec process: %s:%s" % (str(addr[0]),real_exec))
            return "001"
        return "002"
    get_spe_tok=re.findall(r"/web\?mk_web=(.*)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
    	real_exec=str(get_spe_tok[0])
        p_gop=WebThreadLog.OperationThreadWeb(connnnnn_fd,g_config_h,c_log_fd,connnnnn,addr,"mk_web=" + real_exec)
        p_gop.daemon=True
        p_gop.start()
        return "004"
    #self.sms_log_queue.put(str(user_data_all.strip()))
    get_spe_tok=re.findall(r"/kmsg\?mk_kmsg=(.*)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        http_sms_log_queue.put(str(get_spe_tok[0]).strip())
        return "008"
    get_spe_tok=re.findall(r"/web\?mk_webshell=(1)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        try:
            fork_s=os.fork()
        except:
            return "001"
        if(fork_s==0):
            ph=ProcessShell.HandleShellProcess(g_config_h,connnnnn,connnnnn_fd)
            ph.operate()
        else:
            GlobalConfigHandleKernel.global_cgi_process_pid.put([fork_s])
            return "002"
    get_spe_tok=re.findall(r"/web\?mk_oscount=(1)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        f_sms=StringIO.StringIO()
        f_sms_have_tok=0
        for key_al in GlobalConfigHandleKernel.global_oscount_data:
            try:
                f_sms_have_tok=1
                f_sms.write(str(GlobalConfigHandleKernel.global_oscount_data[key_al]) + "\n")
                f_sms.flush()
            except:
                break
        if(f_sms_have_tok==0):
            f_sms.write("NO DATA\n")
            f_sms.flush()
        c_file_obj=connnnnn.makefile()
        f_sms.seek(0)
        try:
            shutil.copyfileobj(f_sms,c_file_obj)
            c_file_obj.flush()
        except:
            pass
        finally:
            f_sms.close()
        return "002"
    get_spe_tok=re.findall(r"/web\?mk_sms=(1)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        f_sms=StringIO.StringIO()
        f_sms_have_tok=0
        while(1):
            if(http_sms_log_queue.empty()):
                break
            f_sms_have_tok=1
            f_sms.write(http_sms_log_queue.get() + "\n")
            f_sms.flush()
        if(f_sms_have_tok==0):
            f_sms.write("NO DATA\n")
            f_sms.flush()
        c_file_obj=connnnnn.makefile()
        f_sms.seek(0)
        try:
            shutil.copyfileobj(f_sms,c_file_obj)
            c_file_obj.flush()
        except:
            pass
        finally:
            f_sms.close()
        return "002"
    #self.log_log_queue.put(str(user_data_all.strip()))
    get_spe_tok=re.findall(r"/kmail\?mk_kmail=(.*)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        http_mail_log_queue.put(str(get_spe_tok[0]).strip())
        return "008"
    get_spe_tok=re.findall(r"/web\?mk_mail=(1)",udata)
    if(not(get_spe_tok is None) and len(get_spe_tok)==1 and not(get_spe_tok[0] is None) and len(get_spe_tok[0])!=0):
        f_sms=StringIO.StringIO()
        f_sms_have_tok=0
        while(1):
            if(http_mail_log_queue.empty()):
                break
            f_sms_have_tok=1
            f_sms.write(http_mail_log_queue.get() + "\n")
            f_sms.flush()
        if(f_sms_have_tok==0):
            f_sms.write("NO DATA\n")
            f_sms.flush()
        c_file_obj=connnnnn.makefile()
        f_sms.seek(0)
        try:
            shutil.copyfileobj(f_sms,c_file_obj)
            c_file_obj.flush()
        except:
            pass
        finally:
            f_sms.close()
        return "002"

    rpath=translate_path(udata,g_config_h)
    suc_tok="200"
    data_send_result=None
    if(not os.path.isfile(rpath) and not os.path.isdir(rpath)):
        #common_send_http(connnnnn)
    	return "001"
    if(os.path.isfile(rpath)):
        ctype = guess_type(rpath)
        c_file_obj=connnnnn.makefile()
        try:
            fs = os.stat(rpath)
    	    f = StringIO.StringIO()
            #h_file_datetime=h_date_time_string(fs.st_mtime)
            f.write("%s 200 OK\r\n" % h_prot)
            f.write("Server: kernelHTTP/1.0\r\n")
            f.write("Content-Type: %s\r\n" % ctype)
            f.write("Content-Length: %s\r\n\r\n" % str(fs[6]))
    	    f.flush()
            f.seek(0)
            shutil.copyfileobj(f,c_file_obj)
            c_file_obj.flush()
        except:
            print "Error to send to client on file %s(%s)" % (addr,udata)
            suc_tok="000"
    	finally:
            f.close()
        if(suc_tok.strip() == "000"):
            return suc_tok
        #def list_http_directory(connnnnn,connnnnn_fd,c_log_fd,epoll_f,addr,udata,g_config_h,h_prot,http_sms_log_queue,http_mail_log_queue,http_method_t="GET",http_cookie="",tok=0):
        if(g_config_h['ASYNC_CLIENT_ENABLE'].strip() == "1"):
            #here error because of the ff will be closed after return from THIS  FUNCTION
            GlobalConfigHandleKernel.global_eventio_queue.put([rpath,connnnnn,"1"])
            return "00k"
        elif(g_config_h['ASYNC_CLIENT_ENABLE'].strip() == "2"):
            GlobalConfigHandleKernel.global_eventio_queue.put([rpath,connnnnn,"2"])
            return "00k"
        else:
            try:
                ff = open(rpath, 'rb')
            except IOError:
                return "001" 
            if(g_config_h['ASYNC_CLIENT_ENABLE'].strip() == "3"):
                #here error because of the ff will be closed after return from THIS  FUNCTION
                GlobalConfigHandleKernel.global_asyncclient_epoll_handle_openfile[connnnnn_fd]=ff
                GlobalConfigHandleKernel.global_asyncclient_epoll_handle_conn[connnnnn_fd]=connnnnn
                GlobalConfigHandleKernel.global_asyncclient_epollfd.register(connnnnn_fd,select.EPOLLOUT|select.EPOLLIN)
                return "00k"
            try:
                shutil.copyfileobj(ff,c_file_obj)
                c_file_obj.flush()
            except:
                pass
            ff.close()
        return suc_tok

    try:
        list = os.listdir(rpath)
    except os.error:
        return "001"
    list.sort(key=lambda a: a.lower())
    f = StringIO.StringIO()
    displaypath = cgi.escape(urllib.unquote(udata))
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
    f.write("<html>\n<title>Index of %s</title>\n" % displaypath)
    f.write("<body>\n<h2>Index of %s</h2>\n" % displaypath)
    #f.write("<hr>\n")
    f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
    f.write("<input name=\"file\" type=\"file\"/>")
    f.write("&nbsp;&nbsp;&nbsp;&nbsp;<input type=\"submit\" value=\"Upload\"/></form>\n")
    f.write("<form action=ok method=\"get\">")
    f.write("<input name=\"mk_dir\" type=\"text\" length=32/>")
    f.write("&nbsp;&nbsp;&nbsp;&nbsp;<input type=\"submit\" value=\"Mkdir\"/><input type=reset value=\"Clear\"></form>\n")
    if(g_config_h['DISPLAY_EXECUTE'] == "1"):
        f.write("<form action=exec method=\"get\">")
        f.write("<input name=\"mk_exec\" type=\"text\" size=100/>")
        f.write("&nbsp;&nbsp;&nbsp;&nbsp;<input type=\"submit\" value=\"Execute\"/><input type=reset value=\"Clear\"></form>\n")
    f.write("<hr>\n")
    #f.write("Go up direcory: <a href=%s>%s</a>\n" % (urllib.quote(displaypath),cgi.escape(displaypath)))
    #f.write("<hr>\n")
    f.write("<table border=0 width=100%>")
    for name in list:
        fullname = os.path.join(rpath, name)
        displayname = linkname = name
        if os.path.isdir(fullname):
            displayname = name + "/"
            linkname = name + "/"
        if os.path.islink(fullname):
            displayname = name + "@"
        if os.path.isfile(fullname):
            c_time_file=(os.stat(fullname))[8]
            c_size_file=(os.stat(fullname))[6]
            c_time_file=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(c_time_file))
            c_md5_file=None
            #f.write('<li><a href="%s">%s</a>&nbsp;&nbsp;&nbsp;&nbsp;<h6><color=red>%s</color></h6>\n' % (urllib.quote(linkname), cgi.escape(displayname),c_time_file))
            f.write('<tr><td><li><a href="%s">%s</a></td><td>%s</td><td><font size=2 color=green>%s</font></td><td><a href="%s">Pack</a></td><td><a href="%s">Unpack</a></td><td><a href="%s%s">Upload</a></td></tr>\n' % (urllib.quote(linkname), cgi.escape(displayname),str(c_size_file),c_time_file,urllib.quote("exec?mk_exec=cd " + rpath + "/ ; tar -cvf "+ cgi.escape(name) + "-" + str(random.random()) +".tar " + cgi.escape(name) + " 2>/dev/null"),urllib.quote("exec?mk_exec=cd " + rpath + "/ ; tar -xvf "+ cgi.escape(name) + " -C . 2>/dev/null"),g_config_h['PACK_UPLOAD_DOMAIN'],urllib.quote("?filepath=" + fullname +"&fileip=" + str(GlobalConfigHandleKernel.global_my_ip))))
            #####f.write(('<li><a$href="%s">%s</a>%s<font$size=2$color=green>%s</font>\n' % (urllib.quote(linkname), cgi.escape(displayname),str(c_size_file).rjust(64-len(cgi.escape(displayname))+len(str(c_size_file))),c_time_file.rjust(64-len(str(c_size_file))+len(c_time_file)))).replace(" ","&nbsp;").replace("$"," "))
            #f.write(('<li><a$href="%s">%s</a>%s<font size=2 color=green>%s</font>\n' % (urllib.quote(linkname), cgi.escape(displayname),str(os.stat(fullname)[6]).rjust(50-len(cgi.escape(displayname))),c_time_file)).replace(" ","&nbsp;").replace("$"," "))
            #f.write(('<li><a$href="%s">%s</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%40s&nbsp;&nbsp;<font size=2 color=green>%40s</font>\n' % (urllib.quote(linkname), cgi.escape(displayname),str(os.stat(fullname)[6]),c_time_file)).replace(" ","&nbsp;").replace("$"," "))
        else:
            f.write('<tr><td><li><a href="%s">%s</a></td><td></td><td></td><td><a href="%s">Pack</td></tr>\n' % (urllib.quote(linkname), cgi.escape(displayname),urllib.quote("exec?mk_exec=" + "tar -cvf " +rpath + "/"+ cgi.escape(name) + "-" + str(random.random()) +".tar " + fullname)))
    f.write("</table>\n<hr>\n</body>\n</html>\n")
    f.flush()
    length = f.tell()
    f.seek(0) 
    data_send_result=None
    c_file_obj=connnnnn.makefile()
    try:
        fs_2=StringIO.StringIO()
        fs_2.write("%s 200 OK\r\n" % h_prot)
        fs_2.write("Server: kernelHTTP/1.0\r\n")
        fs_2.write("Content-Type: text/html\r\n")
        fs_2.write("Content-Length: %s\r\n\r\n" % str(length))
        fs_2.flush()
        fs_2.seek(0)
        shutil.copyfileobj(fs_2,c_file_obj)
        shutil.copyfileobj(f,c_file_obj)
    except:
        print "Error to send to client on %s(%s)" % (addr,udata)
    	suc_tok="000"
    finally:
        fs_2.close()
    f.close()
    return suc_tok

#operation_web_log_write(conns,self.config_log_fd,sock_address,need_to_write_log_data,self.config_log_fd_web,self.web_queue)
def operation_web_log_write(conns,config_log_fd,sock_address,need_to_write_log_data,config_log_fd_web,web_queue,l_date,l_code):
    web_queue.put([need_to_write_log_data,l_date,l_code])
    try:
        conns.send("ok\r\n")
    except:
        return "error"
    return "ok"

def error_send_to_client(connnnnn,connnnnn_fd,send_string,c_log_fd,epoll_f,addr,udata,tok=0):
    if(tok==1):
        rlw=LogRecord.RecordLogWriter(c_log_fd)
        rlw_result=rlw.write_log("Here get reqeust from %s(%s)\n" % (addr,udata))
        if(rlw_result is None or rlw_result !=0):
            print "Error to write log file on %s(%s)" % (addr,udata)
            return "error"
        return "ok"
    
    data_send_result=None
    try:
        data_send_result=connnnnn.send(send_string)
    except:
        print "Error to send to client on %s(%s)" % (addr,udata)

    if(data_send_result is None or data_send_result<=0):
        rlw=LogRecord.RecordLogWriter(c_log_fd)
        rlw_result=rlw.write_log("Failed send error result to client through fd %s on %s(%s)\n" % (send_string,addr,udata))
        if(rlw_result is None or rlw_result !=0):
            print "Error to write log file on %s(%s)" % (addr,udata)
        epoll_f.unregister(connnnnn_fd)
        connnnnn.close()
        return "error"
    return "ok"

class OperationHttpPostfile(threading.Thread):
    def __init__(self,global_config_hash,config_log_fd,epollhandle,conns,p_id,sock_address,raw_user_string,post_dst_dir,http_protcols,boundary,allbytes,p_id_post,alive_post,cgi_upload_token,t_dst,t_dst_fix,a_cookie,save_allbytes):
        threading.Thread.__init__(self)
        self.global_config_hash=global_config_hash
        self.p_id_post=p_id_post
        self.config_log_fd=config_log_fd
        self.epollhandle=epollhandle
        self.conns=conns
        self.p_id=p_id
        self.sock_address=sock_address
        self.raw_user_string=raw_user_string
        self.post_dst_dir=post_dst_dir
        self.http_protcols=http_protcols
        self.boundary=boundary
        self.allbytes=allbytes
        self.alive_post=alive_post
        self.cgi_upload_token=cgi_upload_token
        self.t_dst=t_dst
        self.t_dst_fix=t_dst_fix
        self.a_cookie=a_cookie
        self.save_allbytes=save_allbytes

    def run(self):
        if True:
            if True:	
    	        rrfn = re.findall(r'Referer: http://([a-zA-Z0-9.:/_-]+)',self.raw_user_string)
                if(rrfn is None or len(rrfn)==0):
                    rrfn="/"
                c_dis_result=self.raw_user_string.find("Content-Disposition:")
                p_id_2=None
                f_dir=StringIO.StringIO()
                if(c_dis_result != -1):
                    f_dir.writelines(self.raw_user_string)
                    f_dir.flush()
                    f_dir.seek(c_dis_result-len(self.boundary)-2-2)
                    p_id_2=f_dir
                else:
                    p_id_2=self.p_id_post
                if(f_dir.tell() == len(self.raw_user_string)):
                    p_id_2=self.p_id_post
                ####add new cgi upload
                cgi_upload_tmp_file=""
                cgi_upload_handle=None
                if(self.cgi_upload_token ==1):
                    cgi_upload_tmp_file="/tmp/." + hashlib.md5(self.boundary).hexdigest() + ".tmpfile"
                    try:
                        cgi_upload_handle=open(cgi_upload_tmp_file,"wb")
                    except:
                        common_send_http_error(conns,"Error postfile,open cgi failed")
                        self.conns.close()
                        self.p_id_post.close()
                        return
                line = p_id_2.readline()
                self.allbytes -= len(line)
                if not self.boundary in str(line):
                    common_send_http_error(self.conns,"Error postfile,bound error")
                    print "Content NOT begin with boundary: %s %s" % (line,self.boundary)
                    self.conns.close()
                    self.p_id_post.close()
                    if(self.cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    return
                if(self.cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(self.raw_user_string)):
                    p_id_2=self.p_id_post
                line=p_id_2.readline()
                self.allbytes=self.allbytes-len(line)
                #fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
                fn = re.findall(r'Content-Disposition.*name=.*; filename="(.*)"', line)
                if(fn is None or len(fn)==0 or fn[0] is None or len(fn[0])==0):
                    common_send_http_error(self.conns,"Error postfile,filename error")
                    self.conns.close()
                    self.p_id_post.close()
                    if(self.cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    return
                fp_0=fn[0].replace("\\","/").split("/")
                fp_1=fp_0[len(fp_0)-1]
                if(fp_1 is None or len(fp_1)==0):
                    common_send_http_error(self.conns,"Error postfile,filename error")
                    self.conns.close()
                    self.p_id_post.close()
                    if(self.cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    return
                #here may be some lacks for hacker
                t_path=self.t_dst_fix
                t_path_save=t_path
                t_path_untar_tok=0
                fn=""
                out=None
                if(t_path == self.global_config_hash['WEB_UNTAR_URL'] or t_path == self.global_config_hash['WEB_UNTAR_URL'] + "/"):
                    t_path= self.global_config_hash['WEB_UNTAR_HOME'] + "/"
                    t_path_untar_tok=1
                if(self.cgi_upload_token==0):
                    #create dir
                    if(not os.path.isdir(t_path)):
                        try:
                            os.makedirs(t_path,0755)
                        except:
                            pass
                    fn = os.path.join(t_path, fp_1)
                if(self.cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(self.raw_user_string)):
                    p_id_2=self.p_id_post
                line=p_id_2.readline()
                self.allbytes=self.allbytes-len(line)
                if(self.cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(self.raw_user_string)):
                    p_id_2=self.p_id_post
                line=p_id_2.readline()
                self.allbytes=self.allbytes-len(line)
                try:
                    if(self.cgi_upload_token==0):
                        out = open(fn, 'wb')
                    else:
                        out=None
                except:
                    common_send_http_error(self.conns,"Error postfile,open failed")
                    self.conns.close()
                    self.p_id_post.close()
                    if(self.cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    return
                if(self.cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(self.raw_user_string)):
                    p_id_2=self.p_id_post
                preline=p_id_2.readline()
                self.allbytes=self.allbytes-len(preline)
                boundary_tok="0"
                cgi_boundary_tok="0"
                last_boundary=self.boundary + "--"
                while(self.allbytes > 0):
                    if(f_dir.tell() == len(self.raw_user_string)):
                        p_id_2=self.p_id_post
                    line = p_id_2.readline()
                    self.allbytes -= len(line)
                    if last_boundary in line:
                        if(self.cgi_upload_token ==1):
                            cgi_upload_handle.write(preline)
                            cgi_upload_handle.write(line)
                            cgi_upload_handle.flush()
                            try:
                                cgi_upload_handle.close()
                            except:
                                break
                            cgi_boundary_tok="1"
                            break
                        preline = preline[0:-1]
                        if preline.endswith('\r'):
                            preline = preline[0:-1]
                        try:
                            out.write(preline)
                            out.flush()
                            out.close()
                        except:
                            break
                        print "File '%s' uploaded success" % fn
                        boundary_tok="1"
                    else:
                        if(self.cgi_upload_token ==1):
                            cgi_upload_handle.write(preline)
                            cgi_upload_handle.flush()
                            preline=line
                            continue
                        if(self.allbytes < len(last_boundary)):
                            out.close()
                            boundary_tok="1"
                            print "File '%s' uploaded success,although no consistent stream" % fn
                            break
                        try:
                            out.write(preline)
                            out.flush()
                        except:
                            break
                        preline = line
                if(boundary_tok=="0"):
                    if(self.cgi_upload_token ==0):
                        print "Unexpect ends of data file '%s'" % fn
                        try:
                            out.close()
                        except:
                            pass
                if(cgi_boundary_tok=="0"):
                    if(self.cgi_upload_token ==1):
                        print "Unexpect ends of cgi data file '%s'" % cgi_upload_tmp_file
                        try:
                            cgi_upload_handle.close()
                        except:
                            pass
                f_dir.close()
                if(t_path_untar_tok == 0 and self.cgi_upload_token==0):
                    post_directory_suc(boundary_tok=="1",self.conns,self.p_id,fn,str(rrfn[0]),self.http_protcols)
                try:
                    #deleted on 2012-08-23 for untar self.conns.close()
                    self.p_id_post.close()
                except:
                    #add self.conns.close() on 2012-08-23 for untar
                    self.conns.close()
                    if(self.cgi_upload_token ==1):
                        try:
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    return
                if(t_path_untar_tok == 1 and boundary_tok =="1" and self.cgi_upload_token==0):
                    if(self.alive_post == "close" or self.alive_post == "none"):
                        GlobalConfigHandleKernel.task_data_queue.put(["utar",fn,self.p_id,self.conns,"close"])
                    else:
                        GlobalConfigHandleKernel.task_data_queue.put(["utar",fn,self.p_id,self.conns,"alive"]) 
                if(self.cgi_upload_token ==1 and cgi_boundary_tok=="1"):
                    #here handle cgi upload file post request and close client fd
                    #post_cgi_upload_file(connnnnn,connnnnn_fd,c_log_fd,addr,udata,noab_url,noab_uri,g_config_h,h_prot,http_cookie,content_len,u_tmpfile,p_boundary):
                    post_cgi_upload_file(self.conns,self.p_id,self.config_log_fd,self.sock_address,self.t_dst_fix,self.t_dst,self.post_dst_dir,self.global_config_hash,self.http_protcols,self.a_cookie,self.save_allbytes,cgi_upload_tmp_file,self.boundary)
                if(self.alive_post == "close"):
                    if(t_path_untar_tok ==0 and self.cgi_upload_token!=1):
                        self.conns.close()
                    else:
                        return
                else:
                    if(t_path_untar_tok ==1 or self.cgi_upload_token ==1):
                        return
    	            try:
    	    	        self.conns.setblocking(0)
                    	self.epollhandle.register(self.p_id, select.EPOLLIN)
    	            except:
                        self.conns.close()
                        #self.p_id_post.close()
                        return
                return


def post_long_parameters(global_config_hash,config_log_fd,epollhandle,conns,p_id,sock_address,raw_user_string,p_id_post,p_dirs,p_protocol,p_sms_log,p_mail_log):
    fn = re.findall(r'Connection: ([a-zA-Z]+)',raw_user_string)
    alive_post=None
    if(fn is None or len(fn)==0):
        #for modifed
        #common_send_http_error(conns,"Error post request,no connection")
        #conns.close()
        #p_id_post.close()
        #return None
        alive_post="close"
    else:
        alive_post=str(fn[0]).lower()
    a_cookie=""
    fn_cookie = re.findall(r'Cookie: ([^\r\n]+)',raw_user_string)
    if(fn_cookie is None or len(fn_cookie)==0):
        a_cookie=""
    else:
        a_cookie=str(fn_cookie[0])
    try:
        conns.setblocking(1)
    except:
        conns.close()
        p_id_post.close()
        return None
    fn = re.findall(r'Content-Length: ([0-9]+)',raw_user_string)
    if(fn is None or len(fn)==0):
        common_send_http_error(conns,"Error post request,no length")
        conns.close()
        p_id_post.close()
        return None
    allbytes=long(fn[0])
    if(allbytes >= long(int(global_config_hash['POST_LONG_PARAMETERS']))):
        conns.close()
        p_id_post.close()
        return "big"
    #    http_post_thread=OperationHttpPostLong(global_config_hash,config_log_fd,epollhandle,conns,p_id,sock_address,raw_user_string,data_split[1].strip(),data_split[2].strip(),boundary,allbytes,p_id_post,alive_post)
    #    http_post_thread.daemon=True
    #    http_post_thread.start()
    #    return "big"
    c_dis_result=raw_user_string.find("\r\n\r\n")
    p_id_2=None
    f_dir=StringIO.StringIO()
    if(c_dis_result != -1):
        f_dir.writelines(raw_user_string)
        f_dir.flush()
        f_dir.seek(c_dis_result + 2)
        p_id_2=f_dir
    else:
        p_id_2=p_id_post
    if(f_dir.tell() == len(raw_user_string)):
        p_id_2=p_id_post
    line = p_id_2.readline()
    line_from_string=""
    if(f_dir.tell() == len(raw_user_string)):
        p_id_2=p_id_post
    else:
        line_from_string=p_id_2.read(len(raw_user_string)-f_dir.tell())
    p_id_2=p_id_post
    line = p_id_2.read(allbytes-long(len(line_from_string)))
    #deleted on 20130719 line = p_id_2.readline()
    f_dir.close()
    if(long(len(line)+len(line_from_string))!= allbytes):
        common_send_http_error(conns,"Error post request bytes")
        conns.close()
        p_id_post.close()
        return None
    list_h_result=list_http_directory(conns,p_id,config_log_fd,epollhandle,sock_address,p_dirs,line_from_string+line,allbytes,global_config_hash,p_protocol,p_sms_log,p_mail_log,"POST",a_cookie)
    if(list_h_result == "000" or list_h_result == "001" or list_h_result == "002" or list_h_result == "008"):
        try:
            #if(list_h_result == "000" or list_h_result == "001"):
            if(list_h_result == "001"):
                common_send_http_error(conns,"Some errors occurred here,please contact the web administrator")
                #conns.send("Some errors occurred\r\n")
            elif(list_h_result == "008"):
                conns.send("Success\r\n")
        except:
            print "Some errors ocurred in sending some addtional error information\n"
        finally:
            conns.close()
            p_id_post.close()
        return None
    p_id_post.close()
    #here post long parameters is suitable for POST request which maybe never return 00k
    if(list_h_result == "004" or list_h_result == "00k"):
        return None
    if(alive_post == "close"):
        try:
            conns.close()
        except:
            return None
    else:
        try:
            conns.setblocking(0)
            epollhandle.register(p_id, select.EPOLLIN)
        except:
            conns.close()
            return None
    return "ok"


class OperationThreadGeneral(threading.Thread):
    
    def __init__(self,thread_queue,global_config_hash,config_log_fd,config_log_fd_web,web_queue,sms_log_fd,sms_log_queue,mail_log_queue):
        threading.Thread.__init__(self)
        self.thread_queue=thread_queue
        self.global_config_hash=global_config_hash
        self.config_log_fd=config_log_fd
        self.config_log_fd_web=config_log_fd_web
        self.web_queue=web_queue
        self.sms_log_fd=sms_log_fd
        self.sms_log_queue=sms_log_queue
        self.mail_log_queue=mail_log_queue

    def run(self):
        GlobalConfigHandleKernel.global_cgi_hash_lst=eval(self.global_config_hash['CGI_SUPPORT'])
        if(self.global_config_hash['REDIS_CACHE_ENABLE'].strip() == "1"):
            import redis
        while(1==1):
            #The following 3 lines is deleted on 2012-08-23
            #if(self.thread_queue.empty()):
            #    usleep(1000)
            #    continue
            #(p_key,p_value,p_id,p_option1,p_option2)=self.thread_queue.get()
            #NEW_THREAD_TOK
            #if MEMCACHED/REDIS epoll unregister
            (epollhandle,conns,p_id,sock_address,user_data_all_r)=self.thread_queue.get()
            GlobalConfigHandleKernel.global_request_counter = GlobalConfigHandleKernel.global_request_counter +1
            GlobalConfigHandleKernel.global_queue_length = GlobalConfigHandleKernel.global_queue_length -1
            mem_rd_split=self.global_config_hash['NEW_THREAD_TOK'].strip().split(',')
            error_send_to_client(conns,p_id,user_data_all_r.strip(),self.config_log_fd,epollhandle,sock_address,user_data_all_r.strip(),1)
            #print user_data_all_r
            user_data_all=(user_data_all_r.strip().split("\r"))[0]
            user_data_all=(user_data_all.strip().split("\n"))[0]
            data_split=user_data_all.strip().split()
            #new added
            data_split = filter(None, data_split)
            ########
            if(len(data_split) < 1):
                epollhandle.register(p_id, select.EPOLLIN)
                error_send_to_client(conns,p_id,"Error command parameters,again\n",self.config_log_fd,epollhandle,sock_address,user_data_all.strip())
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and (data_split[0].strip() == "shell" or data_split[0].strip() == "script")):
                try:
                    fork_s=os.fork()
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                if(fork_s==0):
                    ph=ProcessShell.HandleShellProcess(self.global_config_hash,conns,p_id)
                    ph.operate()
                else:
                    GlobalConfigHandleKernel.global_cgi_process_pid.put([fork_s])
                    conns.close()
                    self.thread_queue.task_done()
                    continue
            elif(len(data_split)>=1 and data_split[0].strip() in mem_rd_split):
                #create special thread
                #def __init__(self,thread_queue,global_config_hash,config_log_fd,epollhandle,conns,p_id,sock_address,user_data_all):
                sot=SpecialOperationThread.OperationThreadSpecial(self.global_config_hash,self.config_log_fd,epollhandle,conns,p_id,sock_address,user_data_all.strip()) 
                sot.daemon=True
                sot.start()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "klog"):
                need_to_write_log_data=(user_data_all.strip())[18:]
                web_log_w_result=operation_web_log_write(conns,self.config_log_fd,sock_address,need_to_write_log_data,self.config_log_fd_web,self.web_queue,data_split[1].strip(),data_split[2].strip())
                if(web_log_w_result == "error"):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "exit"):
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "localconger"):
                for key_al in GlobalConfigHandleKernel.global_ksms_alarm_timer:
                    try:
                        conns.send(str(GlobalConfigHandleKernel.global_ksms_alarm_timer[key_al]) + " " + str(GlobalConfigHandleKernel.global_ksms_alarm_counter[key_al]) + " " + str(GlobalConfigHandleKernel.global_ksms_alarm_content[key_al]) + "\r\n")
                    except:
                        break
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "getoscount"):
                for key_al in GlobalConfigHandleKernel.global_oscount_data:
                    try:
                        conns.send(key_al + "=>" + str(GlobalConfigHandleKernel.global_oscount_data[key_al]) + "\r\n")
                    except:
                        break
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "autountarhash"):
                for key_al in GlobalConfigHandleKernel.global_tar_all_hash:
                    try:
                        conns.send(key_al + "=>" + str(GlobalConfigHandleKernel.global_tar_all_hash[key_al]) + "\r\n")
                    except:
                        break
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "syncuntarhash"):
                for key_al in GlobalConfigHandleKernel.global_syncuntar_fail_hash:
                    try:
                        conns.send(key_al + "=>" + str(GlobalConfigHandleKernel.global_syncuntar_fail_hash[key_al]) + "\r\n")
                    except:
                        break
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "congervency"):
                for key_al in GlobalConfigHandleKernel.global_congervency_alarm:
                    try:
                        conns.send(str(GlobalConfigHandleKernel.global_congervency_timer[key_al]) + " " + str(GlobalConfigHandleKernel.global_congervency_alarm[key_al]) + " " + str(GlobalConfigHandleKernel.global_congervency_content[key_al]) + "\r\n")
                    except:
                        break
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "serverstatus"):
                try:
                    conns.send("AllRequests: %.f\r\n" % GlobalConfigHandleKernel.global_request_counter)
                except:
                    pass
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "serverlength"):
                try:
                    #conns.send("AllLengths: %.f\r\n" % GlobalConfigHandleKernel.global_queue_length)
                    conns.send("AllLengths: %.f\r\n" % self.thread_queue.qsize())
                except:
                    pass
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==3 and data_split[0].strip().lower() == "post" and (data_split[2].strip().lower() == "http/1.1" or data_split[2].strip().lower() == "http/1.0") and (data_split[1].strip())[0] == "/"):
                if(".." in data_split[1].strip()):
                    common_send_http_error(conns,"Error post request,url wrong")
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                data_split[1]=urllib.unquote(data_split[1].strip())
                p_id_post=conns.makefile()
                raw_user_string=str(user_data_all_r)
                fn = re.findall(r'boundary=([0-9a-zA-Z-]+)',raw_user_string)
                if(fn is None or len(fn)==0):
                    #common_send_http_error(conns,"Error postfile")
                    #conns.close()
                    #p_id_post.close()
                    post_long_parameters(self.global_config_hash,self.config_log_fd,epollhandle,conns,p_id,sock_address,raw_user_string,p_id_post,data_split[1].strip(),data_split[2].strip(),self.sms_log_queue,self.mail_log_queue)
                    self.thread_queue.task_done()
                    continue
     	        boundary=str(fn[0])
                #####add new cgi upload
                cgi_upload_token=0
                cgi_upload_tmp_file=""
                cgi_upload_handle=""
                t_dst=(data_split[1].strip().split("?")[0]).split("=")[0]
                t_dst_fix=translate_path(t_dst,self.global_config_hash)
                if(t_dst[:10] == "/kcgi-bin/"):
                    if(not os.path.isfile(t_dst_fix)):
                        common_send_http_error(conns,"Error post request,not cgi file")
                        conns.close()
                        self.thread_queue.task_done()
                        continue
                    cgi_upload_token=1
                fn = re.findall(r'Connection: ([a-zA-Z]+)',raw_user_string)
                alive_post=None
                if(fn is None or len(fn)==0):
                    #modified
                    #common_send_http_error(conns,"Error post request,no connection")
                    #conns.close()
                    #p_id_post.close()
                    #self.thread_queue.task_done()
                    #continue
                    alive_post="close"
                else:
                    alive_post=str(fn[0]).lower()
                a_cookie=""
                fn_cookie = re.findall(r'Cookie: ([^\r\n]+)',raw_user_string)
                if(fn_cookie is None or len(fn_cookie)==0):
                    a_cookie=""
                else:
                    a_cookie=str(fn_cookie[0])
                conns.setblocking(1)
                fn = re.findall(r'Content-Length: ([0-9]+)',raw_user_string)
                if(fn is None or len(fn)==0):
                    common_send_http_error(conns,"Error postfile,no content length")
                    conns.close()
                    p_id_post.close()
                    self.thread_queue.task_done()
                    continue
                allbytes=long(fn[0])
                save_allbytes=long(fn[0])
                if(allbytes >= long(2048000)):
                    http_post_thread=OperationHttpPostfile(self.global_config_hash,self.config_log_fd,epollhandle,conns,p_id,sock_address,raw_user_string,data_split[1].strip(),data_split[2].strip(),boundary,allbytes,p_id_post,alive_post,cgi_upload_token,t_dst,t_dst_fix,a_cookie,save_allbytes)
                    http_post_thread.daemon=True
                    http_post_thread.start()
                    self.thread_queue.task_done()
                    continue
                rrfn = re.findall(r'Referer: http://([a-zA-Z0-9.:/_-]+)',raw_user_string)
                if(rrfn is None or len(rrfn)==0):
        		    rrfn="/"
                c_dis_result=raw_user_string.find("Content-Disposition:")
                p_id_2=None
                f_dir=StringIO.StringIO()
                if(c_dis_result != -1):
                    f_dir.writelines(raw_user_string)
                    f_dir.flush()
                    f_dir.seek(c_dis_result-len(boundary)-2-2)
                    p_id_2=f_dir
                else:
                    p_id_2=p_id_post
                if(f_dir.tell() == len(raw_user_string)):
                    p_id_2=p_id_post
                ####add new cgi upload
                if(cgi_upload_token ==1):
                    cgi_upload_tmp_file="/tmp/." + hashlib.md5(boundary).hexdigest() + ".tmpfile"
                    try:
                        cgi_upload_handle=open(cgi_upload_tmp_file,"wb")
                    except:
                        common_send_http_error(conns,"Error postfile,open cgi failed")
                        conns.close()
                        p_id_post.close()
                        self.thread_queue.task_done()
                        continue
                line = p_id_2.readline()
       	        allbytes -= len(line)
                if not boundary in str(line):
                    common_send_http_error(conns,"Error postfile,bound error")
                    print "Content NOT begin with boundary: %s %s" % (line,boundary)
                    conns.close()
                    p_id_post.close()
                    self.thread_queue.task_done()
                    if(cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass  
                    continue
                if(cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(raw_user_string)):
                    p_id_2=p_id_post
                line=p_id_2.readline()
                allbytes=allbytes-len(line)
                #fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
                fn = re.findall(r'Content-Disposition.*name=.*; filename="(.*)"', line)
                if(fn is None or len(fn)==0 or fn[0] is None or len(fn[0])==0):
                    common_send_http_error(conns,"Error postfile, disposition filename error")
                    conns.close()
                    p_id_post.close()
                    self.thread_queue.task_done()
                    if(cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    continue
                #fp_0=fn[0].split("\\")
                fp_0=fn[0].replace("\\","/").split("/")
                fp_1=fp_0[len(fp_0)-1]
                if(fp_1 is None or len(fp_1)==0):
                    common_send_http_error(conns,"Error postfile,filename is None")
                    conns.close()
                    p_id_post.close()
                    self.thread_queue.task_done()
                    if(cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    continue
                #here may be some lacks for hacker
                #t_path=self.global_config_hash['LISTHOME'] + t_dst
                t_path=t_dst_fix
                t_path_save=t_path
                t_path_untar_tok=0
                fn=""
                out=None
                if(t_path == self.global_config_hash['WEB_UNTAR_URL'] or t_path == self.global_config_hash['WEB_UNTAR_URL'] + "/"):
                    t_path= self.global_config_hash['WEB_UNTAR_HOME'] + "/"
                    t_path_untar_tok=1
                #here create dir or .php file without creating
                if(cgi_upload_token==0):
                    #create dir
                    if(not os.path.isdir(t_path)):
                        try:
                            os.makedirs(t_path,0755)
                        except:
                            pass
                    fn = os.path.join(t_path, fp_1)
                if(cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(raw_user_string)):
                    p_id_2=p_id_post
                line=p_id_2.readline()
                allbytes=allbytes-len(line)
                if(cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(raw_user_string)):
                    p_id_2=p_id_post
                line=p_id_2.readline()
                allbytes=allbytes-len(line)
                try:
                    if(cgi_upload_token==0):
            	        out = open(fn, 'wb')
                    else:
                        out=None
                except:
                    common_send_http_error(conns,"Error postfile,open general failed")
                    conns.close()
                    p_id_post.close()
                    self.thread_queue.task_done()
                    if(cgi_upload_token ==1):
                        try:
                            cgi_upload_handle.close()
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    continue
                if(cgi_upload_token ==1):
                    cgi_upload_handle.write(line)
                    cgi_upload_handle.flush()
                if(f_dir.tell() == len(raw_user_string)):
                    p_id_2=p_id_post
                preline=p_id_2.readline()
                allbytes=allbytes-len(preline)
                #if(cgi_upload_token ==1):
                #    cgi_upload_handle.write(preline.rstrip())
                #    cgi_upload_handle.flush()
                boundary_tok="0"
                cgi_boundary_tok="0"
                last_boundary=boundary + "--"
                while(allbytes > 0):
                    if(f_dir.tell() == len(raw_user_string)):
                        p_id_2=p_id_post
                    line = p_id_2.readline()
                    allbytes -= len(line)
                    if last_boundary in line:
                        if(cgi_upload_token ==1):
                            cgi_upload_handle.write(preline)
                            cgi_upload_handle.write(line)
                            cgi_upload_handle.flush()
                            try:
                                cgi_upload_handle.close()
                            except:
                                break
                            cgi_boundary_tok="1"
                            break
                        preline = preline[0:-1]
                        if preline.endswith('\r'):
                            preline = preline[0:-1]
                        try:
                            out.write(preline)
                            out.flush()
                            out.close()
                        except:
                            break
                    	print "File '%s' uploaded success" % fn
                        boundary_tok="1"
                    else:
                        if(cgi_upload_token ==1):
                            cgi_upload_handle.write(preline)
                            cgi_upload_handle.flush()
                            preline=line
                            continue
                        if(allbytes < len(last_boundary)):
                            out.close()
                            boundary_tok="1"
                            print "File '%s' uploaded success,although no consistent stream" % fn
                            break
                        try:
                            out.write(preline)
                            out.flush()
                        except:
                            break
                        preline = line
                if(boundary_tok=="0"):
                    if(cgi_upload_token ==0):
                        print "Unexpect ends of data file '%s'" % fn
                        try:
                            out.close()
                        except:
                            pass
                if(cgi_boundary_tok=="0"):
                    if(cgi_upload_token ==1):
                        print "Unexpect ends of cgi data file '%s'" % cgi_upload_tmp_file
                        try:
                            cgi_upload_handle.close()
                        except:
                            pass
                f_dir.close()
                if(t_path_untar_tok == 0 and cgi_upload_token==0):
                    post_directory_suc(boundary_tok=="1",conns,p_id,fn,str(rrfn[0]),data_split[2].strip())
                try:
                    #delete on 2012-08-23 for untar conns.close()
                    p_id_post.close()
                except:
                    #add conns.close() on 2012-08-23 for untar
                    conns.close()
                    self.thread_queue.task_done()
                    if(cgi_upload_token ==1):
                        try:
                            os.unlink(cgi_upload_tmp_file)
                        except:
                            pass
                    continue
                if(t_path_untar_tok == 1 and boundary_tok =="1" and cgi_upload_token==0):
                    if(alive_post == "close"):
                        GlobalConfigHandleKernel.task_data_queue.put(["utar",fn,p_id,conns,"close"])
                    else:
                        GlobalConfigHandleKernel.task_data_queue.put(["utar",fn,p_id,conns,"alive"])
                ################################################################here unlink cgi tmp file and close cgi handle#####need
                if(cgi_upload_token ==1 and cgi_boundary_tok=="1"):
                    #here handle cgi upload file post request and close client fd
                    #post_cgi_upload_file(connnnnn,connnnnn_fd,c_log_fd,addr,udata,noab_url,noab_uri,g_config_h,h_prot,http_cookie,content_len,u_tmpfile,p_boundary):
                    post_cgi_upload_file(conns,p_id,self.config_log_fd,sock_address,t_dst_fix,t_dst,data_split[1].strip(),self.global_config_hash,data_split[2].strip(),a_cookie,save_allbytes,cgi_upload_tmp_file,boundary)
                if(alive_post == "close" or alive_post == "none"):
                    if(t_path_untar_tok ==0 and cgi_upload_token!=1):
                        conns.close()
                    else:
                        self.thread_queue.task_done()
                        continue
                else:
                    if(t_path_untar_tok ==1 or cgi_upload_token ==1):
                        self.thread_queue.task_done()
                        continue
                    try:
                        conns.setblocking(0)
                        epollhandle.register(p_id, select.EPOLLIN)
                    except:
                        conns.close()
                        #p_id_post.close()
                        self.thread_queue.task_done()
                        continue
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==3 and (data_split[0].strip().lower() == "get" or data_split[0].strip().lower() == "post") and (data_split[2].strip().lower() == "http/1.1" or data_split[2].strip().lower() == "http/1.0") and (data_split[1].strip())[0:7] == "http://"):
                    tmp_request_location=data_split[1].strip()[7:]
                    lindex_curveline=tmp_request_location.find("/")
                    if(lindex_curveline == -1):
                        common_send_http_error(conns,"Error http request")
                        conns.close()
                        self.thread_queue.task_done()
                        continue
                    else:
                        host_domain=tmp_request_location[0:lindex_curveline]
                    if(host_domain is None or host_domain==""):
                        common_send_http_error(conns,"Error http request")
                        conns.close()
                        self.thread_queue.task_done()
                        continue
                    host_port=host_domain.split(":")
                    if(len(host_port)==2):
                        host_port=host_port[1]
                    else:
                        host_port="80"
                    host_domain=host_domain.split(":")[0]
                    peer_ip=host_domain
                    match_re=re.match(r'([0-9]{1,3}\.){3}[0-9]{1,3}',host_domain)
                    if(match_re is None):
                        b_dnsip=socket.getaddrinfo(host_domain,None)
                        if(b_dnsip is None):
                            common_send_http_error(conns,"Error http request")
                            conns.close()
                            self.thread_queue.task_done()
                            continue
                        peer_ip=b_dnsip[0][4][0]
                        if(peer_ip is None or peer_ip ==""):
                            common_send_http_error(conns,"Error to resolve ip")
                            conns.close()
                            self.thread_queue.task_done()
                            continue
                    first_b=user_data_all_r.find(":")+3
                    send_remote_web_string=user_data_all_r[first_b:]
                    send_remote_web_string=send_remote_web_string[send_remote_web_string.find("/"):]
                    send_remote_web_string=data_split[0].strip() + " " + send_remote_web_string
                    try:
                        remote_web_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    except:
                        common_send_http_error(conns,"Error to create socket to remote web")
                        conns.close()
                        self.thread_queue.task_done()
                        continue
                    try:
                        remote_web_socket.settimeout(10)
                        remote_web_socket.connect((peer_ip,int(host_port)))
                        remote_web_socket.settimeout(None)
                        web_counter=0
                        #print send_remote_web_string + "@@@@@@@@@@@@"
                        while True:
                            send_to_web=send_remote_web_string[web_counter:4096]
                            if(send_to_web is None or send_to_web ==""):
                                break
                            remote_web_socket.send(send_to_web)
                            web_counter=web_counter+4096
                    except:
                        common_send_http_error(conns,"Error to connect to remote web host: " + host_domain + ":" + host_port)
                        conns.close()
                        remote_web_socket.close()
                        self.thread_queue.task_done()
                        continue
                    try:
                        remote_web_socket.setblocking(0)
                        conns.setblocking(0)
                    except:
                        common_send_http_error(conns,"Error occured during setblocking")
                        conns.close()
                        remote_web_socket.close()
                        self.thread_queue.task_done()
                        continue
                    GlobalConfigHandleKernel.global_proxy_web_fd[remote_web_socket.fileno()]=conns
                    GlobalConfigHandleKernel.global_proxy_web_cons[remote_web_socket.fileno()]=remote_web_socket
                    GlobalConfigHandleKernel.global_connections_all[remote_web_socket.fileno()]=remote_web_socket
                    epollhandle.register(remote_web_socket.fileno(), select.EPOLLIN) 
                    self.thread_queue.task_done()
                    continue
            elif(len(data_split)==3 and (data_split[0].strip().lower() == "get" or data_split[0].strip().lower() == "head") and (data_split[2].strip().lower() == "http/1.1" or data_split[2].strip().lower() == "http/1.0") and (data_split[1].strip())[0] == "/"):
                #set_http_tok(p_id,data_split[0].strip(),data_split[1].strip(),data_split[2].strip())
                raw_user_request=HTTPMeRequest(str(user_data_all_r))
                if((raw_user_request.error_message is not None) or (".." in data_split[1].strip())):
                    common_send_http_error(conns,"Error get request,try again")
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                fn=(("close"),)
                if("connection" in raw_user_request.headers):
                    fn=((str(raw_user_request.headers["connection"])),)
                a_cookie=""
                if("cookie" in raw_user_request.headers):
                    a_cookie=raw_user_request.headers["cookie"]
                try:
                    conns.setblocking(1)
                except:
                    self.thread_queue.task_done()
                    continue
                list_h_result=list_http_directory(conns,p_id,self.config_log_fd,epollhandle,sock_address,data_split[1].strip(),"GET",0,self.global_config_hash,data_split[2].strip(),self.sms_log_queue,self.mail_log_queue,"GET",a_cookie)
                if(list_h_result == "000" or list_h_result == "001" or list_h_result == "002" or list_h_result == "008"):
                    try:
                        #if(list_h_result == "000" or list_h_result == "001"):
                        if(list_h_result == "001"):
                            common_send_http_error(conns,"Some errors occurred here,please contact the web administrator")
                            #conns.send("Some errors occurred\r\n")
                        elif(list_h_result == "008"):
                            conns.send("Success\r\n")
                    except:
                        print "Some errors ocurred in sending some addtional error information\n"
                    finally:
                        conns.close()
                    self.thread_queue.task_done()
                    continue
                if(list_h_result == "004" or list_h_result == "00k"):
                    self.thread_queue.task_done()
                    continue
                if(str(fn[0]).lower() == "close" or str(fn[0]).lower() == "none"):
                    try:
                        conns.close()
                    except:
                        self.thread_queue.task_done()
                        continue
                else:
                    try:
                        conns.setblocking(0)
                        epollhandle.register(p_id, select.EPOLLIN)
                    except:
                        conns.close()
                        self.thread_queue.task_done()
                        continue
                #clear_http_tok(p_id)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "help"):
                epollhandle.register(p_id, select.EPOLLIN)
                p_gop=GeneralOperationProcess.ProcessBashGeneral("all","print",p_id,self.global_config_hash,self.config_log_fd,conns,str(sock_address))
            elif(len(data_split)>1 and data_split[0].strip() == "sms"):
                p_gop=GeneralOperationProcess.ProcessBashGeneral("sms",user_data_all.strip(),p_id,self.global_config_hash,self.config_log_fd,conns,str(sock_address))
                conns.close()
            elif(len(data_split)>1 and data_split[0].strip() == "getlsms"):
                error_getksms_tok=0
                while(1==1):
                    try:
                        t_alarm=GlobalConfigHandleKernel.local_sms_queue.get_nowait()
                    except:
                        break
                    if(t_alarm is None):
                        break
                    try:
                        conns.send(t_alarm+"\n")
                    except:
                        conns.close()
                        error_getksms_tok=1
                        break
                if(error_getksms_tok==0):
                    epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>3 and data_split[0].strip() == "rstore"):
                if(self.global_config_hash['REDIS_CACHE_ENABLE'].strip() != "1"):
                    try:
                        conns.send("RStored failed\r\n")
                    except:
                        pass
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                rstore_key=data_split[2].strip()
                rstore_value=user_data_all_r.strip()[(len(data_split[1].strip()) + len(rstore_key) + 9):]
                rhostport=self.global_config_hash['REDIS_CONN'].strip().split(":")
                if(len(rhostport)!=2):
                    try:
                        conns.send("RStored failed,no rserver configed\r\n")
                    except:
                        pass
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                rstorehandle=redis.Redis(host=rhostport[0],port=int(rhostport[1]),db=0,password=None,socket_timeout=3)
                try:
                    if(data_split[1].strip() == "get"):
                        rvv=rstorehandle.get(rstore_key)
                        if(rvv is None or rvv==""):
                            conns.send("No DATA\r\n")
                        else:
                            conns.send(rvv + "\r\n")
                    elif(data_split[1].strip() == "set"):
                        rvv=rstorehandle.set(rstore_key,rstore_value)
                        if(rvv is None or rvv is False or rvv==""):
                            conns.send("RStored failed\r\n")
                        else:
                            conns.send("RStored ok\r\n")
                    elif(data_split[1].strip() == "del"):
                        rvv=rstorehandle.delete(rstore_key)
                        conns.send("RDelete ok\r\n")
                    else:
                        conns.send("Error rstore command\r\n")
                except:
                    pass
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>1 and data_split[0].strip() == "getksms"):
                error_getksms_tok=0
                while(1==1):
                    try:
                        t_alarm=self.sms_log_queue.get_nowait()
                    except:
                        break
                    if(t_alarm is None):
                        break
                    try:
                        conns.send(t_alarm+"\n")
                    except:
                        conns.close()
                        error_getksms_tok=1
                        break
                if(error_getksms_tok==0):
                    epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>1 and data_split[0].strip() == "ksms"):
                #here write log to sms log and sms queue
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + "\n")
                if(self.global_config_hash['ALARM_LEAST_ENABLE'].strip() != "1"):
                    self.sms_log_queue.put(str(user_data_all.strip()))
                else:
                    GlobalConfigHandleKernel.global_ksms_temp_queue.put([str(user_data_all.strip()),str(sock_address)])
                try:
                    conns.send("ok\r\n")
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                #conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==5 and data_split[0].strip() == "setuntar"):
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + str(sock_address)  + "\n")
                if(self.global_config_hash['UNTAR_SYNC_ENABLE'].strip() == "1"):
                    GlobalConfigHandleKernel.global_untar_iptask.put([str(user_data_all.strip()),str(sock_address)])
                else:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                try:
                    conns.send("ok\r\n")
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==5 and data_split[0].strip() == "autountar"):
                #here maybe need to clean the mem if many python servers 50000
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + str(sock_address) + "\n")
                if(self.global_config_hash['UNTAR_SERVER_ENABLE'].strip() == "1"):
                    GlobalConfigHandleKernel.global_autountar_iptask.put([str(user_data_all.strip()),conns,p_id])
                else:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                #try:
                #    conns.send("ok\r\n")
                #except:
                #    conns.close()
                #    self.thread_queue.task_done()
                #    continue
                #epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==2 and (data_split[0].strip() == "autocoming" or data_split[0].strip() =="delcoming" or data_split[0].strip() =="cleancoming" or data_split[0].strip() =="removecoming")):
                if(self.global_config_hash['UNTAR_SERVER_ENABLE'].strip() == "1"):
                    GlobalConfigHandleKernel.global_autountar_iptask.put([str(user_data_all.strip()),conns,p_id])
                else:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                self.thread_queue.task_done()
                continue
            elif(len(data_split)==3 and data_split[0].strip() == "globals"):
                self.global_config_hash[data_split[1].strip()]=data_split[2].strip()
                try:
                    conns.send("ok\r\n")
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>1 and data_split[0].strip() == "lsms"):
                #here write log to sms log and lms queue
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + "\n")
                GlobalConfigHandleKernel.local_sms_queue.put(str(user_data_all.strip()))
                try:
                    conns.send("ok\r\n")
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                #conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>3 and data_split[0].strip() == "rrsms"):
                #here write log to sms log and sms queue
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + "\n")
                #self.sms_log_queue.put(str(user_data_all.strip()))
                GlobalConfigHandleKernel.global_rrsms_queue.put([str(user_data_all.strip()),str(sock_address)])
                try:
                    conns.send("ok\r\n")
                except:
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                epollhandle.register(p_id, select.EPOLLIN)
                #conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>1 and data_split[0].strip() == "kmail"):
                #here write log to sms log and mail queue
                unversal_write_log_2(self.sms_log_fd,str(user_data_all.strip()) + "\n")
                self.mail_log_queue.put(str(user_data_all.strip()))
                conns.close()
                self.thread_queue.task_done()
                continue
            elif(len(data_split)>=1 and data_split[0].strip() == "current"):
                epollhandle.register(p_id, select.EPOLLIN)
                p_gop=GeneralOperationProcess.ProcessBashGeneral("current","print",p_id,self.global_config_hash,self.config_log_fd,conns,str(sock_address))
            elif(len(data_split)>=1 and data_split[0].strip() == "all"):
                epollhandle.register(p_id, select.EPOLLIN)
                p_gop=GeneralOperationProcess.ProcessBashGeneral("all","print",p_id,self.global_config_hash,self.config_log_fd,conns,str(sock_address))
            elif(len(data_split)<3):
                epollhandle.register(p_id, select.EPOLLIN)
                error_send_to_client(conns,p_id,"Error command parameters,again '%s'\n" % str(data_split),self.config_log_fd,epollhandle,sock_address,user_data_all.strip())
                self.thread_queue.task_done()
                continue
            elif(data_split[1] == "set" and len(data_split)!=4):
                epollhandle.register(p_id, select.EPOLLIN)
                error_send_to_client(conns,p_id,"Error command parameters,again '%s'\n" % str(data_split),self.config_log_fd,epollhandle,sock_address,user_data_all.strip())
                self.thread_queue.task_done()
                continue
            elif(data_split[1] == "set" and len(data_split)==4):
                epollhandle.register(p_id, select.EPOLLIN)
                p_gop=GeneralOperationProcess.ProcessBashGeneral(data_split[2].strip(),data_split[3].strip(),p_id,self.global_config_hash,self.config_log_fd,conns,str(sock_address))
#sprintf(send_tmp,"kernel %s %s %llu stand %s %s\r\n",const_cast<char *>(n_auser.c_str()),const_cast<char *>(filedir_need_send.c_str()),st.st_size,const_cast<char *>(dstdir.c_str()),const_cast<char *>(dstmode.c_str()));
#---->return ok\r\n
#---->then send file data
#snprintf(up_tmp,sizeof(up_tmp),"kernel downtar %s %s down\r\n",s_file,s_user);
#--->return size
#--->send ok\r\n
#--->return file data
            elif(data_split[0] == "kernel" and data_split[4] == "down" and len(data_split) == 5):
                #if(data_split[3].strip() != str(os.getlogin()) and data_split[3].strip() != "nmd5=0"):
                if(data_split[3].strip() == "root"):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                if(not (os.path.isfile(data_split[2].strip()))):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                #here fork / threading to handle this download process
                unversal_write_log_2(self.config_log_fd,"Here get request for downloading file from client\n")
                #def __init__(self,log_fd,client_sock_fd,client_conn,epoll_fd,file_name,file_user):
                d_thread=DownloadFile.FileDownload(self.config_log_fd,p_id,conns,epollhandle,data_split[2].strip(),data_split[3].strip(),self.global_config_hash)
                d_thread.daemon=True
                d_thread.start()
                self.thread_queue.task_done()
                continue
            elif(data_split[0] == "kernel" and (data_split[4] == "stand" or data_split[4] == "standu") and len(data_split) == 7):
                #[task_tok,task_filename,task_id,task_conns,task_option]
                #print "get user: %s " % os.getlogin()
                #if(data_split[1].strip() != str(os.getlogin()) and data_split[1].strip() != "nmd5=0"):
                if(data_split[1].strip() == "root"):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                #deleted on 2012 09 16
                #if(not (os.path.isdir(data_split[5].strip()))):
                #    conns.close()
                #    self.thread_queue.task_done()
                #    continue
                if(len(data_split[6].strip())!=3 or (not data_split[6].strip().isdigit()) or (not data_split[3].strip().isdigit())):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                if(int(data_split[6].strip())>777 or int(data_split[6].strip()) <0):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                #here check file dir /xxxx.xxxx
                file_dr_result=check_valid_file(self.config_log_fd,data_split[2].strip())
                if(file_dr_result !=1):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                file_dr_result=check_valid_dir(self.config_log_fd,data_split[5].strip())
                if(file_dr_result !=1):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                unversal_write_log_2(self.config_log_fd,"Here get request for uploading file from client: " + data_split[2].strip() + " " + data_split[5].strip() + "\n")
                some_result=do_some_thing_for_file_upload(p_id,data_split[3].strip(),data_split[2].strip(),data_split[5].strip(),data_split[6].strip(),data_split[4].strip())
                if(some_result!=1):
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                #here new add for upload
                epollhandle.register(p_id, select.EPOLLIN)
                try:
                    conns.send("ok\r\n")
                except:
                    print "Error while send ok"
                    epollhandle.unregister(p_id)
                    conns.close()
                    self.thread_queue.task_done()
                    continue
                self.thread_queue.task_done()
                continue
            else:
                print "get error: %s" % user_data_all.strip()
                epollhandle.register(p_id, select.EPOLLIN)
                self.thread_queue.task_done()
                continue
                
            #here process the data got from the self.thread_queue
            #p_gop=GeneralOperationProcess.ProcessBashGeneral(p_key,p_value,p_id,self.global_config_hash,self.config_log_fd)
            gop_exec_result=p_gop.exe_process()
            if(gop_exec_result != "ok"):
                rlw=LogRecord.RecordLogWriter(self.config_log_fd)
                rlw_result=rlw.write_log("Execute shell of %s=%s on %s/%s failed ,here in thread handle\n" % (data_split[2].strip(),data_split[3].strip(),self.global_config_hash['BACKEND_monitor_config'],str(sock_address)))
                if(rlw_result is None or rlw_result !=0):
                    print "Error to write log file hear in thread handle %s" % str(sock_address)
            self.thread_queue.task_done()
            #deleted on 2012-08-23 usleep(100)
            continue
