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
    body = f"New Amazon job posted:\n{link}"
    url = os.getenv("URL")
    params = {"chat_id": os.getenv("CHAT_ID"), "text": body}
    requests.get(url + "/sendMessage", params=params)


def build_driver(chromedriver_path, isHeadless, windowSize):
    options = Options()
    options.add_argument(f"--window-size={windowSize}")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    if isHeadless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(executable_path=chromedriver_path), options=options
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        },
    )
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {"headers": {"Cache-Control": "no-cache", "Pragma": "no-cache"}},
    )

    return driver


def initialize():
    load_dotenv()
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)
    driver = build_driver(
        config["chrome"]["driver_path"],
        config["chrome"]["headless"],
        config["chrome"]["window_size"],
    )
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {"headers": {"Cache-Control": "no-cache", "Pragma": "no-cache"}},
    )

    return config, driver


def login(driver, cfg):
    print("\t\tLogging in...")
    print("Navigating to login page...")
    driver.get(cfg["url"]["login_url"])

    # Look for and click on consent
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button",
            )
        )
    )
    driver.find_element(
        By.XPATH,
        "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button",
    ).click()
    print("Gained consent!")

    # Uncomment if need to select a country
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

    # enter email
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="login"]'))
    )
    email = driver.find_element(By.CSS_SELECTOR, "#login")
    email.click()
    email.send_keys(cfg["creds"]["email"])
    print("Email entered!")
    driver.find_element(
        By.XPATH, '//*[@id="pageRouter"]/div/div/div[2]/div[1]/button'
    ).click()
    print("Approaching PIN...")

    # enter PIN        print("\t\tLogging in...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="pin"]'))
    )
    pin = driver.find_element(By.CSS_SELECTOR, "#pin")
    pin.click()
    pin.send_keys(cfg["creds"]["pin"])
    print("PIN entered!")
    driver.find_element(By.XPATH, '//*[@id="pageRouter"]/div/div/div/button').click()
    print("Approaching OTP...")
    time.sleep(5)
    driver.find_element(By.XPATH, '//*[@id="pageRouter"]/div/div/div/button').click()

    # solve captchas and recieve otp
    print("Captcha should be on the screen now. Please solve it in the browser.")
    print("When you have finished the captcha, Check your email for OTP.")
    otp = input("Enter the OTP, then press ↵ Enter to continue.\n\n> ")
    # look for otp input
    WebDriverWait(driver, 300).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '[data-test-id="input-test-id-confirmOtp"]')
        )
    )

    otp_input = driver.find_element(
        By.CSS_SELECTOR, '[data-test-id="input-test-id-confirmOtp"]'
    )
    otp_input.click()
    otp_input.send_keys(otp)
    print("OTP entered!")

    return -1


def fetch_jobs(driver):
    print("\nFetching for jobs...")
    token = driver.execute_script("return window.localStorage.getItem('sessionToken')")
    if not token:
        raise RuntimeError("sessionToken not found in localStorage")

    # GraphQL request
    url = (
        "https://e5mquma77feepi2bdn4d6h3mpu.appsync-api.us-east-1.amazonaws.com/graphql"
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Authorization": f"Bearer {token}",
        "Country": "United States",
    }
    body = {
        "operationName": "searchJobCardsByLocation",
        "variables": {
            "searchJobRequest": {
                "locale": "en-US",
                "country": "United States",
                "keyWords": "",
                "equalFilters": [
                    {"key": "shiftType", "val": "All"},
                    {"key": "scheduleRequiredLanguage", "val": "en-US"},
                ],
                "containFilters": [
                    {"key": "isPrivateSchedule", "val": ["false"]},
                    {
                        "key": "jobTitle",
                        "val": [
                            "Amazon Fulfillment Center Warehouse Associate",
                            "Amazon Sortation Center Warehouse Associate",
                            "Amazon Delivery Station Warehouse Associate",
                            "Amazon Distribution Center Associate",
                            "Amazon Grocery Warehouse Associate",
                            "Amazon Air Associate",
                            "Amazon Warehouse Team Member",
                            "Amazon XL Warehouse Associate",
                        ],
                    },
                ],
                "rangeFilters": [
                    {"key": "hoursPerWeek", "range": {"minimum": 0, "maximum": 80}}
                ],
                "dateFilters": [
                    {"key": "firstDayOnSite", "range": {"startDate": "2025-05-01"}}
                ],
                "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
                "pageSize": 100,
                "consolidateSchedule": True,
            }
        },
        "query": """
          query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
            searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
              jobCards {
                jobId
                jobTitle
                city
                state
                totalPayRateMax
              }
            }
          }
        """,
    }
    print("Built request...")
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()["data"]["searchJobCardsByLocation"]["jobCards"]
    print("Response recieved...\n")
    return data


def main():
    cfg, driver = initialize()

    try:
        login(driver, cfg)

        seen = set()
        interval = cfg["interval"]

        print(f"\nFetching every {interval}s for new jobs…")
        while True:
            try:
                jobs = fetch_jobs(driver)
            except Exception:
                # if token expired or network error, re-login
                print("Fetch failed. Logging in...")
                login(driver, cfg)
                jobs = fetch_jobs(driver)

            for job in jobs:
                jid = job["jobId"]
                if jid not in seen:
                    seen.add(jid)
                    link = f"https://hiring.amazon.com/app#/jobDetail?jobId={jid}"
                    telegram(link)
                    print(f"\tSent: {link}")

            print(f"Sleeping for {interval}s…\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nGracefully Exiting...")
    except Exception:
        print("\n\n\tGAME \tO V E R")
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
