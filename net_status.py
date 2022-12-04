from dis import disco
from distutils.debug import DEBUG
import os
from pickle import FALSE
from threading import Thread, Lock
import sched, time
import socket
# from menu_launcher import *
import sys
from Pricli import Pricli, InfoWindow, ControlPanel, Settings, Option
from ProMan import ProMan
from NetworkScanner import NetworkScanner
import ipaddress 
import argparse

from Host import *

lock = Lock()


class Nemo:
    def __init__(self,mode):
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
        self.port_scan_period = 30
        self.port_stress = 1
        self.ports_to_scan = None

        #### add these settings to the binder
        self.AddSetting('scan_type',self.scan_type)
        self.AddSetting('port_scan_period',self.port_scan_period)
        self.AddSetting('port_stress',self.port_stress)
        self.AddSetting('ports_to_scan',self.ports_to_scan)

        self.mode = mode
        self.network_status = None
        self.pricli = None
        self.network_scanner = None

        if self.mode[0] == self.INFORMER:
            self.fancy = False

        self.scan_type = self.mode[2]
        self.port_scan_period = self.mode[3]
        self.port_stress = self.mode[4]
        self.ports_to_scan = self.mode[5]

        if self.port_stress == self.SCAN_STRESS_FAST:
            self.nmap_options.append('-F') 
        elif self.port_stress == self.SCAN_STRESS_FULL:
            self.nmap_options.append('-p1-65535')

        if self.ports_to_scan is not None:
            self.nmap_options.append(self.ports_to_scan)
    
    def AddSetting(self,key,value):
        self.settings_bindings[key] = value
    
    def GetSetting(self,key):
        return self.settings_bindings[key]
    
    def SetSetting(self,key,value):
        setattr(self,key,value)
    
    def ChangeMember(self,member,value):
        member = value

    def SetNetworkStatus(self,network_status):
        self.network_status = network_status
    
    def SetNetworkScanner(self,network_scanner):
        self.network_scanner = network_scanner
    
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
        self.stopped = False
    
    def Clear(self):
        for host in self.hosts:
            del host
            self.hosts.remove(host)
        self.hosts = []

        for host in self.disconnected:
            del host
            self.disconnected.remove(host)
        self.disconnected = []

        for host in self.new_hosts:
            del host
            self.new_hosts.remove(host)
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
        os.mkdir(networks_path)


    #### Every network scanned, has its own folder placed inside the 'Networks' folder ####
    def InitJson(self):
        networks_path = os.getcwd()+'/Networks'
        #### check if path exists. If not initialize the directories (create folder etc)
        if os.path.exists(networks_path):
            self.host_files = next(os.walk(networks_path), (None, None, []))[2]  # [] if no file
            for host in self.hosts:
                host.LoadJsonData()
        else:
            self.FirstTimeInit()


    def ConnectToMonitor(self):
        host = '127.0.0.1'
        # port = 1998
        # client_socket = socket.socket()        

        global cur_line
        cur_line = 1
        Print2('Trying to connect to monitor')
            
        try:
            self.client_socket.connect((host,int(self.port)))
        except socket.error as e:
            Print2(str(e))
            screen2.refresh()
            return False
        Print2("Connected!")
        screen2.refresh()
        time.sleep(2)

        # poller = select.poll()
        # poller.register(client_socket,select.POLLIN)
        # fd_to_sock = {client_socket.fileno():client_socket,}

        # Check for Client Disconnect
        # while True:
            # fdVsEvent = poller.poll(10000)
            # fd = -1
            # for fd, event in fdVsEvent:
                # Print("fd: " + str(fd)+" event: "+str(event))
                # top_frame.UpdateStatusTop("Connected with client")
                # top_frame.UpdateStatusIcon(True)
            # if fd != -1:
                # check for connection
            # msg = client_socket.(4)
            # if msg.decode() == str(1):
            #     # begin send data
            #     ack = '2'
            #     os.send(fd,ack.encode())
            #     self.connected = True
            #     return fd

            # Print(msg)
            # screen.refresh()
        # time.sleep(2)

