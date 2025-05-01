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
    print("Clicked consent")

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
    print("Entered email")
    driver.find_element(
        By.XPATH, '//*[@id="pageRouter"]/div/div/div[2]/div[1]/button'
    ).click()
    print("Prompting PIN")
    print("entered PIN\n")

    # enter PIN
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="pin"]'))
    )
    pin = driver.find_element(By.CSS_SELECTOR, "#pin")
    pin.click()
    pin.send_keys(cfg["creds"]["pin"])
    driver.find_element(By.XPATH, '//*[@id="pageRouter"]/div/div/div/button').click()
    print("Prompting OTP")
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

    time.sleep(200)
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
