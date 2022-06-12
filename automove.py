#!/usr/bin/python
import os
import magic
import importlib
import shutil
import progressbar
from config import Config

mime = magic.Magic(mime=True)


class IAutoDB(object):
    def __init__(self, conf, dest=None):
        self.dest = dest
        self.conf = conf

    def __str__(self):
        return "AutoDB"

    def log(self, message, level=0):
        print("[{}] {}".format(self, message))


class IAutoVerify(object):
    def __init__(self, conf):
        self.conf = conf

    def verify(self, a, b):
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        return True
        if os.system("cmp '{}' '{}'".format(a, b)) != 0:
            return False
        return True


class IAutoNotify(object):
    def __init__(self, conf):
        self.conf = conf
        self.params = conf.note.get("module parameters", {})
        self.message = []

    def send(self, body, title=None):
        self.log("send(body='{}', title='{}'".format(self, body, title))

    def send_all(self, title=None):
        if self.message:
            if self.conf.note.get("summary", True):
                self.send("\n".join(self.message), title=title)
            else:
                for m in self.message:
                    self.send(m, title=title)
        else:
            self.log("send_all: empty message")

    def add(self, message):
        self.message.append(message)

    def __str__(self):
        return "IAutoNotify<stdout>"

    def log(self, message, level=0):
        print("[{}] {}".format(self, message))


