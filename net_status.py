from concurrent.futures import thread
from dis import disco
from distutils.debug import DEBUG
from http import client
import os
from pickle import FALSE
import subprocess
from threading import Thread, Lock
import sched, time
import logging
import socket
import select
# from menu_launcher import *
import curses
import queue
import sys
from Pricli import Pricli, InfoWindow, ControlPanel
from ProMan import ProMan
from NetworkScanner import NetworkScanner

from yaml import parse

from Host import *

lock = Lock()

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

class Settings:
    def __init__(self):
        self.options = ['Network','Theme','Exit']
    
    def Show(self):
        title = ['SETTINGS']




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





    def Update(self):
        self.numHosts = len(self.hosts)

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




def simple_scan(pricli):
    if network_status.stopped:
        pricli.Clear()
        return

    x = proman.StartThread(SimpleScan,(pricli,))
    return x

def SimpleScan(pricli):
    global network_status
    if network_status.stopped:
        pricli.Clear()
        return
    while(1):
        network_scanner.NetworkDiscovery(network_status.network)
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

def port_scan(pricli,port_scan_type=1):
    if network_status.stopped:
        pricli.Clear()
        return

    x = proman.StartThread(PortScan,(port_scan_type,pricli,))
    return x

def PortScan(scan_type,pricli):
    stopped = False
    while True:
        if stopped:
            break
        # UpdateHosts(network_status,pricli,locking=False)
        # network_status.Update()
        network_scanner.NetworkDiscovery(network_status.network)
        network_status.Update()

        pricli.Clear()
        pricli.Init()
        pricli.Refresh()

        pricli.UpdatePage(["====================== PORT SCAN ======================"])
        pricli.RefreshPage()
        for host in network_status.hosts:
            if network_status.stopped:
                stopped = True
                break

            if network_scanner.IsHostUp(host.ip):
                host.ports = network_scanner.ServiceScan(host.ip,scan_type)
            else:
                continue

        
            ## The first section until AssessText, checks if the text to be printed will fit the screen rows. 
            ## If not, it will be (hopefully) printed on a new column, right to the already printed ones
            ## and on the top row.

            if len(host.ports) > 0:
                Port_Scan_Txt = ""
                Port_Scan_Txt += "Host: "+host.ip+" ( "+host.hostname+")\n"
                Port_Scan_Txt += "Ports:\n\t"
                for port in host.ports:
                    if scan_type == 2:
                        Port_Scan_Txt += str(port.num)+'\n\t'+port.service+"\n\t"+port.version+"\n\t"
                    else:
                        Port_Scan_Txt += str(port.num)+'\n\t'+port.service+'\n\t'
                if not pricli.AssessText(Port_Scan_Txt):
                    pricli.CreateNewPage()

                ## Assessment finished, will now try to print the actual formated (with colors etc. ) text
                pricli.UpdatePage(["Host: ",host.ip,"\t"," (",host.hostname,")"],[pricli.WHITE,pricli.BLUE,None,None,pricli.RED,None])
                pricli.UpdatePage(["Ports:"],[pricli.GREEN])
                # pricli.AddTab()
                for port in host.ports:
                    Port_Scan_Txt += str(port.num)
                    pricli.UpdatePage([str(port.num)],[pricli.YELLOW])
                    pricli.UpdatePage(["\t","Service:","\t",port.service],[None,pricli.CYAN,None,pricli.RED])
                    if scan_type == 2: ## print version if selected
                        pricli.UpdatePage(["\t","Version:","\t",port.version],[None,pricli.MAGENTA,None,pricli.RED])

                    # pricli.RemoveTab()
                # pricli.RemoveTab()
        pricli.RefreshPage()

        time.sleep(30)
        pricli.ClearPages()

# def analyzer(pricli):
#     if network_status.stopped:
#         pricli.Clear()
#         return

#     x = proman.StartThread(Analyzer,(pricli,))
#     return x

def PortScanResults(host_ip,scan_type):
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
            lines.append(['\t','Service: ',port.service])
            colors.append([pricli.normal_color,pricli.CYAN,pricli.RED])
        else:
            lines.append(['\t','Service: ',port.service, '  ', port.version])
            colors.append([pricli.normal_color,pricli.CYAN,pricli.RED,pricli.normal_color,pricli.MAGENTA])
    
    return lines,colors
        

def OsDetectionResults(host_ip):
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

def analyzer(pricli):
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
                    lines,colors = OsDetectionResults(host_ip)
                    info_window = InfoWindow(pricli,["OS INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()

                elif action == 5:
                    title = ['Services and OS info for: ',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    os_lines, os_colors = OsDetectionResults(host_ip)
                    port_lines, port_colors = PortScanResults(host_ip,scan_type=2)

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

def MainMenu(pricli):
    global network_status
    global process_list
    global thread_list
    # is_in_another_menu = False ### becomes true if user selects one of the options and false if user is in current menu
    while True:
        # if is_in_another_menu:
        #     time.sleep(2)
        #     continue
        actions = ["Simple scan","Port Scan","Analyzer","Exit"] 
        choice = pricli.menu.Menu("Select an action...",actions)
        network_status.stopped = False

        if choice == 1:
            pricli.ChangeWindow(reset=True)
            scan_thread = simple_scan(pricli)
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

            ## User has pressed q
            pricli.ChangeWindow(reset=True)
            portscan_thread = port_scan(pricli,scan_type)
        elif choice == 3:
            analyzer_thread = analyzer(pricli)
            # pricli.lock.acquire()
            # is_in_another_menu = True
            continue
            # time.sleep(1)
            

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


if __name__ == "__main__":
    pricli = Pricli()
    # theme = Theme(pricli)
    # theme.CreateWalls()
    proman = ProMan()

    network = getNetInfo(pricli)
    if 'Exit' in network:
        Exit(pricli)
    else:
        network_status = NetworkStatus(network,None)
        network_scanner = NetworkScanner(network_status)
        # Analyzer(pricli)
        MainMenu(pricli)
