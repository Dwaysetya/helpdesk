import logging
from playwright.sync_api import sync_playwright
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KibanaScraper")
def handle_kibana_login_if_needed(page):
    """
    Checks if Kibana has redirected the browser to a login screen.
    If detected, automatically fills in credentials and logs in.
    """
    username_selectors = [
        'input[name="username"]',
        '[data-test-subj="loginUsername"]',
        'input[placeholder*="username" i]',
        'input[placeholder*="Username" i]'
    ]
    combined_sel = ", ".join(username_selectors)
    
    try:
        # Check if the login inputs appear within 4 seconds.
        # If not, we are already logged in or the page does not require login.
        page.wait_for_selector(combined_sel, timeout=4000, state="visible")
        logger.info("Kibana login page detected. Attempting automated login...")
        
        # Fill Username
        page.locator(combined_sel).first.fill(config.KIBANA_USERNAME)
        
        # Fill Password
        password_selectors = [
            'input[name="password"]',
            '[data-test-subj="loginPassword"]',
            'input[type="password"]'
        ]
        page.locator(", ".join(password_selectors)).first.fill(config.KIBANA_PASSWORD)
        
        # Click Sign In button
        submit_selectors = [
            'button[type="submit"]',
            '[data-test-subj="loginSubmit"]'
        ]
        page.locator(", ".join(submit_selectors)).first.click()
        
        # Wait for the login screen to disappear (login success and redirection start)
        logger.info("Waiting for login page to disappear...")
        page.wait_for_selector(combined_sel, state="hidden", timeout=15000)
        logger.info("Login submitted successfully. Resuming dashboard extraction.")
    except Exception:
        # Timeout means the login form is not visible, so we are already logged in.
        logger.debug("No login screen detected. Proceeding to dashboard.")

def scrape_grafana_screenshot(context) -> str:
    """
    Navigates to the Grafana dashboard, logs in, and takes a screenshot.
    Returns the path to the saved screenshot image.
    """
    logger.info("Starting Grafana screenshot process...")
    page = context.new_page()
    screenshot_path = "grafana_screenshot.png"
    
    try:
        # Navigate to Grafana
        page.goto(config.GRAFANA_URL, wait_until="networkidle")
        
        # Check if login is required
        # Grafana login inputs usually have names "user" and "password"
        if page.locator('input[name="user"]').is_visible(timeout=5000):
            logger.info("Grafana login detected. Entering credentials...")
            page.locator('input[name="user"]').fill(config.GRAFANA_USERNAME)
            page.locator('input[name="password"]').fill(config.GRAFANA_PASSWORD)
            page.locator('button[type="submit"], button[aria-label="Login button"]').first.click()
            page.wait_for_load_state("networkidle")
            
        # Give Grafana panels a few seconds to load metrics and render graphs
        logger.info("Waiting for Grafana panels to render...")
        try:
            # Wait for panel contents or canvases to appear to ensure data is rendering
            page.wait_for_selector('div[class*="panel-container"], canvas, div[data-testid*="panel"]', state="visible", timeout=60000)
            logger.info("Grafana panels detected. Waiting an additional 15 seconds for graphs to fully populate...")
            page.wait_for_timeout(15000)
        except Exception:
            logger.warning("Could not detect specific Grafana panels. Falling back to a long 60-second wait.")
            page.wait_for_timeout(60000)
        
        # Activate Opera and forcefully maximize it to fill the entire screen (2560x1600).
        # This accurately reproduces the user's reference screenshot with the Mac Menu Bar visible at the top.
        try:
            import subprocess
            logger.info("Activating and maximizing Opera via AppleScript...")
            applescript = '''
tell application "Finder"
    set desktopBounds to bounds of window of desktop
end tell
tell application "Opera"
    activate
    set bounds of window 1 to desktopBounds
end tell
'''
            subprocess.run(["osascript", "-e", applescript])
            page.wait_for_timeout(2000) # Wait for window resize
        except Exception as e:
            logger.warning(f"Could not resize window via AppleScript: {e}")
            
        # Take an OS-level full-screen screenshot to capture the Mac menu bar and full browser
        subprocess.run(["screencapture", "-x", screenshot_path])
        logger.info(f"Grafana screenshot saved successfully to {screenshot_path} (AppleScript Maximized)")
        return screenshot_path
    except Exception as e:
        logger.error(f"Failed to scrape Grafana screenshot: {str(e)}")
        return ""
    finally:
        page.close()

