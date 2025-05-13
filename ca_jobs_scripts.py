from lib.job_poller import JobPoller
from lib.notifier import Notifier
import sys
import time
import random


def run_bot():
    jb = JobPoller()
    n = Notifier()
    tries = 1
    hits = 1

    start_time = time.time()

    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        jobs = jb.get_jobs_ca()
        print(f"Try: {tries} | Elapsed Time: {minutes}m {seconds}s | RESP: {jobs}\n")
        # n.notify(f"Try: {tries} | Elapsed Time: {minutes}m {seconds}s | RESPONSE: {jobs}\n")
        if jobs:
            n.notify("Shifta aagia guys")
            if hits == 100:
                sys.exit(0)
        time.sleep(random.uniform(3.0, 5.0))
        tries += 1


if __name__ == "__main__":
    while True:
        try:
            run_bot()
            break
        except KeyboardInterrupt:
            print("\n\n||\tGracefully exiting...")
            break
        except Exception as e:
            print("******** Unhandled exception in run_bot(), restarting in 5s:\n", e)
            print("******** Restarting bot...")
