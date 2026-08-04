import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    
    print("DEBUGGING HOMEPASS")
    page.goto(config.DASHBOARDS["homepass"]["url"])
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(10000)
    
    page.screenshot(path="debug_homepass_24h.png", full_page=True)
    metrics = page.locator('.echMetricText__value').all_inner_texts()
    titles = page.locator('.echMetricText__title span').all_inner_texts()
    print("HOMEPASS TITLES:", titles)
    print("HOMEPASS METRICS:", metrics)
    
    print("DEBUGGING RESERVASI HOMEPASS")
    page.goto(config.DASHBOARDS["reservasi_homepass"]["url"])
    page.wait_for_timeout(10000)
    page.screenshot(path="debug_reservasi_24h.png", full_page=True)
    
    metrics = page.locator('.echMetricText__value').all_inner_texts()
    titles = page.locator('.echMetricText__title span').all_inner_texts()
    print("RESERVASI TITLES:", titles)
    print("RESERVASI METRICS:", metrics)
    
    browser.close()
