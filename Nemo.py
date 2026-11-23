import os
import re
from threading import Event, Lock
import sched, time
import socket
# from menu_launcher import *
import sys
from Pricli import Pricli, InfoWindow, ControlPanel, Settings, Option
from ProMan import ProMan
from NetworkScanner import NetworkScanner
import ipaddress 
import argparse
# from informer import Informer 
import informer
# from analyzer import Analyzer
import analyzer

from Host import *

# main_lock = Lock()
# thread_lock = Lock()


class Nemo:
    def __init__(self,mode):
        self.main_lock = Lock()
        self.thread_lock = Lock()

        self.settings = None
        self.NORMAL = 0
        self.NOFANCY = 1
        self.DAEMON = 2
        self.INFORMER = 3

        self.SCAN_STRESS_NORMAL = 1
        self.SCAN_STRESS_FAST = 2
        self.SCAN_STRESS_FULL = 3


        #### General options
        self.settings_bindings = dict()
        self.setting = None

        self.network = None
        self.netmask = None
        self.dns_server = None
        self.AddSetting('network',self.network)
        self.AddSetting('netmask',self.netmask)
        self.AddSetting('dns_server',self.dns_server)
        

        self.nmap_options = []

        #### Fancy terminal with colors (ncurses) ####
        self.fancy = True

        #### These Arguments are used by the **** INFORMER **** switch ####
        #### Scan type to use when port scanning (required by informer switch) ####
        self.scan_type = 1
        self.scan_period = 30
        self.port_stress = 1
        self.ports_to_scan = None

        self.send_mail = True

        #### add these settings to the binder
        #### Scan type Parameters
        self.AddSetting('scan_type',self.scan_type)
        self.AddSetting('scan_period',self.scan_period)
        self.AddSetting('port_stress',self.port_stress)
        self.AddSetting('ports_to_scan',self.ports_to_scan)

        #### Informer parameters
        self.AddSetting('send_mail',self.send_mail)

        self.mode = mode
        self.network_status = None
        self.pricli = None
        self.network_scanner = None
        self.proman = None


        if self.mode[0] == self.INFORMER:
            self.fancy = False

        self.scan_type = self.mode[2]
        self.scan_period = self.mode[3]
        self.port_stress = self.mode[4]
        self.ports_to_scan = self.mode[5]
        self.UpdateNmapOptions()

    def UpdateNmapOptions(self):
        options = []

        ports = self.ports_to_scan
        if isinstance(ports,(list,tuple)):
            ports = ','.join([str(p) for p in ports])

        #### specific ports override the port stress option
        if ports is not None and str(ports).strip() not in ['','None']:
            ports = str(ports).strip()
            if ports.startswith('-p'):
                ports = ports[2:].strip()
            options.append('-p'+ports)
        elif self.port_stress == self.SCAN_STRESS_FAST:
            options.append('-F') 
        elif self.port_stress == self.SCAN_STRESS_FULL:
            options.append('-p1-65535')

        #### the list is shared with the network scanner, so it is changed in place
        self.nmap_options[:] = options
        
        #### append netmask to (network) ip if not provided ####
        if self.network is not None and self.netmask is not None:
            if '/' not in self.network:
                self.network += '/'+str(self.netmask).strip('/')

    
    def AddSetting(self,key,value):
        self.settings_bindings[key] = value
    
    def GetSetting(self,key):
        return self.settings_bindings[key]

    #### Values coming from the settings menu are text typed by the user,
    #### so they are converted to the type that each setting expects.
    def NormalizeSetting(self,key,value):
        if key in ['scan_type','scan_period','port_stress']:
            try:
                value = int(value)
            except (TypeError, ValueError):
                return getattr(self,key)
            if key == 'scan_type' and value not in [1,2]:
                return getattr(self,key)
            if key == 'port_stress' and value not in [1,2,3]:
                return getattr(self,key)
            if key == 'scan_period' and value < 1:
                return getattr(self,key)
        elif key == 'send_mail':
            if isinstance(value,str):
                value = value.strip().lower() in ['true','1','yes','on']
            else:
                value = bool(value)
        elif key in ['network','netmask','dns_server','ports_to_scan']:
            if isinstance(value,bool):
                value = str(int(value))
            if isinstance(value,str) and value.strip() in ['','None']:
                value = None
        return value
    
    def SetSetting(self,key,value):
        value = self.NormalizeSetting(key,value)
        setattr(self,key,value)
        self.settings_bindings[key] = value
        self.UpdateNmapOptions()
    
    def SetSettings(self,settings):
        for key,value in settings.items():
            value = self.NormalizeSetting(key,value)
            setattr(self,key,value)
            self.settings_bindings[key] = value
            #### show the value that is actually used in the settings menu
            settings[key] = value
        self.UpdateNmapOptions()
    # def ChangeMember(self,member,value):
    #     member = value

    def SetNetworkStatus(self,network_status):
        self.network_status = network_status
    
    def SetNetworkScanner(self,network_scanner):
        self.network_scanner = network_scanner
    
    def SetProMan(self,proman):
        self.proman = proman
    
    def SetPricli(self,pricli):
        self.pricli = pricli
    
    def SetScanType(self,scan_type):
        self.scan_type = scan_type

    def AddSettings(self,settings):
        self.settings = settings

