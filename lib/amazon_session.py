"""

The Amazon Session object.

"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import requests
import imaplib
import logging
import email
import yaml
import time
import re
import os


class AmazonSession:
    def __init__(self, user, notifier, region="us"):
        self.name = user["name"]
        self.login = user["login"]
        self.pin = user["pin"]

        self.imap_conf = user["imap"]
        self.notifier = notifier

        self.conf = self.config()
        self.driver = self.build_driver()
        self.session = requests.Session()
        self.candidate_id = None
        self.application = {}

        self.region = region

    def config(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config

    def build_driver(self):
        opts = Options()

        chrome_bin = "/usr/bin/google-chrome-stable"
        opts.binary_location = chrome_bin

        profile_root = self.conf["chromedriver"]["profiles_root"]
        os.makedirs(profile_root, exist_ok=True)
        data_dir = os.path.join(profile_root, f"profile_{self.login}1")
        opts.add_argument(f"--user-data-dir={data_dir}")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--disable-blink-features=AutomationControlled")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=opts)

        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )

        return driver

    def fetch_amazon_otp(self, imap_conf, since_seconds=120):
        M = imaplib.IMAP4_SSL(imap_conf["host"], imap_conf["port"])
        M.login(imap_conf["user"], imap_conf["pass"])
        M.select(imap_conf.get("folder", "INBOX"))

        logging.info("Fetching otp from email...")
        typ, data = M.search(None, '(UNSEEN FROM "no-reply@jobs.amazon.com")')
        if typ != "OK":
            return None

        for num in reversed(data[0].split()):
            typ, msg_data = M.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            m = re.search(r"\b(\d{6})\b", body)
            if m:
                M.store(num, "+FLAGS", "\\Seen")
                M.logout()
                return m.group(1)
        return None

    def _login(self):
        logging.info("Log in initiated...")
        logging.info("Navigating to login page...")
        cfg = self.conf
        driver = self.driver

        CONSENT_XPATH = (
            "/html/body/div[3]/div/div[2]/div/div/div/div/div/div/div/div[2]/button"
        )
        LOGIN_CSS = "#login"

        driver.get(cfg["url"][f"login_url_{self.region}"])

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_CSS))
        )

        # Look for and click on consent
        try:
            driver.find_element(By.XPATH, CONSENT_XPATH).click()
            logging.info("Gained consent!")
        except Exception:
            logging.warning("Did not see a consent btn!")

        # enter email
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_CSS))
        )
        email = driver.find_element(By.CSS_SELECTOR, LOGIN_CSS)
        email.click()
        email.send_keys(self.login)
        logging.info("Email entered!")
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div[2]/div[1]/button'
        ).click()
        logging.info("Approaching PIN...")

        # enter PIN
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pin"]'))
        )
        pin = driver.find_element(By.CSS_SELECTOR, "#pin")
        pin.click()
        pin.send_keys(self.pin)
        logging.info("PIN entered!")
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div/button'
        ).click()
        logging.info("Approaching OTP...")
        time.sleep(5)
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div/button'
        ).click()

        time.sleep(7)

        otp = self.fetch_amazon_otp(self.imap_conf)
        if otp:
            logging.info(f"****OTP fetched: {otp}")
        else:
            n = self.notifier
            n.notify(
                f"TYPE: LOGIN-HELP\nYou need to enter otp for {self.name} with email: {self.login}"
            )
            otp = input("****Couldn’t fetch OTP—please enter manually:\n> ")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '[data-test-id="input-test-id-confirmOtp"]')
            )
        )

        otp_input = driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="input-test-id-confirmOtp"]'
        )
        otp_input.click()
        otp_input.send_keys(str(otp))
        logging.info("OTP entered!")

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

        resp = self.session.post(
            self.conf["url"][f"create_app_url_{self.region}"], json=body
        )
        resp.raise_for_status()

        logging.info("RESPONSE:\n\n")
        logging.info(resp)

        data = resp.json().get("data", {})

        return data

    def update_application(self, jobId, scheduleId, applicationId):
        self.set_headers_with_fresh_tokens()
        if self.candidate_id is None:
            self.set_candidate()

        body = {
            "applicationId": applicationId,
            "type": "job-confirm",
            "dspEnabled": True,
            "payload": {"jobId": jobId, "scheduleId": scheduleId},
        }
        resp = self.session.put(
            self.conf["url"][f"update_app_url_{self.region}"], json=body
        )
        resp.raise_for_status()

        logging.info("RESPONSE:\n\n")
        logging.info(resp)

        data = resp.json().get("data", {})

        return data

    def update_workflow(self, applicationId):
        self.set_headers_with_fresh_tokens()
        if self.candidate_id is None:
            self.set_candidate()

        body = {
            "applicationId": applicationId,
            "workflowStepName": "general-questions",
        }
        resp = self.session.put(
            self.conf["url"][f"update_flow_url_{self.region}"], json=body
        )
        resp.raise_for_status()

        logging.info("RESPONSE:\n\n")
        logging.info(resp)

        data = resp.json().get("data", {})

        return data

    def start_timer(self):
        url = self.conf["url"][f"my_applications_{self.region}"]
        logging.info(f"Initiating timer for {self.name}")
        try:
            self.driver.get(url)
            logging.info("Arrived at url, awaiting my jobs to appear")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="pageRouter"]/div/div/div[2]/div[1]/div/div',
                    )
                )
            )
            logging.info(f"My jobs loaded {url}")
        except Exception as e:
            logging.exception("Navigation to timer failed:", e)

        logging.info("Awaiting jobs to appear.")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[normalize-space(.)="Select Shift"]')
            )
        )
        select_shift = self.driver.find_element(
            By.XPATH, '//*[normalize-space(.)="Select Shift"]'
        )

        select_shift.click()
        logging.info("Clicked on the job")

        logging.info("Awaiting Schedules to appear.")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[normalize-space(.)="Start Date:"]')
            )
        )
        logging.info("A schedule appeared")
        element = self.driver.find_element(
            By.XPATH, '//*[normalize-space(.)="Start Date:"]'
        )
        element.click()
        logging.info("Clicked on the first schedule")

        logging.info("Awaiting select job btn to appear.")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="root"]/div[1]/div/div/main/div/div/div[4]/button')
            )
        )
        logging.info("btn appeared")
        element = self.driver.find_element(
            By.XPATH, '//*[@id="root"]/div[1]/div/div/main/div/div/div[4]/button'
        )

        element.click()
        logging.info("Clicked on the first schedule")
        logging.info("Run succesful. TImer started!\n")
