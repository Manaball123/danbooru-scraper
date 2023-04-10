
import hashlib

from functools import partial
import requests
import utils
import shutil
import os
        
import multiprocessing
import datetime
import threading
import time
import json
import config as cfg
import scraperlib





#ARGS HERE







#cache format:
#cache/session_time/tags.json
#cache/session_time/page_index(200 posts/page assumed).json


#queuery info















class Task:
    def __init__(self, url : str, id : int, ext : str) -> None:
        self.url = url
        self.id = id
        self.md5 = None
        self.extention : str = ext
        
        
    #only do this after task arrives at destination cuz large size prob
    #nvm i dont actually care
    def initialize_props(self) -> None:
        global dir

        #file name
        #42069666.png
        self.fname : str = str(self.id) + self.extention

        #relative path
        #./root/.png/66/42069666.png
        self.path : str = cfg.ROOT_DIR +                    \
            self.extention + "/"                        \
            + str(self.id % cfg.FOLDER_SPLIT_COUNT) + "/"   \
            + self.fname
    
    def is_valid(self) -> bool:

        
        #if file does not exist, download
        if(not os.path.exists(self.path)):
            return True
        #if not doing checksum
        #assume that the file is complete
        if(not cfg.CHECK_MD5):
            return False
        #if checking md5
        #if checksum is incomplete, redownload
        if(not utils.check_hash(self.path, self.md5)):
            print(self.fname + " exists but has an incorrect file hash, redownloading...")
            return True
        #if checksum is complete
        print(self.fname + " exists, aborting download")
        return False

        


#state object, get task queue and completion status here
class SharedState:
    def __init__(self, session_id : str):
        self.queue = multiprocessing.Queue(cfg.MAX_TASKS)
        self.completion = multiprocessing.Value("i", cfg.STATE_INCOMPLETE)
        self.session_id = session_id
        self.cache_path = cfg.CACHE_DIR + session_id + "/"
        

    def is_complete(self) -> bool:
        if(self.completion.value == cfg.STATE_COMPLETE and self.queue.empty()):
            return True
        return False
    
#returns json-loaded dict from api, or none
def get_data(page : int, shared_info : SharedState) -> dict:


    print("Requesting for tasks on page: " + str(page))
    url_paged = cfg.TAGGED_BASE_URL + "&page=" + str(page)
    success : bool = False
    while(not success):


        data = scraperlib.req_data(url_paged)
        if(data == None):
            continue
        
        if(cfg.SAVE_API_CACHE):
            with open(shared_info.cache_path + str(page) + ".json", "w+") as f:
                f.write(json.dumps(data))
        print("REQUESTS PROCESS: New tasks requested.")
        return data
        
            

    

#response data parsing
def data_to_tasks(data : dict) -> list:

    res = []
    
    #TODO: implement load from cache

    for dat in data:
        #if no id
        if(not dat.__contains__("id")):
            continue
        #if no extension
        if(not dat.__contains__("file_ext")):
            continue
        #if no cdn url
        url = utils.get_cdn_url(dat)
        id = dat["id"]
        ext = "." + dat["file_ext"]
        if(cfg.KNOWN_ONLY):
            #if either false or none type
            if(not cfg.KNOWN_EXTENSIONS.__contains__(ext)):
                continue

        if(url == None):
            continue

        task : Task = Task(url, id, ext)
        #optional md5 checksum
        if(cfg.CHECK_MD5 and dat.__contains__("md5")):
            task.md5 = dat["md5"]
        #if no md5 in strict mode
        if(cfg.STRICT_MD5 and (not dat.__contains__("md5"))):
            continue
        res.append(task)
        
    return res

    



