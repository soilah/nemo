# Introduction
NeMo (Network Monitor) is a tool that can monitor a specific network in a way that informs the administrator when a host is connected or disconnected, when a port opens or closes and send that information via email notification or analyze a specific host and give information about its open ports, services and OS details. It is uses Nmap to obtain all the information about the network and each host. The results are printed in the terminal using Pricli (Print Cli) which is a Python Curses library wrapper.

## Usage
Run nemo using Python 3.x. `python Nemo.py`. Some functions of NeMo require root privileges because some functions of Nmap such as OS detection, Udp scanning etc require root permissions. Upon starting NeMo, you have to choose which network to monitor. A list of available networks as seen from your current interfaces is presented for you to choose from.

![Nemo1](https://github.com/soilah/nemo/assets/37487882/af1693c1-13fe-4f42-8079-619102e45fcc)

## Informer
The first mode of NeMo is the Informer mode. After choosing a target network, select the informer option. 
![nemo_2](https://github.com/soilah/nemo/assets/37487882/33eb6df2-5a89-493f-8669-06f21dd11dd4)

Then there are 3 distinct options: Simple Network Scan, Network Port Scan, Specific Host Monitor.
![nemo_3](https://github.com/soilah/nemo/assets/37487882/4e39341f-aac1-4daf-b1b3-33bd4293ed13)

### Simple Network Scan
![informer_results](https://github.com/soilah/nemo/assets/37487882/6c81b99e-2cfd-4a17-95d9-e520cbb6e68a)

Informer also shows when hosts are connected or disconnected.
![informer_disc_con](https://github.com/soilah/nemo/assets/37487882/9416457a-2229-4820-91ef-f9be9c8d9be9)
![informer_disc](https://github.com/soilah/nemo/assets/37487882/a22b6917-79e0-4dfb-9625-da6092f6e453)

### Network Port Scan
![nemo_ports](https://github.com/soilah/nemo/assets/37487882/0eba4496-708b-4041-86e6-d4b6f0a900b3)

The first time the network port scan mode is run, just shows the results. Then, the next time, if it finds differences between the states of the hosts (i.e. some ports open or a port closed), it prints the results and can also notify the administrator by sending an email stating the host and which ports are different.

### Specific Host Monitor

When choosing this option, the user has to choose one of the hosts in the network and then there are two actions that can be applied on that host: 1) Monitor the hosts's online status, 2) Monitor the hosts's ports (which is the same as Network Port Scan but for a single host only)
![nemo_specific](https://github.com/soilah/nemo/assets/37487882/399e43c9-fbcd-45a2-aa56-2abbdcee80fd)

Example output for Host's online status:
![Host Up](https://github.com/soilah/nemo/assets/37487882/01734301-95fc-423a-b20b-2afff615cff5)

Example output for Host's port monitoring:
![host ports ](https://github.com/soilah/nemo/assets/37487882/22bbee3e-98d6-4337-84d0-3b7d0de24009)

The banner says ANALYZER because both are functions of the Analyzer feature which will be discussed below.
