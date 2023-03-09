import multiprocessing
from multiprocessing.pool import ThreadPool
import requests
import time
from functools import partial
import os
import json
#only downloads the api image metadata, multithreaded

PAGE_START = 1
PAGE_STOP = 2
PAGE_RANGE = range(PAGE_START, PAGE_STOP + 1)


THREADS_N = 16



CHECK_MD5 = True
STRICT_MD5 = True
KNOWN_ONLY : bool = True
SAVE_API_CACHE : bool = True
LOAD_TASKS_FROM_CACHE : bool = True
#only effective if previous is true
SESSION_ID : str = "1678343863044889500"

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
    "order%3Ascore",
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


#saves data to path
def get_data(path : str, page : int) -> dict:


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
            print("REQUESTS THREAD: Tasks request failed. Retrying after timeout of " + str(REQUEST_TIMEOUT) + "s...")
            time.sleep(REQUEST_TIMEOUT)
            continue
        
        data = resp.text()

        if(SAVE_API_CACHE):
            with open(path + str(page) + ".json", "w+") as f:
                f.write(data)
        print("REQUESTS THREAD: New tasks requested.")
        return data
    

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

        

if __name__ == "__main__":
    pool = ThreadPool(THREADS_N)

    session_id : str = str(time.time_ns())
    cache_path = CACHE_DIR + session_id + "/"

    get_data_part = partial(get_data, cache_path)
    mkrootdir()
    mkcachedir(cache_path)

    pool.map(get_data_part, PAGE_RANGE)
    


            