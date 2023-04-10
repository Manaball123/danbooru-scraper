import requests
import config as cfg
import time
import json


#literally just requests data from a url
#u can just make the task queue a bunch of strs and just pool.map this shit
#returns json data or None type btw
def req_data(url : str) -> dict:
    try:
        resp = requests.get(url = url)
        if(resp.status_code == 200):
            return resp.json()
            
    except:
        print("Request failed. Retrying after timeout of " + str(cfg.REQUEST_TIMEOUT) + "s...")
        time.sleep(cfg.REQUEST_TIMEOUT)
            
    #there is 100% a cleaner way to do this but im lazy so 2 bad
    if(resp.status_code != 200):
        print("Request failed. Retrying after timeout of " + str(cfg.REQUEST_TIMEOUT) + "s...")
        time.sleep(cfg.REQUEST_TIMEOUT)
        return None
        

#saves the dict to a file as a json what did u expect...
#appends ".json" btw
def save_data(data : dict, fname : str, path : str = cfg.CACHE_DIR) -> None:
    with open(path + fname + ".json", "w+") as f:
            f.write(json.dumps(data))