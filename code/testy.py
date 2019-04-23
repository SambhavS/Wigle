import pickledb
from utils import *
import logging
import scrapy
from scrapy.crawler import CrawlerProcess


class GenSpider(scrapy.Spider):
    name = "gen"
    base = "https://en.wikipedia.org/wiki/"
    custom_settings = {"LOG_FILE":"out2.log", "DEPTH_PRIORITY": 1, "DEPTH_MAX": 3}
    def __init__(self, titles, d):
        self.titles = titles
        self.d = d
        self.i = 0
        self.links = set()

    def fill_dict(self, lst):
        lst = list(lst)
        title = True
        while lst:
            title = lst.pop()
            if len(self.links) % 1000 == 0:
                print(len(self.links))
            if title not in self.links:
                self.links.add(title)
                if title not in self.d:
                    self.d[title] = [title]
                for word in title.split("_"):
                    if word not in self.d:
                        self.d[word] = []
                    self.d[word].append(title)

    def start_requests(self):
        self.fill_dict(self.titles)
        for title in self.titles:
            yield scrapy.Request(url=self.base+title, callback=self.parse)
        print(len(self.links))

    def extract_links(self, response):
        """extracts all valid links from an HTML response"""
        lst = response.css('a::attr(href)').getall()
        links = [i.split("/")[1:] for i in lst]
        links = [link_pair[1] for link_pair in links if len(link_pair) == 2 and link_pair[0] == "wiki"]
        links = [i.lower() for i in links if ":" not in i]
        return links

    def parse(self, response):
        links = self.extract_links(response)
        self.fill_dict(links)
        print(self.i)
        self.i += 1
def main():
    db = pickledb.load('all_names.db', False)
    db.dcreate("all_names")
    with open("names.txt", "r") as f_in:
        titles = []
        for i in range(8500):
            t = f_in.readline().split("/")[-1]
            if not t:
                break
            titles.append(t.strip())

    d = dict()
    logging.getLogger('scrapy').setLevel(logging.WARNING)
    process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
    process.crawl(GenSpider, titles=titles,d=d)
    process.start()
    print("finished")
    for key, value in d.items():
        db.dadd("all_names", (key, value))
    print("wrote")
    db.dump()




