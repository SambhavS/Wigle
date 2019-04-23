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
    
def single_word_answers(db, article_names, i):
    """ 
    Returns top eight results. Ordered by: exact match, match & rep, match, rep
    """
    results = db.dget("master", i)
    final = [(link, score, db.dget("reputation", link)) for link, score in results.items()]
    scored_links = dict()
    for link, rel, rep in final:
        scored_links[link] = -1 * (5*rel + rep + 2*(rel*rep)/(rel+rep))
    crawled = sorted([(link, score) for link, score in scored_links.items()], key=lambda x:x[1])
    matches = []
    matched_links = set()
    if article_names.dexists("all_names", i):
        articles = article_names.dget("all_names", i)
        for article in articles:
            if article in scored_links:
                matches.append((article, scored_links[article]))
            else:
                matches.append((article, 0))
            matched_links.add(article)
    matches = sorted(matches, key=lambda x: x[1])
    for link, score in crawled:
        if link not in matched_links:
            matches.append((link, -1))

    # Exact match
    if article_names.dexists("all_names", i):
        matches = [i] + [m for m,s in matches if m != i]
    else:
        matches = [m for m,s in matches]
    return matches[:8]
    
def multi_word_answers(db, article_names, i):
    """
    Returns top eight results. Based mostly on reputation/relevance.
    """
    def sort_results(item):
        """ Function for calculating reputation/relevance score"""
        link, scores  = item
        rep = db.dget("reputation", link) 
        rel = 1
        for score in scores:
            rel *= max(score, 0.25)
        final = -1 * (5*rel + rep + 2*(rel*rep)/(rel+rep))    
        return final

    def k_factor(link, i):
        """ Gives score multiple based on number of matching words in string """
        return 1 + len(set(link.split("_")).intersection(set(i.split())))

    # Multi word queries
    d = dict()
    for ind, k in enumerate(i.split()):
        if db.dexists("master", k):
            results = db.dget("master", k)
            for link, score in results.items():
                if link not in d:
                    d[link] = [0] *  len(i.split())
                d[link][ind] = score
    crawled = sorted([(link, sort_results((link,score))) for link, score in sorted(d.items())], key=lambda x:x[1])
    crawled = crawled[:30]    
    matches = [(link, score * k_factor(link, i)) for link,score in crawled]
    matches = sorted(matches, key=lambda x: x[1])
    mod_i = i.replace(" ", "_").strip()
    if article_names.dexists("all_names", mod_i):
        matches = [i.replace(" ", "_")] + [m for m,s in matches if m != mod_i]
    else:
        matches = [m for m,s in matches]
    return matches[:8]

def search():
    db = pickledb.load("n2.db", False)
    article_names = pickledb.load("all_names.db", False)
    base = "https://en.wikipedia.org/wiki/"
    while True:
        i = input("🔍 ").lower()
        if i in ("quit", "exit"):
            break
        if db.dexists("master", i):
            answers = [fix_url(base+a) for a in single_word_answers(db, article_names, i)]
        else:
            answers = [fix_url(base+a) for a in multi_word_answers(db, article_names, i)]
        for each in answers:
            print(each)
        if not answers:
            print("no results found")
        print()
search()