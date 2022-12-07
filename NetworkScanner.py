from ProMan import ProMan
import time
from Host import Host, Port
from SString import FindSubstr

## This is an Nmap wrapper (hellooo)

def RefreshHosts(new_hosts,old_hosts):
    # for n in new_hosts:
    #     Print2(n.ip)
    # for o in old_hosts:
    #     Print2(o.ip)
    disconnected = []
    same_hosts = []
    new_list = new_hosts.copy()
    while True:
        found = False
        for n_h in new_hosts:
            for o_h in old_hosts:
                if n_h.ip == o_h.ip:
                    found = True
                    # Print("SAME IP FOUND: ",n_h.ip)
                    same_hosts.append(n_h)
                    new_hosts.remove(n_h)
                    break
        if not found:
            break

    for o_h in old_hosts:
        found = False
        for n_h in new_list:
            if n_h.ip == o_h.ip:
                found = True
                break
        if not found:
            disconnected.append(o_h)
    # for n in new_hosts:
    #     Print2("NEW " + n.ip)

    # for n in disconnected:
    #     Print2("DIS" + n.ip)
    
    return new_hosts,same_hosts,disconnected

 


class NmapParser:
    def __init__(self,network_status):
        self.network_status = network_status
    
    def ParseHostUp(self,result):
        if 'down' in result:
            return False
        return True
    
    def ParsePingScan(self,result):
        self.result_text = result
        lines = result.split('\n') ## Breaks the Nmap output into a list of its lines.
        lines.pop(len(lines)-1)    ## But it has to remove the last element which is an empty string
        self.network_status.disconnected = []
        self.network_status.new_hosts = []

        # self.network_status.hosts = []
        # if "MAC" in lines[4]:
        ### Nmap prints a number of lines dedicated to each host.
        ### If run as root, nmap will also print the mac address of each host
        ### and so each host will consume three (3) lines. The step variable
        ### is assigned accordingly so to jump at the corresponding line of each host.
        ### !! MAY NOT USE THIS TECHNIQUE !!
        # for line in lines:
        #     if "MAC" in line:
        #         step = 3
        #         break
        # else:
        #     step = 2 

        ### Nmap prints a number of lines dedicated to each host.
        ### Nmap output is of the following style:
        ### Nmap scan report for hostname (xxx.xxx.xxx.xxx), if a hostname is found for that host, or
        ### Nmap scan report for xxx.xxx.xxx.xxx, if not
        ### Generaly, If the line starts with 'Nmap', it contains info about the IP and the hostname (if any)

        new_hosts = []
        host_id = 0
        mac = 'LOCALHOST'
        ip = ""
        hostname = ""
        for line in lines:
            host_found = False
            if 'MAC' in line:
                mac = FindSubstr(line,'MAC Address:',' (').strip()
            if 'Nmap scan report' in line:
                # line = lines[i]
                ### If the 'Nmap' line contains '(': it has info about the hostname
                if '(' in line: ### Parse Hostname and Ip 
                    ip_index = line.find('(')+1
                    host_index = line.find("for") + 4
                    ip = line[ip_index:len(line)-1]
                    hostname = line[host_index:ip_index-2]
                else: ### Parse IP
                    ip_index = line.find("for") + 4
                    ip = line[ip_index:len(line)]
                    hostname = "Unnamed Host"
                host_found = True
            if host_found:
                found_host = Host([ip,hostname],mac=mac)
                new_hosts.append(found_host)
                host_found = False
                ### Create a Host object with found Ip,Hostname
        # host_id += 1

        ### Categorize the Hosts found as new,current or disconnected
        new_hosts, same_hosts, disconnected = RefreshHosts(new_hosts,self.network_status.hosts)
        curr_hosts = new_hosts + same_hosts
        self.network_status.disconnected = disconnected
        self.network_status.hosts = curr_hosts
        self.network_status.new_hosts = new_hosts
        # self.network_status.Update()
    
    def ParseServiceScan(self,res,scan_type=1):
        
        if self.network_status.stopped.is_set():
            # stopped = True
            return

        lines = res.split('\n')
        reached_PORT = False
        ports = []
        for line in lines:
            if reached_PORT:
                if 'tcp' in line:
                    data = line.split(' ')
                    data = [el for el in data if el != '']
                    if 'open' not in data[1]:
                        continue
                    port = data[0]
                    service = data[2]
                    version = ''
                    if str(scan_type) == str(2):
                        for i in range(3,len(data)):
                            version += data[i]
                            version += ' '
                    ports.append(Port(port,None,service,version))

            else:
                if 'PORT' in line:
                    reached_PORT = True
                continue
        return ports
    
    def ParseOsScan(self,res):
        if self.network_status.stopped.is_set():
            return
        os_info = []
        
        if 'Running' in res:
            os_info.append(FindSubstr(res,'MAC Address:'))
            os_info.append(FindSubstr(res,'Device type:'))
            os_info.append(FindSubstr(res,'Running:'))
            os_info.append(FindSubstr(res,'OS CPE:'))
            os_info.append(FindSubstr(res,'OS details:'))
        elif 'No exact' in res or 'Too many' in res:
            os_info.append(FindSubstr(res,'MAC Address'))

        return os_info

class NetworkScanner:
    def __init__(self,network_status,bin='nmap'):
        self.nmap_bin = bin
        self.proman = ProMan()
        self.network_status = network_status
        self.parser = NmapParser(self.network_status)
        self.nmap_options = None
    
    def SetOptions(self,options):
        self.nmap_options = options
    
    def IsHostUp(self,ip):
        cmd = []
        cmd.append(self.nmap_bin)
        cmd.append(ip)
        cmd.append('-sP')

        return self.parser.ParseHostUp(self.proman.RunProcessWait(cmd))
   
    def NetworkDiscovery(self,network):
        cmd = []
        cmd.append(self.nmap_bin)
        cmd.append('-sP') ## Ping scan, just check if hosts are up
        cmd.append(network)

        ## ececute the command and pass it to the parser
        self.parser.ParsePingScan(self.proman.RunProcessWait(cmd))
        # self.parser.ParsePingScan(self.proman.RunProcessWait(cmd))
    
    def ServiceScan(self,ip,scan_type=1):
        cmd=[]
        cmd.append(self.nmap_bin)
        if str(scan_type) == str(2):
            cmd.append("-sV")
            cmd.append("-Pn")
        for opt in self.nmap_options:
            cmd.append(opt)
        cmd.append(ip)
        

        return self.parser.ParseServiceScan(self.proman.RunProcessWait(cmd),scan_type=scan_type)
    
    def OsScan(self,ip):
            
        cmd=[]
        cmd.append(self.nmap_bin)
        cmd.append('-O')
        cmd.append('-Pn')
        cmd.append(ip)

        # return self.proman.RunProcessWait(cmd)
        return self.parser.ParseOsScan(self.proman.RunProcessWait(cmd))
