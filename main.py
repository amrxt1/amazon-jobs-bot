from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from dotenv import load_dotenv
import traceback
import requests
import time
import yaml
import os


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


def login(driver, cfg):
    print("Navigating to login page...")
    driver.get(cfg["url"]["login_url"])
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button",
            )
        )
    )
    consent = driver.find_element(
        By.XPATH,
        "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button",
    )
    consent.click()
    print("Clicked consent")

    # WebDriverWait(driver, 10).until(
    #     EC.visibility_of_element_located(
    #         (By.CSS_SELECTOR, cfg["selectors"]["login"]["country_input"])
    #     )
    # )
    # print("Found country selection")
    # country_input = driver.find_element(
    #     By.CSS_SELECTOR, cfg["selectors"]["login"]["country_input"]
    # )
    # country_input.click()
    driver.quit()
    return -1


def main():
    cfg, drv = initialize()
    try:
        # FLOW
        # Login
        print("\n\tSTEP1. LOGIN:")
        login(drv, cfg)
        # prompt for otp
        # start checking
        # go to the job page, if there is one
        # select a shift
        # create application
        # NOTIFY
        print("\nSuccessful run!!")
    except Exception as e:
        print("Something ain't right\nTraceback:\n")
        # print(e)
        traceback.print_exc()
    finally:
        drv.quit()


main()
