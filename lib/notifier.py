"""

The Notifying Telegram obj

"""

import requests
import logging
import yaml


class Notifier:
    def __init__(self):
        self.cfg = self.config()

    def config(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config["telegram"]

    def notify(self, message):
        url = self.cfg["url"]
        requests.get(
            url + "/sendMessage",
            params={"chat_id": self.cfg["chat_id"], "text": message},
        )
        # requests.get(
        #     url + "/sendMessage",
        #     params={"chat_id": self.cfg["chat_id_lv"], "text": message},
        # )
        # requests.get(
        #     url + "/sendMessage",
        #     params={"chat_id": self.cfg["chat_id_am"], "text": message},
        # )
        logging.info(f"NOTIFIER: {message}")
