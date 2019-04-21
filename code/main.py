import time
import scrapy
import string
import html2text
import pickledb
from spider import *
from utils import *
from scrapy.crawler import CrawlerProcess


def clear_db(check1, check2, check3):
    """
    CLEARS ENTIRE DATABASE | Be careful!!
    """
    print("*Clearing DB!*")
    if check1 == True and check2 == True and check3 == True:
        db = pickledb.load('n2.db', False)
        db.dcreate("master")
        db.dcreate("reputation")
        db.lcreate("links")
        db.dump()
    print("*Clearing DB Cleared!*")

def crawl(num_urls=500):
    db = pickledb.load("n2.db", False)
    master_dict = dict()
    reputation = dict()
    link_set = set(db.lgetall("links"))
    logging.getLogger('scrapy').setLevel(logging.WARNING)
    process = CrawlerProcess({'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'})
    process.crawl(WikiSpider, link_set=link_set, db=db, num_urls=num_urls,
                                 master_dict=master_dict, reputation=reputation)
    tX = time.time()
    process.start()
    tY = time.time() - tX
    print(tY)
    print("*Finished Crawling*")
    print("Total Pages Crawled: ", len(link_set))

    # Update master dict
    for searchword, d in master_dict.items():
        if not db.dexists("master", searchword):
            db.dadd("master", (searchword, d))
        else:
            orig_dict = db.dget("master", searchword)
            new_dict = {**orig_dict, **d}
            db.dadd("master", (searchword, new_dict))

    # Update reputation
    for link in reputation:
        if not db.dexists("reputation", link):
            db.dadd("reputation", (link, reputation[link]))
        else:
            curr_rep = db.dget("reputation", link)
            new_rep = curr_rep + reputation[link]
            db.dadd("reputation", (link, new_rep))

    # Update list of links
    write_list(db, "links", sorted(list(link_set)))
    db.dump()    
    print("*Updated Database*")
    dict2file("master", master_dict)
    dict2file("reputation", reputation)
    list2file("links", sorted(list(link_set)))
    
    
def search():
    db = pickledb.load("n2.db", False)
    while True:
        i = input("🔍 ").lower()
        if i in ("quit", "exit"):
            break
        if(len(i.split()) > 7):
            print("query must be seven or fewer words")
            continue
        if db.dexists("master", i):
            results = db.dget("master", i)
            final = [(link, score, db.dget("reputation", link))
                      for link, score in results.items() if db.dexists("reputation", link)]
            final = sorted(final, key = lambda x: -1 * (x[1]+x[2]))[:40]
            for link, relevance, reputation in final:
                print("https://en.wikipedia.org/wiki/{}".format(link), int(relevance), int(reputation))
            print()
        else:
            print("word not found")



search()