class Theme:
    def __init__(self,pricli):
        self.pricli = pricli
        self.top_wall_style = '='
        self.left_wall_style = '|'
        self.right_wall_style = '|'
        self.bottom_wall_style = '='

        self.top_wall_width = 1
        self.left_wall_width = 1
        self.right_wall_width = 1
        self.bottom_wall_width = 1

        self.left_space_start_pos = 1
        self.top_space_start_pos = 1

        self.width = self.pricli.screen_cols
        self.height = self.pricli.screen_rows

        ### colors
        self.top_wall_color = self.pricli.normal_color
        self.right_wall_color = self.pricli.normal_color
        self.left_wall_color = self.pricli.normal_color
        self.bottom_wall_color = self.pricli.normal_color


    def InitPricli(self):
        self.pricli.ChangePos(self.left_space_start_pos)
        self.pricli.ChangeCur(self.top_space_start_pos)
        self.pricli.ChangeTop(self.top_space_start_pos)
    

    def CreateWalls(self):
        self.pricli.Printlnr(self.top_wall_style*self.width,self.top_wall_color)
        for row in range(self.height):
            self.pricli.Printlnr(self.left_wall_style,self.left_wall_color)
        self.pricli.ChangePos(self.width)
        for row in range(self.height):
            self.pricli.Printlnr(self.right_wall_style,self.right_wall_color)
        self.pricli.ChangeCur(self.height-1)
        self.pricli.ChangePos(2)
        self.pricli.Printlnr(self.bottom_wall_style*(self.width-2),self.bottom_wall_color)
        self.top_space_start_pos += self.top_wall_width
        self.left_space_start_pos += self.left_wall_width
        time.sleep(2)
        self.InitPricli()
        
        
        
        

class InputHandler:
    def __init__(self,pricli,key_bindings=None):
        self.pricli = pricli
        if key_bindings is None:
            self.key_bindings = dict()
            self.key_bindings['q'] = 'Quit'
            self.key_bindings['l'] = 'Next Page'
            self.key_bindings['k'] = 'Prev page'
            
        else:
             self.key_bindings=key_bindings
        self.input = None
    
    def Listen(self):
        self.input = self.pricli.Input()



def parse_arguments():
    if len(sys.argv) == 1:
        print("Using default port 1997...")
        return '1997'
    else:
        port = sys.argv[1]
        if port.isnumeric():
            return port
        else:
            print("Invalid port number. BB.")
            sys.exit()

#### Main Class of the program that holds info about all hosts in
#### the network, their ports, their hostname etc...

