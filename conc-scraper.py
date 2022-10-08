



import re


def default_modifier_fn(url, it):
    return url + "&page=" + it


#scraper that automatically searches images from an api and downloads them
class Scraper:
    def __init__(self, request_url, url_modifier_fn = default_modifier_fn, url_range = range(0,100), folder_split_n = 100):
        self.url_modifier = url_modifier_fn
        
        #api to get the cdn urls
        self.request_url = request_url




