### Utils
import pickledb 
import string

def clean(word):
    return ''.join(i for i in word if i in string.ascii_letters+" 1234567890")

def is_clean(word):
    return all([i for i in word if i not in "%#!@"])

def get_base(full_url):
    return full_url.split("/")[-1]

def write_dict(db, fname, dictionary):
    """ Update database """
    for key, value in dictionary.items():
        if type(value) is dict:
            orig_dict = db.dget(fname, key)
            new_dict = {**orig_dict, **value}
            db.dadd(fname, (key, new_dict))
        elif type(value) is int:
            orig_int = db.dget(fname, key)
            new_int = value + orig_int
            db.dadd(fname, (key, new_int))

def write_list(db, fname, lst):
    db.lremlist(fname)
    db.lcreate(fname)
    for val in lst:
        db.ladd(fname, val)

def dict2file(fname, dictionary):
    with open("{}.txt".format(fname), "w") as f_out:
        i = 0
        for k, v in dictionary.items():
            i += 1
            if i > 1000:
                break
            f_out.write("{}:\n".format(k))
            f_out.write("{}\n".format(v))

def list2file(fname, lst):
    with open("{}.txt".format(fname), "w") as f_out:
        for i, each in enumerate(lst):
            f_out.write(each + " | "+ "\n"*(i%100 == 0))
