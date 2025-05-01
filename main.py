from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import time
import yaml
import os
from dotenv import load_dotenv

LOGIN_URL = "https://auth.hiring.amazon.com/#/login"


def telegram(link):
    body = f"Go to: {'some prefix' + link}"

    print("Sending to TELEGRAM")

    url = os.getenv("URL")
    params = {"chat_id": os.getenv("CHAT_ID"), "text": body}
    r = requests.get(url + "/sendMessage", params=params)

    print(r.url)
    print("Sent on TELEGRAM")


def build_driver(chromedriver_path, isHeadless, windowSize):
    options = Options()
    options.add_argument(f"--window-size={windowSize}")
    if isHeadless:
        options.add_argument("--headless")
    return webdriver.Chrome(
        service=Service(executable_path=chromedriver_path), options=options
    )


def initialize():
    load_dotenv()
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)
    driver = build_driver(
        config["chrome"]["driver_path"],
        config["chrome"]["headless"],
        config["chrome"]["window_size"],
    )

    return config, driver


def main():
    cfg, drv = initialize()
    try:
        drv.get(cfg["url"]["login_url"])
        # FLOW
        # Login
        # prompt for otp
        # start checking
        # go to the job page, if there is one
        # select a shift
        # create application
        # NOTIFY
    except Exception as e:
        print(e)
    finally:
        drv.quit()


main()
