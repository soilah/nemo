# from Nemo import OsDetectionResults, PortScanResults
import Nemo
from Pricli import ControlPanel, InfoWindow

def Analyzer(nemo):
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
                actions = ['Service Port Scan','Service Version Port Scan','OS Detection','OS Detection/Service Scan','Exit']
                action = pricli.menu.Menu('Select an action on host: '+host_ip,actions)

                #### Port-Service Scanning with option for version scan ####
                if action == 1 or action == 2:
                    title = ['Port Scan for:',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    nemo.SetScanType(1)
                    if action == 3:
                        nemo.SetScanType(2)

                    lines,colors = Nemo.PortScanResults(host_ip,nemo)
                       
                    info_window = InfoWindow(pricli,["PORT INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()
                
                #### OS detection ####
                elif action == 3:
                    title = ['OS Info for: ',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    lines,colors = Nemo.OsDetectionResults(host_ip,nemo)
                    info_window = InfoWindow(pricli,["OS INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()

                #### BOTH OS detection and Port Scan ####
                elif action == 4:
                    nemo.SetScanType(2)
                    title = ['Services and OS info for: ',host_ip,' (',hostname,')']
                    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]
                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    os_lines, os_colors = Nemo.OsDetectionResults(host_ip,nemo)
                    port_lines, port_colors = Nemo.PortScanResults(host_ip,nemo)

                    os_info_window = InfoWindow(pricli,['OS INFO'],os_lines,os_colors)
                    port_info_window = InfoWindow(pricli,['Port/Services Info'],port_lines,port_colors)
                    control_panel.InsertWindow(os_info_window)
                    control_panel.InsertWindow(port_info_window)
                    control_panel.Draw()

                elif action == len(actions): # Exit
                    host_selected = False
                    break
                
                input = pricli.Input()
                while input != ord('q'):
                    input = pricli.Input()
                pricli.ClearPages()


        # lock.release()
        # pricli.lock.release()

