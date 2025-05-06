"""

The Amazon Session object.

"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
import requests
import yaml
import time
import os


class AmazonSession:
    def __init__(self, login, pin):
        self.login = login
        self.pin = pin
        self.conf = self.config()
        self.driver = self.build_driver()
        self.session = requests.Session()
        self.candidate_id = None
        self.application = {}

    def config(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config

    def build_driver(self):
        opts = Options()

        chrome_bin = "/usr/bin/google-chrome-stable"
        opts.binary_location = chrome_bin

        profile_root = "/home/amrit/.config/amazon-bot-profiles"
        os.makedirs(profile_root, exist_ok=True)
        data_dir = os.path.join(profile_root, f"profile_{self.login}1")
        opts.add_argument(f"--user-data-dir={data_dir}")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(
            "/usr/bin/chromedriver"
        )  # make sure this matches your Chrome version
        driver = webdriver.Chrome(service=service, options=opts)

        # driver.execute_cdp_cmd(
        #     "Network.setExtraHTTPHeaders",
        #     {"headers": {"Cache-Control": "no-cache", "Pragma": "no-cache"}},
        # )
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )

        return driver

    def _login(self):
        print("\t\tLogging in...")
        print("Navigating to login page...")
        cfg = self.conf
        driver = self.driver

        CONSENT_XPATH = (
            "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button"
        )
        LOGIN_CSS = "#login"

        driver.get(cfg["url"]["login_url"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_CSS))
        )

        # Look for and click on consent
        try:
            driver.find_element(By.XPATH, CONSENT_XPATH).click()
            print("Gained consent!")
        except Exception:
            print("Not found")

        # enter email
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_CSS))
        )
        email = driver.find_element(By.CSS_SELECTOR, LOGIN_CSS)
        email.click()
        email.send_keys(self.login)
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
        pin.send_keys(self.pin)
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

        return True

    def sessionToken(self):
        script = """
          const entry = Object.entries(localStorage)
            .find(([key, _]) => key.endsWith('sessionToken'));
          return entry ? entry[1] : null;
        """
        return self.driver.execute_script(script)

    def idToken(self):
        script = """
          const entry = Object.entries(localStorage)
            .find(([key, _]) => key.endsWith('idToken'));
          return entry ? entry[1] : null;
        """
        return self.driver.execute_script(script)

    def accessToken(self):
        script = """
          const entry = Object.entries(localStorage)
            .find(([key, _]) => key.endsWith('accessToken'));
          return entry ? entry[1] : null;
        """
        return self.driver.execute_script(script)

    def set_candidate(self):
        # use dummy values to imitate request creation
        # self.candidate_id = "87af95e0-abac-11ee-accf-dbe181f4485b"
        # return -1
        script = """
          const entry = Object.entries(localStorage)
            .find(([key, _]) => key.endsWith('bbCandidateId'));
          return entry ? entry[1] : null;
        """
        self.candidate_id = self.driver.execute_script(script)

    def set_headers_with_fresh_tokens(self):
        self.session.headers.update(
            {
                "Authorization": self.accessToken(),
                "Content-Type": "application/json;charset=UTF-8",
            }
        )
        return True

    def create_application(self, jobId, scheduleId):
        # prepare session
        self.set_headers_with_fresh_tokens()
        if self.candidate_id is None:
            self.set_candidate()

        body = {
            "jobId": jobId,
            "dspEnabled": True,
            "scheduleId": scheduleId,
            "candidateId": self.candidate_id,
            "activeApplicationCheckEnabled": True,
        }

        resp = self.session.post(self.conf["url"]["create_app_url"], json=body)
        resp.raise_for_status()

        print("RESPONSE:\n\n")
        print(resp)

        data = resp.json().get("data", {})

        return data

    def update_application(self, jobId, scheduleId, applicationId):
        # prepare session
        self.set_headers_with_fresh_tokens()
        if self.candidate_id is None:
            self.set_candidate()

        body = {
            "applicationId": applicationId,
            "type": "job-confirm",
            "dspEnabled": True,
            "payload": {"jobId": jobId, "scheduleId": scheduleId},
        }
        resp = self.session.put(self.conf["url"]["update_app_url"], json=body)
        resp.raise_for_status()

        print("RESPONSE:\n\n")
        print(resp)

        data = resp.json().get("data", {})

        return data

    def update_workflow(self, applicationId):
        # prepare session
        self.set_headers_with_fresh_tokens()
        if self.candidate_id is None:
            self.set_candidate()

        body = {
            "applicationId": applicationId,
            "workflowStepName": "general-questions",
        }
        resp = self.session.put(self.conf["url"]["update_flow_url"], json=body)
        resp.raise_for_status()

        print("RESPONSE:\n\n")
        print(resp)

        data = resp.json().get("data", {})

        return data

    def nav_to_timer_page(self):
        url = self.conf["url"]["my_applications"]
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="StencilTabPanel-myApplicationTab-active-panel"]/div/div[1]/div[2]/b',
                    )
                )
            )
            print("Browser keep-alive hit:", url)
            self.set_headers_with_fresh_tokens()
        except Exception as e:
            print("Keep-alive navigation failed:", e)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="StencilTabPanel-myApplicationTab-active-panel"]/div/div[1]/div[1]/div/div/div[2]/div[2]/div[11]/button[1]',
                )
            )
        )
        select_shift = self.driver.find_element(
            By.XPATH,
            '//*[@id="StencilTabPanel-myApplicationTab-active-panel"]/div/div[1]/div[1]/div/div/div[2]/div[2]/div[11]/button[1]',
        )
        select_shift.click()
