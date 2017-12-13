import automove


class AutoDB(automove.IAutoDB):
    def __init__(self, conf, dest=None):
        super(AutoDB, self).__init__(conf, dest)
        
        if dest:
            # load tags from filesystem
            

    def search(self, fname):





