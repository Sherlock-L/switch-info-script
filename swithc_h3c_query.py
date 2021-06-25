#!/usr/bin/python
# coding=utf-8

import paramiko
import time
import datetime
import json
import sys
import re
import logging
import os
import subprocess

class H3C:

    sshClient=None
    username=''
    ip=''
    funcName=''
    password = ''
    port = ''

    def recordLog(self,txt):
      
        logging.info(txt)           
        # cmd =  "echo \'{0}\' >>{1} ".format(txt,self.exeLog)
        # handle = os.popen(cmd)
        # retTxt = handle.read()
        # handle.close()

    def run_command(self,cmd,logCmdFlag =False ):
        if logCmdFlag:
            self.recordLog(cmd)
        p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        (stdout, stderr) = p.communicate()
        if stdout:
            self.recordLog(stdout)
        if stderr:
            self.recordLog(stderr)
        
        return (stdout,stderr)
  
    def buildReponse(self,success = True,info = ''):
        res = {
            "success":success,
            "info": info
        }
        return res
   
    def outJson(self,str):  
        totalLen = len(str)
        readLen = 0
        while readLen < totalLen:
            if readLen + 4096 < totalLen:
                sys.stdout.write(str[readLen:readLen + 4096])
                readLen += 4096
            else:
                sys.stdout.write(str[readLen:])
                readLen = totalLen

            sys.stdout.flush()
            time.sleep(0.1) 

    def initSSHClient(self):
        self.sshClient = paramiko.SSHClient()
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshClient.connect(self.ip, username =self.username, password=self.password,port=int(self.port)) 


    def closeSSHClient():
        if self.sshClient:
            self.sshClient.close()
        


    def queryLogicPort(self):
        ret = {}
        cmd='disp link-aggregation  verbose'
        stdin,stdout,stderr = self.sshClient.exec_command(cmd)
        resultTxt=stdout.read()
        lines = resultTxt.decode().split("\n")
        regAgg = r"(Bridge-Aggregation[0-9]*)"
        patternAgg = re.compile(regAgg, re.M | re.I)

        regPort = r"(GE|XGE|FE|E0|E2|E1|E3|E4|40GE)([0-9\/]{2,})"
        patternPort = re.compile(regPort, re.M )

        currentAgg = ''
        find='Agg'
        for line in lines:
            if 'Remote' in line:
                find=''
                continue
            serObjAgg = re.search(patternAgg, line)
            if serObjAgg:
                find='port'
                ret[serObjAgg.group(1)]=[]
                currentAgg= serObjAgg.group(1)
                continue
            if find=='port':
                find='port'
                serObjPort= re.search(patternPort, line)
                if serObjPort and serObjPort.group(1) and serObjPort.group(2):
                    port=serObjPort.group(1)+serObjPort.group(2)
                    ret[currentAgg].append(port)
                    continue
        return ret            

if __name__ == '__main__':
    try:
        obj = H3C()
        obj.run_command('mkdir -p /var/log/ihm/')
        t = time.time()
        timenow = (int(t))   
        obj.exeLog = '/var/log/ihm/swithc-query-{0}-{1}.log'.format(datetime.date.today(),timenow)
        logging.basicConfig(level=logging.DEBUG,
                    filename=obj.exeLog,
                    filemode='a',
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    )
        # xxx.sh 192.168.1.1  test testpwd 22 queryLogicPort
        obj.ip = sys.argv[1]
        obj.username = sys.argv[2]
        obj.password = sys.argv[3]
        obj.port = int(sys.argv[4])
        obj.funcName = sys.argv[5]
        obj.initSSHClient()
        ret = ''
        if obj.funcName == 'queryLogicPort':
            ret = obj.buildReponse(True,obj.queryLogicPort())
        else:
            ret = obj.buildReponse(False,'unknown function '+sys.argv[5])
        tmpJson = json.dumps(ret)
        obj.outJson(tmpJson)

    except Exception as e:
        msg = str(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        info = (exc_type, fname, exc_tb.tb_lineno)
        msg += str(info)
        ret = obj.buildReponse(False,msg)
        obj.outJson(json.dumps(ret))
    obj.initSSHClient()
    os._exit(0)
