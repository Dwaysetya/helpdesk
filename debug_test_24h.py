import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800}, timezone_id="Asia/Jakarta")
    page = context.new_page()
    
    # Homepass with 24h
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/e97317ed-e39d-47bf-a423-db31311d2d42?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-24h%2Fh,to:now))")
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(10000)
    print("HOMEPASS 24h TITLES:", page.locator('.echMetricText__title span').all_inner_texts())
    print("HOMEPASS 24h METRICS:", page.locator('.echMetricText__value').all_inner_texts())
    
    # Reservasi with 24h
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/f6a3c50e-d2d0-43bc-825c-56fa03c451e1?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-24h%2Fh,to:now))")
    page.wait_for_timeout(10000)
    print("RESERVASI 24h TITLES:", page.locator('.echMetricText__title span').all_inner_texts())
    print("RESERVASI 24h METRICS:", page.locator('.echMetricText__value').all_inner_texts())
    
    browser.close()
