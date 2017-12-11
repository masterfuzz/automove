#!/usr/bin/python
import os
import magic
import importlib
import json
mime = magic.Magic(mime=True)


class IAutoDB(object):
    def __init__(self, conf):
        self.conf = conf

class Config:
    def __init__(self, conf_file):
        with open(conf_file) as f:
            j = json.load(f)

        self.src_dirs = j["src_dirs"]
        self.dest_dirs = j["dest_dirs"]
        self.dbs = j["dbs"]


class Automove:
    def __init__(self, conf_file):
        self.conf = Config(conf_file)
        self.dbs = {}
        self._load_dbs()

    def run(self):
        res = []
        for d in self.conf.src_dirs:
            res.extend(self.scan_src(d))
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
            if self.conf.dest_dirs[d]['file_type'] in self.get_file_type(fname):
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


if __name__ == "__main__":
    am = Automove("conf.json")
    print(am.run())

