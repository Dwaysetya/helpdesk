import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    
    # Original Homepass
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/295c9906-7c3d-4689-8770-ab04db443e37?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))")
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(10000)
    
    titles = page.locator('.echMetricText__title span').all_inner_texts()
    print("ORIGINAL HOMEPASS TITLES:", titles)
    
    # Original Reservasi Homepass
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/df50703d-0e5d-4096-800d-265596469dd5?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))")
    page.wait_for_timeout(10000)
    titles = page.locator('.echMetricText__title span').all_inner_texts()
    print("ORIGINAL RESERVASI TITLES:", titles)
    
    browser.close()