class NetworkStatus(object):
    def __init__(self,network,port):
        self.connected = False
        # self.client_socket = socket.socket()        
        self.hosts = []
        self.disconnected = []
        self.new_hosts = []
        self.numHosts = 0
        self.network = network
        self.s = sched.scheduler(time.time, time.sleep)
        #self.port = port #port to connect to monitor
        #self.monitor_fd = self.ConnectToMonitor()
        self.host_files = None
        self.host_json_data = []
        self.InitJson()
        # self.stopped = False
        self.stopped = Event()
    
    def GetHostByIp(self,ip):
        for host in self.hosts:
            if ip == host.ip:
                return host
        return None
    
    def Clear(self):
        self.hosts = []
        self.disconnected = []
        self.new_hosts = []
        self.numHosts = 0
    
    def SortHosts(self):
        ip_list = sorted([h.ip for h in self.hosts],key=ipaddress.IPv4Address)

        temp_hosts = []
        for ip in ip_list:
            for host in self.hosts:
                if ip == host.ip:
                    temp_hosts.append(host)
        
        self.hosts = temp_hosts

    def Update(self):
        self.numHosts = len(self.hosts)
        for host in self.hosts:
            host.LoadJsonData()
        
        self.SortHosts()
    
    def FirstTimeInit(self):
        networks_path = os.getcwd()+'/Networks'
        os.makedirs(networks_path+'/tcp',exist_ok=True)
        os.makedirs(networks_path+'/udp',exist_ok=True)


    #### Every network scanned, has its own folder placed inside the 'Networks' folder ####
    def InitJson(self):
        networks_path = os.getcwd()+'/Networks'
        #### make sure that the directories exist (create folder etc)
        self.FirstTimeInit()
        self.host_files = next(os.walk(networks_path), (None, None, []))[2]  # [] if no file
        for host in self.hosts:
            host.LoadJsonData()


#### Used in place of pricli when there is no curses screen (--informer switch),
#### so that every color requested is just 0.
class NoColors:
    def __getattr__(self,name):
        return 0


def Exit(pricli):
    pricli.End()


def print_simple_scan_header(pricli,art_width,network_status,biggest_mac_type):
    pricli.UpdatePage(['='*int((art_width - 6)/2)+" SCAN "+'='*int((art_width - 5)/2)],[pricli.RED])
    pricli.UpdatePage(["Found ", str(network_status.numHosts)," total hosts"],[pricli.WHITE, pricli.YELLOW, pricli.YELLOW])
    pricli.UpdatePage(['='*int((art_width - 6)/2)+" SCAN "+'='*int((art_width - 5)/2)],[pricli.RED])

    number_of_spaces = int(pricli.screen_cols/10)
    

    pricli.UpdatePage(['IP'+' '*number_of_spaces+'MAC'+' '*number_of_spaces+'TYPE'+' '*(biggest_mac_type-1)+'HOSTNAME'])
    pricli.UpdatePage(['\n'])


def simple_scan(nemo):
    x = nemo.proman.StartThread(SimpleScan,(nemo,))
    return x

