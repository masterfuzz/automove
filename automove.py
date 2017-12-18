#!/usr/bin/python
import os
import magic
import importlib
import yaml
import shutil
mime = magic.Magic(mime=True)


class IAutoDB(object):
    def __init__(self, conf, dest=None):
        self.dest = dest
        self.conf = conf
    def __str__(self):
        return "AutoDB"
    def log(self, message, level=0):
        print("[{}] {}".format(self, message))

class IAutoNotify(object):
    def __init__(self, conf, params=None):
        self.conf = conf
        self.params = conf.note.get('module parameters', {})

    def send(self, body, title=None):
        self.log("send(body='{}', title='{}'".format(self, body, title))

    def __str__(self):
        return "IAutoNotify<stdout>"
    def log(self, message, level=0):
        print("[{}] {}".format(self, message))


class Config:
    def __init__(self, conf_file):
        with open(conf_file) as f:
            y = yaml.load(f)

        self.src_dirs = y["Sources"]
        self.dest_dirs = y["Destinations"]
        self.dbs = y["Databases"]
        self.note = y["Notifications"]
        if 'Transfer' in y:
            self.overwrite = y['Transfer'].get('overwrite', False)
            self.delete = y['Transfer'].get('delete', False)
        else:
            self.overwrite = False
            self.delete = False


class Automove:
    def __init__(self, conf_file):
        self.conf = Config(conf_file)
        self.dbs = {}
        self._load_dbs()
        self._load_notifier()
        self.matches = []

    def run(self):
        self.log("Starting scan")
        self.matches = self._run()
        self.log("Scan completed")
        self.log("Starting move")
        self.move(self.matches)
        self.log("Move completed")

    def log(self, message, part=None, level=0):
        if part:
            print("[main.{}] {}".format(part, message))
        else:
            print("[main] {}".format(message))

    def _run(self):
        res = []
        for d in self.conf.src_dirs:
            res.extend(self.scan_src(d))

        for mfile in res:
            if mfile.ftypes:
                for t in mfile.ftypes:
                    self.log("Getting tags for {} as {}".format(mfile, t), part="scan")
                    mfile.tags += self.get_tags(self.conf.dest_dirs[t]['db'], mfile.fname)
            else:
                self.log("No types for '{}'".format(mfile), part="scan")

        return [r for r in res if r.ftypes]

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
            if self.conf.dest_dirs[d]['file type'] in self.get_file_type(fname):
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
                    self.log("Database plugin '{}' loaded".format(loaded_dbs[-1]), part="plugins")
                except Exception as e:
                    self.log(e)
                    raise e
            self.dbs[dlist] = loaded_dbs

    def _load_notifier(self):
        if self.conf.note and self.conf.note.get('module'):
            try:
                mod = importlib.import_module(self.conf.note['module'])
                self.note = mod.AutoNotify(self.conf)
            except Exception as e:
                self.log(e)
                raise e
        else:
            self.note = IAutoNotify(self.conf)
        self.log("Notifier plugin '{}' loaded".format(self.note), part="plugins")


    def get_tags(self, ftype, fname):
        tags = []
        if self.dbs[ftype]:
            for d in self.dbs[ftype]:
                self.log("\tSearching db {}".format(d), part="search")
                tags.append(d.search(fname))
        return tags

    def move(self, matches):
        for mfile in matches:
            if mfile.tags:
                new_path = self.get_dest(mfile)
                if new_path:
                    self.log("Found match for '{}' in '{}'".format(mfile, new_path), part="move")
                    if self._copy(mfile, new_path):
                        self._delete(mfile)
                        self.note.send("Copied '{}' to '{}'".format(mfile, new_path))
            else:
                if self.conf.note.get('when no tags', False):
                    self.note.send("No tags for {}".format(mfile))

    def _copy(self, mfile, dst):
        # check if exists
        #if os.path.isdir(dst)
        # TODO create directory!?
        dst = os.path.join(dst, mfile.fname)
        if os.path.isfile(dst):
            if self.conf.overwrite:
                # copy anyway
                shutil.copyfile(mfile.full_path, dst)
                self.log("Copied '{}' to '{}' (OVERWROTE)".format(mfile, dst))
            else:
                self.log("Not overwriting '{}' in '{}'".format(mfile, dst))
                return False
        else:
            shutil.copyfile(mfile.full_path, dst)
            self.log("Copied '{}' to '{}'".format(mfile, dst))
        return True

    def _delete(self, mfile):
        self.log("(Not) deleting {}".format(mfile))

    def get_dest(self, mfile):
        if len(mfile.ftypes) > 1:
            self.log("{} has more than one type".format(mfile), part="move")

        ftype = mfile.ftypes[0]
        org_tags = self.conf.dest_dirs[ftype]['org'].split('/')
        path = self.conf.dest_dirs[ftype]['path']

        # find each part of org to assemble path
        # list of {tag name: {name: hits}}
        # [{'series': {'Stranger Things': 2}}]
        for o in org_tags:
            org_matches = [x[o].keys()[0] for x in mfile.tags if o in x]
            if len(org_matches) == 1:
                path = os.path.join(path, org_matches[0])
                self.log("Found {} match for '{}' as '{}'".format(o, mfile, org_matches[0]), part="move")
            else:
                self.log("Too many matches for '{}' for '{}'".format(o, mfile), part="move")
                return None
        return path






class MediaFile:
    def __init__(self, fname, ftypes=None, tags=None, mime=None):
        self.full_path = fname
        self.path, self.fname = os.path.split(fname)
        self.ftypes = ftypes if ftypes else []
        self.mime = mime
        self.tags = tags if tags else []

    def __str__(self):
        return self.fname


if __name__ == "__main__":
    am = Automove("conf.yaml")
    am.run()

