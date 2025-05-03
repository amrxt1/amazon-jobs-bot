"""

The Notifying Telegram obj

"""

import requests
import yaml


class Notifier:
    def __init__(self):
        self.cfg = self.config()

    def config(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config["telegram"]

    def notfy(self, message):
        url = self.cfg["url"]
        params = {"chat_id": self.cfg["chat_id"], "text": message}
        requests.get(url + "/sendMessage", params=params)


n = Notifier()
n.notfy("Kiidaaa Sengghhhh!")