def SimpleScan(nemo):
    network_status = nemo.network_status
    # network_status.network = nemo.network
    pricli = nemo.pricli
    network_scanner = nemo.network_scanner
    # global network_status
    if network_status.stopped.is_set():
        pricli.Clear()
        return
    while(1):
        if network_status.stopped.is_set():
            pricli.Clear()
            return

        network_scanner.NetworkDiscovery(nemo.network)
        network_status.Update()
        if network_status.stopped.is_set():
            pricli.Clear()
            return

        pricli.Clear()
        pricli.Init()
        pricli.Refresh()
        
        if network_status.stopped.is_set():
            pricli.Clear()
            return

        art_width = int(pricli.screen_cols/3)
        # pricli.UpdatePage(['='*int((art_width - 6)/2)+" SCAN "+'='*int((art_width - 5)/2)],[pricli.RED])
        # pricli.UpdatePage(["Found ", str(network_status.numHosts)," total hosts"],[pricli.WHITE, pricli.YELLOW, pricli.YELLOW])
        # pricli.UpdatePage(['='*int((art_width - 6)/2)+" SCAN "+'='*int((art_width - 5)/2)],[pricli.RED])

        
        # pricli.UpdatePage(['IP'+' '*number_of_spaces+'MAC'+' '*number_of_spaces+'TYPE'+' '*biggest_mac_type+'HOSTNAME'])
        # pricli.UpdatePage(['\n'])


        biggest_mac_type = 0
        for host in network_status.hosts:
            if len(host.mac_type) > biggest_mac_type:
                biggest_mac_type = len(host.mac_type)

        number_of_spaces = int(pricli.screen_cols/10)
        print_simple_scan_header(pricli,art_width,network_status,biggest_mac_type)

        for host in network_status.hosts:
            ScanText = host.ip + '\t' + host.hostname
            if not pricli.AssessText(ScanText):
                pricli.CreateNewPage()
                print_simple_scan_header(pricli,art_width,network_status,biggest_mac_type)

                # if pricli.current_page.current_line + 1 > pricli.screen_rows:
                    # pricli.CreateNewPage()
            pricli.UpdatePage([host.ip,' '*(number_of_spaces-len(host.ip)+2),host.mac,' '*(number_of_spaces-len(host.mac)+3),host.mac_type, ' '*(biggest_mac_type-len(host.mac_type)+3),host.hostname],[pricli.BLUE,pricli.WHITE,pricli.YELLOW,pricli.WHITE,pricli.CYAN,pricli.WHITE,pricli.RED])

        if len(network_status.new_hosts):
            pricli.UpdatePage(['\n'])
            pricli.UpdatePage(['='*int((art_width - 10)/2)+" New hosts "+'='*int((art_width - 11)/2)],[pricli.MAGENTA])
            for host in network_status.new_hosts:
                if nemo.send_mail:
                    host.NotifyUp()

                if not pricli.AssessText(host.ip + '\t' + host.hostname):
                    pricli.CreateNewPage()
                    print_simple_scan_header(pricli,art_width,network_status,biggest_mac_type)
                pricli.UpdatePage([host.ip,' '*(number_of_spaces-len(host.ip)+2),host.mac,' '*(number_of_spaces-len(host.mac)+3),host.mac_type,' '*(biggest_mac_type-len(host.mac_type)+3),host.hostname],[pricli.BLUE,pricli.WHITE,pricli.YELLOW,pricli.WHITE,pricli.CYAN,pricli.WHITE,pricli.RED])

        if len(network_status.disconnected):
            pricli.UpdatePage(['\n'])
            pricli.UpdatePage(['='*int((art_width - 20)/2)+" Disconnected hosts "+'='*int((art_width - 20)/2)],[pricli.GREEN])
            for host in network_status.disconnected:
                if nemo.send_mail:
                    host.NotifyDown()

                if not pricli.AssessText(host.ip + '\t' + host.hostname):
                    pricli.CreateNewPage()
                    print_simple_scan_header(pricli,art_width,network_status,biggest_mac_type)
                pricli.UpdatePage([host.ip,' '*(number_of_spaces-len(host.ip)+2),host.mac,' '*(number_of_spaces-len(host.mac)+3),host.mac_type,' '*(biggest_mac_type-len(host.mac_type)+3),host.hostname],[pricli.BLUE,pricli.WHITE,pricli.YELLOW,pricli.WHITE,pricli.CYAN,pricli.WHITE,pricli.RED])

        pricli.RefreshPage()
        counter = int(nemo.scan_period)
        while counter > 0:
            time.sleep(0.1)
            if nemo.network_status.stopped.is_set():
                return
            counter -= 0.1
        pricli.ClearPages()

def port_scan(nemo):
    x = nemo.proman.StartThread(PortScan,(nemo,))
    return x

def PortScan(nemo):
    pricli = nemo.pricli
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    fancy = nemo.fancy
    #### without curses there are no colors
    palette = pricli if fancy else NoColors()
    stopped = False
    while True:

        if stopped:
            break

        network_scanner.NetworkDiscovery(nemo.network)
        network_status.Update()

        if fancy:
            pricli.Clear()
            pricli.Init()
            pricli.Refresh()

        for host in network_status.hosts:
            if network_status.stopped.is_set():
                stopped = True
                break
            lines = []
            colors = []
            if network_scanner.IsHostUp(host.ip):
                if host.hostname != '':
                    lines,colors = PortScanResults(host.ip,nemo,proto=1,colr=[[palette.normal_color,palette.RED,palette.normal_color,palette.BLUE,palette.normal_color]]) 
                else:
                    lines,colors = PortScanResults(host.ip,nemo,proto=1,colr=[[palette.normal_color,palette.RED]]) 
            else:
                continue

            if network_status.stopped.is_set():
                stopped = True
                break

            if host.hostname != '':
                lines.insert(0,["PORT INFO FOR ",host.ip,' (',host.hostname,')'])
            else:
                lines.insert(0,["PORT INFO FOR ",host.ip])

            if fancy:
                if len(lines) + pricli.current_page.current_line > pricli.screen_rows:
                    pricli.CreateNewPage()

                for line_index in range(len(lines)):
                    pricli.UpdatePage(lines[line_index],colors[line_index])
                pricli.RefreshPage()
            else:
                for line in lines:
                    print(''.join(line),flush=True)
                print('',flush=True)

        if stopped:
            break

        counter = int(nemo.scan_period)
        while counter > 0:
            time.sleep(0.1)
            counter -= 0.1
            if nemo.network_status.stopped.is_set():
                return

        if fancy:
            pricli.ClearPages()