def save_image(task : Task):

    

    try:
        res = requests.get(url = task.url ,headers=cfg.REQ_HEADES, stream=True)
        print("Downloading " + task.fname)

        if res.status_code == 200:
            #note: may have unexpected behavior if terminated before eof reached
            with open(task.path,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            
            
            if(cfg.STRICT_MD5):
                if(not utils.check_hash(task.path, task.md5)):
                    print("File hash of " + task.fname +" is incorrect. Redownloading...")
                    
                    return False
            
            print('File sucessfully Downloaded: ', task.fname)
            
            return True
        else:
            print('File Couldn\'t be retrieved, Error:')
            print(res)
            
            return False

    except:
        
        print("Downloading of " + task.fname + " aborted as an exception is thrown.")
        
        return False
    


#==============================================MKDIRS======================================
#makes subfolders of extension
def mkdir():
    for k in cfg.KNOWN_EXTENSIONS:
        if(not os.path.isdir(cfg.ROOT_DIR + k)):
            os.mkdir(cfg.ROOT_DIR + k)
        for i in range(cfg.FOLDER_SPLIT_COUNT):
            cdir = cfg.ROOT_DIR + k + "/" + str(i)
            if(not os.path.isdir(cdir)):
                os.mkdir(cdir)

#makes the anime porn folder
def mkrootdir():
    if(not os.path.isdir(cfg.ROOT_DIR)):
        os.mkdir(cfg.ROOT_DIR)

def mkcachedir(session_dir : str):
    
    if(not os.path.isdir(cfg.CACHE_DIR)):
        os.mkdir(cfg.CACHE_DIR)

    if(not os.path.isdir(session_dir)):
        os.mkdir(session_dir)

    

    #create tags.json
    with open(session_dir + "/tags.json", "w") as f:
        f.write(json.dumps(cfg.TAGS))

#==============================================END MKDIRS======================================

#=========================================THREAD AND PROCESS PROCS======================================

def downloads_thread(shared_obj : SharedState):
    
    #only stop if both completion set to 1 AND queue is empty
    while(not shared_obj.is_complete()):

        try:
            ctask = shared_obj.queue.get(True, cfg.QUEUE_TIMEOUT)
        #check if task is valid
        except:
            #print("DOWNLOADS_THREAD: Queue is currently empty, retrying after 5s...")
            time.sleep(5)
            continue
        
        ctask.initialize_props()
        #if task is invalid, dont start download
        if(not ctask.is_valid()):
            continue
        #print("Exectuting task: " + str(ctask["tid"]))
        #retry if failed
        while(not save_image(ctask)):
            print("Error is thrown while downloading. Retrying...")
        
        
    
    
    print("Download complete. Closing thread..")

        


#subprocesses here


def requests_subprocess(shared_obj : SharedState):
    for i in cfg.PAGE_RANGE:
        resp_data = None
        if(cfg.LOAD_TASKS_FROM_CACHE):
            with open(shared_obj.cache_path + str(i) + ".json", "r") as f:
                resp_data = json.loads(f.read())
        else:
            resp_data = get_data(i, shared_obj)

        tasks_to_push = data_to_tasks(resp_data)
        assert(tasks_to_push != None)

        for task in tasks_to_push:
            shared_obj.queue.put(task)
    
    #mark completion when finished executing
    shared_obj.completion.value = 1
    


def downloads_subprocess(shared_obj : SharedState):
    #pool = ThreadPool(processes = threads) 
    
    pool_fn = partial(downloads_thread, shared_obj)
    pool = utils.ConcurrentThreadPool(cfg.THREADS_PER_PROCESS, pool_fn, ())

    pool.execute()
        

#========================================MAIN======================================

if __name__ ==  "__main__":

    session_id : str = str(time.time_ns())
    if(cfg.LOAD_TASKS_FROM_CACHE):
        session_id = cfg.SESSION_ID
        
    shared_obj = SharedState(session_id)
    mkrootdir()

    mkcachedir(shared_obj.cache_path)
    mkdir()
    

    

    req_p = multiprocessing.Process(target = requests_subprocess, args = (shared_obj,))
    
    downloads_pool = utils.ConcurrentProcessPool(cfg.PROCESSES_N, downloads_subprocess, args = (shared_obj,))
    

    #it = range(0,processes)
    
    
    req_p.start()
    downloads_pool.execute()

    req_p.join()
    

