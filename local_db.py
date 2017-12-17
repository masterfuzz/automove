import automove
import os
import re


class AutoDB(automove.IAutoDB):
    def __init__(self, conf, dest=None):
        super(AutoDB, self).__init__(conf, dest)
        
        if dest:
            org = conf.dest_dirs[dest]['org']
            if org:
                path = conf.dest_dirs[dest]['dir']
                self.tags = org.split('/')
                self.db = {}
                for t in self.tags:
                    self.db[t] = []

                self.load_tags(path, self.tags)
            
    def load_tags(self, path, tags):
        if not tags:
            return
        print("Loading {}".format(path))

        for x in os.listdir(path):
            if os.path.isdir(os.path.join(path,x)):
                print("[{}] add {}".format(tags[0], x))
                self.db[tags[0]].append(x)
                self.load_tags(os.path.join(path, x), tags[1:])

    def search(self, fname):
        if not self.tags:
            print("no tags so no results")
            return None
        ret = {x: {} for x in self.tags}
        tokens = self.tokenize(fname)
        for tag in self.tags:
            for name in self.db[tag]:
                score = 0
                for t in tokens:
                    if t in name.lower():
                        score += 1
                if score > 0:
                    ret[tag][name] = score
        return ret

    def tokenize(self, name):
        return re.split('[^a-zA-Z]', name.lower())



#ldb = AutoDB(automove.Config("conf.yaml"), dest='TV')
#mdb = AutoDB(automove.Config("conf.yaml"), dest='MUSIC')

