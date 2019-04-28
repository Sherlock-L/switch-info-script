#!/usr/local/python27/bin/python2
# -*- coding: utf-8 -*-
import re
import telnetlib
import time
import json
import sys
import os


class Cisco:
    __tnConn = None             #
    #为了在后面的正则匹配其他文本时，过滤系统名
    __filterTag = None          #

    #--------------------#
    #
    __sysname = None            #
    __manage_vlan_ints = {}     #
    __mem={}                    #
    __flash = {}                #
    __os_version = ""           #
    __phy_ports = {}            #
    __bagg_ports = {}           #
    __vlans ={}                 #
    __vlan_tag_ports = {}       # Vlan Tagged Port
    __vlan_untag_ports = {}     #Vlan Untagged Port
    __bagg_phy_port_rels = {}   #
    __port_mac_port_list = {}   #
    __port_ip_mac_map = {}   # 端口互连对应的设备ip和mac映射
    __port_mac_ip_map = {}   # 端口互连对应的设备ip和mac映射

    attrs={
        "phy_port":[
            {'name': 'port_name', 'doc': '', 'get_mode': 'manual','reg': '', 'def_val':''},
            {'name': 'description', 'doc': '', 'get_mode': 'regular', 'reg': 'Description: ([a-zA-Z0-9-_.\/ ]+)\r\n',  'def_val':''},
            {'name': 'port_status', 'doc': '', 'get_mode': 'manual', 'reg': '',  'def_val':''},
            {'name': 'port_mac', 'doc': '', 'get_mode': 'regular', 'reg': 'address is ([a-zA-Z0-9.]+)',  'def_val':''},
            {'name': 'port_access_type', 'doc': '', 'get_mode': 'manual', 'reg': 'switchport mode ([a-zA-Z]+)',  'def_val':''},
            {'name': 'port_type', 'doc': '', 'get_mode': 'regular', 'reg': ' media type is [0-9\/Base]+[-]*(SX|TX)',  'def_val':''},
            {'name': 'port_rate', 'doc': '', 'get_mode': 'regular', 'reg': ' media type is ([0-9\/Base]+)',  'def_val':''},
            {"name": "port_rate_xs", "doc": "", "get_mode": "regular", "reg": "-duplex, ([a-zA-Z0-9\/]+)(-speed,|,)",  'def_val':''},
            {"name": "port_duplex", "doc": "", "get_mode": "regular", "reg": "([a-zA-Z0-9]+)-duplex",  'def_val':''}
        ],
        "bagg_port": [
            {'name': 'port_name', 'doc': '', 'get_mode': 'manual', 'reg': '',  'def_val':''},
            {'name': 'full_port_name', 'doc': '', 'get_mode': 'manual', 'reg': '',  'def_val':''},
            {'name': 'description', 'doc': '', 'get_mode': 'regular', 'reg': 'Description: ([a-zA-Z0-9-_.\/ ]+)\r\n',  'def_val':''},
            {'name': 'port_status', 'doc': '', 'get_mode': 'manual', 'reg': '',  'def_val':''},
            {'name': 'port_mac', 'doc': '', 'get_mode': 'regular', 'reg': 'address is ([a-zA-Z0-9.]+)',  'def_val':''},
            {'name': 'port_access_type', 'doc': '', 'get_mode': 'manual', 'reg': 'switchport mode ([a-zA-Z]+)',  'def_val':''},
            {'name': 'port_rate', 'doc': '', 'get_mode': 'regular', 'reg': 'Bandwidth: ([0-9]+[ ]*[mgkbpsit]*)',  'def_val':''},
            {"name": "port_rate_xs", "doc": "", "get_mode": "regular", "reg": "-duplex, ([a-zA-Z0-9\/]+)(-speed,|,)",  'def_val':''},
            {"name": "port_duplex", "doc": "", "get_mode": "regular", "reg": "([a-zA-Z0-9]+)-duplex",  'def_val':''}
        ]

    }

    def __setitem__(self, k, v):
        self.k = v


    def __init__(self, tnIp, username, password1, password2):

        self.tnIp = tnIp
        self.username = username
        self.password1 = password1
        self.password2 = password2


    def patten_find(self, patten, str, defValue=''):

        #
        re_pattern = re.compile(patten, re.M | re.I)
        serObj = re.search(re_pattern, str)
        if serObj:
            return serObj.group(1)
        else:
            return defValue


    def get_items(self, text, attrs):
        result = {}

        for attr in attrs:
            if attr['get_mode'] == r'regular':
                name=attr['name']

                #
                pattern = re.compile(attr['reg'], re.M | re.I)
                serObj = re.search(pattern, text)
                if serObj:
                    result[name] = serObj.group(1)
                else:
                    result[name] = ""

        return result;


		#获取下一页  更多， tn为建立的连接。
    def more(self, tn, cmd, timeout=1.5, more=True):

        escTxt = '\x08\x08'
        moreTxt=" --More-- "

        result = ''
        tn.write(cmd + '\n')
        time.sleep(timeout)
        result = tn.read_very_eager()
        if '--More--' in result:

            #result.replace('---- More ----', '')
            result = result.replace(escTxt, '')
            result = result.replace(moreTxt, '')
            if more:
                while more:
                    #tn.write('\n')
                    tn.write(' ')
                    time.sleep(1)
                    res = tn.read_very_eager()

                    if '--More--' in res:
                        res = res.replace(escTxt, '')
                        res = res.replace(moreTxt, '')
                        result += res
                    else:
                        res = res.replace(escTxt, '')
                        res = res.replace(moreTxt, '')
                        result += res
                        break
            else:
                #
                tn.write('q')
                time.sleep(1)

        return result

		#建立连接
    def telnet_connect(self):

        tnconn = telnetlib.Telnet()
        try:
            tnconn.open(self.tnIp)
        except:
            print "Cannot open host"
            return

        tnconn.read_until('Username:')
        tnconn.write(self.username + '\n')

        tnconn.read_until('Password:')
        tnconn.write(self.password1 + '\n')

        time.sleep(1)
        tnconn.write('enable\n')

        tnconn.read_until('Password:')
        tnconn.write(self.password2 + '\n')

        time.sleep(1)

        self.__tnConn = tnconn

        return tnconn

		#建立连接  获取系统名称
    def get_sysname(self):
        cmd = 'show running-config  | include hostname'
        resultTxt = self.more(self.__tnConn, cmd,2)
        if resultTxt:
            reg = r"hostname ([a-zA-Z0-9\-_]+)"
            hostname = self.patten_find(reg, resultTxt, '')
            if hostname:
                self.__sysname = hostname
                #为了在后面的正则匹配其他文本时，过滤系统名，
                self.__filterTag = self.__sysname + '#'

		
    def parse_vlaninterface(self, vlanIntTxt, name):
        one_vlan_int = {}
        one_vlan_int['name'] = name

        #state
        reg = name + r"[ ]+is[ ]+(administratively)"
        adminWord = self.patten_find(reg, vlanIntTxt, '')
        if adminWord:
            reg = name + r"[ ]+is[ ]+administratively (\w+),"
            one_vlan_int['state'] = self.patten_find(reg, vlanIntTxt, '')
        else:
            reg = name + r"[ ]+is[ ]+(\w+),"
            one_vlan_int['state'] = self.patten_find(reg, vlanIntTxt, '')

        #mac
        reg = r"address is ([a-zA-Z0-9.]+)"
        one_vlan_int['mac'] = self.patten_find(reg, vlanIntTxt, '')

        #ip
        reg = r"Internet address is ([0-9.]+)"
        one_vlan_int['ip'] = self.patten_find(reg, vlanIntTxt, '')

        return one_vlan_int


    #获得管理口信息
    def get_manager_info(self):

        #
        cmd = 'show interfaces | include ^Vlan'
        resultTxt = self.more(self.__tnConn, cmd)
        manage_vlan_ints = {}
        manage_vlan_int_names = {}

        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:

                if not "Vlan" in line:
                    continue

                if self.__filterTag in line:
                    continue

                reg = r"(Vlan[0-9]+) is"
                vlanIntName = self.patten_find(reg, line, '')
                if vlanIntName:
                    manage_vlan_int_names[vlanIntName] = vlanIntName

        #
        for name in manage_vlan_int_names:
            cmd = 'show interfaces ' + name
            resultTxt = self.more(self.__tnConn, cmd)

            oneVlanInt = self.parse_vlaninterface(resultTxt, name)
            manage_vlan_ints[name]=oneVlanInt

        self.__manage_vlan_ints=manage_vlan_ints

        return manage_vlan_ints

    #获得内存 注意级联，多台交换机累加
    def get_mem_info(self):

        mems={}

        #
        cmd = 'show memory summary '
        memText = self.more(self.__tnConn, cmd, 2, False)
        if memText:

            total=0
            used=0
            usedRate=0

            #
            reg = r"Processor[ ]*[a-zA-Z0-9]+[ ]*([0-9]+)"
            procTotal = self.patten_find(reg, memText, '')
            if procTotal:
                total += int(procTotal)

            #
            reg = r"Processor[ ]*[a-zA-Z0-9]+[ ]*[0-9]+[ ]*([0-9]+)"
            procUsed = self.patten_find(reg, memText, '')
            if procUsed:
                used += int(procUsed)

            #
            reg = r"I/O[ ]*[a-zA-Z0-9]+[ ]*([0-9]+)"
            ioTotal = self.patten_find(reg, memText, '')
            if ioTotal:
                total += int(ioTotal)

            #
            reg = r"I/O[ ]*[a-zA-Z0-9]+[ ]*[0-9]+[ ]*([0-9]+)"
            ioUsed = self.patten_find(reg, memText, '')
            if ioUsed:
                used += int(ioUsed)

            #
            reg = r"Driver te[ ]*[a-zA-Z0-9]+[ ]*([0-9]+)"
            drTotal = self.patten_find(reg, memText, '')
            if drTotal:
                total += int(drTotal)

            #
            reg = r"Driver te[ ]*[a-zA-Z0-9]+[ ]*[0-9]+[ ]*([0-9]+)"
            drUsed = self.patten_find(reg, memText, '')
            if drUsed:
                used += int(drUsed)

            tmpRate=float(used)*100/float(total)
            usedRate=int(round(tmpRate,0))

            mems['total_mem'] = total
            mems['used_mem'] =used
            mems['used_rate'] = usedRate

        else:
            mems['total_mem'] = 0
            mems['used_mem'] = 0
            mems['used_rate'] = 0

        self.__mem = mems


        return mems

    #
    def get_flash_info(self):

        flashs = {}

        cmd = 'dir'
        resultText = self.more(self.__tnConn, cmd)
        if resultText:

            #
            reg = r"([0-9]+) bytes total"
            flashs['total_flash'] = int(self.patten_find(reg, resultText, ''))

            #
            reg = r"([0-9]+) bytes free"
            flashs['free_flash'] = int(self.patten_find(reg, resultText, ''))

        self.__flash = flashs


        return flashs


    #获得固件版本信息
    def get_os_version(self):

        cmd = 'show version | include Version'
        resultText = self.more(self.__tnConn, cmd)
        if resultText:

            reg = r", (Version [a-zA-Z0-9. \(\)]*),"
            self.__os_version = self.patten_find(reg, resultText, '')

        return self.__os_version


    #获得物理端口信息
    def get_phy_port_info(self):

        #
        cmd = 'show interfaces | include (Gigabit|Fast)Ethernet'
        resultTxt = self.more(self.__tnConn, cmd, 2)

        phy_ports = {}
        port_names = {}

        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:
                if cmd in line:
                    continue

                if self.__filterTag in line:
                    continue

                tmpPort = self.patten_find(r"(Gigabit|Fast)Ethernet[0-9\/]+", line, '')
                if not tmpPort:
                    continue

                arr = line.split()
                portName = arr[0]
                port_names[portName] = portName

        #
        for name in port_names:

            #
            cmd = 'show interfaces ' + name
            resultTxt = self.more(self.__tnConn, cmd, 1.5)

            onePhyPort={}
            onePhyPort=self.get_items(resultTxt, self.attrs['phy_port'])

            onePhyPort['port_name']=name

            #
            reg=name+r"[ ]+is[ ]+(administratively)"
            adminWord=self.patten_find(reg, resultTxt, '')
            if adminWord:
                reg = name + r"[ ]+is[ ]+administratively (\w+),"
                onePhyPort['port_status'] = self.patten_find(reg, resultTxt, '')
            else:
                reg = name + r"[ ]+is[ ]+(\w+),"
                onePhyPort['port_status'] = self.patten_find(reg, resultTxt, '')

            #--------------------#
            #
            cmd = 'sh run interface ' + name
            resultTxt = self.more(self.__tnConn, cmd, 1.5)

            reg = r"switchport[ ]+mode[ ]+(\w+)"
            onePhyPort['port_access_type'] = self.patten_find(reg, resultTxt, '')

            # --------------------#
            #
            self.parse_port_vlans(resultTxt, name)

            phy_ports[name] = onePhyPort

        self.__phy_ports = phy_ports

        return phy_ports


		
    def parse_port_vlans(self, portTxt, portName):

        #
        #1-10, 13
        reg = r" vlan ([0-9\-, ]+)"
        vlanTxt = self.patten_find(reg, portTxt, '')

        if vlanTxt:
            sections = vlanTxt.split(",")
            for section in sections:
                pos=section.find('-')
                if pos == -1:
                    #13
                    vlanId=int(section.strip())
                    if self.__vlans.has_key(vlanId) and portName not in self.__vlans[vlanId]['ports']:
                        self.__vlans[vlanId]['ports'].append(portName)
                else:
                    #1-10
                    rag = section.split("-")
                    start=int(rag[0].strip())
                    end = int(rag[1].strip())+1
                    for i in range(start, end):
                        if self.__vlans.has_key(i) and portName not in self.__vlans[i]['ports']:
                            self.__vlans[i]['ports'].append(portName)

        return


    #获取逻辑口包含了哪些物理口
    def get_bagg_phy_rel(self, baggName):

        #
        cmd = 'show interfaces ' + baggName + ' etherchannel'
        resultTxt = self.more(self.__tnConn, cmd, 1.5)

        relPorts = []
        start = False
        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:

                if not start:
                    if '------' in line:
                        #
                        start = True
                    continue

                if 'Time' in line:
                    #
                    break

                #
                port=self.convert_port_brief_to_full(line)
                if port:
                    relPorts.append(port)

        return relPorts


    #获取逻辑口信息
    def get_bagg_port_info(self):

        #
        cmd = 'show interfaces | include Port-channel'
        resultTxt = self.more(self.__tnConn, cmd, 2)

        bagg_ports = {}
        port_names = {}

        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:

                if "Description:" in line:
                    continue

                if cmd in line:
                    continue

                if self.__filterTag in line:
                    continue

                reg = r"(Port-channel[0-9]*)"
                pattern = re.compile(reg, re.M | re.I)
                serObj = re.search(pattern, line)

                if serObj:
                    portName = serObj.group(1)
                    port_names[portName] = portName

        # ----------------------------------------#
        #
        for name in port_names:

            cmd = 'show interfaces ' + name
            resultTxt = self.more(self.__tnConn, cmd, 1.5)

            oneBaggPort = self.get_items(resultTxt, self.attrs['bagg_port'])
            oneBaggPort['full_port_name'] = name
            num=self.patten_find(r"Port-channel([0-9]*)", name, '')
            if num:
                oneBaggPort['port_name'] = 'BAGG' + num
            else:
                oneBaggPort['port_name'] = num

            #
            reg = name + r"[ ]+is[ ]+(administratively)"
            adminWord = self.patten_find(reg, resultTxt, '')
            if adminWord:
                reg = name + r"[ ]+is[ ]+administratively (\w+),"
                oneBaggPort['port_status'] = self.patten_find(reg, resultTxt, '')
            else:
                reg = name + r"[ ]+is[ ]+(\w+),"
                oneBaggPort['port_status'] = self.patten_find(reg, resultTxt, '')

            # --------------------#
            # port_rate
            if not oneBaggPort['port_rate']:
                reg = r",[ ]*BW[ ]+([0-9]+[ ]*[a-zA-Z]+),"
                oneBaggPort['port_rate'] = self.patten_find(reg, resultTxt, '')

            # --------------------#
            #
            cmd = 'sh run interface ' + name
            resultTxt = self.more(self.__tnConn, cmd, 1.5)

            #
            reg = r"switchport[ ]+mode[ ]+(\w+)"
            oneBaggPort['port_access_type'] = self.patten_find(reg, resultTxt, '')

            # --------------------#
            #
            self.parse_port_vlans(resultTxt, name)

            bagg_ports[name] = oneBaggPort

        self.__bagg_ports = bagg_ports

        #----------------------------------------#
        #
        baggPhyRels={}
        for name in port_names:
            relPorts=self.get_bagg_phy_rel(name)
            baggPhyRels[name]=relPorts


        self.__bagg_phy_port_rels=baggPhyRels

        return bagg_ports


    #
    def  convert_port_brief_to_full(self, portBrief):

        portFull=''
        reg = r"([a-zA-Z]+)([0-9\/]+)"
        re_pattern = re.compile(reg, re.M | re.I)
        serObj = re.search(re_pattern, portBrief)
        if serObj:
            portType = serObj.group(1)
            portNum = serObj.group(2)
            #这里如果碰到Ten-Gigabit的就可能匹配不到
            if 'Gi' == portType:
                #
                portFull = 'GigabitEthernet' + portNum
            elif 'Po' == portType:
                #
                portFull = 'Port-channel' + portNum
            elif 'Fa'== portType:
                #
                portFull = 'FastEthernet' + portNum

        return portFull


    #
    #
    def parse_vlan_port_list(self, portList):

        ports=[]
        lines = portList.split(",")
        for line in lines:

            port=self.convert_port_brief_to_full(line)
            if port:
                ports.append(port)

        return ports


    #
    def get_def_vlan_ports(self, vlanId, vlanName):

        def_vlan_port=[]

        strVlanId=str(vlanId)
        #
        cmd = 'show vlan id '+ strVlanId
        resultTxt = self.more(self.__tnConn, cmd, 2)

        start=False
        firstIn=True
        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:

                if not start:
                    reg = r"(VLAN[ ]+Name[ ]+Status)"
                    startPos = self.patten_find(reg, line, '')
                    if startPos:
                        start = True
                        continue

                if firstIn:
                    #
                    reg = strVlanId + r"[ ]+"+vlanName+r"[ ]+[a-zA-Z\/]+[ ]+([a-zA-Z0-9\/, ]+)"
                    portList = self.patten_find(reg, line, '')
                    ports=self.parse_vlan_port_list(portList)
                    if ports:
                        def_vlan_port.extend(ports)
                        firstIn=False
                else:
                    reg =  r"[ ]+([a-zA-Z0-9\/, ]+)"
                    portList = self.patten_find(reg, line, '')
                    ports = self.parse_vlan_port_list(portList)
                    if ports:
                        def_vlan_port.extend(ports)

                #end check
                reg = r"(VLAN[ ]+Type[ ]+)"
                endPos = self.patten_find(reg, line, '')
                if endPos:
                    break

        return def_vlan_port


    #获取vlan信息
    def get_vlan_info(self):

        #
        cmd = 'show vlan brief'
        resultTxt = self.more(self.__tnConn, cmd, 1)

        vlans = {}
        vlan_ids = {}

        start = False
        if resultTxt:
            lines = resultTxt.split("\n")
            for line in lines:

                if not start:
                    if '----' in line:
                        #
                        start = True
                    continue

                #
                reg = r"([0-9]+)[ ]+([a-zA-Z0-9-_&]+)[ ]+([a-zA-Z]+)"
                re_pattern = re.compile(reg, re.M | re.I)
                serObj = re.search(re_pattern, line)
                if serObj:
                    vlanId = int(serObj.group(1))
                    if vlanId <= 1024:
                        oneVlan={};
                        oneVlan['id']=vlanId
                        oneVlan['name'] = serObj.group(2)
                        oneVlan['status'] = serObj.group(3)
                        oneVlan['ports'] = []

                        #
                        #
                        #if oneVlan['name'].lower() == 'default':
                        oneVlan['ports'] = self.get_def_vlan_ports(vlanId, oneVlan['name'])

                        vlans[vlanId]=oneVlan

        self.__vlans=vlans

        return vlans


    def get_info(self):

        try:
            #
            self.telnet_connect()
            self.get_sysname()
            self.get_manager_info()
            self.get_mem_info()
            self.get_flash_info()
            self.get_os_version()
            self.get_vlan_info()
            self.get_phy_port_info()
            self.get_bagg_port_info()
            self.get_neighbor_info()

            #--------------------#
            #
            result={}
            result['host_name']=self.__sysname
            result['manage'] = self.__manage_vlan_ints
            result['memory'] = self.__mem
            result['flash'] = self.__flash
            result['os_version'] = self.__os_version
            result['phy_ports'] = self.__phy_ports
            result['bagg_ports'] = self.__bagg_ports
            result['bagg_phy_port_rels'] = self.__bagg_phy_port_rels
            result['port_mac'] = self.__port_mac_port_list
            result['vlans'] = self.__vlans

            tmpJson = json.dumps(result)
            totalLen=len(tmpJson)
            readLen=0
            while readLen<totalLen:
                if readLen+4096 < totalLen:
                    sys.stdout.write(tmpJson[readLen:readLen+4096])
                    readLen+=4096
                else:
                    sys.stdout.write(tmpJson[readLen:])
                    readLen=totalLen

                sys.stdout.flush()
                time.sleep(0.1)

            # filename = self.tnIp + ".atout.txt"
            # doc = open(filename, 'w')
            # doc.write(tmpJson)
            # doc.close()

        except Exception, e:
            msg=str(e).encode('utf-8')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            msg += "\r\n"
            info = (exc_type, fname, exc_tb.tb_lineno)
            msg += str(info)
            print msg
        except:
            print "execute exception"

    # 获取连接端信息
    def get_neighbor_info(self):

         self._get_neighbor_info_by_arp()
         #学习到的mac ip 并不一定是直接连接
         #self._get_neighbor_info_by_learn()
         self._get_neighbor_info_by_cdp()

    def _get_neighbor_info_by_learn(self):
        cmd = 'show  mac-address-table'
        resultTxt = self.moreV1(self.__tnConn, cmd)
        if not resultTxt:
            return
        #   16    0002.b642.0a21   dynamic ip                    Port-channel1
        reg = r'[0-9]+[ ]+([0-9a-zA-Z]+\.[0-9a-zA-Z]+\.[0-9a-zA-Z]+)[ ]+[a-zA-Z\, ]+[ ]+([Ten\-Gigabit|forty\-Gigabit|Gigabit|Fast|]+?Ethernet[0-9\/]+|Port-channel[0-9]+)'
        pattern = re.compile(reg, re.M | re.I)

        lines = resultTxt.split("\n")
        for line in lines:
            seObj = re.search(pattern, line)
            if seObj:

                portName = seObj.group(2)
                mac = seObj.group(1)
                if self.__port_mac_ip_map.has_key(mac):
                    ip = self.__port_mac_ip_map[mac]
                else:
                    ip = ''

                # ip后面根据lldp 协议和三层的arp 补全
                if not self.__port_mac_port_list.has_key(portName):
                    self.__port_mac_port_list[portName] = {}

                key = self._get_port_mac_arr_key(mac,ip)
                self.__port_mac_port_list[portName][key] = {'mac':mac,'ip':ip}

    def _get_port_mac_arr_key(self,mac,ip):
        return 'm:'+mac+'|ip:'+ip

    def _get_neighbor_info_by_cdp(self):
        cmd = 'show cdp neighbors detail'
        resultTxt = self.moreV1(self.__tnConn, cmd)

        if resultTxt:
            resultTxt = re.split(r'(--------)', resultTxt)
            regIp = r"IP address:[ ]+([0-9/.]+)\r\nPlatform"
            regPortName = r"Interface:[ ]+([0-9a-zA-Z\./-]+),[ ]+Port ID"
            patternIp = re.compile(regIp, re.M | re.I)
            patternPortName= re.compile(regPortName, re.M | re.I)
            for item in resultTxt:
                #对端的ip，不是管理ip
                ip = re.search(patternIp, item)
                #当前设备的端口
                portName = re.search(patternPortName,  item)
                if ip and portName:

                    if self.__port_ip_mac_map.has_key(ip.group(1)):
                        mac = self.__port_ip_mac_map[ip.group(1)]
                    else:
                        mac = ''

                    if not self.__port_mac_port_list.has_key(portName.group(1)):
                        self.__port_mac_port_list[portName.group(1)] = {}
                    key = self._get_port_mac_arr_key(mac, ip.group(1))
                    self.__port_mac_port_list[portName.group(1)][key] = {'mac': mac, 'ip': ip.group(1)}

    def _get_neighbor_info_by_arp(self):
        cmd = 'show arp'
        resultTxt = self.moreV1(self.__tnConn, cmd)
        if not resultTxt:
            return
        #   Internet  192.168          0   0023.24cc.7d94  ARPA   Vlan16
        reg = r'[a-zA-Z]+[ ]+([0-9\.]+)[ ]+[0-9\-]+[ ]+([0-9a-zA-Z]+\.[0-9a-zA-Z]+\.[0-9a-zA-Z]+)[ ]+[\S\s]*'
        pattern = re.compile(reg, re.M | re.I)
        lines = resultTxt.split("\n")
        for line in lines:
            seObj = re.search(pattern, line)
            if seObj:
                ip = seObj.group(1)
                mac = seObj.group(2)
                self.__port_mac_ip_map[mac] = ip
                self.__port_ip_mac_map[ip] = mac

    #新的获取方式，适合一次读取多条数据
    def moreV1(self, tnConn, cmd, timeout=1.5, more=True):
        escTxt = '\x08\x08'
        moreTxt = "--More--"
        tnConn.write(cmd + '\n')
        time.sleep(timeout)
        result = tnConn.read_very_eager()

        if '--More--' in result:
            result = result.replace(escTxt, '')
            result = result.replace(moreTxt, '')
            if more:
                while more:

                    for i in range(0, 54):
                        tnConn.write(' ')
                    time.sleep(2)
                    res = tnConn.read_very_eager()
                    if '--More--' in res:
                        res = res.replace(escTxt, '')
                        res = res.replace(moreTxt, '')
                        result += res
                    else:
                        res = res.replace(escTxt, '')
                        res = res.replace(moreTxt, '')
                        result += res
                        break
            else:
                #
                tnConn.write('q')
                time.sleep(1)

        return result


if __name__ == '__main__':
   

    ip=sys.argv[1]
    username=sys.argv[2]
    password1 = sys.argv[3]
    password2 = sys.argv[4]

    cisco = Cisco(ip, username, password1, password2)
    cisco.get_info()
    os._exit(0)