def Exit(pricli):
    # if who == 1:
    #     screen.keypad(False)
    # else:
    #     screen2.keypad(False)
    # curses.nocbreak()
    # curses.echo()
    # curses.endwin()
    pricli.End()




def simple_scan(nemo):
    x = proman.StartThread(SimpleScan,(nemo,))
    return x

def SimpleScan(nemo):
    network_status = nemo.network_status
    # network_status.network = nemo.network
    pricli = nemo.pricli
    network_scanner = nemo.network_scanner
    # global network_status
    if network_status.stopped:
        pricli.Clear()
        return
    while(1):
        network_scanner.NetworkDiscovery(nemo.network)
        network_status.Update()
        if network_status.stopped:
            pricli.Clear()
            return

        pricli.Clear()
        pricli.Init()
        pricli.Refresh()
        
        if network_status.stopped:
            pricli.Clear()
            return
        pricli.UpdatePage(["======================== SCAN =========================="],[pricli.RED])
        pricli.UpdatePage(["Found ", str(network_status.numHosts)," total hosts"],[pricli.WHITE, pricli.YELLOW, pricli.YELLOW])
        pricli.UpdatePage(["======================== SCAN =========================="],[pricli.RED])

        for host in network_status.hosts:

            ScanText = host.ip + '\t' + host.hostname
            if not pricli.AssessText(ScanText):
                pricli.CreateNewPage()
            pricli.UpdatePage([host.ip,"\t",host.hostname],[pricli.BLUE,pricli.WHITE,pricli.RED])

        if len(network_status.new_hosts):
            pricli.UpdatePage(["==================== New hosts ======================="])

            for host in network_status.new_hosts:
                pricli.UpdatePage([host.ip,"\t",host.hostname],[pricli.BLUE,pricli.WHITE,pricli.RED])

        if len(network_status.disconnected):
            pricli.UpdatePage(["==================== Disconnected hosts ======================="])
            for host in network_status.disconnected:
                pricli.UpdatePage([host.ip,"\t",host.hostname],[pricli.BLUE,pricli.WHITE,pricli.RED])
        pricli.RefreshPage()
        time.sleep(5)
        pricli.ClearPages()

def port_scan(nemo):
    x = proman.StartThread(PortScan,(nemo,))
    return x

def PortScan(nemo):
    pricli = nemo.pricli
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    fancy = nemo.fancy
    scan_type = nemo.scan_type
    port_scan_period = nemo.port_scan_period
    stopped = False
    while True:
        if stopped:
            break
        # UpdateHosts(network_status,pricli,locking=False)
        # network_status.Update()
        network_scanner.NetworkDiscovery(nemo.network)
        network_status.Update()

        if fancy:
            pricli.Clear()
            pricli.Init()
            pricli.Refresh()

            pricli.UpdatePage(["====================== PORT SCAN ======================"])
            pricli.RefreshPage()

        for host in network_status.hosts:
            if not fancy:
                print('Host: '+host.ip)
            if network_status.stopped:
                stopped = True
                break

            if network_scanner.IsHostUp(host.ip):
                host.ports = network_scanner.ServiceScan(host.ip,scan_type)
                host.CheckChanges()
                host.SaveJson()
            else:
                continue

            if fancy:
                ## The first section until AssessText, checks if the text to be printed will fit the screen rows. 
                ## If not, it will be (hopefully) printed on a new column, right to the already printed ones
                ## and on the top row.

                if len(host.ports) > 0:
                    Port_Scan_Txt = ""
                    Port_Scan_Txt += "Host: "+host.ip+" ("+host.hostname+")\n"
                    Port_Scan_Txt += "Ports:\n\t"
                    for port in host.ports:
                        if scan_type == 2:
                            Port_Scan_Txt += str(port.num)+'\n\t'+port.service+"\n\t"+port.version+"\n\t"
                        else:
                            Port_Scan_Txt += str(port.num)+'\n\t'+port.service+'\n\t'
                    if not pricli.AssessText(Port_Scan_Txt):
                        pricli.CreateNewPage()

                    ## Assessment finished, will now try to print the actual formated (with colors etc. ) text
                    pricli.UpdatePage(["Host: ",host.ip," (",host.hostname,")"],[pricli.WHITE,pricli.BLUE,None,pricli.RED,None])
                    pricli.UpdatePage(["Ports:"],[pricli.GREEN])
                    # pricli.AddTab()
                    for port in host.ports:
                        Port_Scan_Txt += str(port.num)
                        pricli.UpdatePage([str(port.num)],[pricli.YELLOW])
                        pricli.UpdatePage(["\t"+"Service:",port.service],[pricli.RED,pricli.CYAN])
                        if scan_type == 2: ## print version if selected
                            pricli.UpdatePage(["\t"+"Version:",port.version],[pricli.RED,pricli.MAGENTA])

                        # pricli.RemoveTab()
                    # pricli.RemoveTab()
                else: 
                    Port_Scan_Txt = ""
                    Port_Scan_Txt += "Host: "+host.ip+" ("+host.hostname+")\n"
                    Port_Scan_Txt += "No open ports found"
                    if not pricli.AssessText(Port_Scan_Txt):
                        pricli.CreateNewPage()

                    ## Assessment finished, will now try to print the actual formated (with colors etc. ) text
                    pricli.UpdatePage(["Host: ",host.ip,"\t"," (",host.hostname,")"],[pricli.WHITE,pricli.BLUE,None,None,pricli.RED,None])
                    pricli.UpdatePage(['\tHas no open ports'],[pricli.GREEN])

            if fancy:
                pricli.RefreshPage()

        time.sleep(port_scan_period)
        if fancy:
            pricli.ClearPages()

