import logging
from playwright.sync_api import sync_playwright
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

def test_reservasi_selectors():
    url = "http://10.60.168.41:5601/app/dashboards#/view/5752234c-1e75-469b-8e91-9960ffdef562?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))"
    
    # CSS Selectors (robust)
    css_total = 'div[data-test-subj="embeddablePanel"]:has(span[title="Total API Hit"]) p.echMetricText__value'
    
    # User's XPath selector to test
    user_xpath = 'xpath=//div[1]/div/div[2]/div[2]/div[2]/div/div/div/div[3]/div[1]/div[2]/div/div/div[3]/div[2]/div/div[1]/div/div[2]/div/div/span'

    print(f"Testing URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/Applications/Opera.app/Contents/MacOS/Opera",
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="load")
            
            # Login if needed
            try:
                page.wait_for_selector('input[name="username"]', timeout=4000, state="visible")
                page.locator('input[name="username"]').fill(config.KIBANA_USERNAME)
                page.locator('input[type="password"]').fill(config.KIBANA_PASSWORD)
                page.locator('button[type="submit"]').click()
                page.wait_for_selector('input[name="username"]', state="hidden", timeout=15000)
            except Exception:
                pass
            
            print("Waiting for page metrics to load...")
            page.wait_for_timeout(10000) # Give Kibana time to load all panels

            print("--- Testing User's XPath ---")
            try:
                page.wait_for_selector(user_xpath, state="visible", timeout=10000)
                xpath_text = page.locator(user_xpath).first.inner_text().strip()
                print(f"[SUCCESS] User's XPath found! Text: '{xpath_text}'")
            except Exception as e:
                print(f"[ERROR] User's XPath failed: {type(e).__name__} - Could not find element.")

            print("--- Testing CSS Selector (Fallback/Robust) ---")
            try:
                page.wait_for_selector(css_total, state="visible", timeout=10000)
                css_text = page.locator(css_total).first.inner_text().strip()
                print(f"[SUCCESS] CSS Selector found! Text: '{css_text}'")
            except Exception as e:
                print(f"[ERROR] CSS Selector failed: {e}")
                
        finally:
            page.close()
            browser.close()

if __name__ == "__main__":
    test_reservasi_selectors()
