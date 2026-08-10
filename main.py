import argparse
import sys
import logging
import time
import os
from datetime import datetime, timedelta

import config
from scraper import scrape_all_dashboards
from notifier import format_report_message, send_telegram_message, send_whatsapp_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KibanaAutomation")

# Global state for prepared reports
PREPARED_REPORT_DATA = None
PREPARED_SCREENSHOT_PATH = None

def prepare_report():
    global PREPARED_REPORT_DATA, PREPARED_SCREENSHOT_PATH
    logger.info("Starting preparation phase: Scraping dashboards...")
    try:
        PREPARED_REPORT_DATA, PREPARED_SCREENSHOT_PATH = scrape_all_dashboards()
        logger.info("Preparation phase finished.")
    except Exception as e:
        logger.error(f"Error during preparation phase: {e}")

def send_prepared_report(target: str):
    global PREPARED_REPORT_DATA, PREPARED_SCREENSHOT_PATH
    import asyncio
    
    if not PREPARED_REPORT_DATA:
        logger.warning("No prepared report found! Running fallback scrape...")
        return run_once(target)
        
    logger.info(f"Sending prepared report. Target: {target.upper()}")
    report_text = format_report_message(PREPARED_REPORT_DATA)
    
    print("\n--- FORMATTED REPORT ---")
    print(report_text)
    print("------------------------\n")
    
    success_telegram = True
    success_whatsapp = True
    
    if target in ["telegram", "all"]:
        success_telegram = asyncio.run(send_telegram_message(report_text, PREPARED_SCREENSHOT_PATH))
        
    if target in ["whatsapp", "all"]:
        success_whatsapp = send_whatsapp_message(report_text)
        
    # Clear after sending
    PREPARED_REPORT_DATA = None
    PREPARED_SCREENSHOT_PATH = None
    
    return success_telegram and success_whatsapp

def run_once(target: str):
    """
    Performs a single scraping run and distributes the report to the selected targets.
    """
    start_time = datetime.now()
    logger.info(f"Starting automated report extraction. Target: {target.upper()}")
    
    # 1. Scrape the dashboards
    scraped_data, screenshot_path = scrape_all_dashboards()
    
    # 2. Format the message
    report_text = format_report_message(scraped_data)
    
    # Print the formatted report locally for console validation
    print("\n--- FORMATTED REPORT ---")
    print(report_text)
    print("------------------------\n")
    
    # 3. Distribute according to the target
    success_telegram = True
    success_whatsapp = True
    
    import asyncio
    
    if target in ["telegram", "all"]:
        success_telegram = asyncio.run(send_telegram_message(report_text, screenshot_path))
        
    if target in ["whatsapp", "all"]:
        success_whatsapp = send_whatsapp_message(report_text)
        
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Execution finished in {duration:.2f} seconds.")
    
    # If anything failed, return False
    return success_telegram and success_whatsapp

def get_prepare_time(t_str: str, minutes: int = 5) -> str:
    t_obj = datetime.strptime(t_str, "%H:%M")
    t_obj = t_obj - timedelta(minutes=minutes)
    return t_obj.strftime("%H:%M")

def run_scheduler_loop(interval_minutes: int, target: str, times: str = None):
    """
    Runs a background daemon loop using Python's schedule library.
    If times are provided, schedules runs daily at those specific times.
    Otherwise, ticks every interval_minutes.
    """
    try:
        import schedule
    except ImportError:
        logger.error("The 'schedule' library is not installed. Run: pip install schedule")
        sys.exit(1)
        
    logger.info("Starting background scheduler daemon.")
    
    # We maintain a state counter.
    # Note: On startup, we run once immediately.
    iteration = 1
    
    logger.info(f"Executing immediate startup run ({target.upper()})...")
    run_once(target=target)
    
    # Schedule the job
    if times:
        time_list = [t.strip() for t in times.split(',')]
        logger.info(f"Scheduling daily runs at: {', '.join(time_list)}")
        
        for t in time_list:
            prep_t = get_prepare_time(t, minutes=5)
            logger.info(f"  - Preparation scheduled at: {prep_t} for {t} send")
            
            def make_prep_job(target_time):
                def _prep():
                    logger.info(f"Preparation triggered for upcoming {target_time} report.")
                    prepare_report()
                return _prep
                
            def make_send_job(target_time):
                def _send():
                    nonlocal iteration
                    iteration += 1
                    logger.info(f"Scheduler tick: Iteration {iteration} (Target Time: {target_time})")
                    
                    target_to_send = target
                    if target == "all":
                        if iteration % 2 == 0:
                            logger.info("Even interval reached. Sending to BOTH Telegram and WhatsApp.")
                            target_to_send = "all"
                        else:
                            logger.info("Odd interval reached. Sending to Telegram only.")
                            target_to_send = "telegram"
                            
                    send_prepared_report(target=target_to_send)
                return _send
                
            schedule.every().day.at(prep_t).do(make_prep_job(t))
            schedule.every().day.at(t).do(make_send_job(t))
    else:
        logger.info(f"Ticking every {interval_minutes} minutes.")
        def job_interval():
            nonlocal iteration
            iteration += 1
            logger.info(f"Scheduler tick: Iteration {iteration}")
            
            if target == "all":
                if iteration % 2 == 0:
                    logger.info("Even interval reached. Sending to BOTH Telegram and WhatsApp.")
                    run_once(target="all")
                else:
                    logger.info("Odd interval reached. Sending to Telegram only.")
                    run_once(target="telegram")
            else:
                logger.info(f"Interval reached. Sending to {target.upper()} only.")
                run_once(target=target)

        schedule.every(interval_minutes).minutes.do(job_interval)
    
    logger.info("Scheduler is active. Waiting for next run...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user request. Exiting...")
            break
        except Exception as e:
            logger.error(f"Error in scheduler main loop: {str(e)}")
            time.sleep(10) # Avoid rapid looping on persistent errors

def main():
    parser = argparse.ArgumentParser(
        description="Automated IT Helpdesk Kibana Scraper & Reporter"
    )
    
    parser.add_argument(
        "--target", "-t",
        choices=["telegram", "whatsapp", "all"],
        default="all",
        help="Target platform to send the report. (Used in single-execution mode)."
    )
    
    parser.add_argument(
        "--loop", "-l",
        action="store_true",
        help="Run continuously as a background daemon instead of a single execution."
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=120,
        help="Interval in minutes for loop execution. Default is 120 (2 hours)."
    )
    
    parser.add_argument(
        "--times",
        type=str,
        default=config.SCHEDULE_TIMES if hasattr(config, 'SCHEDULE_TIMES') else "",
        help="Comma-separated list of specific times to run daily (e.g., '08:00,12:00,18:00'). Overrides --interval if provided."
    )
    
    args = parser.parse_args()
    
    # Ensure .env is loaded
    if not os.path.exists(".env"):
        logger.warning("Warning: .env file not found. Script will rely on system environment variables.")
        
    if args.loop:
        run_scheduler_loop(args.interval, args.target, args.times)
    else:
        success = run_once(args.target)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