# def analyzer(pricli):
#     if network_status.stopped:
#         pricli.Clear()
#         return

#     x = proman.StartThread(Analyzer,(pricli,))
#     return x

def PortScanResults(host_ip,scan_type,network_scanner,pricli):
    ports = network_scanner.ServiceScan(host_ip,scan_type=scan_type)

    lines = []
    colors = [[pricli.RED]]

    lines.append(['Ports: '])
    colors.append([pricli.GREEN])
    if len(ports) < 1:
        lines.append(['No scanned ports open'])
        colors.append([pricli.RED])
    for port in ports:
        lines.append([port.num])
        colors.append([pricli.YELLOW])
        if scan_type == 1:
            lines.append(['Service: ',port.service])
            colors.append([pricli.CYAN,pricli.RED])
        else:
            lines.append(['Service: ',port.service, '  ', port.version])
            colors.append([pricli.CYAN,pricli.RED,pricli.normal_color,pricli.MAGENTA])
    
    return lines,colors
        

def OsDetectionResults(host_ip,network_scanner,pricli):
    os = network_scanner.OsScan(host_ip)
    # pricli.UpdatePage(['OS Info for: ', host_ip ,' (',hostname,')'],[pricli.BLUE,pricli.GREEN,pricli.WHITE,pricli.YELLOW,pricli.WHITE])
    # pricli.UpdatePage(['Mac Address: ',os[0]],[pricli.BLUE,pricli.RED])
    # pricli.UpdatePage(['Device Type: ',os[1]],[pricli.BLUE,pricli.RED])
    # pricli.UpdatePage(['Running: ',os[2]],[pricli.BLUE,pricli.RED])
    # pricli.UpdatePage(['OS CPE: ',os[3]],[pricli.BLUE,pricli.RED])
    # pricli.UpdatePage(['OS Details: ',os[4]],[pricli.BLUE,pricli.RED])
    lines = []
    colors = []
    colors.append([pricli.RED])
    lines.append(['Mac Address: ',os[0]])
    colors.append([pricli.normal_color,pricli.YELLOW])

    if len(os) > 1:

        lines.append(['Device Type: ',os[1]])
        colors.append([pricli.normal_color,pricli.YELLOW])
        lines.append(['Running: ',os[2]])
        colors.append([pricli.normal_color,pricli.YELLOW])
        lines.append(['OS CPE: ',os[3]])
        colors.append([pricli.normal_color,pricli.YELLOW])
        lines.append(['OS Details: ',os[4]])
        colors.append([pricli.normal_color,pricli.YELLOW])
    else:
        lines.append(['OS: ','Unknown'])
        colors.append([pricli.normal_color,pricli.YELLOW])
    return lines,colors

