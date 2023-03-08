
import hashlib

from functools import partial
import requests
import utils
import shutil
import os
        
import multiprocessing
import threading
import time




#consts
tag_score_order = "order%3Ascore"

#ARGS HERE



start = 1
stop = 50

threads_per_process = 32
processes = 16

check_md5 = True
strict_md5 = True
known_only : bool = True
max_tasks = threads_per_process * processes * 2

requests_check_cooldown = 5.0

dirname = "anime-porn"

folder_split_count = 100

timeout_time = 3


baseurl = "https://danbooru.donmai.us/posts.json?"


#queuery info

page_lim = 200
tags = [
    tag_score_order,
    "rating%3Aexplicit",

    #lmao
    #"sex"
]

#constant lookup time
known_extentions = {
    ".png" : True,
    ".jpg" : True,
    ".gif" : True, 
    ".mp4" : True
}

def get_tags(tags):
    s = tags[0]
    for i in range(1, len(tags)):
        s += "+" + tags[i]
    return s



qinfo = "limit=" + str(page_lim) + "&tags=" + get_tags(tags)
url : str = baseurl + qinfo

dir : str = "./" + dirname + "/"




cf = r"pKC9inHoylW0t4Ip4QecCiw7P6g0xmGWXjjRWWJNiKY-1653062338-0-150"
headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers',
}

proxy = {
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
        self.fname : str = str(id) + self.extention

        #relative path
        #./dirname/.png/66/42069666.png
        self.path : str = dir +                         \
            self.extention + "/"                        \
            + str(self.id % folder_split_count) + "/"   \
            + self.fname
    
    def is_valid(self) -> bool:
        global known_extentions
        if(known_only):
            #if either false or none type
            if(not known_extentions[self.extention]):
                return False
        
        #if file does not exist, download
        if(not os.path.exists(self.path)):
            return True
        #if not doing checksum
        #assume that the file is complete
        if(not check_md5):
            return False
        #if checking md5
        #if checksum is incomplete, redownload
        if(not utils.check_hash(self.path, self.md5)):
            print(self.fname + " exists but was not fully downloaded, redownloading...")
            return True
        #if checksum is complete
        print(self.fname + " exists, aborting download")
        return False

        



def get_request(page):
    global url
    global known_extentions
    print("Requesting for tasks...")
    url_paged = url + "&page=" + str(page)

    try:
        resp = requests.get(url = url_paged)
        if(resp.status_code != 200):
            raise("L request status is not 200")
        
        data = resp.json()
    except:
        print("REQUESTS PROCESS: Tasks request failed. Retrying after timeout of " + str(timeout_time) + "s...")
        time.sleep(timeout_time)
        
        return []
        
    res = []

    for dat in data:
        #if no id
        if(not dat.__contains__("id")):
            continue
        #if no cdn url
        url = utils.get_cdn_url(dat)

        if(url == None):
            continue

        task : Task = Task(url, dat["id"], dat["ext"])
        #optional md5 checksum
        if(check_md5 and dat.__contains__("md5")):
            task.md5 = dat["md5"]
        #if no md5 in strict mode
        if(strict_md5 and (not dat.__contains__("md5"))):
            continue
            


        print("REQUESTS PROCESS: New tasks requested.")
        return res

    



def save_image(task : Task):

    

    try:
        res = requests.get(url = task.url ,headers=headers, stream=True)
        print("Downloading " + task.fname)

        if res.status_code == 200:
            #note: may have unexpected behavior if terminated before eof reached
            with open(task.path,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            
            
            if(strict_md5):
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
        
        print("Downloading of" + task.fname + "aborted as an exception is thrown.")
        del res
        return False

#makes subfolders of extension
def mkdir():
    for k in known_extentions:
        if(not os.path.isdir(dir + k)):
            os.mkdir(dir + k)
        for i in range(folder_split_count):
            cdir = dir + k + "/" + str(i)
            if(not os.path.isdir(cdir)):
                os.mkdir(cdir)

#makes the anime porn folder
def mkrootdir():
    if(not os.path.isdir(dirname)):
        os.mkdir(dirname)


def downloads_thread(shared_obj):
    
    #only stop if both completion set to 1 AND queue is empty
    while(shared_obj["completion"].value == 0 or shared_obj["queue"].empty() == False):
        ctask = shared_obj["queue"].get()
        #check if task is valid
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


def requests_subprocess(shared_queue : multiprocessing.Queue, page_range : int, completion_mark):
    
    for i in page_range:
        tasks_to_push = get_request(i)
        for j in range(len(tasks_to_push)):
            shared_queue.put(tasks_to_push[j])
    
    #mark completion when finished executing
    completion_mark.value = 1
    


def downloads_subprocess(shared_queue : multiprocessing.Queue, completion_mark):
    #pool = ThreadPool(processes = threads)
    
    shared_obj = {
        "queue" : shared_queue,
        "completion" : completion_mark
    }

    pool_fn = partial(downloads_thread, shared_obj)
    pool = utils.ConcurrentThreadPool(threads_per_process, pool_fn, ())

    pool.execute()
        






if __name__ ==  "__main__":

    mkrootdir()
    mkdir()
    page_range = range(start,stop)

    
    comp_mark = multiprocessing.Value("i", 0)

    queue = multiprocessing.Queue(maxsize = max_tasks)

    req_p = multiprocessing.Process(target = requests_subprocess, args = (queue, page_range, comp_mark))


    downloads_pool = utils.ConcurrentProcessPool(processes, downloads_subprocess, args = (queue, comp_mark))
    

    #it = range(0,processes)
    
    
    req_p.start()
    downloads_pool.execute()

    req_p.join()
    

