import requests
import os
from dotenv import load_dotenv

load_dotenv()


def telegram(link):
    body = f"Go to: {'some prefix' + link}"

    print("Sending to TELEGRAM")

    url = os.getenv("URL")
    params = {"chat_id": os.getenv("CHAT_ID"), "text": body}
    r = requests.get(url + "/sendMessage", params=params)

    print(r.url)
    print("Sent on TELEGRAM")
