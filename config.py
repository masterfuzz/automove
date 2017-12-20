import os
import yaml

class Config:
    def __init__(self, get_args=False):
        if get_args:
            self._get_args()
        else:
            self._load(self._get_conf())

    def _load(self, conf_file):
        with open(conf_file) as f:
            y = yaml.load(f)

        self.raw_conf = y
        self.src_dirs = y["Sources"]
        self.dest_dirs = y["Destinations"]
        self.dbs = y["Databases"]
        self.note = y["Notifications"]
        if 'Transfer' in y:
            self.overwrite = y['Transfer'].get('overwrite', False)
            self.delete = y['Transfer'].get('delete', False)
            self.dry_run = y['Transfer'].get('dry run', False)
            self.verify = y['Transfer'].get('verify', False)
            self.mkdir = y['Transfer'].get('make dir', False)
        else:
            self.overwrite = False
            self.delete = False
            self.dry_run = False
            self.verify = False
            self.mkdir = False

    def _get_args(self):
        import argparse
        ap = argparse.ArgumentParser(description="Automove")
        ap.add_argument("--conf", "-c", action="store",
                help="Use a specific configuration file")

        args = ap.parse_args()

        if args.conf:
            self._load(args.conf)
        else:
            self._load(self._get_conf())

    def _get_conf(self):
        # conf search order
        search = [
                "./automove.yaml",
                "{XDG_CONFIG_HOME}/automove/conf.yaml",
                "{HOME}/.config/automove/conf.yaml",
                "/etc/automove/conf.yaml"
                ]
        for s in search:
            try:
                s = s.format(**os.environ)
            except:
                continue
            if os.path.isfile(s):
                return s

        raise Exception("No configuration file found")

