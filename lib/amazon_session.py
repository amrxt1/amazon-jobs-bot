"""

The Amazon Session object.

"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import email.utils
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

        self.check = user["check"]

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

    def fetch_amazon_otp(self, imap_conf, since_seconds=15, wait_for=3):
        logging.info("Fetching otp from email...")
        time.sleep(wait_for)
        M = imaplib.IMAP4_SSL(imap_conf["host"], imap_conf["port"])
        M.login(imap_conf["user"], imap_conf["pass"])
        M.select(imap_conf.get("folder", "INBOX"))
        typ, data = M.search(None, '(UNSEEN FROM "no-reply@jobs.amazon.com")')
        logging.info(f"IMAP response: {typ}")
        if typ != "OK":
            logging.warning(f"IMAP response: {typ}")
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

        # send otp
        logging.info("Awaiting send OTP button...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="pageRouter"]/div/div/div/button')
            )
        )
        time.sleep(3)
        driver.find_element(
            By.XPATH, '//*[@id="pageRouter"]/div/div/div/button'
        ).click()

        logging.info("Awaiting confirm OTP dialog...")
        try:
            WebDriverWait(driver, 150).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-id="input-test-id-confirmOtp"]')
                )
            )
        except Exception:
            logging.exception("Captcha error probably")
            self.notifier.notify(
                f"Agent failed during login {self.name} could not get to confirmOtp\nCaptcha error probably"
            )

        otp = self.fetch_amazon_otp(self.imap_conf)
        if otp:
            logging.info(f"****OTP fetched: {otp}")
        else:
            self.notifier.notify(
                f"You need to manually enter otp for {self.name} with email: {self.login}"
            )
            otp = input("****Couldn’t fetch OTP—please enter manually:\n> ")

        # entering otp below
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

    def aws_authenticated_request(
        self,
        url,
        body,
        method,
        caller="caller_function_name",
        max_retries=5,
        timeout=11,
    ):
        """
        Imitates an authenticated call to the amazon-hiring backend api
        """
        if not self.candidate_id:
            self.set_candidate()
        for attempt in range(1, max_retries + 1):
            self.set_headers_with_fresh_tokens()

            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    json=body,
                    timeout=timeout,
                )
            except requests.exceptions.RequestException as e:
                logging.warning(f"Attempt {attempt}: request failed — {e}")
                continue

            if resp.status_code == 401:
                logging.warning("Unauthorized. Logging in and retrying...")
                self._login()
                continue

            if resp.status_code == 200:
                logging.info(f"{caller}() successful")
                logging.info(resp)
                return resp.json().get("data", {})

            logging.warning(
                f"Attempt {attempt}: unexpected status {resp.status_code} — {resp.text}"
            )

        raise Exception(f"{caller}() failed after all retries")

    def create_application(self, jobId, scheduleId, max_retries=5, timeout=11):
        body = {
            "jobId": jobId,
            "dspEnabled": True,
            "scheduleId": scheduleId,
            "candidateId": self.candidate_id,
            "activeApplicationCheckEnabled": True,
        }
        return self.aws_authenticated_request(
            self.conf["url"][f"create_app_url_{self.region}"],
            body=body,
            method="POST",
            caller="create_application",
        )

    def update_application(
        self, jobId, scheduleId, applicationId, max_retries=5, timeout=11
    ):
        body = {
            "applicationId": applicationId,
            "type": "job-confirm",
            "dspEnabled": True,
            "payload": {"jobId": jobId, "scheduleId": scheduleId},
        }
        return self.aws_authenticated_request(
            self.conf["url"][f"update_app_url_{self.region}"],
            body=body,
            method="PUT",
            caller="update_application",
        )

    def update_workflow(self, applicationId):
        body = {
            "applicationId": applicationId,
            "workflowStepName": "general-questions",
        }
        return self.aws_authenticated_request(
            self.conf["url"][f"update_flow_url_{self.region}"],
            body=body,
            method="PUT",
            caller="update_workflow",
        )

    def start_timer(self):
        url = self.conf["url"][f"my_applications_{self.region}"]
        logging.info(f"Initiating timer for {self.name}")

        try:
            try:
                self.driver.get(url)
                logging.info("Arrived at url, awaiting my jobs to appear")
                WebDriverWait(self.driver, 200).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-test-id="activeMyApplicationTabItem"]')
                    )
                )
                logging.info(f"My jobs loaded {url}")
            except Exception:
                logging.exception("Navigation to timer failed")

            logging.info("Awaiting 'Select Shift' button to appear.")
            WebDriverWait(self.driver, 200).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[normalize-space(.)="Select Shift"]')
                )
            )
            select_shift = self.driver.find_element(
                By.XPATH, '//*[normalize-space(.)="Select Shift"]'
            )

            select_shift.click()
            logging.info("Clicked on Select Shift")

            logging.info("Awaiting Schedules to appear.")
            WebDriverWait(self.driver, 200).until(
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
            WebDriverWait(self.driver, 200).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="root"]/div[1]/div/div/main/div/div/div[4]/button',
                    )
                )
            )
            logging.info("btn appeared")
            element = self.driver.find_element(
                By.XPATH, '//*[@id="root"]/div[1]/div/div/main/div/div/div[4]/button'
            )

            element.click()
            logging.info("Clicked on the first schedule")
            self.notifier.notify(
                f"Run succesful. TImer started!\nClosing driver for {self.name}."
            )
            self.check = False
            time.sleep(3)
        except Exception:
            logging.exception(
                f"Unable to Navigate to timer for {self.name} {self.login}"
            )
            self.check = True