#### proto=1 for tcp and 2 for udp ####
def PortScanResults(host_ip,nemo,proto=1,colr=None):
    host = nemo.network_status.GetHostByIp(host_ip)
    #### without curses (--informer switch) there are no colors
    pricli = nemo.pricli if nemo.pricli is not None else NoColors()

    lines = []
    colors = []
    if colr is None:
        colors = [[pricli.RED]]
    else:
        colors = colr

    #### host disappeared from the network since it was selected
    if host is None:
        lines.append(['Host is not in the network any more'])
        colors.append([pricli.RED])
        return lines,colors

    # udp
    if proto == 2:
        ports,protocol = nemo.network_scanner.UdpScan(host_ip,scan_type=0) # scan_type = 0 for udp
    # tcp
    else:
        ports,protocol = nemo.network_scanner.ServiceScan(host_ip,scan_type=nemo.scan_type)

    #### scan was stopped or failed. Do not touch the saved state of the host,
    #### otherwise all its ports would be reported as closed.
    if ports is None:
        lines.append(['Scan did not finish'])
        colors.append([pricli.RED])
        return lines,colors

    host.ports = ports
    if protocol == 'tcp':
        host.ports_tcp = host.ports
    if protocol == 'udp':
        host.ports_udp = host.ports
        
    host.CheckChanges(nemo.send_mail,protocol)
    host.SaveJson(protocol)

    # lines.append(['Ports: '])
    # colors.append([pricli.GREEN])
    if len(host.ports) < 1:
        lines.append(['No scanned ports open'])
        colors.append([pricli.RED])
    for port in host.ports:
        lines.append([port.num+'/'+protocol])
        colors.append([pricli.YELLOW])
        if protocol == 'udp' or nemo.scan_type == 1:
            lines.append(['Service: ',port.service])
            colors.append([pricli.CYAN,pricli.RED])
        else:
            lines.append(['Service: ',port.service, '  ', port.version])
            colors.append([pricli.CYAN,pricli.RED,pricli.normal_color,pricli.MAGENTA])
    
    return lines,colors
        

def OsDetectionResults(host_ip,nemo):
    pricli = nemo.pricli 

    #### check once again if host is up and try until it is or until 3 tries have been passed ####
    tries = 3
    while tries > 0:
        if nemo.network_scanner.IsHostUp(host_ip):
            break
        tries -= 1
        if nemo.network_status.stopped.is_set():
            break
        time.sleep(1)

    os = nemo.network_scanner.OsScan(host_ip)
    lines = []
    colors = []
    colors.append([pricli.RED])

    if os is None:
        lines.append(['Could not determine OS.', 'Maybe that host is on another network?'])
        colors.append([pricli.RED,pricli.YELLOW])
    else:
        lines.append(['Mac Address: ',os[0]])
        colors.append([pricli.normal_color,pricli.YELLOW])

        titles = ['Device type','Running','OS Details']
        if len(os) > 1:
            for indx in range(1,len(os)):
                if len(os[indx]) >= pricli.screen_cols:
                    os[indx] = os[indx][0:pricli.screen_cols-50] 
                lines.append([titles[indx-1]+": ",os[indx]])
                colors.append([pricli.normal_color,pricli.YELLOW])

            # lines.append(['Device Type: ',os[1]])
            # colors.append([pricli.normal_color,pricli.YELLOW])
            # lines.append(['Running: ',os[2]])
            # colors.append([pricli.normal_color,pricli.YELLOW])
            # lines.append(['OS CPE: ',os[3]])
            # colors.append([pricli.normal_color,pricli.YELLOW])
            # lines.append(['OS Details: ',os[3]])
            # colors.append([pricli.normal_color,pricli.YELLOW])
        else:
            lines.append(['OS: ','Unknown'])
            colors.append([pricli.normal_color,pricli.YELLOW])
    return lines,colors

   

