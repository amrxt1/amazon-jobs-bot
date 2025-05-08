import threading
import queue
import time
import random
import sys
import creds
import traceback

from amazon_session import AmazonSession
from job_poller import JobPoller
from notifier import Notifier

SESSION_QUEUE = queue.Queue()
THRESHOLD = 0.96


def jittered_sleep(min_s=5, max_s=15):
    """Wait a bit before the next poll, to avoid a rigid bot fingerprint."""
    t = random.uniform(min_s, max_s)
    print(f"Sleeping {t:.1f}s before next poll...")
    time.sleep(t)


AMTMP = 0


def _relogin_worker(session, interval_minutes):
    """
    Background loop: sleep for interval_minutes, then re-login & refresh headers.
    """
    while True:
        time.sleep(interval_minutes * 60)
        try:
            print(f"\n{session.login}: refreshing session...")
            session._login()
            session.set_headers_with_fresh_tokens()
            print(f"{session.login}: session refreshed")
        except Exception as e:
            print(f"{session.login}: failed to refresh session:", e)


def schedule_relogin(session, interval_minutes: int = 55):
    """
    Spins off a daemon thread that runs _relogin_worker.
    """
    t = threading.Thread(
        target=_relogin_worker, args=(session, interval_minutes), daemon=True
    )
    t.start()


def init_agent(user):
    a = AmazonSession(user["name"], user["login"], user["pin"], user["imap"])
    a._login()
    print("\n\nlogin succesful")
    time.sleep(7)
    a.set_headers_with_fresh_tokens()

    schedule_relogin(a, interval_minutes=55)

    SESSION_QUEUE.put(a)


def run_bot():
    for user in creds.CREDS:
        init_agent(user)

    poller = JobPoller()
    notifier = Notifier()

    seen = set()

    print("Initialized, queue size:", SESSION_QUEUE.qsize())
    print("Ready to go...")

    try:
        while True:
            print("\n----Polling for new schedules----")
            jobs = poller.get_jobs_us()
            for job in jobs:
                job_id = job["jobId"]
                scheds = poller.get_job_schedules_us(job_id)
                if not scheds:
                    continue

                scored = poller.score_schedules(scheds)
                scored.sort(key=lambda s: s["score"], reverse=True)

                for s in scored:
                    key = (job_id, s["scheduleId"])
                    if key in seen:
                        continue
                    seen.add(key)

                    print(
                        f"  {s['scheduleId']:16}  scored: {s['score']:.3f}"
                        + ("  ← candidate" if s["score"] >= THRESHOLD else "")
                    )

                    if s["score"] < THRESHOLD:
                        continue

                    try:
                        agent = SESSION_QUEUE.get(timeout=5)
                    except queue.Empty:
                        print("No free sessions...")
                        print("Exiting...")
                        sys.exit(0)
                    except Exception:
                        continue

                    try:
                        print(
                            f"***STEP1. Found a match, creating application... using {job_id} with the schedule: {s['scheduleId']}"
                        )

                        app = agent.create_application(job["jobId"], s["scheduleId"])
                        print("***STEP2. Created Application:", app)

                        print("***STEP3. Update Application Invoked...")
                        agent.update_application(
                            job["jobId"], s["scheduleId"], app["applicationId"]
                        )
                        print("Update Successful!")

                        print("***STEP4. Update Work-flow State")
                        agent.update_workflow(app["applicationId"])

                        print(
                            f"Reserved.\n***STEP5. Notifying and closing agent for {agent.login}"
                        )

                        try:
                            agent.nav_to_timer_page()
                        except Exception:
                            print("Nah v bni ni gal")
                            time.sleep(5)

                        notifier.notify(
                            f"Reserved for {agent.login}\n\n"
                            f"Reserved {job_id}@{s['scheduleId']}  score={s['score']:.3f} \n"
                            + (
                                f"application_id: {app['applicationId']} \ncandidateId: {app['candidateId']}"
                                if app
                                else ""
                            )
                        )
                    except Exception as e:
                        print("Agent failed, rotating:", e)
            jittered_sleep()
    except Exception as e:
        print("\nSomething happened which would cause exiting:\n", e)


if __name__ == "__main__":
    while True:
        try:
            run_bot()
            break
        except KeyboardInterrupt:
            print("\n\n||\tGracefully exiting...")
            break
        except Exception:
            print("******** Unhandled exception in run_bot(), restarting in 5s:")
            traceback.print_exc()
            time.sleep(5)
            print("******** Restarting bot...")
