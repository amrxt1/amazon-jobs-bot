from playwright.sync_api import sync_playwright
import time
import yaml
import os
from dotenv import load_dotenv

load_dotenv()


def telegram(link):
    import requests

    body = f"New Amazon job posted:\n{link}"
    url = os.getenv("URL")
    params = {"chat_id": os.getenv("CHAT_ID"), "text": body}
    requests.get(url + "/sendMessage", params=params)


def wait_and_click(page, text, timeout=10000):
    print(f"Waiting for and clicking: {text}")
    page.locator(f"text={text}").first.wait_for(timeout=timeout)
    page.locator(f"text={text}").first.click()


def main():
    with open("config.yml", "r") as f:
        cfg = yaml.safe_load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=cfg["chrome"]["headless"])
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        print("🔐 Navigating to login...")
        page.goto(cfg["url"]["login_url"])

        # Click "I Agree" (consent)
        wait_and_click(page, "I consent")
        print("Clicked consent\n")
        # Email
        page.fill("#login", cfg["creds"]["email"])
        page.click('button:has-text("Continue")')

        # PIN
        page.fill("#pin", cfg["creds"]["pin"])
        page.click("button:has-text('Continue')")

        print("🔐 CAPTCHA and OTP required. Please complete manually.")
        input("✅ Press ENTER after solving CAPTCHA and entering OTP in browser...")

        # Confirm OTP manually, wait for full login
        time.sleep(5)

        # Check token
        token = page.evaluate("localStorage.getItem('sessionToken')")
        print("SessionToken:", token)
        if not token or "unauthenticated" in token.lower():
            print("❌ Invalid token. Login may have failed.")
            return

        print("✅ Logged in successfully.")

        while True:
            print("🧭 Navigate to job page and try schedule...")
            job_id = "JOB-US-0000010301"  # You should pull this dynamically
            schedule_id = "SCH-US-0000576212"  # Same here

            apply_url = (
                f"https://hiring.amazon.com/application/us/?jobId={job_id}"
                f"&scheduleId={schedule_id}#/pre-consent?"
                f"jobId={job_id}&scheduleId={schedule_id}"
            )
            page.goto(apply_url)
            print("✅ Loaded application page")

            try:
                wait_and_click(page, "I Agree")
                print("✅ Consent clicked")
                wait_and_click(page, "Next")
                print("✅ Next clicked")
                input(
                    "✅ Manually click 'Create Application' if needed, then press ENTER..."
                )
            except Exception as e:
                print("⚠️ Failed to click one of the buttons:", e)

            print("⏳ Waiting before retrying...")
            time.sleep(cfg["interval"])

        browser.close()


if __name__ == "__main__":
    main()
