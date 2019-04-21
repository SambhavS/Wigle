import scrapy 
import random
import logging
import os
from utils import *
import time
from selectolax.parser import HTMLParser

"""
search all real links, especially for ranking
-how to deal with multi-word search terms?

if multi_word term in dictionary ()

"""

def html_to_text(html):
    tree = HTMLParser(html)
    if tree.body is None:
        return None
    for tag in tree.css('script'):
        tag.decompose()
    for tag in tree.css('style'):
        tag.decompose()
    text = tree.body.text(separator='\n')
    return text

def shuffle(lst):
    random.shuffle(lst)
    return lst

class WikiSpider(scrapy.Spider):
    name = "test"
    base = "https://en.wikipedia.org"
    custom_settings = {"LOG_FILE":"out.log"}
    
    def __init__(self, db, link_set, master_dict, reputation, num_urls):
        self.num_urls = num_urls
        self.db = db
        self.link_set = link_set
        self.master_dict = master_dict
        self.reputation = reputation

    def start_requests(self):
        """creates a list of urls to search through """
        print("*Start Crawling*")
        
        with open("seeds.txt", "r") as f_in:
            self.urls = f_in.read().split()
        
        # Inject some randomness
        links = list(self.link_set)
        for link_base in links[:20]:
            yield scrapy.Request(url=self.base + "/wiki/" + link_base, callback=self.parse)

        with open("names.txt", "r") as f_in:
            for entry in f_in.read().split():
                if get_base(entry).lower() not in self.link_set:
                    self.urls.append(self.base + entry)

        while self.num_urls:
            if self.num_urls % 20 == 0:
                print("rem: ", self.num_urls)
            url = self.urls.pop()
            self.num_urls -= 1
            yield scrapy.Request(url=url, callback=self.parse)

        # Write out seeds for next crawl
        with open("seeds.txt", "w") as f_out:
            filtered = [link for link in self.urls if get_base(link).lower() not in self.link_set]
            for link in filtered[:10000]:
                f_out.write("{}\n".format(link))

    def extract_links(self, response):
        """extracts all valid links from an HTML response"""
        lst = response.css('a::attr(href)').getall()
        links = [i.split("/")[1:] for i in lst ]
        links = [link_pair[1] for link_pair in links if len(link_pair) == 2 and link_pair[0] == "wiki"]
        links = [i for i in links if ":" not in i]
        return links

    def reparse(self, response):
        links = self.extract_links(response)
        self.urls += [self.base + "/wiki/" + link for link in links[:200] if link not in self.link_set]

    def update_master_dict(self, word_list, lname):
        for i, word in enumerate(word_list):
            word = word.lower()
            found_weak, found_med, found_strong = 0, 0, 0
            if is_clean(word):
                if word not in self.master_dict:
                    self.master_dict[word] = dict()
                if lname not in self.master_dict[word]:
                    self.master_dict[word][lname] = 0
                if i < 30:
                    found_strong = 500  
                elif i < 150:
                    found_med = 150  
                found_weak += 20 
            self.master_dict[word][lname] += min(200, found_weak) + found_med + found_strong

    def parse(self, response):
        t1 = time.time()
        lname = get_base(response.url).lower()
        links = self.extract_links(response)
        # Add current url to list of crawled links
        self.link_set.add(lname)

        # Give very high priority to exact matches
        for subword in lname.split("_"):
            if subword not in self.master_dict:
                self.master_dict[subword] = dict()
            self.master_dict[subword][lname] = 10000
        if lname not in self.master_dict:
            self.master_dict[lname] = dict()
        self.master_dict[lname][lname] = 50000

        master_para = html_to_text(''.join(response.css("p").getall()[:25]))
        words = [clean(i) for i in master_para.split()]
        words = [i+" " for i in words if len(i) < 20]

        # Update master dictionary
        for k in range(1, 4):
            lsts = [words[i:i+k] for i in range(len(words)-k)]
            string_lists = [''.join(word).strip() for word in lsts]
            self.update_master_dict(string_lists, lname)
        
    
        # Update reputation
        for link in [lname] + links:
            if link not in self.reputation:
                self.reputation[link] = 0
            self.reputation[link] += 1 + self.reputation[lname]/100.0
            self.reputation[link] = min(self.reputation[link], 400)

        # Extend list of which links to crawl
        random.shuffle(links)
        if len(self.urls) < 100000:
            self.urls = [self.base + "/wiki/" + link for link in links[:200] if link not in self.link_set and is_clean(link)] + self.urls
        t2 = time.time() - t1
        #print("Total:", int(t2 * 1000), "ms")
        
        
        
        
       
                






                
