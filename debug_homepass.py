import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    page.goto(config.DASHBOARDS["homepass"]["url"])
    
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(10000)
    
    page.screenshot(path="debug_homepass.png")
    
    metrics = page.locator('.echMetricText__value').all_inner_texts()
    print("METRICS on HOMEPASS:", metrics)
    
    browser.close()
