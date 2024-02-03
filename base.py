import os

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

class MediaFile:
    def __init__(self, fname, ftypes=None, tags=None, mime=None):
        self.full_path = fname
        self.path, self.fname = os.path.split(fname)
        self.ftypes = ftypes if ftypes else []
        self.mime = mime
        self.tags = tags if tags else []

    def __str__(self):
        return self.fname