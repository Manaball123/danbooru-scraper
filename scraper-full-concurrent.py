
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




#consts
tag_score_order = "order%3Ascore"

#ARGS HERE



PAGE_START = 1
PAGE_STOP = 50
PAGE_RANGE = range(PAGE_START, PAGE_STOP)

THREADS_PER_PROCESS = 1
PROCESSES_N = 1


CHECK_MD5 = True
STRICT_MD5 = True
KNOWN_ONLY : bool = True
SAVE_API_CACHE : bool = True
LOAD_TASKS_FROM_CACHE : bool = False
#only effective if previous is true
SESSION_ID : str = "1678342904547157100"

MAX_TASKS = THREADS_PER_PROCESS * PROCESSES_N * 2

#cache format:
#cache/session_time/tags.json
#cache/session_time/page_index(200 posts/page assumed).json

REQUESTS_CHECK_COOLDOWN = 5.0

ROOT_DIR_NAME = "anime-porn"

CACHE_DIR_NAME = "cache"

FOLDER_SPLIT_COUNT = 100

REQUEST_TIMEOUT = 5
QUEUE_TIMEOUT = 5


BASE_URL = "https://danbooru.donmai.us/posts.json?"

ROOT_DIR : str = "./" + ROOT_DIR_NAME + "/"

STATE_COMPLETE : int = 1
STATE_INCOMPLETE : int = 0


CACHE_DIR = ROOT_DIR + CACHE_DIR_NAME + "/"


#queuery info

MAX_ENTRIES_PER_PAGE = 200
TAGS = [
    tag_score_order,
    "rating%3Aexplicit",

    #lmao
    #"sex"
]

#constant lookup time
KNOWN_EXTENSIONS = {
    ".png" : True,
    ".jpg" : True,
    ".gif" : True, 
    ".mp4" : True,
    ".zip" : True
}

def parse_tags(tags):
    s = tags[0]
    for i in range(1, len(tags)):
        s += "+" + tags[i]
    return s



QUERY_INFO = "limit=" + str(MAX_ENTRIES_PER_PAGE) + "&tags=" + parse_tags(TAGS)
TAGGED_BASE_URL : str = BASE_URL + QUERY_INFO





CF_TOKEN = r"pKC9inHoylW0t4Ip4QecCiw7P6g0xmGWXjjRWWJNiKY-1653062338-0-150"
REQ_HEADES = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers',
}

PROXY = {
    "https" : "https://127.0.0.1:7890"
}


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
        self.path : str = ROOT_DIR +                    \
            self.extention + "/"                        \
            + str(self.id % FOLDER_SPLIT_COUNT) + "/"   \
            + self.fname
    
    def is_valid(self) -> bool:

        
        #if file does not exist, download
        if(not os.path.exists(self.path)):
            return True
        #if not doing checksum
        #assume that the file is complete
        if(not CHECK_MD5):
            return False
        #if checking md5
        #if checksum is incomplete, redownload
        if(not utils.check_hash(self.path, self.md5)):
            print(self.fname + " exists but was not fully downloaded, redownloading...")
            return True
        #if checksum is complete
        print(self.fname + " exists, aborting download")
        return False

        


#state object, get task queue and completion status here
class SharedState:
    def __init__(self, session_id : str):
        self.queue = multiprocessing.Queue(MAX_TASKS)
        self.completion = multiprocessing.Value("i", STATE_INCOMPLETE)
        self.session_id = session_id
        self.cache_path = CACHE_DIR + session_id + "/"
        

    def is_complete(self) -> bool:
        if(self.completion.value == STATE_COMPLETE and self.queue.empty()):
            return True
        return False
    