def host_monitor_status(nemo,ip,name):
    nemo.proman.StartThread(informer.HostMonitorStatus,(nemo,ip,name,))

def host_monitor_ports(nemo,ip,name):
    nemo.proman.StartThread(informer.HostMonitorPorts, (nemo,ip,name,))



def MainMenu(nemo):
    # global network_status
    pricli = nemo.pricli
    network_status = nemo.network_status
    proman = nemo.proman
    # is_in_another_menu = False ### becomes true if user selects one of the options and false if user is in current menu
    while True:
        # if is_in_another_menu:
        #     time.sleep(2)
        #     continue
        # nemo.main_lock.acquire()
        actions = ["Informer","Analyzer","Options","Exit"] 
        choice = pricli.menu.Menu("Select an action...",actions)
        network_status.stopped.clear()

        if choice == 1:
            # pricli.ChangeWindow(reset=True)
            informer.Informer(nemo)
            continue
            # is_in_another_menu = True
            
        elif choice == 2:
            analyzer.Analyzer(nemo)
            # pricli.lock.acquire()
            # is_in_another_menu = True
            continue
            # time.sleep(1)

        elif choice == 3:
            settings_choice = 0
            while True:
                settings_choice = nemo.settings.Draw()
                if settings_choice == -1: #### Exit chosen
                    break
                settings = nemo.settings.DrawOption(settings_choice-1)
                nemo.SetSettings(settings)
                continue
            continue
            

        elif choice == len(actions):
            Exit(pricli)
            break

        key = ''
        while key != ord('q'):
            # if is_in_another_menu:
                # pricli.lock.acquire()
                # lock.acquire()
            key = pricli.Input()
            if key == ord("l"):
                if len(pricli.pages) > 1:
                    pricli.GoToNextPage()
            elif key == ord("k"):
                pricli.GoToPreviousPage()
        # is_in_another_menu = False

        pricli.ClearPages()
        network_status.stopped.set() 
        proman.KillProcesses()
        proman.JoinThreads()
        network_status.stopped.clear()
        pricli.ChangeWindow(reset=True)

def getNetInfo(pricli,proman):
    cmd = r"ip addr | grep inet | awk '{print $2}' | grep -v 127.0.0.1 | grep -E -i '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,3}$'"
    ## The above command, prints all the networks that each interface is connected to, except the localhost net.
    res = proman.RunProcess(cmd,shell=True).split('\n')[:-1]
    res.append("Exit")
    choice = pricli.menu.Menu("Choose a network to scan...",res)
    return res[choice-1]

