from ProMan import ProMan
import time
from Host import Host, Port
from SString import FindSubstr
import xml.etree.ElementTree as ET

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

        self.network_status.disconnected = []
        self.network_status.new_hosts = []

        new_hosts = []
        host_id = 0

        nmap_xml_root = ET.fromstring(self.result_text)
        for host in nmap_xml_root.iter('host'):
            mac = '____LOCALHOST____'
            mac_type = 'Unknown'
            ip = "x.x.x.x"
            hostname = ''
            for element in host:
                for field in element.iter('address'):
                    if field.attrib['addrtype'] == 'ipv4':
                        ip = field.attrib['addr']
                    elif field.attrib['addrtype'] == 'mac':
                        mac = field.attrib['addr']
                        if 'vendor' in field.attrib.keys():
                            mac_type = field.attrib['vendor']
                    else:
                        print("WX KATI PHGE SKATA STA ADDRESSES (oute ipv4 oute mac)")
                for hname in element.iter('hostname'):
                    hostname = hname.attrib['name']
                    if hostname == ip:
                        hostname = ''
            new_hosts.append(Host([ip,hostname],mac=mac,mac_type=mac_type))

        ### Categorize the Hosts found as new,current or disconnected
        new_hosts, same_hosts, disconnected = RefreshHosts(new_hosts,self.network_status.hosts)
        curr_hosts = new_hosts + same_hosts
        self.network_status.disconnected = disconnected
        self.network_status.hosts = curr_hosts
        self.network_status.new_hosts = new_hosts
    
    def ParseServiceScan(self,res,scan_type=1):
        self.result_text = res
        
        if self.network_status.stopped.is_set():
            # stopped = True
            return


        ports = []

        nmap_xml_root = ET.fromstring(self.result_text)
        
        for port_info in nmap_xml_root.iter('port'):
            port = ''
            service = ''
            version = ''
            port = port_info.attrib['portid']
            version_prefix = ' '
            attributes = ['product','extrainfo','ostype']
            for field in port_info.iter('service'):
                service = field.attrib['name']
                if 'version' in field.attrib.keys():
                    version = field.attrib['version']
                    version_prefix = ' - '

                for attr in attributes:
                    if attr in field.attrib.keys():
                        version += version_prefix + field.attrib[attr]

            ports.append(Port(port,None,service,version))

        return ports
    
    def ParseOsScan(self,res):
        self.result_text = res
        if self.network_status.stopped.is_set():
            return
        os_info = []
        
        nmap_xml_root = ET.fromstring(self.result_text)
        
        mac = ''
        mac_type = ''
        mac_not_found = True
        for mac_info in nmap_xml_root.iter('address'):
            if mac_info.attrib['addrtype'] == 'mac' and mac_not_found:
                mac_not_found = False
                mac = mac_info.attrib['addr']
                if 'vendor' in mac_info.attrib.keys():
                    mac_type = mac_info.attrib['vendor']
                os_info.append(mac)
                # os_info.append(mac_type)

        osfamily = ''
        osgen = ''
        dev_type = ''
        extra_vendor = ''
        # cpe = ''
        found_keywords = []
        for osclass in nmap_xml_root.iter('osclass'):
            if 'type' in osclass.attrib.keys():
                dev_type = osclass.attrib['type']
            if 'vendor' in osclass.attrib.keys():
                # if extra_vendor == '':
                #     extra_vendor = osclass.attrib['vendor']
                # else:
                #     extra_vendor = '|' + osclass.attrib['vendor']
                extra_vendor = osclass.attrib['vendor']
                if extra_vendor not in found_keywords:
                    found_keywords.append(extra_vendor)
            if 'osfamily' in osclass.attrib.keys():
                # if osfamily == '':
                #     osfamily = osclass.attrib['osfamily']
                # else:
                #     osfamily += '|' + osclass.attrib['osfamily']
                osfamily = osclass.attrib['osfamily']
                if osfamily not in found_keywords:
                    found_keywords.append(osfamily)

            if 'osgen' in osclass.attrib.keys():
                # osgen += osclass.attrib['osgen'] + '|'
                osgen = osclass.attrib['osgen']
                if osgen not in found_keywords:
                    found_keywords.append(osgen)

            # found_cpes = []
            # cpes_num = 0
            # for cpeinfo in osclass.iter('cpe'):
            #     if cpeinfo.text not in found_cpes:
            #         cpe += cpeinfo.text + '|'
            #         cpes_num += 1
            #         if cpes_num > 2:
            #             break
        
        

        
        if osgen != '':
            osgen = osgen[0:len(osgen) - 1]
        
        # running = osfamily + ' ' + osgen
        # if extra_vendor != '' and extra_vendor != osfamily:
        #     running +=  ' ' +extra_vendor
        running = ''
        for keywords in found_keywords:
            running += keywords + '|'

        if mac_type.strip() != '' or dev_type.strip() != '': 
            os_info.append(mac_type+' '+dev_type)
        if running.strip() != '':
            os_info.append(running)
        # if cpe.strip() != '':
        #     os_info.append(cpe)
        # if cpe.strip() == '' and len(os_info) > 1:
        #     os_info.append('No cpe info')

        os_details = ''
        os_matches_found = 0
        for osinfo in nmap_xml_root.iter('osmatch'):
            os_details += osinfo.attrib['name'] + '|'
            os_matches_found += 1
            if os_matches_found > 2:
                os_details += ' ....'
                break

        if os_details.strip() != '': 
            os_info.append(os_details[0:len(os_details)-1])

        # if 'Running' in res:
        #     mac_info.append(FindSubstr(res,'MAC Address:'))
        #     mac_info.append(FindSubstr(res,'Device type:'))
        #     mac_info.append(FindSubstr(res,'Running:'))
        #     mac_info.append(FindSubstr(res,'OS CPE:'))
        #     mac_info.append(FindSubstr(res,'OS details:'))

        # elif 'No exact' in res or 'Too many' in res in res:
        #     mac_info.append(FindSubstr(res,'MAC Address'))

        # elif 'unreliable' in res:
        #     return None
        # print(os_info)
        # time.sleep(5)

        #### check if all values are empty. This probably means that host is offline or in another network ####
        empty = True
        for el in os_info:
            if el.strip() != '':
                empty = False
                break
        if empty:
            return None
        
        return os_info
    
    # def ParseUdpScan(self,res):
    #     self.result_text = res

    #     if self.network_status.stopped.is_set():
    #         return

    #     udp_info = []
    #     nmap_xml_root = ET.fromstring(self.result_text)



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
        cmd.append('-oX')
        cmd.append('-')

        ## ececute the command and pass it to the parser
        self.parser.ParsePingScan(self.proman.RunProcessWait(cmd))
        # self.parser.ParsePingScan(self.proman.RunProcessWait(cmd))
    
    def ServiceScan(self,ip,scan_type=1):
        cmd=[]
        cmd.append(self.nmap_bin)
        if str(scan_type) == str(2):
            cmd.append("-sV")
            # cmd.append("-Pn")
        for opt in self.nmap_options:
            cmd.append(opt)
        cmd.append(ip)
        cmd.append('-oX')
        cmd.append('-')
        

        return self.parser.ParseServiceScan(self.proman.RunProcessWait(cmd),scan_type=scan_type)
    
    def OsScan(self,ip):
            
        cmd=[]
        cmd.append(self.nmap_bin)
        cmd.append('-O')
        cmd.append('-Pn')
        cmd.append(ip)
        cmd.append('-oX')
        cmd.append('-')

        # return self.proman.RunProcessWait(cmd)
        return self.parser.ParseOsScan(self.proman.RunProcessWait(cmd))
    
    def UdpScan(self,ip,scan_type=1):
        
        cmd = []
        cmd.append(self.nmap_bin)
        cmd.append('-sU')
        cmd.append('-Pn')
        cmd.append(ip)
        cmd.append('-oX')
        cmd.append('-')

        return self.parser.ParseServiceScan(self.proman.RunProcessWait(cmd),scan_type=scan_type)