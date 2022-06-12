import automove
import pushbullet


class AutoNotify(automove.IAutoNotify):
    def __init__(self, conf):
        super(AutoNotify, self).__init__(conf)

        # get api key
        if "api key" in self.params:
            self.key = self.params["api key"]
        elif "keyring user" in self.params:
            import keyring
            import keyrings.alt

            keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
            self.key = keyring.get_password(*self.params["keyring user"])

        # init pushbullet
        self.pb = pushbullet.PushBullet(self.key, proxy=self.params.get("proxy", None))

    def send(self, body, title=None):
        super(AutoNotify, self).send(body, title)

        if title:
            self.pb.push_note(title, body)
        else:
            self.pb.push_note("Automove", body)

    def __str__(self):
        return "AutoNotify<PushBullet>"


# pb = AutoNotify(automove.Config("conf.yaml"))
