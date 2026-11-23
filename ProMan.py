import subprocess
from threading import Thread, Lock
import queue


class ProMan:
    def __init__(self):
        self.process_list = []
        self.process_lock = Lock()
        self.thread_list = queue.Queue()
        self.running_process = None
    
    def StartThread(self,func,args):
        thread = Thread(target=func, args=args)    #start host scanning thread
        thread.start()
        self.thread_list.put(thread) 
        return thread
    
    #### Waits for all threads to finish. The threads are expected to have been
    #### told to stop, so any process that they start in the meantime is killed.
    def JoinThreads(self):
        while not self.thread_list.empty():
            thread = self.thread_list.get()
            while thread.is_alive():
                self.KillProcesses()
                thread.join(0.1)

    def RunProcess(self,command,shell=False):
        return self.RunProcessWait(command,shell=shell)

    #### Runs a command and returns its output when it finishes.
    #### If the process gets killed (see KillProcesses), the output is whatever
    #### was written until then (possibly truncated or empty).
    def RunProcessWait(self,command,shell=False):
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,shell=shell)
        self.running_process = proc
        with self.process_lock:
            self.process_list.append(proc)
        try:
            #### communicate() reads the output while waiting, so a big output
            #### can not fill the pipe and block the child process
            res = proc.communicate()[0].decode("utf-8",errors="replace") #command output
        finally:
            with self.process_lock:
                if proc in self.process_list:
                    self.process_list.remove(proc)
        return res

    ## Kills the last process created and removes it from the process list
    def KillProcess(self): 
        with self.process_lock:
            if len(self.process_list) == 0:
                return
            process = self.process_list.pop()
        if process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
    
    def KillProcesses(self):
        while self.HasProcesses():
            self.KillProcess()

    
    def HasProcesses(self):
        with self.process_lock:
            return len(self.process_list) > 0
    
    def GetOutputWhileRunning(self):
        proc = self.process_list[-1]
        for stdout_line in iter(proc.stdout.readline, b""):
            yield stdout_line
