# from net_status import simple_scan, port_scan, PortScanResults, host_monitor_ports, host_monitor_status
import Nemo
from Pricli import ControlPanel, InfoWindow
import time

def Informer(nemo):
    proman = nemo.proman
    while True:
        pricli = nemo.pricli
        actions = ['Simple Network Scan','Network Port Scan','Specific Host Monitor','Exit']
        # nemo.main_lock.acquire()
        choice = pricli.menu.Menu("Select an action...",actions)

        if choice == 1:
            Nemo.simple_scan(nemo)
        elif choice == 2:
            Nemo.port_scan(nemo)
        elif choice == 3:
            # lock.acquire()
            # print('getting 1 lock'+str(main_lock))
            # main_lock.acquire()
            HostMonitorMenu(nemo)
            continue
        else:
            return

        key = ''
        while key != ord('q'):
            key = pricli.Input()
            if key == ord("l"):
                if len(pricli.pages) > 1:
                    pricli.GoToNextPage()
            elif key == ord("k"):
                pricli.GoToPreviousPage()
        nemo.network_status.stopped.set()
        # pricli.ChangeWindow(reset=True)
        proman.KillProcesses()
        proman.JoinThreads()
        nemo.network_status.stopped.clear()
        pricli.ClearPages()



def HostMonitorMenu(nemo):
    proman = nemo.proman
    network_status = nemo.network_status
    pricli = nemo.pricli
    # network_scanner = nemo.network_scanner
    nemo.pricli.Printlnr('Searching for hosts...')
    nemo.network_scanner.NetworkDiscovery(nemo.network)    

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
        # thread_lock.acquire()
        host_index = pricli.menu.Menu('Select host to monitor.',hosts)
        if host_index == len(hosts):
            # pricli.lock.release()
            # lock.release()
            # main_lock.release()
            return
        host_selected = True
        while host_selected:
            host_ip = network_status.hosts[host_index-1].ip
            hostname = network_status.hosts[host_index-1].hostname
            # nemo.main_lock.acquire()
            actions = ['Status Monitor (Up/Down)','Port Monitor','Back']
            action = pricli.menu.Menu('Select an action on host: '+host_ip,actions)

            # main_lock.release()
            # nemo.main_lock.acquire()
            if action == 1:
                Nemo.host_monitor_status(nemo,host_ip,hostname)
            if action == 2:
                Nemo.host_monitor_ports(nemo,host_ip,hostname)
            elif action == len(actions): # Back
                host_selected = False
                break

            ## wait for thread to finish. And then go back to menu
            # nemo.main_lock.acquire()
            time.sleep(1)
            input = ''

            while input != ord('q'):
                input = pricli.Input()

            pricli.ClearPages()
            nemo.network_status.stopped.set()
            # pricli.ChangeWindow(reset=True)
            proman.KillProcesses()
            proman.JoinThreads()
            nemo.network_status.stopped.clear()
            # nemo.main_lock.release()



def HostMonitorPorts(nemo,host_ip,hostname):
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    pricli = nemo.pricli

    title = ['Monitoring ports of :',host_ip,' (',hostname,')']
    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]

    while not network_status.stopped.is_set():
        control_panel = ControlPanel(pricli,None,title,title_colors)
        control_panel.Draw()
        IsAlive = network_scanner.IsHostUp(host_ip)
        lines = []
        colors = []
        if not IsAlive:
            text = ['Host is currently ']
            text.append('DOWN')
            colors.append([pricli.RED])
            lines.append(text)
            colors.append([pricli.normal_color,pricli.RED])
        else:
            lines,colors = Nemo.PortScanResults(host_ip,nemo)
        
        info_window = InfoWindow(pricli,["Host Status"],lines,colors)
        control_panel.InsertWindow(info_window)

        counter = int(nemo.scan_period)
        while(counter > 0):
            info_text = str(counter) +'  seconds until next scan.'
            control_panel.AddInfoText(info_text)
            control_panel.Draw()
            counter -= 1
            if nemo.network_status.stopped.is_set():
                # nemo.main_lock.release()
                pricli.ClearPages()
                return
            time.sleep(1)
        
    # nemo.main_lock.release()
    pricli.ClearPages()



def HostMonitorStatus(nemo,host_ip,hostname):
    network_status = nemo.network_status
    network_scanner = nemo.network_scanner
    pricli = nemo.pricli

    title = ['Monitoring status of :',host_ip,' (',hostname,')']
    title_colors = [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]


    # counter = int(nemo.scan_period)
    control_panel = ControlPanel(pricli,None,title,title_colors)
    control_panel.Draw()

    prev_alive = network_scanner.IsHostUp(host_ip)
    first = True
    while not network_status.stopped.is_set():
        time.sleep(1)
        IsAlive = network_scanner.IsHostUp(host_ip)
        if IsAlive == prev_alive and not first:
            continue 
        colors =[[pricli.normal_color]]
        lines = []
        text = ['Host is currently ']
        if IsAlive:
            text.append('UP')
            colors.append([pricli.normal_color,pricli.GREEN])
        else:
            text.append('DOWN')
            colors.append([pricli.normal_color,pricli.RED])

        lines.append(text)
        
        info_window = InfoWindow(pricli,["Host Status"],lines,colors)
        # control_panel.InsertWindow(info_window)
        control_panel.UpdateWindow(info_window)

        # info_text = str(counter) +'  seconds until next scan.'
        # control_panel.AddInfoText(info_text)
        control_panel.Draw()
        # counter -= 1
        prev_alive = IsAlive
        if nemo.network_status.stopped.is_set():
            # nemo.main_lock.release()
            return
        first = False

    # nemo.main_lock.release()

 