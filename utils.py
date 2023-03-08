import hashlib
import multiprocessing
import threading


#input: file url
#returns extention of file
def find_ext(url : str):

    strlen = len(url)
    #print(str)
    i = strlen - 1
    while i > 0:
        if(url[i] == "."):

            return url[i:]
        else:
            i -= 1
    return None

#md5 hash check, returns true if both are the same, false otherwise
def check_hash(fname, hash):
    fhash = ""
    with open(fname, "rb") as f:
        data = f.read()
        fhash = hashlib.md5(data).hexdigest()
        
    if(hash == fhash):
        return True
    else: 
        return False
    
def get_cdn_url(data):
    if(data.__contains__("large_file_url")):
        return data["large_file_url"]
    elif(data.__contains__("file_url")):
        return data["file_url"]


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