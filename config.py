import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Telegram configuration
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE_NUMBER = os.getenv("TELEGRAM_PHONE_NUMBER", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080/message/sendText")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_RECIPIENT_PHONE = os.getenv("WHATSAPP_RECIPIENT_PHONE", "")

# Playwright Settings
HEADLESS = os.getenv("KIBANA_HEADLESS", "True").lower() in ("true", "1", "yes")
# Playwright timeout in milliseconds (default 60 seconds)
TIMEOUT_MS = int(os.getenv("KIBANA_TIMEOUT_MS", "60000"))

# Kibana Credentials
KIBANA_USERNAME = os.getenv("KIBANA_USERNAME", "elastic")
KIBANA_PASSWORD = os.getenv("KIBANA_PASSWORD", "ZOKBvOoqNBFrbtaVsVFd")

# Grafana Settings
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://10.60.168.11:3030/d/84ff48f1-3262-475b-9bf5-809793699f2a/mo-dimas-aggr?from=now-3h&to=now")
GRAFANA_USERNAME = os.getenv("GRAFANA_USERNAME", "tma-dev")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "e1e175013a75")

# Report Time Format:
# Use "%H.00" to display only the current hour (e.g. 15.00)
# Use "%H.%M" to display the exact minute of execution (e.g. 15.28)
REPORT_TIME_FORMAT = "%H.%M"

# Schedule Times (comma-separated, e.g., '08:00,12:00,16:00')
SCHEDULE_TIMES = os.getenv("SCHEDULE_TIMES", "")
WHATSAPP_SCHEDULE_TIMES = os.getenv("WHATSAPP_SCHEDULE_TIMES", "")

# Kibana Dashboards Configuration
# We specify the URL and selectors (CSS Selector or XPath) for each dashboard.
# Playwright supports both:
#   - CSS selector (e.g. 'div.total-hits-value')
#   - XPath (e.g. 'xpath=//span[@class="hits"]') or starts with '//'
DASHBOARDS = {
    "assurance": {
        "name": "Assurance Q4",
        "url": "http://10.60.168.41:5601/app/dashboards#/view/22164c79-5342-4bb6-8761-22f42c1572b4?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))",
        "total_hits_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Total API Hit"]) p.echMetricText__value',
        "success_rate_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Succes Rate Service"]) p.echMetricText__value',
    },
    "surrounding": {
        "name": "Surrounding Q4",
        "url": "http://10.60.168.41:5601/app/dashboards#/view/6f7201bd-fd5a-4164-87b4-61a2ae4d81fb?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))",
        "total_hits_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Total API Hit"]) p.echMetricText__value',
        "success_rate_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Succes Rate Service"]) p.echMetricText__value',
    },
    "homepass": {
        "name": "Homepass Q4",
        "url": "http://10.60.168.41:5601/app/dashboards#/view/f2eebe08-f7ab-4f81-8c9d-bd05b4c62873?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))",
        "total_hits_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Total API Hit"]) p.echMetricText__value',
        "success_rate_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Succes Rate Service"]) p.echMetricText__value',
    },
    "reservasi_homepass": {
        "name": "Reservasi Homepass Q4",
        "url": "http://10.60.168.41:5601/app/dashboards#/view/5752234c-1e75-469b-8e91-9960ffdef562?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now%2Fd,to:now%2Fd))",
        "total_id_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="Total API Hit"]) p.echMetricText__value',
        "success_rate_selector": 'div[data-test-subj="embeddablePanel"]:has(span[title="P95 Latency"]) p.echMetricText__value',
    }
}
