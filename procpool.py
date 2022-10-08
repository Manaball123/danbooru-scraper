import multiprocessing
import threading


class ConcurrentThreadPool:
    def __init__(self, threads_n,task_fn,args):
        self.threads = []
        for i in range(threads_n):
            self.threads.append(threading.Thread(target = task_fn, args = args))
        
    def execute(self):
        for i in range(len(self.threads)):
            self.threads[i].start()
        
        
        for i in range(len(self.threads)):
            self.threads[i].join()

class ConcurrentProcessPool:
    def __init__(self, process_n,task_fn,args):
        self.processes = []
        for i in range(process_n):
            self.processes.append(multiprocessing.Process(target = task_fn, args = args))
        
    def execute(self):
        for i in range(len(self.processes)):
            self.processes[i].start()
        
        
        for i in range(len(self.processes)):
            self.processes[i].join()