class Automove:
    def __init__(self, conf):
        self.conf = conf
        self.dbs = {}
        self._load_dbs()
        self._load_notifier()
        self._load_verifier()
        self.matches = []

    def run(self):
        self.log("Starting scan")
        self.matches = self._run()
        self.log("Scan completed")
        self.log("Starting move")
        self.move(self.matches)
        self.log("Move completed")
        self.note.send_all("Automove")

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
                    mfile.tags += self.get_tags(self.conf.dest_dirs[t]["db"], mfile)
            else:
                self.log("No types for '{}'".format(mfile), part="scan")

        return [r for r in res if r.ftypes]

    def scan_src(self, src):
        self.log("Scanning '{}'...".format(src), part="scan")
        flist = []
        for (dirpath, dirnames, filenames) in os.walk(src):
            flist.extend(map(lambda x: os.path.join(dirpath, x), filenames))

        self.log("Getting file types for {} files...".format(len(flist)), part="scan")
        mlist = []
        bar = progressbar.ProgressBar()
        for f in bar(flist):
            mlist.append(MediaFile(f, ftypes=self.ftype_match(f)))

        return mlist

    def get_file_type(self, fname):
        return magic.from_file(fname).lower() + " " + mime.from_file(fname).lower()

    def ftype_match(self, fname):
        matches = []
        for d in self.conf.dest_dirs:
            if self.conf.dest_dirs[d]["file type"] is None:
                matches.append(d)
            elif self.conf.dest_dirs[d]["file type"] in self.get_file_type(fname):
                matches.append(d)
        return matches

    def _load_verifier(self):
        # only one verifier supported right now (do we really need others?)
        if self.conf.verify:
            self.verifier = IAutoVerify(self.conf)
        else:
            self.verifier = None

    def _load_dbs(self):
        for dest in self.conf.dest_dirs:
            loaded_dbs = []
            dlist = self.conf.dest_dirs[dest]["db"]
            for db in self.conf.dbs[dlist]:
                try:
                    mod = importlib.import_module(db)
                    loaded_dbs.append(mod.AutoDB(self.conf, dest))
                    self.log(
                        "Database plugin '{}' loaded".format(loaded_dbs[-1]),
                        part="plugins",
                    )
                except Exception as e:
                    self.log(e)
                    raise e
            self.dbs[dlist] = loaded_dbs

    def _load_notifier(self):
        if self.conf.note and self.conf.note.get("module"):
            try:
                mod = importlib.import_module(self.conf.note["module"])
                self.note = mod.AutoNotify(self.conf)
            except Exception as e:
                self.log(e)
                raise e
        else:
            self.note = IAutoNotify(self.conf)
        self.log("Notifier plugin '{}' loaded".format(self.note), part="plugins")

    def get_tags(self, ftype, mfile):
        tags = []
        if self.dbs[ftype]:
            for d in self.dbs[ftype]:
                self.log("\tSearching db {}".format(d), part="search")
                tags.append(d.search(mfile))
        return tags

    def move(self, matches):
        for mfile in matches:
            if mfile.tags:
                new_path = self.get_dest(mfile)
                if new_path:
                    self.log(
                        "Found match for '{}' in '{}'".format(mfile, new_path),
                        part="move",
                    )
                    if self._copy(mfile, new_path):
                        self._delete(mfile)
                        self.note.add("Copied '{}' to '{}'".format(mfile, new_path))
                    else:
                        self.note.add("Copy failed for '{}'".format(mfile))
            else:
                if self.conf.note.get("when no tags", False):
                    self.note.add("No tags for '{}'".format(mfile))

    def _copy(self, mfile, dst):
        # check if exists
        # if os.path.isdir(dst)
        # TODO create directory!?
        if not os.path.isdir(dst) and self.conf.mkdir:
            if self.conf.dry_run:
                self.log("DRY RUN: Would create directory '{}'".format(dst))
            else:
                self.log("Creating directory '{}'".format(dst))
                os.makedirs(dst)
        dst = os.path.join(dst, mfile.fname)
        if os.path.isfile(dst):
            if self.conf.overwrite:
                # copy anyway
                if self.conf.dry_run:
                    self.log("DRY RUN: Would overwrite '{}'".format(mfile))
                else:
                    shutil.copyfile(mfile.full_path, dst)
                    if self.conf.verify:
                        if not self.verifier.verify(mfile.full_path, dst):
                            self.log(
                                "Failed to copy (overwrite) '{}' to '{}'".format(
                                    mfile, dst
                                )
                            )
                            return False
                    self.log("Copied '{}' to '{}' (OVERWROTE)".format(mfile, dst))
            else:
                self.log("Not overwriting '{}' in '{}'".format(mfile, dst))
                return False
        else:
            if self.conf.dry_run:
                self.log("DRY RUN: Would copy '{}' to '{}'".format(mfile, dst))
            else:
                shutil.copyfile(mfile.full_path, dst)
                if self.conf.verify:
                    if not self.verifier.verify(mfile.full_path, dst):
                        self.log("Failed to copy '{}' to '{}'".format(mfile, dst))
                        return False
                self.log("Copied '{}' to '{}'".format(mfile, dst))
        return True

    def _delete(self, mfile):
        if self.conf.delete:
            if self.conf.dry_run:
                self.log("DRY RUN: would delete '{}'".format(mfile))
            else:
                self.log("(Not) deleting '{}'".format(mfile))
        else:
            self.log("Not deleteing '{}'".format(mfile))

    def get_dest(self, mfile):
        if len(mfile.ftypes) > 1:
            self.log("{} has more than one type".format(mfile), part="move")

        ftype = mfile.ftypes[0]
        org_tags = self.conf.dest_dirs[ftype]["org"].split("/")
        path = self.conf.dest_dirs[ftype]["path"]

        # find each part of org to assemble path
        # list of {tag name: {name: hits}}
        # [{'series': {'Stranger Things': 2}}]
        for o in org_tags:
            org_matches = [x[o].keys()[0] for x in mfile.tags if x[o] and o in x]
            if len(org_matches) == 1:
                path = os.path.join(path, org_matches[0])
                self.log(
                    "Found {} match for '{}' as '{}'".format(o, mfile, org_matches[0]),
                    part="move",
                )
            else:
                self.log(
                    "Too many matches for '{}' for '{}'".format(o, mfile), part="move"
                )
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


def cli():
    am = Automove(Config(get_args=True))
    am.run()


if __name__ == "__main__":
    cli()
