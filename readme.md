# Introduction
NeMo (Network Monitor) is a tool that monitors a network and informs the administrator when a host connects or disconnects and when a port opens or closes. Port changes can also be sent as an email notification. It can also analyze a specific host and give information about its open ports, services and OS details. It uses Nmap to obtain all the information about the network and each host. The results are printed in the terminal using Pricli (Print Cli), which is a Python Curses library wrapper.

## Requirements
* Linux (the available networks are found using the `ip` command)
* Python 3.x. Only the standard library is used, so there is nothing to install with pip.
* [Nmap](https://nmap.org/), available in your `PATH`
* Root privileges for some features. OS detection and UDP scanning are Nmap functions that require root permissions, and MAC addresses and vendors are only reported when running as root.

## Usage
Run NeMo using Python 3.x: `python Nemo.py` (or `sudo python Nemo.py` for the features that need root). Upon starting NeMo, you have to choose which network to monitor. A list of available networks, as seen from your current interfaces, is presented for you to choose from.

Menus are traversed with the UP/DOWN arrows and an option is selected with ENTER. While a scan is running:

| Key | Action |
|---|---|
| `q` | Stop the scan and go back to the menu |
| `l` | Next page of results |
| `k` | Previous page of results |

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

When choosing this option, the user has to choose one of the hosts in the network and then there are two actions that can be applied on that host: 1) Monitor the host's online status, 2) Monitor the host's ports (which is the same as Network Port Scan but for a single host only)

![nemo_specific](https://github.com/soilah/nemo/assets/37487882/cc85e3da-9282-4fcf-aade-625af0b944f8)

Example output for Host's online status:
![Host Up](https://github.com/soilah/nemo/assets/37487882/01734301-95fc-423a-b20b-2afff615cff5)

Example output for Host's port monitoring:
![host ports ](https://github.com/soilah/nemo/assets/37487882/22bbee3e-98d6-4337-84d0-3b7d0de24009)

The banner says ANALYZER because both are functions of the Analyzer feature which will be discussed below.

## Analyzer
The second mode of NeMo is the Analyzer mode. It scans the network once, lets you choose one of the hosts that were found and then runs one of the following actions on it:

| Action | Description | Needs root |
|---|---|---|
| Service Port Scan | Open TCP ports and the service behind each one | No |
| Service Version Port Scan | Same as above, with the version of each service (`nmap -sV`) | No |
| OS Detection | MAC address, device type and OS details (`nmap -O`) | Yes |
| OS Detection/Service Scan | Both OS detection and service port scan | Yes |
| UDP Scan | Open UDP ports (`nmap -sU`) | Yes |

Keys available when the results are shown:

| Key | Action |
|---|---|
| `n` | Switch between the result windows |
| `w` / `s` | Scroll the current window up / down |
| `x` | Select a port of the ports window (work in progress) |
| `r` | Run the same scan again |
| `q` | Go back to the menu |

## Options
The Options entry of the main menu changes the settings of the current session. Select a setting with ENTER, type the new value and press ENTER again. Press `q` to go back.

| Setting | Values | Default |
|---|---|---|
| `network` / `netmask` | The network to scan | The network chosen at startup |
| `scan_type` | `1` simple port discovery, `2` version scan | `1` |
| `scan_period` | Seconds between two scans | `30` |
| `port_stress` | `1` normal (1000 ports), `2` fast, `3` full (all 65535 ports, slow) | `1` |
| `ports_to_scan` | Specific ports, e.g. `22,80,8000-8100`. Overrides `port_stress` | None |
| `send_mail` | `True` / `False` | `True` |

## Command line options
The scan settings can also be given as arguments:

```
python Nemo.py [--informer --network NETWORK] [--port-scan-type {simple,version}]
               [--scan-period SECONDS] [--port-stress {normal,fast,full}]
               [--ports PORTS [PORTS ...]]
```

| Option | Description |
|---|---|
| `--informer` | Run the Network Port Scan without the curses interface and print the results as plain text. Requires `--network` |
| `--network` | The network (or host) to scan, e.g. `192.168.1.0/24` |
| `--port-scan-type` | `simple` for simple port discovery, `version` for version scan. Default is `simple` |
| `--scan-period` | Time in seconds after which the scan is repeated. Default is 30 |
| `--port-stress` | `normal` (1000 ports), `fast` or `full` (all 65535 ports). Default is `normal` |
| `--ports` | Specific ports or port ranges to scan. Cannot be used together with `--port-stress` |

Examples:

```
# Monitor the ports of a network every 5 minutes, without curses
sudo python Nemo.py --informer --network 192.168.1.0/24 --scan-period 300

# Only check some ports, with service versions
python Nemo.py --informer --network 192.168.1.0/24 --ports 22 80,443 8000-8100 --port-scan-type version
```

The `--nofancy` and `--daemon` switches are not implemented yet.

## Email notifications
When a port opens or closes on a host, NeMo calls `SendMail(subject, message)` from a `SendMail.py` file placed next to `Nemo.py`. That file is not part of the repository (it is ignored by git, because it holds your mail credentials), so you have to create it. A minimal example:

```python
import smtplib
from email.message import EmailMessage

def SendMail(subject, message):
    mail = EmailMessage()
    mail['Subject'] = subject
    mail['From'] = 'nemo@example.com'
    mail['To'] = 'admin@example.com'
    mail.set_content(message)
    with smtplib.SMTP_SSL('smtp.example.com', 465) as server:
        server.login('nemo@example.com', 'password')
        server.send_message(mail)
```

If `SendMail.py` does not exist, NeMo works normally but no mails are sent. Mails can also be turned off with the `send_mail` setting. Hosts that connect or disconnect are shown on the screen but are not sent by mail for now.

## Saved data
The ports found on each host are saved in `Networks/tcp/` and `Networks/udp/` (one JSON file per host), inside the directory NeMo is started from. This is what each new scan is compared with, in order to find which ports opened or closed. Run NeMo from the same directory each time to keep that history, or delete the `Networks` folder to start from scratch.

## Disclaimer
Only scan networks that you own or that you are allowed to scan.
