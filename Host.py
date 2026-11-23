import json
import os
# from TelegramBot import SendMessage
#### SendMail.py is not part of the repository (it holds the mail credentials).
#### It must provide a SendMail(subject,message) function. Without it, no mails are sent.
try:
    from SendMail import SendMail
except ImportError:
    def SendMail(subject,message):
        pass
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
        self.json_tcp_ports = None
        self.json_udp_ports = None

        self.ports_tcp = None
        self.ports_udp = None
        #Print("Created Host with ip: ",self.ip," and hostname: ",self.hostname)
    

    def SaveJson(self,proto):
        if self.ports is None:
            return
        json_data = {
            'ip': self.ip,
            'hostname': self.hostname,
            'mac': self.mac,
            'ports': [{'port': port.num, 'service': port.service or '', 'version': port.version or ''} for port in self.ports]
        }
        proto_path = os.path.join(os.getcwd(),'Networks',proto)
        os.makedirs(proto_path,exist_ok=True)
        with open(os.path.join(proto_path,'host'+str(self.ip)+'.json'),'w') as json_file_object:
            json.dump(json_data,json_file_object,indent='\t')

        #### Refresh json data
        self.LoadJsonData()
    
    def LoadJsonData(self):
        tcp_path = os.getcwd()+'/Networks/tcp/host'+str(self.ip)+'.json'
        udp_path = os.getcwd()+'/Networks/udp/host'+str(self.ip)+'.json'
        for path in [tcp_path,udp_path]:
            if not os.path.exists(path):
                continue
            try:
                with open(path,'r') as json_file_object:
                    json_data = json.load(json_file_object)
                #### the saved data belongs to another machine that had the same ip
                if json_data['mac'] != self.mac:
                    continue
                ports = []
                for port in json_data['ports']:
                    ports.append(Port(port['port'],None,port['service'],port['version']))
            except (OSError, ValueError, KeyError, TypeError):
                #### unreadable or corrupted file. It will be rewritten on the next scan
                continue
            self.json_ip = json_data.get('ip')
            self.json_hostname = json_data.get('hostname')
            self.json_mac = json_data['mac']
            if path == tcp_path:
                self.json_tcp_ports = ports
            elif path == udp_path:
                self.json_udp_ports = ports
    
    #### Compares the ports found by the last scan with the ones saved from the previous scan.
    #### proto can be 'tcp' or 'udp' to check only that protocol. By default both are checked.
    def CheckChanges(self,send_mail_flag,proto=None):
        protocols = ['tcp','udp'] if proto is None else [proto]

        for proto in protocols:
            if proto == 'tcp':
                old_ports = self.json_tcp_ports
                new_ports = self.ports_tcp
            else:
                old_ports = self.json_udp_ports
                new_ports = self.ports_udp

            #### nothing to compare with (first scan or no scan for this protocol)
            if old_ports is None or new_ports is None:
                continue

            old_port_nums = [p.num for p in old_ports]
            new_port_nums = [p.num for p in new_ports]

            #### CHECK FOR NEW OPENED PORTS
            opened_ports = [p for p in new_ports if p.num not in old_port_nums]
            #### CHECK FOR PORTS THAT ARE CLOSED (previously opened)
            closed_ports = [p for p in old_ports if p.num not in new_port_nums]

            for op in opened_ports:
                message = "New "+proto +" port opened: " + op.num +' on host '+self.ip +'('+self.hostname+')\nService: '+(op.service or '') +'\nVersion: '+(op.version or '')
                if send_mail_flag:
                    SendMail('OPEN PORT ALERT',message)

            for cp in closed_ports:
                message = proto+" Port closed: " + cp.num +' on host '+self.ip +'('+self.hostname+')\nService: '+(cp.service or '') +'\nVersion: '+(cp.version or '')
                if send_mail_flag:
                    SendMail('CLOSED PORT ALERT',message)
    
    def NotifyUp(self):
        message = 'Host '+self.ip +' ('+self.hostname+') with mac: '+self.mac+' is UP'
        # SendMail('NEW HOST ALIVE',message)

    def NotifyDown(self):
        message = 'Host '+self.ip +' ('+self.hostname+') with mac: '+self.mac+' is DOWN'
        # SendMail('HOST DOWN',message)



        


