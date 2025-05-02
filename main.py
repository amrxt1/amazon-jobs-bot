from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import undetected_chromedriver as uc

from urllib.parse import urlencode, quote
from dotenv import load_dotenv
import traceback
import requests
import time
import json
import yaml
import os


def telegram(link):
    body = f"New Amazon job posted:\n{link}"
    url = os.getenv("URL")
    params = {"chat_id": os.getenv("CHAT_ID"), "text": body}
    requests.get(url + "/sendMessage", params=params)


def build_driver(chromedriver_path, isHeadless, windowSize):
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


def fetch_jobs_us(driver, cfg):
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
    print(data[0])
    return data


def fetch_jobs_ca(driver, cfg):
    print("\nFetching for jobs…")

    token = driver.execute_script("return window.localStorage.getItem('sessionToken')")
    if not token:
        raise RuntimeError("sessionToken not found in localStorage")

    raw_geo = driver.execute_script("return window.localStorage.getItem('geoInfo')")
    if raw_geo:
        geo = json.loads(raw_geo)
        lat = geo.get("lat")
        lng = geo.get("lng")
    else:
        lat = cfg["location"]["lat"]
        lng = cfg["location"]["lng"]

    url = (
        "https://e5mquma77feepi2bdn4d6h3mpu.appsync-api.us-east-1.amazonaws.com/graphql"
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Authorization": f"Bearer {token}",
        "Country": "Canada",
    }

    body = {
        "operationName": "searchJobCardsByLocation",
        "variables": {
            "searchJobRequest": {
                "locale": "en-CA",
                "country": "Canada",
                "pageSize": 100,
                "geoQueryClause": {
                    "lat": lat,
                    "lng": lng,
                    "unit": "km",
                    "distance": 100,
                },
                "dateFilters": [
                    {"key": "firstDayOnSite", "range": {"startDate": "2025-05-01"}}
                ],
            }
        },
        "query": """
          query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
            searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
              nextToken
              jobCards {
                jobId
                language
                dataSource
                requisitionType
                jobTitle
                jobType
                employmentType
                city
                state
                postalCode
                locationName
                totalPayRateMin
                totalPayRateMax
                tagLine
                bannerText
                image
                jobPreviewVideo
                distance
                featuredJob
                bonusJob
                bonusPay
                scheduleCount
                currencyCode
                geoClusterDescription
                surgePay
                jobTypeL10N
                employmentTypeL10N
                bonusPayL10N
                surgePayL10N
                totalPayRateMinL10N
                totalPayRateMaxL10N
                distanceL10N
                monthlyBasePayMin
                monthlyBasePayMinL10N
                monthlyBasePayMax
                monthlyBasePayMaxL10N
                jobContainerJobMetaL1
                virtualLocation
                poolingEnabled
                __typename
              }
              __typename
            }
          }
        """,
    }

    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()

    data = resp.json()["data"]["searchJobCardsByLocation"]["jobCards"]
    print("Response received…\n")
    print(data[0])
    return data


def get_job_schedules_us(driver, jobId, cfg):
    print(f"\nFetching for Job Schedule for: {jobId}")
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
        "operationName": "searchScheduleCards",
        "variables": {
            "searchScheduleRequest": {
                "locale": "en-US",
                "country": "United States",
                "keyWords": "",
                "equalFilters": [],
                "containFilters": [{"key": "isPrivateSchedule", "val": ["false"]}],
                "rangeFilters": [
                    {"key": "hoursPerWeek", "range": {"minimum": 0, "maximum": 80}}
                ],
                "orFilters": [],
                "dateFilters": [
                    {"key": "firstDayOnSite", "range": {"startDate": "2025-05-01"}}
                ],
                "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
                "pageSize": 1000,
                "jobId": jobId,
                "consolidateSchedule": True,
            }
        },
        "query": "query searchScheduleCards($searchScheduleRequest: SearchScheduleRequest!) {\n  searchScheduleCards(searchScheduleRequest: $searchScheduleRequest) {\n    nextToken\n    scheduleCards {\n      hireStartDate\n      address\n      basePay\n      bonusSchedule\n      city\n      currencyCode\n      dataSource\n      distance\n      employmentType\n      externalJobTitle\n      featuredSchedule\n      firstDayOnSite\n      hoursPerWeek\n      image\n      jobId\n      jobPreviewVideo\n      language\n      postalCode\n      priorityRank\n      scheduleBannerText\n      scheduleId\n      scheduleText\n      scheduleType\n      signOnBonus\n      state\n      surgePay\n      tagLine\n      geoClusterId\n      geoClusterName\n      siteId\n      scheduleBusinessCategory\n      totalPayRate\n      financeWeekStartDate\n      laborDemandAvailableCount\n      scheduleBusinessCategoryL10N\n      firstDayOnSiteL10N\n      financeWeekStartDateL10N\n      scheduleTypeL10N\n      employmentTypeL10N\n      basePayL10N\n      signOnBonusL10N\n      totalPayRateL10N\n      distanceL10N\n      requiredLanguage\n      monthlyBasePay\n      monthlyBasePayL10N\n      vendorKamName\n      vendorId\n      vendorName\n      kamPhone\n      kamCorrespondenceEmail\n      kamStreet\n      kamCity\n      kamDistrict\n      kamState\n      kamCountry\n      kamPostalCode\n      __typename\n    }\n    __typename\n  }\n}\n",
    }
    print("Built request...")
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()["data"]["searchScheduleCards"]["scheduleCards"]
    print("Schedules recieved...\n")
    print()
    return data


def click_element_by_xpath(driver, xpath, timeout=10):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    element.click()


def build_application_url(job_id, schedule_id, token):
    base_url = "https://hiring.amazon.com/application/"
    params = {
        "page": "pre-consent",
        "jobId": job_id,
        "scheduleId": schedule_id,
        "CS": "true",
        "locale": "en-US",
        "token": token,
        "ssoEnabled": "1",
    }
    return f"{base_url}?{urlencode(params, quote_via=quote)}"


def sync_cookies_to_requests(driver, session):
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])


def main():
    cfg, driver = initialize()

    try:
        login(driver, cfg)

        seen = set()
        interval = cfg["interval"]

        print(f"\nFetching every {interval}s for new jobs…")
        while True:
            try:
                jobs = fetch_jobs_us(driver, cfg)
            except Exception:
                print("Fetch failed. Logging in...")
                login(driver, cfg)
                jobs = fetch_jobs_us(driver, cfg)
            if jobs:
                jid = jobs[0]["jobId"]
                if jid not in seen:
                    seen.add(jid)
                    schedules = get_job_schedules_us(driver, jid, cfg)
                    if schedules:
                        schedule_id = schedules[0]["scheduleId"]
                        token = driver.execute_script(
                            "return window.localStorage.getItem('accessToken')"
                        )

                        time.sleep(7)

                        print("Navigating to the first schedule apply page")
                        driver.get(build_application_url(jid, schedule_id, token))

                        driver.execute_script("""
                        fetch('/application/api/candidate-application/candidate', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Authorization': localStorage.getItem('accessToken'),
                            'bb-ui-version': 'bb-ui-v2'
                        },
                        credentials: 'include'
                        }).then(res => res.json()).then(console.log);
                        """)

            print(f"Sleeping for {interval}s…\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nGracefully Exiting...")
    except Exception:
        print("\n\n\tGAME \tO V E R")
        traceback.print_exc()

        print("Try to debug ill give you some time")
        time.sleep(1000000)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
