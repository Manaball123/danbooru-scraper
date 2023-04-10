#ik this is pretty messy
#but too bad

THREADS_PER_PROCESS = 32
PROCESSES_N = 16

CHECK_MD5 = True
STRICT_MD5 = True
KNOWN_ONLY : bool = True
SAVE_API_CACHE : bool = True
LOAD_TASKS_FROM_CACHE : bool = True
#only effective if previous is true
SESSION_ID : str = "1678381950055370700"


MAX_TASKS = THREADS_PER_PROCESS * PROCESSES_N * 2


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
MAX_ENTRIES_PER_PAGE = 200
TAGS = [
    "order%3Ascore",
    "rating%3Aexplicit",

    #lmao
    #"sex"
]

PAGE_START = 1
PAGE_STOP = 255
PAGE_RANGE = range(PAGE_START, PAGE_STOP + 1)
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