def ParseArguments():
    parser = argparse.ArgumentParser(prog='net_status',description='A network monitor/analyzer')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--nofancy',action='store_true',help='Show classic terminal output (without curses)')
    mode_group.add_argument('--daemon',action='store_true',help='Run in background')
    mode_group.add_argument('--informer',action='store_true',help='Monitor for opened/closed ports and report to admin')
    parser.add_argument('--network',action='store',help='The network to scan. Required with --informer option')
    parser.add_argument('--port-scan-type',choices=['simple','version'],help='simple for simple port discovery, version for version scan (-sV). Default is simple.')
    parser.add_argument('--scan-period',action='store',type=int,help='Time in seconds after which the port scan will be repeated. Default is 30 seconds')
    parser.add_argument('--port-stress',choices=['normal','fast','full'],help='Number of ports to be scanned. Default is normal (1000) ports. Fast scans less than 1000 and full scans all 65535 ports (slow).')
    parser.add_argument('--ports',metavar='PORTS',nargs='+',help='Specific ports or port ranges to scan. Ex: --ports 22 80 5001, --ports 1-65535')
    args = parser.parse_args()

    mode = 0
    if args.nofancy:
        parser.error('--nofancy is not implemented yet. Use --informer for output without curses.')
    elif args.daemon:
        parser.error('--daemon is not implemented yet.')
    elif args.informer:
        mode = 3
        if args.network is None:
            parser.error('--network option is required with the --informer switch')

    #### GENERAL options
    scan_period = 30
    port_stress = 1

    if args.scan_period is not None:
        if args.scan_period < 1:
            parser.error('--scan-period must be a positive number of seconds.')
        scan_period = int(args.scan_period)

    #### simple port discovery, unless version scan is requested
    scan_type = 1
    if args.port_scan_type == 'version':
        scan_type = 2

    if args.port_stress is not None:
        if args.ports is not None:
            parser.error('--ports option cannot be used alongside with --port-stress option.')
        if args.port_stress == 'fast':
            port_stress = 2
        elif args.port_stress == 'full':
            port_stress = 3

    ports = None
    if args.ports is not None:
        port_list = []
        for port_arg in args.ports:
            port_list += [p for p in port_arg.split(',') if p != '']
        for port in port_list:
            valid = re.fullmatch(r'(\d{1,5})(-(\d{1,5}))?',port)
            if valid is not None:
                first = int(valid.group(1))
                last = int(valid.group(3)) if valid.group(3) is not None else first
                valid = 1 <= first <= last <= 65535
            if not valid:
                parser.error('invalid port or port range: '+port)
        ports = ','.join(port_list)

    return mode,args.network,scan_type,scan_period,port_stress,ports

def CreateSettings(nemo,pricli):
    settings = Settings(pricli,nemo)
    network_settings = Option(pricli=pricli,title='Network')
    network_settings.AddParameter('network',nemo.network)
    network_settings.AddParameter('netmask',nemo.netmask)
    settings.AddOption(network_settings)
    scan_settings = Option(pricli=pricli,title='Scan settings')
    scan_settings.AddParameter('scan_type',nemo.scan_type)
    scan_settings.AddParameter('scan_period',nemo.scan_period)
    scan_settings.AddParameter('port_stress',nemo.port_stress)
    scan_settings.AddParameter('ports_to_scan',nemo.ports_to_scan)
    settings.AddOption(scan_settings)
    settings.AddOption(Option(pricli=pricli,title='Port settings'))
    informer_settings = Option(pricli=pricli,title='Informer settings')
    informer_settings.AddParameter('send_mail',nemo.send_mail)
    settings.AddOption(informer_settings)
    settings.AddOption(Option(pricli=pricli,title='Theme'))
    settings.AddOption(Option(pricli=pricli,title='Exit'))

    return settings

    # settings.Draw()

def StartNemo(nemo):
    mode = nemo.mode

    pricli = None
    network = ''
    if mode[0] == nemo.INFORMER:
        network = mode[1]
        nemo.SetSetting('network',network)
    else:
        pricli = Pricli()
        nemo.SetPricli(pricli)
        network = getNetInfo(pricli,nemo.proman)

        if 'Exit' in network:
            Exit(pricli)
            return
        # nemo.SetNetwork(network)
        nemo.SetSetting('network',network)
        nemo.SetSetting('netmask',network.split('/')[1])
        # nemo.SetSetting('dns_server',network[0:-4]+)
        nemo.AddSettings(CreateSettings(nemo,pricli=pricli))

    network_status = NetworkStatus(network,None)
    network_scanner = NetworkScanner(network_status,proman=nemo.proman)
    network_scanner.SetOptions(nemo.nmap_options)
    nemo.SetNetworkStatus(network_status)
    nemo.SetNetworkScanner(network_scanner)
    # theme = Theme(pricli)
    # theme.CreateWalls()

    if mode[0] == nemo.INFORMER:
        PortScan(nemo)
    else:
        MainMenu(nemo)


    
    # Analyzer(pricli)


if __name__ == "__main__":
    mode = ParseArguments()
    proman = ProMan()
    nemo = Nemo(mode)
    nemo.SetProMan(proman)
    # network_status = None

    StartNemo(nemo)
    # sys.exit()

