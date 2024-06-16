# Introduction
NeMo (Network Monitor) is a tool that can monitor a specific network in a way that informs the administrator when a host is connected or disconnected, when a port opens or closes and send that information via email notification or analyze a specific host and give information about its open ports, services and OS details. It is uses Nmap to obtain all the information about the network and each host. The results are printed in the terminal using Pricli (Print Cli) which is a Python Curses library wrapper.

## Usage
Run nemo using Python 3.x. `python Nemo.py`. Some functions of NeMo require root privileges because some functions of Nmap such as OS detection, Udp scanning etc require root permissions. Upon starting NeMo, you have to choose which network to monitor. A list of available networks as seen from your current interfaces is presented for you to choose from.

![Nemo1](https://github.com/soilah/nemo/assets/37487882/2fa1ecf9-4d36-44b8-948d-0e5e450c83d7)


## Informer
The first mode of NeMo is the Informer mode. After choosing a target network, select the informer option. 
![nemo_2](https://github.com/soilah/nemo/assets/37487882/2e9238f2-99e8-45d6-a9ed-3fdab2122be8)

Then there are 3 distinct options: Simple Network Scan, Network Port Scan, Specific Host Monitor.
![nemo_3](https://github.com/soilah/nemo/assets/37487882/42355878-e0a0-45c6-8ccd-326981c9c25e)

### Simple Network Scan
![informer_results](https://github.com/soilah/nemo/assets/37487882/de280ac3-bfe6-4f5e-88be-8bd069fd283a)

Informer also shows when hosts are connected or disconnected.
![informer_disc_con](https://github.com/soilah/nemo/assets/37487882/28e32cc0-e11d-40a1-a24e-c9b56221ad8f)
![informer_disc](https://github.com/soilah/nemo/assets/37487882/8d0d0e5d-8be9-446b-94eb-eb7ebda9e44b)

### Network Port Scan
![nemo_ports](https://github.com/soilah/nemo/assets/37487882/970e371c-5d58-4bfe-bac6-0ed4e21ee7e8)

The first time the network port scan mode is run, just shows the results. Then, the next time, if it finds differences between the states of the hosts (i.e. some ports open or a port closed), it prints the results and can also notify the administrator by sending an email stating the host and which ports are different.

### Specific Host Monitor

When choosing this option, the user has to choose one of the hosts in the network and then there are two actions that can be applied on that host: 1) Monitor the hosts's online status, 2) Monitor the hosts's ports (which is the same as Network Port Scan but for a single host only)

![nemo_specific](https://github.com/soilah/nemo/assets/37487882/cc85e3da-9282-4fcf-aade-625af0b944f8)

Example output for Host's online status:
![Host Up](https://github.com/soilah/nemo/assets/37487882/01734301-95fc-423a-b20b-2afff615cff5)

Example output for Host's port monitoring:
![host ports ](https://github.com/soilah/nemo/assets/37487882/22bbee3e-98d6-4337-84d0-3b7d0de24009)

The banner says ANALYZER because both are functions of the Analyzer feature which will be discussed below.
