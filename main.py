import threading
import argparse
import logging
import pprint
import random
import queue
import creds
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from lib.amazon_session import AmazonSession
from lib.job_poller import JobPoller
from lib.notifier import Notifier
from datetime import datetime


logfile = f"logs/main/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(logfile), logging.StreamHandler()],
)


def jittered_sleep(min_s=5, max_s=15):
    """Wait a bit before the next poll, to avoid a rigid bot fingerprint."""
    t = random.uniform(min_s, max_s)
    logging.info(f"Sleeping {t:.1f}s before next poll...")
    time.sleep(t)


def _relogin_worker(session, interval_minutes):
    """
    Background loop: sleep for interval_minutes, then re-login & refresh headers.
    """
    while True:
        time.sleep(interval_minutes * 60)
        try:
            logging.info(f"{session.login}: refreshing session...")
            session._login()
            session.set_headers_with_fresh_tokens()
            logging.info(f"{session.login}: session refreshed")
        except Exception as e:
            logging.info(f"{session.login}: failed to refresh session:", e)


def schedule_relogin(session, interval_minutes: int = 55):
    """
    Spins off a daemon thread that runs _relogin_worker.
    """
    t = threading.Thread(
        target=_relogin_worker, args=(session, interval_minutes), daemon=True
    )
    t.start()


def init_agent(user, notifier, SESSION_QUEUE, region):
    a = AmazonSession(user, notifier=notifier, region=region)
    a._login()
    logging.info(f"Login succesful for: {a.name}")
    time.sleep(7)
    a.set_headers_with_fresh_tokens()

    schedule_relogin(a, interval_minutes=55)

    SESSION_QUEUE.put(a)


def main(region="us"):
    SESSION_QUEUE = queue.Queue()
    timer_futures = []
    executor = ThreadPoolExecutor(max_workers=(len(creds.CREDS)))

    poller = JobPoller()
    notifier = Notifier()
    seen = set()

    for user in creds.CREDS:
        init_agent(user, notifier, SESSION_QUEUE, region)

    logging.info(f"Initialized, queue size: {SESSION_QUEUE.qsize()}")
    logging.info("Ready to go...")

    try:
        while True:
            logging.info(f"\n----Polling for new schedules ({region})----")
            jobs = poller.get_jobs_us() if (region == "us") else poller.get_jobs_ca()
            for job in jobs:
                job_id = job["jobId"]
                scheds = (
                    poller.get_job_schedules_us(job_id)
                    if (region == "us")
                    else poller.get_job_schedules_ca(job_id)
                )
                if not scheds:
                    continue

                scored = poller.score_schedules(scheds)
                scored.sort(key=lambda s: s["score"], reverse=True)

                for s in scored:
                    key = (job_id, s["scheduleId"])
                    if key in seen:
                        continue
                    seen.add(key)

                    logging.info(
                        f"  {s['scheduleId']:16}  scored: {s['score']:.3f}"
                        + ("  ← candidate" if s["score"] >= THRESHOLD else "")
                    )

                    if s["score"] < THRESHOLD:
                        continue

                    try:
                        agent = SESSION_QUEUE.get(timeout=5)
                    except queue.Empty:
                        logging.info("No free sessions...exiting")
                        return True
                    except Exception as e:
                        logging.exception(f"SessionQueue exception :\n{e}")
                        continue

                    try:
                        logging.info(
                            f"***STEP1. Found a match, creating application... using {job_id} with the schedule: {s['scheduleId']}"
                        )

                        app = agent.create_application(job["jobId"], s["scheduleId"])
                        logging.info(
                            f"***STEP2. Created Application:\n{pprint.pformat(app)}"
                        )

                        # try to update application once created, if not, just move to UI
                        try:
                            logging.info("***STEP3. Update Application Invoked...")
                            app = agent.update_application(
                                job["jobId"], s["scheduleId"], app["applicationId"]
                            )
                            logging.info(f"Update Successful!\n{app}")

                            logging.info("***STEP4. Update Work-flow State")
                            agent.update_workflow(app["applicationId"])

                            logging.info(
                                f"Reserved.\n***STEP5. Notifying and closing agent for {agent.login}"
                            )
                        except Exception:
                            logging.exception(
                                "Application created but unable to Update."
                            )
                            notifier.notify(
                                "UNABLE TO START UI TIMER\n"
                                + f"Reserved for {agent.login}\n\n"
                                f"Reserved {job_id}@{s['scheduleId']}  score={s['score']:.3f} \n"
                                + (
                                    f"application_id: {app['applicationId']} \ncandidateId: {app['candidateId']}"
                                    if app
                                    else ""
                                )
                            )

                        try:
                            future = executor.submit(agent.start_timer)
                            timer_futures.append(future)
                        except Exception:
                            logging.exception("Start Timer Failed")

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
                        logging.exception(f"Agent failed, rotating: {e}")
            jittered_sleep()
    except Exception as e:
        logging.exception(f"Something happened which would cause exiting:\n {e}")
    finally:
        logging.info("Shutting down ThreadPoolExecutor")
        executor.shutdown(wait=True)


THRESHOLD = 0.75

if __name__ == "__main__":
    """
    CLI docs.
    """
    parser = argparse.ArgumentParser(
        prog="amazon-job-picker", description="Reserve Amazon shifts (US or CA)"
    )
    parser.add_argument(
        "--country",
        "-c",
        choices=["us", "ca"],
        default="us",
        help="Which region to target (default: us)",
    )
    args = parser.parse_args()
    close_script = False

    logging.info(f"""
    Welcome to BotJob-Sniper3000

    Region seleted:{args.country}

    DISCLAIMER: This is purely for educational and experimental basis.
    """)

    while True:
        close_script = False
        try:
            if args.country == "us":
                close_script = main(region="us")
            else:
                close_script = main(region="ca")
        except KeyboardInterrupt:
            logging.info("\n\n||\tGracefully exiting...")
            break
        except Exception as e:
            logging.exception(
                f"******** Unhandled exception in run_bot(), restarting in 5s:\n{e}"
            )
            logging.info("******** Restarting bot...")
        if close_script:
            break
