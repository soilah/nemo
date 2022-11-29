import subprocess
from threading import Thread, Lock
import queue


class ProMan:
    def __init__(self):
        self.process_list = []
        self.thread_list = queue.Queue()
        self.running_process = None
    
    def StartThread(self,func,args):
        thread = Thread(target=func, args=args)    #start host scanning thread
        thread.start()
        self.thread_list.put(thread) 
        return thread
    
    def JoinThreads(self):
        while not self.thread_list.empty():
            thread = self.thread_list.get()
            thread.join()

    def RunProcess(self,command,shell=False):
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,shell=shell)
        self.running_process = proc 
        self.process_list.append(proc)
        res = proc.communicate()[0].decode("utf-8") #command output
        return res

    def RunProcessWait(self,command,shell=False):
        # proc1 = subprocess.Popen(['echo','spacerouren!$'], stdout=subprocess.PIPE)
        # command.insert(0,'-S')
        # command.insert(0,'sudo')
        # proc = subprocess.Popen(command,stdin=proc1.stdout,stdout=subprocess.PIPE,shell=shell)
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,shell=shell)
        self.process_list.append(proc)
        proc.wait() 
        res = proc.communicate()[0].decode("utf-8") #command output
        self.process_list.remove(proc)
        return res

    ## Kills the last process created and removes it from the process list
    def KillProcess(self): 
        process = self.process_list.pop()
        if process.returncode is None:
            kill_cmd = ['kill','-9',str(process.pid)]
            subprocess.Popen(kill_cmd)
    
    def KillProcesses(self):
        while self.HasProcesses() > 0:
            self.KillProcess()

    
    def HasProcesses(self):
        if len(self.process_list) > 0:
            return True
        return False
    
    def GetOutputWhileRunning(self):
        proc = self.process_list[-1]
        for stdout_line in iter(proc.stdout.readline, ""):
            yield stdout_line
        
