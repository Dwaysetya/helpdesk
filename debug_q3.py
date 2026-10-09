import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800}, timezone_id="Asia/Jakarta")
    page = context.new_page()
    
    print("DEBUGGING RESERVASI Q4 (b55b83ac)")
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/b55b83ac-1ccb-4edb-b546-c967e9a050f1?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-24h%2Fh,to:now))")
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(15000)
    
    titles = page.locator('.echMetricText__title span').all_inner_texts()
    metrics = page.locator('.echMetricText__value').all_inner_texts()
    print("TITLES:", titles)
    print("METRICS:", metrics)
    
    # Let's extract any percentages on the screen
    percentages = page.locator('text=/\\d+\\.\\d+%/').all_inner_texts()
    print("PERCENTAGES:", percentages)
    
    page.screenshot(path="debug_q4.png", full_page=True)
    browser.close()
