import config
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800}, timezone_id="Asia/Jakarta")
    page = context.new_page()
    
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/df50703d-0e5d-4096-800d-265596469dd5?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-24h%2Fh,to:now))")
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(15000)
    
    text = page.locator('body').inner_text()
    matches = re.findall(r'[0-9]+(?:\.[0-9]+)?%', text)
    print("ALL PERCENTAGES FOUND:", matches)
    
    browser.close()
