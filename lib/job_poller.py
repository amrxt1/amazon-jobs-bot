"""

The Job Polling object.

"""

from datetime import datetime
from typing import List, Dict

from datetime import date
import requests
import logging


class JobPoller:
    def __init__(self):
        self.baseURL = "https://e5mquma77feepi2bdn4d6h3mpu.appsync-api.us-east-1.amazonaws.com/graphql"
        self.headers_us = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Country": "United States",
            "authorization": "Bearer Status|unauthenticated|",
        }
        self.headers_ca = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "authorization": "Bearer Status|unauthenticated|Session|",
            "Country": "Canada",
        }

    def graphQL(self, body, headers):
        resp = requests.post(self.baseURL, headers=headers, json=body)
        resp.raise_for_status()

        data = resp.json()
        return data

    def get_jobs_us(self):
        logging.info("\nFetching for jobs( US )...")

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
                        {
                            "key": "firstDayOnSite",
                            "range": {"startDate": date.today().isoformat()},
                        }
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
        data = self.graphQL(body=body, headers=self.headers_us)
        data = data["data"]["searchJobCardsByLocation"]["jobCards"]
        if data:
            logging.info("Response recieved...\n")
            logging.info(f"Recieved {len(data)} openings")
            return data
        else:
            logging.info("Response empty")
            return []

    def get_jobs_ca(self):
        logging.info("\nFetching for jobs( CA )…")

        # van coordinates
        lat = "49.2827"
        lng = "-123.1207"

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
                        "distance": 150,
                    },
                    "dateFilters": [
                        {
                            "key": "firstDayOnSite",
                            "range": {"startDate": date.today().isoformat()},
                        }
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

        data = self.graphQL(body=body, headers=self.headers_ca)
        data = data["data"]["searchJobCardsByLocation"]["jobCards"]
        if data:
            logging.info("Response recieved...\n")
            logging.info(f"Recieved {len(data)} openings")
            return data
        else:
            logging.info("Response empty")
            return []

    def get_job_schedules_us(self, jobId):
        logging.info(f"\nFetching for Job Schedule for: {jobId}")

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
                        {
                            "key": "firstDayOnSite",
                            "range": {"startDate": date.today().isoformat()},
                        }
                    ],
                    "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
                    "pageSize": 1000,
                    "jobId": jobId,
                    "consolidateSchedule": True,
                }
            },
            "query": "query searchScheduleCards($searchScheduleRequest: SearchScheduleRequest!) {\n  searchScheduleCards(searchScheduleRequest: $searchScheduleRequest) {\n    nextToken\n    scheduleCards {\n      hireStartDate\n      address\n      basePay\n      bonusSchedule\n      city\n      currencyCode\n      dataSource\n      distance\n      employmentType\n      externalJobTitle\n      featuredSchedule\n      firstDayOnSite\n      hoursPerWeek\n      image\n      jobId\n      jobPreviewVideo\n      language\n      postalCode\n      priorityRank\n      scheduleBannerText\n      scheduleId\n      scheduleText\n      scheduleType\n      signOnBonus\n      state\n      surgePay\n      tagLine\n      geoClusterId\n      geoClusterName\n      siteId\n      scheduleBusinessCategory\n      totalPayRate\n      financeWeekStartDate\n      laborDemandAvailableCount\n      scheduleBusinessCategoryL10N\n      firstDayOnSiteL10N\n      financeWeekStartDateL10N\n      scheduleTypeL10N\n      employmentTypeL10N\n      basePayL10N\n      signOnBonusL10N\n      totalPayRateL10N\n      distanceL10N\n      requiredLanguage\n      monthlyBasePay\n      monthlyBasePayL10N\n      vendorKamName\n      vendorId\n      vendorName\n      kamPhone\n      kamCorrespondenceEmail\n      kamStreet\n      kamCity\n      kamDistrict\n      kamState\n      kamCountry\n      kamPostalCode\n      __typename\n    }\n    __typename\n  }\n}\n",
        }

        data = self.graphQL(body=body, headers=self.headers_us)
        data = data["data"]["searchScheduleCards"]["scheduleCards"]

        logging.info("Schedules recieved...\n")
        if data:
            logging.info("Response recieved...\n")
            logging.info(f"Recieved {len(data)} schedules for {jobId}")
            return data
        else:
            logging.info("Response empty")
            return []

    def get_job_schedules_ca(self, jobId):
        logging.info(f"\n(CA)\tFetching for Job Schedule for: {jobId}")

        body = {
            "operationName": "searchScheduleCards",
            "variables": {
                "searchScheduleRequest": {
                    "locale": "en-CA",
                    "country": "Canada",
                    "keyWords": "",
                    "equalFilters": [],
                    "containFilters": [{"key": "isPrivateSchedule", "val": ["false"]}],
                    "rangeFilters": [
                        {"key": "hoursPerWeek", "range": {"minimum": 0, "maximum": 80}}
                    ],
                    "orFilters": [],
                    "dateFilters": [
                        {
                            "key": "firstDayOnSite",
                            "range": {"startDate": date.today().isoformat()},
                        }
                    ],
                    "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
                    "pageSize": 1000,
                    "jobId": jobId,
                    "consolidateSchedule": True,
                }
            },
            "query": "query searchScheduleCards($searchScheduleRequest: SearchScheduleRequest!) {\n  searchScheduleCards(searchScheduleRequest: $searchScheduleRequest) {\n    nextToken\n    scheduleCards {\n      hireStartDate\n      address\n      basePay\n      bonusSchedule\n      city\n      currencyCode\n      dataSource\n      distance\n      employmentType\n      externalJobTitle\n      featuredSchedule\n      firstDayOnSite\n      hoursPerWeek\n      image\n      jobId\n      jobPreviewVideo\n      language\n      postalCode\n      priorityRank\n      scheduleBannerText\n      scheduleId\n      scheduleText\n      scheduleType\n      signOnBonus\n      state\n      surgePay\n      tagLine\n      geoClusterId\n      geoClusterName\n      siteId\n      scheduleBusinessCategory\n      totalPayRate\n      financeWeekStartDate\n      laborDemandAvailableCount\n      scheduleBusinessCategoryL10N\n      firstDayOnSiteL10N\n      financeWeekStartDateL10N\n      scheduleTypeL10N\n      employmentTypeL10N\n      basePayL10N\n      signOnBonusL10N\n      totalPayRateL10N\n      distanceL10N\n      requiredLanguage\n      monthlyBasePay\n      monthlyBasePayL10N\n      vendorKamName\n      vendorId\n      vendorName\n      kamPhone\n      kamCorrespondenceEmail\n      kamStreet\n      kamCity\n      kamDistrict\n      kamState\n      kamCountry\n      kamPostalCode\n      __typename\n    }\n    __typename\n  }\n}\n",
        }

        data = self.graphQL(body=body, headers=self.headers_us)
        data = data["data"]["searchScheduleCards"]["scheduleCards"]

        logging.info("Schedules recieved...\n")
        if data:
            logging.info("Response recieved...\n")
            logging.info(f"Recieved {len(data)} schedules for {jobId}")
            return data
        else:
            logging.info("Response empty")
            return []

    def score_schedules(
        self,
        schedules: List[Dict],
        weights: Dict[str, float] = None,
        date_window_days: int = 30,
    ) -> List[Dict]:
        """
        Given a list of schedule objects , return a new list where each
        dict has an extra 'score' key. Higher is better.
        """

        if weights is None:
            weights = {"pay": 0.5, "soon": 0.3, "hours": 0.1, "avail": 0.1}
        today = datetime.now().date()

        # prep for normalization
        max_pay = max(s["totalPayRate"] for s in schedules)
        max_avail = max((s.get("laborDemandAvailableCount") or 0) for s in schedules)

        scored = []
        for s in schedules:
            # normalized 0–1
            pay_norm = (s["totalPayRate"] / max_pay) if max_pay else 0

            try:
                first_day = datetime.fromisoformat(s["firstDayOnSite"]).date()
                delta = (first_day - today).days
            except Exception:
                delta = date_window_days + 1
            # inverted cause less is more
            soon_norm = max(0.0, (date_window_days - delta) / date_window_days)

            hours_norm = min(s["hoursPerWeek"] / 40.0, 1.0)

            avail_norm = (
                (s.get("laborDemandAvailableCount") or 0) / max_avail
                if max_avail
                else 0
            )

            # combined score
            score = (
                pay_norm * weights["pay"]
                + soon_norm * weights["soon"]
                + hours_norm * weights["hours"]
                + avail_norm * weights["avail"]
            )

            scored.append({**s, "score": score})

        return scored
