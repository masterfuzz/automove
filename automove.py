#!/usr/bin/python
import os
import magic
import importlib
import yaml
mime = magic.Magic(mime=True)


class IAutoDB(object):
    def __init__(self, conf, dest=None):
        self.dest = dest
        self.conf = conf
    def __str__(self):
        return "AutoDB"

class Config:
    def __init__(self, conf_file):
        with open(conf_file) as f:
            y = yaml.load(f)

        self.src_dirs = y["Sources"]
        self.dest_dirs = y["Destinations"]
        self.dbs = y["Databases"]


class Automove:
    def __init__(self, conf_file):
        self.conf = Config(conf_file)
        self.dbs = {}
        self._load_dbs()

    def run(self):
        res = []
        for d in self.conf.src_dirs:
            res.extend(self.scan_src(d))

        for mfile in res:
            for t in mfile.ftypes:
                print("Getting tags for {} as {}".format(mfile, t))
                mfile.tags += self.get_tags(self.conf.dest_dirs[t]['db'], mfile.fname)

        return res

    def scan_src(self, src):
        flist=[]
        for (dirpath, dirnames, filenames) in os.walk(src):
            flist.extend(map(lambda x: os.path.join(dirpath,x), filenames))

        return [MediaFile(f, ftypes=self.ftype_match(f)) for f in flist]

    def get_file_type(self, fname):
        return magic.from_file(fname).lower() + " " + mime.from_file(fname).lower()

    def ftype_match(self, fname):
        matches = []
        for d in self.conf.dest_dirs:
            if self.conf.dest_dirs[d]['file_type'] in self.get_file_type(fname):
                matches.append(d)
        return matches

    def _load_dbs(self):
        for dest in self.conf.dest_dirs:
            loaded_dbs = []
            dlist = self.conf.dest_dirs[dest]['db']
            for db in self.conf.dbs[dlist]:
                try:
                    mod = importlib.import_module(db)
                    loaded_dbs.append(mod.AutoDB(self.conf, dest))
                except Exception as e:
                    print(e)
            self.dbs[dlist] = loaded_dbs

    def get_tags(self, ftype, fname):
        tags = []
        if self.dbs[ftype]:
            for d in self.dbs[ftype]:
                print("\tSearching db {}".format(d))
                tags.append(d.search(fname))
        return tags



class MediaFile:
    def __init__(self, fname, ftypes=None, tags=None):
        self.path, self.fname = os.path.split(fname)
        self.ftypes = ftypes if ftypes else []
        self.tags = tags if tags else []

    def __str__(self):
        return self.fname


if __name__ == "__main__":
    am = Automove("conf.yaml")
    res = am.run()

