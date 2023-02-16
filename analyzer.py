# from Nemo import OsDetectionResults, PortScanResults
import Nemo
from Pricli import ControlPanel, InfoWindow

def Analyzer(nemo):
    pricli = nemo.pricli
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    stopped = False
    control_panel = None
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
            if host.hostname != '':
                hosts.append(host.ip + '('+host.hostname+')')
            else:
                hosts.append(host.ip)
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
                actions = ['Service Port Scan','Service Version Port Scan','OS Detection','OS Detection/Service Scan','UDP Scan','Exit']
                action = pricli.menu.Menu('Select an action on host: '+host_ip,actions)

                #### Port-Service Scanning with option for version scan ####
                if action == 1 or action == 2:
                    title = ['Service info for: ',host_ip]
                    title_colors = [pricli.normal_color,pricli.BLUE]

                    if hostname != '':
                        title += [' (',hostname,')']
                        title_colors += [pricli.normal_color,pricli.RED,pricli.normal_color]

                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    nemo.SetScanType(int(action))

                    lines,colors = Nemo.PortScanResults(host_ip,nemo)
                       
                    info_window = InfoWindow(pricli,["PORT INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()
                
                #### OS detection ####
                elif action == 3:
                    title = ['OS info for: ',host_ip]
                    title_colors = [pricli.normal_color,pricli.BLUE]

                    if hostname != '':
                        title += [' (',hostname,')']
                        title_colors += [pricli.normal_color,pricli.RED,pricli.normal_color]

                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    lines,colors = Nemo.OsDetectionResults(host_ip,nemo)
                    info_window = InfoWindow(pricli,["OS INFO"],lines,colors)
                    control_panel.InsertWindow(info_window)
                    control_panel.Draw()

                #### BOTH OS detection and Port Scan ####
                elif action == 4:
                    nemo.SetScanType(2)
                    title = ['OS and Service info for: ',host_ip]
                    title_colors = [pricli.normal_color,pricli.BLUE]

                    if hostname != '':
                        title += [' (',hostname,')']
                        title_colors += [pricli.normal_color,pricli.RED,pricli.normal_color]

                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()
                    os_lines, os_colors = Nemo.OsDetectionResults(host_ip,nemo)
                    port_lines, port_colors = Nemo.PortScanResults(host_ip,nemo)

                    os_info_window = InfoWindow(pricli,['OS INFO'],os_lines,os_colors)
                    port_info_window = InfoWindow(pricli,['Port/Services Info'],port_lines,port_colors)
                    control_panel.InsertWindow(os_info_window)
                    control_panel.InsertWindow(port_info_window)
                    control_panel.Draw()
                
                #### UDP Scan ####
                elif action == 5:
                    title = ['UDP info for: ',host_ip]
                    title_colors = [pricli.normal_color,pricli.BLUE]

                    if hostname != '':
                        title += [' (',hostname,')']
                        title_colors += [pricli.normal_color,pricli.RED,pricli.normal_color]

                    control_panel = ControlPanel(pricli,None,title,title_colors)
                    control_panel.Draw()

                    port_lines, port_colors = Nemo.PortScanResults(host_ip,nemo,proto=2)

                    port_info_window = InfoWindow(pricli,['Port/Services Info'],port_lines,port_colors)
                    control_panel.InsertWindow(port_info_window)
                    control_panel.Draw()



                elif action == len(actions): # Exit
                    host_selected = False
                    break
                
                while(1):
                    input = pricli.Input()
                    if input == ord('n'):
                        control_panel.ToggleWindow()

                    if input == ord('q'):
                        break

                pricli.ClearPages()


        # lock.release()
        # pricli.lock.release()