def scrape_all_dashboards() -> tuple[dict, str]:
    """
    Opens Kibana dashboards using Playwright, waits for metrics to load,
    scrapes target numbers, and returns a structured dictionary of results.
    """
    results = {}
    
    logger.info("Initializing Playwright and launching browser...")
    with sync_playwright() as p:
        # Launch browser (Chromium) with headless=False to allow OS screen capture
        # Set up Chromium to launch Opera explicitly
        browser = p.chromium.launch(
            executable_path="/Applications/Opera.app/Contents/MacOS/Opera",
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        # Use no_viewport=True so Playwright automatically resizes the internal page to match the OS window bounds perfectly
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
            timezone_id="Asia/Jakarta"
        )
        
        # Set a default timeout for navigation and waiting
        context.set_default_timeout(config.TIMEOUT_MS)
        
        for db_key, db_info in config.DASHBOARDS.items():
            name = db_info["name"]
            url = db_info["url"]
            logger.info(f"Navigating to dashboard: {name}...")
            
            results[db_key] = {}
            page = None
            try:
                page = context.new_page()
                
                # Navigate to the dashboard. Wait for load state to complete.
                page.goto(url, wait_until="load")
                
                # Check and complete login if Kibana asks for username/password
                handle_kibana_login_if_needed(page)
                
                # --- OPTIONAL KIBANA LOADING INDICATOR HANDLING ---
                # Kibana dashboards dynamically fetch data from Elasticsearch using internal APIs.
                # In many versions, a global loading indicator (e.g. data-test-subj="globalLoadingIndicator-hidden")
                # shows when it's idle.
                # We can try waiting for the loading indicator to disappear, but the most robust check is waiting
                # for our specific metric element to become visible.
                
                if db_key == "reservasi_homepass":
                    key_name = "total_id"
                    total_sel = db_info["total_id_selector"]
                else:
                    key_name = "total_hits"
                    total_sel = db_info["total_hits_selector"]
                    
                logger.info(f"Waiting for {key_name} selector: {total_sel}")
                page.wait_for_selector(total_sel, state="visible")
                # Extract text
                total_text = page.locator(total_sel).first.inner_text().strip()
                total_text = total_text.replace("\n", "").replace(" ", "")
                results[db_key][key_name] = total_text or "N/A"
                
                # Scrape "Success Rate"
                if db_key == "reservasi_homepass":
                    try:
                        logger.info("Extracting Success Reserve percentage from Lens table...")
                        page.wait_for_selector('div[data-test-subj="lnsTableCellContent"]', timeout=30000)
                        success_rate_text = page.evaluate("""() => {
                            const cells = Array.from(document.querySelectorAll('div[data-test-subj="lnsTableCellContent"]'));
                            let successCount = 0;
                            let totalCount = 0;
                            for (let i = 0; i < cells.length; i++) {
                                if (cells[i].classList.contains('lnsTableCell--right')) {
                                    let val = parseInt(cells[i].innerText.replace(/,/g, ''), 10);
                                    if (!isNaN(val)) {
                                        totalCount += val;
                                        if (i > 0 && cells[i-1].innerText.includes('Port successfully reserved')) {
                                            successCount = val;
                                        }
                                    }
                                }
                            }
                            if (totalCount > 0) {
                                return (successCount / totalCount * 100).toFixed(2) + '%';
                            }
                            return 'N/A';
                        }""")
                    except Exception as e:
                        logger.error(f"Failed to calculate pie chart percentage: {e}")
                        success_rate_text = "N/A"
                else:
                    success_rate_sel = db_info["success_rate_selector"]
                    logger.info(f"Waiting for Success Rate selector: {success_rate_sel}")
                    page.wait_for_selector(success_rate_sel, state="visible")
                    # Extract text
                    success_rate_text = page.locator(success_rate_sel).first.inner_text().strip()
                    success_rate_text = success_rate_text.replace("\n", "").replace(" ", "")
                
                results[db_key]["success_rate"] = success_rate_text or "N/A"
                
                logger.info(f"Successfully scraped {name}: {results[db_key]}")
                
            except Exception as e:
                logger.error(f"Failed scraping dashboard '{name}': {str(e)}")
                # Fill values with error label so the message delivery still works
                if db_key == "reservasi_homepass":
                    results[db_key] = {
                        "total_id": "Error (Timeout/Failed)",
                        "success_rate": "Error (Timeout/Failed)"
                    }
                else:
                    results[db_key] = {
                        "total_hits": "Error (Timeout/Failed)",
                        "success_rate": "Error (Timeout/Failed)"
                    }
            finally:
                if page:
                    page.close()
                    
        # Scrape Grafana screenshot
        screenshot_path = scrape_grafana_screenshot(context)

        # Close the browser instance
        browser.close()
        
    return results, screenshot_path

if __name__ == "__main__":
    # Test execution in headful mode for debugging
    import sys
    print("Testing Playwright Kibana Scraper run...")
    config.HEADLESS = False  # Toggle headful for visual verification
    data, screenshot_path = scrape_all_dashboards()
    print("Scrape results:")
    print(data)
    print(f"Screenshot Path: {screenshot_path}")
