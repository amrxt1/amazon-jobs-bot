from job_poller import JobPoller
from notifier import Notifier
import time
import random

jb = JobPoller()
n = Notifier()
tries = 1

start_time = time.time()

while True:
    current_time = time.time()
    elapsed = current_time - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    jobs = jb.get_jobs_ca()
    print(f"Try: {tries} | Elapsed Time: {minutes}m {seconds}s | RESP: {jobs}\n")
    if jobs:
        n.notify("Shifta aagia guys")
    time.sleep(random.uniform(10.0, 17.0))
    tries += 1
