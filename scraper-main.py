
from multiprocessing.pool import ThreadPool
import multiprocessing
import requests
import shutil
import os



#ARGS HERE

start = 1
stop = 50
threads = 128










url = "https://danbooru.donmai.us/posts.json?limit=200&tags=order%3Ascore"
dir = "./anime-porn/"

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

posturl = "https://danbooru.donmai.us/posts/"
def get_request(page):
    url_paged = url + "&page=" + str(page)

    resp = requests.get(url = url_paged)

    data = resp.json()
    
    res = []
    for i in range(len(data)):
        
        if(data[i].__contains__("id") and data[i].__contains__("large_file_url")):
            res.append({
                "tid" : data[i]["id"],
                "url" : data[i]["large_file_url"]
            })
        
        
            
    

    return res
    

    

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
    sdir = dir + str(task["tid"] % 100) + "/"
    name = str(task["tid"]) + ext
    if(os.path.exists(sdir + name)):
        print(name + " Exists")
        return
    #print("Downloading " + name)
    res = requests.get(url=task["url"],headers=headers, stream=True)
    
    #print("Retrieving from " + url)
    if res.status_code == 200:
        with open(sdir + name,'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print('File sucessfully Downloaded: ', name)
    else:
        print('File Couldn\'t be retrieved, Error:')
        print(res)


def mkdir():
    for i in range(100):
        cdir = dir + str(i)
        if(not os.path.isdir(cdir)):
            os.mkdir(cdir)

#makes the anime porn folder
def mkrootdir():
    if(not os.path.isdir("anime-porn")):
        os.mkdir("anime-porn")



if __name__ ==  "__main__":

    mkrootdir()
    mkdir()
    page_range = range(start,stop)

    

    pool = ThreadPool(processes = threads)
    
    for i in page_range:
        tasks = get_request(i)


        print("Starting downloads for page " + str(i))
        print("\n\n")
        pool.map(save_image, tasks)
        print("\n\n")

        print("Finished downloading page " + str(i))
