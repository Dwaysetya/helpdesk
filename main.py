import argparse
import sys
import logging
import time
import os
from datetime import datetime

import config
from scraper import scrape_all_dashboards
from notifier import format_report_message, send_telegram_message, send_whatsapp_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KibanaAutomation")

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
    # We ask if they want to run immediately, or just start scheduling. Let's run a test run on startup.
    iteration = 1
    
    logger.info(f"Executing immediate startup run ({target.upper()})...")
    run_once(target=target)
    
    def job():
        nonlocal iteration
        iteration += 1
        logger.info(f"Scheduler tick: Iteration {iteration}")
        
        if target == "all":
            # Every even iteration (e.g. 2nd run = 4 hours, 4th run = 8 hours...) send to both.
            if iteration % 2 == 0:
                logger.info("4-hour interval reached. Sending to BOTH Telegram and WhatsApp.")
                run_once(target="all")
            else:
                logger.info("2-hour interval reached. Sending to Telegram only.")
                run_once(target="telegram")
        else:
            logger.info(f"Interval reached. Sending to {target.upper()} only.")
            run_once(target=target)

    # Schedule the job
    if times:
        time_list = [t.strip() for t in times.split(',')]
        logger.info(f"Scheduling daily runs at: {', '.join(time_list)}")
        for t in time_list:
            schedule.every().day.at(t).do(job)
    else:
        logger.info(f"Ticking every {interval_minutes} minutes.")
        schedule.every(interval_minutes).minutes.do(job)
    
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
