"""

The Amazon Session object.

"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
import yaml
import time


class AmazonSession:
    def __init__(self):
        self.conf = self.config()
        self.driver = self.build_driver()

    def config(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config

    def build_driver(self):
        # options = Options()
        # options.add_argument(f"--window-size={windowSize}")
        # options.add_argument(
        #     "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        #     "AppleWebKit/537.36 (KHTML, like Gecko) "
        #     "Chrome/136.0.0.0 Safari/537.36"
        # )
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option("useAutomationExtension", False)
        # options.add_argument("--disable-blink-features=AutomationControlled")

        # if isHeadless:
        #     options.add_argument("--headless")
        driver = uc.Chrome(use_subprocess=False)
        # driver.execute_cdp_cmd(
        #     "Page.addScriptToEvaluateOnNewDocument",
        #     {
        #         "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        #     },
        # )
        # driver.execute_cdp_cmd(
        #     "Network.setExtraHTTPHeaders",
        #     {"headers": {"Cache-Control": "no-cache", "Pragma": "no-cache"}},
        # )
        driver.execute_cdp_cmd(
            "Network.setExtraHTTPHeaders",
            {"headers": {"Cache-Control": "no-cache", "Pragma": "no-cache"}},
        )

        return driver

    def login(self, driver, cfg):
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

        # enter PIN
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pin"]'))
        )
        pin = driver.find_element(By.CSS_SELECTOR, "#pin")
        pin.click()
        pin.send_keys(cfg["creds"]["pin"])
        print("PIN entered!")
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div/button'
        ).click()
        print("Approaching OTP...")
        time.sleep(5)
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div/button'
        ).click()

        # solve captchas and recieve otp
        print("When you have finished the captcha, Check your email for OTP.")
        otp = input("Enter the OTP, then press Enter to continue.\n\n> ")
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
