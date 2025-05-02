"""

The Job Polling object.

"""

import requests
from datetime import date


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
        print("\nFetching for jobs( US )...")

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
            print("Response recieved...\n")
            print(f"Recieved {len(data)} openings")
            return data
        else:
            print("Response empty")
            return []

    def get_jobs_ca(self):
        print("\nFetching for jobs( CA )…")

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
            print("Response recieved...\n")
            print(f"Recieved {len(data)} openings")
            return data
        else:
            print("Response empty")
            return []

    def get_job_schedules_us(self, jobId):
        print(f"\nFetching for Job Schedule for: {jobId}")

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

        print("Schedules recieved...\n")
        data = self.graphQL(body=body, headers=self.headers_us)
        print(data)
        data = data["data"]["searchScheduleCards"]["scheduleCards"]
        if data:
            print("Response recieved...\n")
            print(f"Recieved {len(data)} schedules for {jobId}")
            return data
        else:
            print("Response empty")
            return []


obj = JobPoller()
print(obj.get_job_schedules_us(obj.get_jobs_us()[2]["jobId"]))
