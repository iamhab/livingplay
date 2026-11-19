import sys, time
from playwright.sync_api import sync_playwright
url, secs = sys.argv[1], float(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    pg = b.new_page(); pg.goto(url); time.sleep(secs); b.close()