def analyzer(nemo):
    pricli = nemo.pricli
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    stopped = False
    while True:
        if stopped:
            break
        # UpdateHosts(network_status,pricli,locking=False)
        # network_status.Update()

        # lock.acquire()
        pricli.Printlnr("Searching for hosts...")
        network_scanner.NetworkDiscovery(network_status.network)
        network_status.Update()

        # pricli.Clear()
        # pricli.Init()
        # pricli.Refresh()

        hosts = []
        for host in network_status.hosts:
            hosts.append(host.ip + '('+host.hostname+')')
        hosts.append("Exit")

        # pricli.lock.acquire()
        analyzing = True
        while analyzing:
            host_index = pricli.menu.Menu('Select host to analyze.',hosts)
            if host_index == len(hosts):
                # pricli.lock.release()
                # lock.release()
                return
            host_selected = True
            while host_selected:
                host_ip = network_status.hosts[host_index-1].ip
                hostname = network_status.hosts[host_index-1].hostname
                actions = ['Simple Port Scan','Service Port Scan','Service Version Port Scan','OS Detection','OS Detection/Service Scan','Exit']
                action = pricli.menu.Menu('Select an action on host: '+host_ip,actions)

                #### Port-Service Scanning with option for version scan ####
                if action == 2 or action == 3:
                    title = ['Port Scan for:',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    scan_type = 1
                    if action == 3:
                        scan_type = 2

                    lines,colors = PortScanResults(scan_type)
                       
                    info_window = InfoWindow(pricli,["PORT INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()
                
                #### OS detection ####
                elif action == 4:
                    title = ['OS Info for: ',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    lines,colors = OsDetectionResults(host_ip,network_scanner=network_scanner,pricli=pricli)
                    info_window = InfoWindow(pricli,["OS INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()

                elif action == 5:
                    title = ['Services and OS info for: ',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    os_lines, os_colors = OsDetectionResults(host_ip,network_scanner=network_scanner,pricli=pricli)
                    port_lines, port_colors = PortScanResults(host_ip,scan_type=2,network_scanner=network_scanner,pricli=pricli)

                    os_info_window = InfoWindow(pricli,['OS INFO'],os_lines,os_colors)
                    port_info_window = InfoWindow(pricli,['Port/Services Info'],port_lines,port_colors)
                    control_panel.InsertWindow(os_info_window)
                    control_panel.InsertWindow(port_info_window)
                    control_panel.Draw()

                elif action == 6: # Exit
                    host_selected = False
                    break
                
                input = pricli.Input()
                while input != ord('q'):
                    input = pricli.Input()


        # lock.release()
        # pricli.lock.release()



def readFromMonitor(client):
    while True:
        time.sleep(2)
        Print("Waiting for server")
        resp = client.recv(1024)

    # Print("ok") 
    # read_thread = Thread(target=lambda:readFromMonitor(client_socket))
    # read_thread.start()

def MainMenu(nemo):
    # global network_status
    pricli = nemo.pricli
    network_status = nemo.network_status
    global process_list
    global thread_list
    # is_in_another_menu = False ### becomes true if user selects one of the options and false if user is in current menu
    while True:
        # if is_in_another_menu:
        #     time.sleep(2)
        #     continue
        actions = ["Simple scan","Port Scan","Analyzer","Options","Exit"] 
        choice = pricli.menu.Menu("Select an action...",actions)
        network_status.stopped = False

        if choice == 1:
            pricli.ChangeWindow(reset=True)
            scan_thread = simple_scan(nemo)
            # is_in_another_menu = True
            
        elif choice == 2:
            # is_in_another_menu = True
            selection = pricli.menu.Menu('Select port scan type...',['Simple port scan','Service version scan','Exit'])
            if selection == 1:
                scan_type = 1
            elif selection == 2:
                scan_type = 2
            elif selection == 3:
                continue

            nemo.SetScanType(scan_type)
            ## User has pressed q
            pricli.ChangeWindow(reset=True)
            portscan_thread = port_scan(nemo)
        elif choice == 3:
            analyzer_thread = analyzer(nemo)
            # pricli.lock.acquire()
            # is_in_another_menu = True
            continue
            # time.sleep(1)
        elif choice == 4:
            settings_choice = 0
            while True:
                settings_choice = nemo.settings.Draw()
                if settings_choice == -1: #### Exit chosen
                    break
                settings = nemo.settings.DrawOption(settings_choice-1)
                for key,value in settings.items():
                    nemo.SetSetting(key,value)
                continue
            continue
            

        elif choice == len(actions):
            Exit(pricli)
            break
        ### skata

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
        network_status.stopped = True 
        proman.KillProcesses()
        proman.JoinThreads()
        network_status.stopped = False
        pricli.ChangeWindow(reset=True)

def getNetInfo(pricli):
    cmd = "ip addr | grep inet | awk '{print $2}' | grep -v 127.0.0.1 | grep -E -i '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,3}$'"
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
    parser.add_argument('--port-scan-period',action='store',type=int,help='Time in seconds after which the port scan will be repeated. Default is 30 seconds')
    parser.add_argument('--port-stress',choices=['normal','fast','full'],help='Number of ports to be scanned. Default is normal (1000) ports. Fast scans less than 1000 and full scans all 65535 ports (slow).')
    parser.add_argument('--ports',metavar='[1-65535]',type=int,nargs='+',help='Specific ports to scan. Ex: --ports 22 80 5001, --ports 1-65535')
    args = parser.parse_args()

    mode = 0
    if args.nofancy:
        return 1
    elif args.daemon:
        return 2
    elif args.informer:
        mode = 3
        if args.network is None:
            parser.error('--network option is required with the --informer switch')
        if args.port_scan_type is None:
            # parser.error('--port_scan_type option is required with the --informer switch')
            scan_type = 1
    else:
        mode = 0

    #### GENERAL options
    port_scan_period = 30
    port_stress = 1

    if args.port_scan_period is not None:
        port_scan_period = int(args.port_scan_period)
    scan_type = 0
    if args.port_scan_type == 'simple':
        scan_type = 1
    else:
        scan_type = 2
    if args.port_stress is not None:
        if args.ports is not None:
            parser.error('--ports option cannot be used alongside with --port-stress option.')
        if args.port_stress == 'fast':
            port_stress = 2
        elif args.port_stress == 'full':
            port_stress = 3

    return mode,args.network,scan_type,port_scan_period,port_stress,args.ports

def CreateSettings(nemo,pricli):
    settings = Settings(pricli,nemo)
    network_settings = Option(pricli=pricli,title='Network')
    network_settings.AddParameter('network',nemo.network)
    network_settings.AddParameter('netmask',nemo.netmask)
    settings.AddOption(network_settings)
    scan_settings = Option(pricli=pricli,title='Scan settings')
    scan_settings.AddParameter('scan_type',nemo.scan_type)
    scan_settings.AddParameter('port_scan_period',nemo.port_scan_period)
    scan_settings.AddParameter('port_stress',nemo.port_stress)
    settings.AddOption(scan_settings)
    settings.AddOption(Option(pricli=pricli,title='Port settings'))
    settings.AddOption(Option(pricli=pricli,title='Informer settings'))
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
        network = getNetInfo(pricli)
        # nemo.SetNetwork(network)
        nemo.SetSetting('network',network)
        nemo.SetSetting('netmask',network[-2:])
        # nemo.SetSetting('dns_server',network[0:-4]+)
        nemo.AddSettings(CreateSettings(nemo,pricli=pricli))
        if 'Exit' in network:
            Exit(pricli)
            return

    network_status = NetworkStatus(network,None)
    network_scanner = NetworkScanner(network_status)
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
    nemo = Nemo(mode)
    proman = ProMan()
    # network_status = None

    StartNemo(nemo)
    # sys.exit()

