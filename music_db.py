
import automove
import eyed3


class AutoDB(automove.IAutoDB):
    def search(self, fname):
        # first check eyed3
        try:
            eye = eyed3.load(fname)
            artist = eye.tag.artist
            title = eye.tag.title
            album = eye.tag.album
        except Exception as e:
            # no id3 i guess
            print(e)

        return {'artist': artist, 'album': album, 'title': title}