#returns json-loaded dict from api, or none
def get_data(page : int, shared_info : SharedState) -> dict:


    print("Requesting for tasks...")
    url_paged = TAGGED_BASE_URL + "&page=" + str(page)
    success : bool = False
    while(not success):

        try:
            resp = requests.get(url = url_paged)
            if(resp.status_code != 200):
                raise("L request status is not 200")
            
        except:
            print("REQUESTS PROCESS: Tasks request failed. Retrying after timeout of " + str(REQUEST_TIMEOUT) + "s...")
            time.sleep(REQUEST_TIMEOUT)
            
        #there is 100% a cleaner way to do this but im lazy so 2 bad
        if(resp.status_code != 200):
            print("REQUESTS PROCESS: Tasks request failed. Retrying after timeout of " + str(REQUEST_TIMEOUT) + "s...")
            time.sleep(REQUEST_TIMEOUT)
            continue
        
        data = resp.json()

        if(SAVE_API_CACHE):
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
        if(KNOWN_ONLY):
            #if either false or none type
            if(not KNOWN_EXTENSIONS.__contains__(ext)):
                continue

        if(url == None):
            continue

        task : Task = Task(url, id, ext)
        #optional md5 checksum
        if(CHECK_MD5 and dat.__contains__("md5")):
            task.md5 = dat["md5"]
        #if no md5 in strict mode
        if(STRICT_MD5 and (not dat.__contains__("md5"))):
            continue
        res.append(task)
        
    return res

    



def save_image(task : Task):

    

    try:
        res = requests.get(url = task.url ,headers=REQ_HEADES, stream=True)
        print("Downloading " + task.fname)

        if res.status_code == 200:
            #note: may have unexpected behavior if terminated before eof reached
            with open(task.path,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            
            
            if(STRICT_MD5):
                if(not utils.check_hash(task.path, task.md5)):
                    print("File hash incorrect. Redownloading...")
                    del res
                    return False
            
            print('File sucessfully Downloaded: ', task.fname)
            del res
            return True
        else:
            print('File Couldn\'t be retrieved, Error:')
            print(res)
            del res
            return False

    except:
        
        print("Downloading of " + task.fname + " aborted as an exception is thrown.")
        del res
        return False
    


#==============================================MKDIRS======================================
#makes subfolders of extension
def mkdir():
    for k in KNOWN_EXTENSIONS:
        if(not os.path.isdir(ROOT_DIR + k)):
            os.mkdir(ROOT_DIR + k)
        for i in range(FOLDER_SPLIT_COUNT):
            cdir = ROOT_DIR + k + "/" + str(i)
            if(not os.path.isdir(cdir)):
                os.mkdir(cdir)

#makes the anime porn folder
def mkrootdir():
    if(not os.path.isdir(ROOT_DIR)):
        os.mkdir(ROOT_DIR)

def mkcachedir(session_dir : str):
    
    if(not os.path.isdir(CACHE_DIR)):
        os.mkdir(CACHE_DIR)

    if(not os.path.isdir(session_dir)):
        os.mkdir(session_dir)

    

    #create tags.json
    with open(session_dir + "/tags.json", "w") as f:
        f.write(json.dumps(TAGS))

#==============================================END MKDIRS======================================

#=========================================THREAD AND PROCESS PROCS======================================

def downloads_thread(shared_obj : SharedState):
    
    #only stop if both completion set to 1 AND queue is empty
    while(not shared_obj.is_complete()):

        try:
            ctask = shared_obj.queue.get(True, QUEUE_TIMEOUT)
        #check if task is valid
        except:
            print("DOWNLOADS_THREAD: Queue is currently empty, retrying after 5s...")
            time.sleep(5)
            continue
        
        ctask.initialize_props()
        #if task is invalid, dont start download
        if(not ctask.is_valid()):
            del ctask
            continue
        #print("Exectuting task: " + str(ctask["tid"]))
        #retry if failed
        while(not save_image(ctask)):
            print("Error is thrown while downloading. Retrying...")
        
        
        del ctask
    
    print("Download complete. Closing thread..")

        


#subprocesses here


def requests_subprocess(shared_obj : SharedState):
    for i in PAGE_RANGE:
        resp_data = None
        if(LOAD_TASKS_FROM_CACHE):
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
    pool = utils.ConcurrentThreadPool(THREADS_PER_PROCESS, pool_fn, ())

    pool.execute()
        

#========================================MAIN======================================

if __name__ ==  "__main__":

    session_id : str = str(time.time_ns())
    if(LOAD_TASKS_FROM_CACHE):
        session_id = SESSION_ID
        
    shared_obj = SharedState(session_id)
    mkrootdir()

    mkcachedir(shared_obj.cache_path)
    mkdir()
    

    

    req_p = multiprocessing.Process(target = requests_subprocess, args = (shared_obj,))
    
    downloads_pool = utils.ConcurrentProcessPool(PROCESSES_N, downloads_subprocess, args = (shared_obj,))
    

    #it = range(0,processes)
    
    
    req_p.start()
    downloads_pool.execute()

    req_p.join()
    

