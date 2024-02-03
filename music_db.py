import base
import eyed3


class AutoDB(base.IAutoDB):
    def search(self, mfile):
        # first check eyed3
        try:
            eye = eyed3.load(mfile.full_path)
            artist = eye.tag.artist
            title = eye.tag.title
            album = eye.tag.album
        except Exception as e:
            # no id3 i guess
            print(e)
            return []

        return {"artist": {artist: 1}, "album": {album: 1}, "title": {title: 1}}

    def __str__(self):
        return "MusicDB"
