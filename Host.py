import json
import os
# from TelegramBot import SendMessage
from SendMail import SendMail
import time

class Port(object):
    def __init__(self,port_num,info,service=None,version=None):
        self.num = port_num
        self.info = info
        self.service = service
        self.version = version

class Host(object):
    def __init__(self,args,ports=None,os=None,mac=None,mac_type=None,host_id=None):
        self.host_id = host_id
        self.ip = args[0]
        self.hostname = args[1]
        self.ports = ports
        self.os = os
        self.mac = mac
        self.mac_type = mac_type

        self.json_ip = None
        self.json_hostname = None
        self.json_mac = None
        self.json_ports = None
        #Print("Created Host with ip: ",self.ip," and hostname: ",self.hostname)
    

    def SaveJson(self):
        json_file = '{\n\t"ip":'+'"'+self.ip+'",\n\t"hostname":'+'"'+self.hostname+'",\n\t"mac":'+'"'+self.mac+'",\n\t"ports":['
        if self.ports is None:
            return
        for port_index in range(len(self.ports)):
            port = self.ports[port_index]
            json_file += '\n\t\t{\n\t\t\t"port":'+'"'+port.num+'",'+'\n\t\t\t"service":'+'"'+port.service+'",\n\t\t\t'+'"version":'+'"'+port.version+'"\n\t\t}'
            if port_index < len(self.ports) - 1:
                json_file += ","
        json_file += '\n\t]\n}'
        json_file_object = open(os.getcwd()+'/Networks/host'+str(self.ip)+'.json','w+')
        json_file_object.write(json_file)
        json_file_object.close()

        #### Refresh json data
        self.LoadJsonData()
    
    def LoadJsonData(self):
        path = os.getcwd()+'/Networks/host'+str(self.ip)+'.json'
        if not os.path.exists(path):
            return
        json_file_object = open(path,'r')
        json_data = json.load(json_file_object)
        mac = json_data['mac']
        if mac == self.mac:
            ip = json_data['ip']
            hostname = json_data['hostname']
            ports = []
            for port in json_data['ports']:
                ports.append(Port(port['port'],None,port['service'],port['version']))
                # print(port['service'])
            self.json_ip = ip
            self.json_hostname = hostname
            self.json_mac = mac
            self.json_ports = ports

            json_file_object.close()
        else:
            json_file_object.close()
            return False
    
    def CheckChanges(self,send_mail_flag):
        # if self.mac == self.json_mac:
        if self.json_ports is None:
            return
        opened_ports = []
        closed_ports = []
        old_port_nums = [p.num for p in self.json_ports]
        new_port_nums = [p.num for p in self.ports]
        # print(old_port_nums)
        # print(new_port_nums)
        #### CHECK FOR NEW OPENED PORTS
        for new_port in self.ports:
            if new_port.num not in old_port_nums: # found new port
                opened_ports.append(new_port)

        #### CHECK FOR PORTS THAT ARE CLOSED 
        for old_port in self.json_ports:
            if old_port.num not in new_port_nums: # found closed port (previously opened)
                closed_ports.append(old_port)
        

        for op in opened_ports:
            message = "New port opened: " + op.num +' on host '+self.ip +'('+self.hostname+')\nService: '+op.service +'\nVersion: '+op.version
            # print(message)
            # SendMessage(message)
            if send_mail_flag:
                SendMail('OPEN PORT ALERT',message)

        for cp in closed_ports:
            message = "Port closed: " + cp.num +' on host '+self.ip +'('+self.hostname+')\nService: '+cp.service +'\nVersion: '+cp.version
            # print(message)
            if send_mail_flag:
                SendMail('CLOSED PORT ALERT',message)
            # SendMessage(message)
    
    def NotifyUp(self):
        message = 'Host '+self.ip +' ('+self.hostname+') with mac: '+self.mac+' is UP'
        # SendMail('NEW HOST ALIVE',message)

    def NotifyDown(self):
        message = 'Host '+self.ip +' ('+self.hostname+') with mac: '+self.mac+' is DOWN'
        # SendMail('HOST DOWN',message)



        


