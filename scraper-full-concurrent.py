
import hashlib

from functools import partial
import requests
import shutil
import os
        
import multiprocessing
import threading



#consts
tag_score_order = "order%3Ascore"

#ARGS HERE



start = 1
stop = 50

threads_per_process = 32
processes = 16

do_checksum = True
max_tasks = threads_per_process * processes * 2

requests_check_cooldown = 5.0

dirname = "anime-porn"

folder_split_count = 100


baseurl = "https://danbooru.donmai.us/posts.json?"


#queuery info

page_lim = 200
tags = [
    tag_score_order,
    "sex"
]

def get_tags(tags):
    s = tags[0]
    for i in range(1, len(tags)):
        s += "+" + tags[i]
    return s



qinfo = "limit=" + str(page_lim) + "&tags=" + get_tags(tags)
url = baseurl + qinfo

dir = "./" + dirname + "/"




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


def get_request(page):
    global url
    print("Requesting for tasks...")
    url_paged = url + "&page=" + str(page)

    try:
        resp = requests.get(url = url_paged)

        data = resp.json()
        
        res = []
        
        for i in range(len(data)):
            
            if(data[i].__contains__("id")):
                url = get_cdn_url(data[i])
                
                if(url != None):
                    task = {
                        "tid" : data[i]["id"],
                        "url" : url
                    }
                
                    if(do_checksum and data[i].__contains__("md5")):
                        task["md5"] = data[i]["md5"]
                        res.append(task)
                    else:
                        res.append(task)


        print("New tasks requested.")
        return res
    except:
        print("Tasks request failed. Retrying...")
        return []
    

    

def find_ext(str):

    strlen = len(str)
    #print(str)
    i = strlen - 1
    while i > 0:
        if(str[i] == "."):

            return str[i:]
        else:
            i -= 1
    return None


def save_image(task):


    ext = find_ext(task["url"])
    if(ext == None):
        return 
    sdir = dir + str(task["tid"] % folder_split_count) + "/"
    name = str(task["tid"]) + ext
    fulldir = sdir + name


    download = False

    if(os.path.exists(fulldir)):

        if(do_checksum):
            #if checksum is incomplete, redownload
            if(not check_hash(fulldir, task["md5"])):
                print(name + " exists but was not fully downloaded, redownloading...")
                download = True
            
            #if exist and checksum is complete
            else:
                download = False

        #if exist and not doing checksum
        else:
            download = False

    #if file does not exist
    else:
        download = True


    if(not download):
        #if not doing checksum OR checksum is complete, abort
        print(name + " exists, aborting download")
        return True


    #print("Downloading " + name)
    try:
        res = requests.get(url=task["url"],headers=headers, stream=True)
        print("Downloading " + name)
        #print("Retrieving from " + url)
        if res.status_code == 200:
            with open(sdir + name,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print('File sucessfully Downloaded: ', name)
            del res
            return True
        else:
            print('File Couldn\'t be retrieved, Error:')
            print(res)
            return False

    except:
        
        print("Downloading of" + name + "aborted as an exception is thrown.")
        return False


def mkdir():
    for i in range(100):
        cdir = dir + str(i)
        if(not os.path.isdir(cdir)):
            os.mkdir(cdir)

#makes the anime porn folder
def mkrootdir():
    if(not os.path.isdir(dirname)):
        os.mkdir(dirname)

def downloads_thread(shared_obj):
    
    while(shared_obj["completion"].value == 0 or shared_obj["queue"].empty() == False):
        ctask = shared_obj["queue"].get()
        #print("Exectuting task: " + str(ctask["tid"]))
        #retry if failed
        while(not save_image(ctask)):
            print("Error is thrown while downloading. Retrying...")
    
    print("Download complete. Closing thread..")

        


#subprocesses here


def requests_subprocess(shared_queue, page_range, completion_mark):
    
    for i in page_range:
        tasks_to_push = get_request(i)
        for j in range(len(tasks_to_push)):
            shared_queue.put(tasks_to_push[j])
    
    #mark completion when finished executing
    completion_mark.value = 1
    


def downloads_subprocess(shared_queue, completion_mark):
    #pool = ThreadPool(processes = threads)
    
    shared_obj = {
        "queue" : shared_queue,
        "completion" : completion_mark
    }
    pool_fn = partial(downloads_thread, shared_obj)
    pool = ConcurrentThreadPool(threads_per_process, pool_fn, ())

    pool.execute()
        


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



if __name__ ==  "__main__":

    mkrootdir()
    mkdir()
    page_range = range(start,stop)

    
    comp_mark = multiprocessing.Value("i", 0)

    queue = multiprocessing.Queue(maxsize=max_tasks)

    req_p = multiprocessing.Process(target = requests_subprocess, args = (queue, page_range, comp_mark))


    downloads_pool = ConcurrentProcessPool(processes, downloads_subprocess, args = (queue, comp_mark))


    #it = range(0,processes)
    
    
    req_p.start()
    downloads_pool.execute()

    req_p.join()
    

