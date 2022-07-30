import multiprocessing

import requests
import shutil
import os

url = "https://danbooru.donmai.us/posts.json?limit=200&tags=order%3Ascore"
dir = "./order-score/"

cf = r"pKC9inHoylW0t4Ip4QecCiw7P6g0xmGWXjjRWWJNiKY-1653062338-0-150"
headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
}
r = []
posturl = "https://danbooru.donmai.us/posts/"
def get_request(page):
    url_paged = url + "&page=" + str(page)
    resp = requests.get(url=url_paged)

    data = resp.json()
    
    res = []
    for i in range(len(data)):
        if data[i].__contains__("id"):
            res.append(data[i]["id"])
    

    return res
    

    

def find_cdn_url_from_resp(respc):
    pattern = "https://cdn.donmai.us/original"
    index = respc.find(pattern)
    

    encounters = 0
    url = ""
    for i in range(index, index + 200):
        
        if(respc[i] == "\""):
            #print(url)
            return url
        url += respc[i]

    return None

def get_cdn_url(id):
    url = posturl + str(id)
    response = requests.get(url, headers=headers)

    return find_cdn_url_from_resp(str(response.content))

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


def save_image(id):

    url = get_cdn_url(id)
    if(url == None):
        return
    ext = find_ext(url)
    if(ext == None):
        return 
    sdir = dir + str(id % 100) + "/"
    name = str(id) + ext
    if(os.path.exists(sdir + name)):
        print(name + " Exists")
    res = requests.get(url=url,headers=headers, stream=True)
    
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
        os.mkdir(dir + str(i))


if __name__ ==  "__main__":

    processes = 50
    page_range = range(1,100)

    

    pool = multiprocessing.Pool(processes)
    
    for i in page_range:
        resp = get_request(i)


        print("Starting downloads for page " + str(i))
        print("\n\n")
        pool.map(save_image, resp)
        print("\n\n")

        print("Finished downloading page " + str(i))
