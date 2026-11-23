from ProMan import ProMan
import time
from Host import Host, Port
from SString import FindSubstr
import xml.etree.ElementTree as ET

## This is an Nmap wrapper (hellooo)

#### Splits the hosts found by the last scan in new hosts and hosts that were
#### already known and finds which of the known hosts are not present any more.
def RefreshHosts(new_hosts,old_hosts):
    old_ips = [o_h.ip for o_h in old_hosts]
    found_ips = [n_h.ip for n_h in new_hosts]

    same_hosts = [n_h for n_h in new_hosts if n_h.ip in old_ips]
    only_new_hosts = [n_h for n_h in new_hosts if n_h.ip not in old_ips]
    disconnected = [o_h for o_h in old_hosts if o_h.ip not in found_ips]

    return only_new_hosts,same_hosts,disconnected


#### Returns the root of nmap's xml output or None if the output is not valid xml
#### (i.e. nmap was killed before finishing or failed to run).
def ParseXml(text):
    if text is None or text.strip() == '':
        return None
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


class NmapParser:
    def __init__(self,network_status):
        self.network_status = network_status
    
    def ParseHostUp(self,result):
        nmap_xml_root = ParseXml(result)
        if nmap_xml_root is None:
            return False
        for host in nmap_xml_root.iter('host'):
            for status in host.iter('status'):
                if status.attrib.get('state') == 'up':
                    return True
        return False
    
    def ParsePingScan(self,result):
        self.result_text = result

        #### scan was interrupted or failed. Keep the previous state.
        nmap_xml_root = ParseXml(self.result_text)
        if nmap_xml_root is None:
            return

        self.network_status.disconnected = []
        self.network_status.new_hosts = []

        new_hosts = []
        host_id = 0

        for host in nmap_xml_root.iter('host'):
            mac = '____LOCALHOST____'
            mac_type = 'Unknown'
            ip = "x.x.x.x"
            hostname = ''
            for element in host:
                for field in element.iter('address'):
                    if field.attrib['addrtype'] == 'ipv4' and ip == "x.x.x.x":
                        ip = field.attrib['addr']
                    elif field.attrib['addrtype'] == 'mac':
                        mac = field.attrib['addr']
                        if 'vendor' in field.attrib.keys():
                            mac_type = field.attrib['vendor']
                for hname in element.iter('hostname'):
                    hostname = hname.attrib['name']
                    if hostname == ip:
                        hostname = ''
            #### skip hosts without an ipv4 address
            if ip == "x.x.x.x":
                continue
            new_hosts.append(Host([ip,hostname],mac=mac,mac_type=mac_type))

        ### Categorize the Hosts found as new,current or disconnected
        new_hosts, same_hosts, disconnected = RefreshHosts(new_hosts,self.network_status.hosts)
        curr_hosts = new_hosts + same_hosts
        self.network_status.disconnected = disconnected
        self.network_status.hosts = curr_hosts
        self.network_status.new_hosts = new_hosts
    
    #### Returns the open ports found and the protocol scanned.
    #### The ports are None if the scan was stopped or failed.
    def ParseServiceScan(self,res,scan_type=1):
        self.result_text = res

        protocol = 'tcp'
        if scan_type == 0:
            protocol = 'udp'
        
        if self.network_status.stopped.is_set():
            return None,protocol

        nmap_xml_root = ParseXml(self.result_text)
        if nmap_xml_root is None:
            return None,protocol

        #### udp ports that do not answer are reported as open|filtered
        open_states = ['open']
        if protocol == 'udp':
            open_states.append('open|filtered')

        ports = []
        
        for port_info in nmap_xml_root.iter('port'):
            state = 'open'
            for state_info in port_info.iter('state'):
                state = state_info.attrib.get('state','open')
            if state not in open_states:
                continue

            service = ''
            version = ''
            port = port_info.attrib['portid']
            version_prefix = ' '
            attributes = ['product','extrainfo','ostype']
            for field in port_info.iter('service'):
                service = field.attrib.get('name','')
                if 'version' in field.attrib.keys():
                    version = field.attrib['version']
                    version_prefix = ' - '

                for attr in attributes:
                    if attr in field.attrib.keys():
                        version += version_prefix + field.attrib[attr]

            ports.append(Port(port,None,service,version))
        
        return ports,protocol
    
    def ParseOsScan(self,res):
        self.result_text = res
        if self.network_status.stopped.is_set():
            return
        os_info = []
        
        nmap_xml_root = ParseXml(self.result_text)
        if nmap_xml_root is None:
            return None
        
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
    def __init__(self,network_status,bin='nmap',proman=None):
        self.nmap_bin = bin
        #### use the process manager of the main program (if given), so that
        #### running scans can be killed when the user stops them
        self.proman = proman if proman is not None else ProMan()
        self.network_status = network_status
        self.parser = NmapParser(self.network_status)
        self.nmap_options = []
    
    def SetOptions(self,options):
        self.nmap_options = options
    
    def IsHostUp(self,ip):
        cmd = []
        cmd.append(self.nmap_bin)
        cmd.append('-sP')
        cmd.append(ip)
        cmd.append('-oX')
        cmd.append('-')

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
        cmd.append(ip)
        for opt in self.nmap_options:
            cmd.append(opt)
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
    
    def UdpScan(self,ip,scan_type=0):
        
        cmd = []
        cmd.append(self.nmap_bin)
        cmd.append('-sU')
        cmd.append('-Pn')
        cmd.append(ip)
        cmd.append('-oX')
        cmd.append('-')

        return self.parser.ParseServiceScan(self.proman.RunProcessWait(cmd),scan_type=scan_type)