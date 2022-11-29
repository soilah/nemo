class Port(object):
    def __init__(self,port_num,info,service=None,version=None):
        self.num = port_num
        self.info = info
        self.service = service
        self.version = version

class Host(object):
    def __init__(self,args,ports=None):
        self.ip = args[0]
        self.hostname = args[1]
        self.ports = ports
        #Print("Created Host with ip: ",self.ip," and hostname: ",self.hostname)

