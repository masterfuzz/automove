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
        print("tokens: {}".format(tokens))
        for tag in self.tags:
            for name in self.db[tag]:
                score = 0
                for t in tokens:
                    if t in name.lower():
                        #print("hit {}".format(t))
                        score += 1
                if score > 0:
                    print("HITx{} {}/{}".format(score, tag, name))
                    ret[tag][name] = score
        return ret

    def tokenize(self, name):
        return [t for t in re.split('[^a-zA-Z0-9]', name.lower()) if t]

    def __str__(self):
        if self.dest:
            return "LocalDB<{}>".format(self.dest)
        else:
            return "LocalDB<NULL>"



ldb = AutoDB(automove.Config("conf.yaml"), dest='TV')
#mdb = AutoDB(automove.Config("conf.yaml"), dest='MUSIC')

