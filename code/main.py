import time
import scrapy
import string
import html2text
import pickledb
import math
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
        rep = min(600, reputation[link]) if reputation[link] < 2000 else reputation[link]
        if not db.dexists("reputation", link):
            db.dadd("reputation", (link, rep))
        else:
            curr_rep = db.dget("reputation", link)
            new_rep = curr_rep + rep
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
        if db.dexists("master", i):
            # Single word queries
            results = db.dget("master", i)
            final = [(link, score, db.dget("reputation", link))
                      for link, score in results.items() if db.dexists("reputation", link)]
            final = sorted(final, key = lambda x: -1 * (5*x[1] + x[2] + 4*(x[1]*x[2])/(x[1]+x[2])))[:10]
            for link, relevance, reputation in final:
                print(fix_url("https://en.wikipedia.org/wiki/{}".format(link)))#, int(relevance), int(reputation))
            print()
        else:
            # Multi word queries
            d = dict()
            for ind, k in enumerate(i.split()):
                if db.dexists("master", k):
                    results = db.dget("master", k)
                    for link, score in results.items():
                        if link not in d:
                            d[link] = [0] *  len(i.split())
                        d[link][ind] = score
            def sort_results(item):
                link, scores  = item
                rep = db.dget("reputation", link) 
                rel = 1
                for score in scores:
                    rel *= max(score, 0.33)
                final = -1 * (5*rel + rep + 4*(rel*rep)/(rel+rep))    
                return final
            top_ten = sorted(d.items(), key = sort_results)[:10]

            for link, _arr in top_ten:
                print(fix_url("https://en.wikipedia.org/wiki/{}".format(link)))


search()

