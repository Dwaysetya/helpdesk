import config
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800}, timezone_id="Asia/Jakarta")
    page = context.new_page()
    
    page.goto("http://10.60.168.41:5601/app/dashboards#/view/df50703d-0e5d-4096-800d-265596469dd5?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-24h%2Fh,to:now))")
    page.locator('input[name="username"], [data-test-subj="loginUsername"]').first.fill(config.KIBANA_USERNAME)
    page.locator('input[name="password"], [data-test-subj="loginPassword"]').first.fill(config.KIBANA_PASSWORD)
    page.locator('button[type="submit"], [data-test-subj="loginSubmit"]').first.click()
    page.wait_for_timeout(15000)
    
    # Try to hover the pie chart Canvas to trigger the tooltip
    # We find the embeddable panel that has the pie chart (usually has echChartCanvas)
    canvas = page.locator('canvas.echChartCanvas').first
    if canvas.count() > 0:
        box = canvas.bounding_box()
        if box:
            # Hover in the middle of the canvas
            page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            page.wait_for_timeout(2000)
            print("TOOLTIP TEXTS:", page.locator('.echTooltip').all_inner_texts())
            page.screenshot(path="debug_hover.png")
            
    browser.close()
