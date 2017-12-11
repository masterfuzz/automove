#!/usr/bin/python
import os
import magic
import importlib
mime = magic.Magic(mime=True)


class IAutoDB(object):
    def __init__(self, conf):
        self.conf = conf

class Automove:
    def __init__(self, conf_file):
        self.conf = load_config(conf_file)
        self._load_dbs()

    def run(self):
        res = []
        for d in src_dirs:
            res.extend(scan_src(d))
        return res

    def scan_src(self, src):
        flist=[]
        for (dirpath, dirnames, filenames) in os.walk(src):
            flist.extend(map(lambda x: os.path.join(dirpath,x), filenames))

        return [(f, self.ftype_match(f)) for f in flist]

    def get_file_type(self, fname):
        return magic.from_file(fname).lower() + " " + mime.from_file(fname).lower()

    def ftype_match(self, fname):
        matches = []
        for d in self.conf.dest_dirs:
            if self.dest_dirs[d]['file_type'] in self.get_file_type(fname):
                matches.append(d)
        return matches

    def _load_dbs(self):
        for dlist in self.conf.dbs:
            loaded_dbs = []
            for db in self.conf.dbs[dlist]:
                try:
                    mod = importlib.import_module(db)
                    loaded_dbs.append(mod.AutoDB(self.conf))
                except Exception as e:
                    print(e)
            self.dbs[dlist] = loaded_dbs

    def db_matches(self, db, fname):
        if dbs[db]:
            pass


