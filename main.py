import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from datetime import datetime, time
import schedule
import time as time_module
import logging
import os

# 📧 EMAIL CONFIGURATION
SENDER_EMAIL = os.getenv('GMAIL_USER', 'tvaalioth26@gmail.com')
SENDER_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'afyt pegw jzcg qyho')
RECIPIENT_EMAIL = os.getenv('NOTIFY_EMAIL', 'tvaalioth26@gmail.com')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ⏰ SCHEDULE CONFIGURATION
SCHEDULE_CONFIG = {
    "start_time": "10:00",  # Start checking from 10 AM
    "end_time": "18:00",  # Stop checking at 6 PM
    "check_interval": 2,  # Check every 2 hours
    "timezone_offset": "+05:30"  # IST timezone (adjust if needed)
}

# 🎯 WEBSITE CONFIGURATION
WEBSITE_CONFIG = {
    "medical": {
        "url": "https://www.medadmgujarat.org/ga/home.aspx",
        "name": "Medical Admission Gujarat",
        "scraper_type": "medical"
    },
    "hackernews": {
        "url": "https://news.ycombinator.com",
        "name": "Hacker News",
        "scraper_type": "hackernews"
    },
    "bbc": {
        "url": "https://www.bbc.com/news",
        "name": "BBC News",
        "scraper_type": "bbc"
    },
    "reddit": {
        "url": "https://old.reddit.com/r/all",
        "name": "Reddit",
        "scraper_type": "reddit"
    }
}

# 🔧 DYNAMIC SITE SELECTION - Change via Environment Variable!
CURRENT_SITE = os.getenv('MONITOR_SITE', 'medical')  # Default to medical, change via Railway Variables!

# 📝 Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)


def is_within_schedule():
    """Check if current time is within scheduled hours"""
    now = datetime.now()
    current_time = now.time()

    start_time = time.fromisoformat(SCHEDULE_CONFIG["start_time"])
    end_time = time.fromisoformat(SCHEDULE_CONFIG["end_time"])

    return start_time <= current_time <= end_time


def send_email_notification(subject, body, update_text, site_name, site_url):
    """Send email notification when new update is found"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d73502;">🚨 New Update from {site_name}!</h2>

                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3>Latest Update:</h3>
                    <p style="font-size: 16px; color: #333;">{update_text}</p>
                </div>

                <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Source:</strong> <a href="{site_url}">{site_name}</a></p>
                    <p><strong>Monitoring:</strong> {CURRENT_SITE.upper()}</p>
                </div>

                <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>📅 Schedule:</strong> Daily {SCHEDULE_CONFIG['start_time']} - {SCHEDULE_CONFIG['end_time']}</p>
                    <p><strong>🔄 Interval:</strong> Every {SCHEDULE_CONFIG['check_interval']} hours</p>
                    <p><strong>🎯 Current Site:</strong> {site_name}</p>
                </div>

                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from your Website Monitor.<br>
                    <strong>To change monitored site:</strong> Update MONITOR_SITE environment variable in Railway<br>
                    <strong>Options:</strong> medical, hackernews, bbc, reddit
                </p>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        logging.info("✅ Email notification sent successfully!")
        return True

    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        return False


def scrape_medical_site(url):
    """Scraper for medical admission websites"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        updates_found = []

        all_divs = soup.find_all("div")
        for div in all_divs:
            text = div.get_text(strip=True)
            if "Updated On:" in text and len(text) > 20:
                updates_found.append(text)

        marquees = soup.find_all("marquee")
        for marquee in marquees:
            text = marquee.get_text(strip=True)
            if text and len(text) > 20:
                updates_found.append(text)

        update_containers = soup.find_all(["div", "td", "span"], class_=re.compile(r"update|notice|news", re.I))
        for container in update_containers:
            text = container.get_text(strip=True)
            if text and len(text) > 20:
                updates_found.append(text)

        updates_found = list(dict.fromkeys(updates_found))

        relevant_updates = []
        for update in updates_found:
            if any(keyword in update.lower() for keyword in
                   ["updated on:", "merit list", "admission", "notice", "counselling", "result"]):
                relevant_updates.append(update)

        if relevant_updates:
            return relevant_updates[0]
        elif updates_found:
            return updates_found[0]
        else:
            return "No updates found on the page"

    except Exception as e:
        logging.error(f"Error scraping medical site: {e}")
        return None


def scrape_hackernews(url):
    """Scraper for Hacker News"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        top_story = soup.find("span", class_="titleline")
        if top_story:
            title_link = top_story.find("a")
            if title_link:
                return title_link.get_text(strip=True)

        return "No top story found"

    except Exception as e:
        logging.error(f"Error scraping Hacker News: {e}")
        return None


def scrape_bbc_news(url):
    """Scraper for BBC News"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        headline = soup.find("h2", {"data-testid": "card-headline"})
        if not headline:
            headline = soup.find("h2") or soup.find("h1")

        if headline:
            return headline.get_text(strip=True)

        return "No headline found"

    except Exception as e:
        logging.error(f"Error scraping BBC News: {e}")
        return None


def scrape_reddit(url):
    """Scraper for Reddit"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        top_post = soup.find("a", class_="title")
        if top_post:
            return top_post.get_text(strip=True)

        return "No top post found"

    except Exception as e:
        logging.error(f"Error scraping Reddit: {e}")
        return None


def scrape_website(config):
    """Main scraper function that routes to appropriate scraper"""
    url = config["url"]
    scraper_type = config["scraper_type"]

    if scraper_type == "medical":
        latest_update = scrape_medical_site(url)
    elif scraper_type == "hackernews":
        latest_update = scrape_hackernews(url)
    elif scraper_type == "bbc":
        latest_update = scrape_bbc_news(url)
    elif scraper_type == "reddit":
        latest_update = scrape_reddit(url)
    else:
        logging.error(f"❌ Unknown scraper type: {scraper_type}")
        return None

    if latest_update:
        latest_update = re.sub(r'\s+', ' ', latest_update).strip()
        return latest_update

    return None


def check_for_updates():
    """Main function to check for updates - called by scheduler"""

    # Check if we're within scheduled hours
    if not is_within_schedule():
        current_time = datetime.now().strftime('%H:%M')
        logging.info(f"⏰ Outside schedule hours ({current_time}). Skipping check.")
        return

    # Validate current site
    if CURRENT_SITE not in WEBSITE_CONFIG:
        logging.error(f"❌ Invalid MONITOR_SITE: {CURRENT_SITE}")
        logging.info(f"Valid options: {list(WEBSITE_CONFIG.keys())}")
        return

    config = WEBSITE_CONFIG[CURRENT_SITE]
    site_name = config["name"]

    logging.info(f"🔍 Scheduled check: {site_name} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

    latest_update = scrape_website(config)

    if not latest_update:
        logging.error("❌ Could not fetch updates from website")
        return

    logging.info(f"Latest Update Found: {latest_update[:100]}{'...' if len(latest_update) > 100 else ''}")

    filename = f"last_update_{CURRENT_SITE}.txt"

    try:
        with open(filename, "r", encoding='utf-8') as f:
            last_seen = f.read().strip()

        if latest_update != last_seen:
            logging.info("🚨 NEW UPDATE DETECTED!")

            subject = f"🚨 New Update from {site_name}!"
            body = f"New update detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            email_sent = send_email_notification(subject, body, latest_update, site_name, config["url"])

            if email_sent:
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(latest_update)
                logging.info("📝 Update saved to file")
            else:
                logging.warning("⚠️  Update not saved due to email failure")

        else:
            logging.info("✅ No new updates since last check")

    except FileNotFoundError:
        with open(filename, "w", encoding='utf-8') as f:
            f.write(latest_update)
        logging.info("📝 First run - baseline saved")

        subject = f"📋 {site_name} Monitor Started"
        body = f"Your {site_name} monitor is now active!"
        send_email_notification(subject, body, f"Current status: {latest_update}", site_name, config["url"])


def run_scheduler():
    """Set up and run the scheduler"""

    # Log startup info
    logging.info("🚀 Website Monitor with Dynamic Site Selection Started!")
    logging.info(f"🎯 Current Site: {CURRENT_SITE.upper()}")

    if CURRENT_SITE in WEBSITE_CONFIG:
        logging.info(f"📍 Monitoring: {WEBSITE_CONFIG[CURRENT_SITE]['name']}")
        logging.info(f"🌐 URL: {WEBSITE_CONFIG[CURRENT_SITE]['url']}")
    else:
        logging.error(f"❌ Invalid site: {CURRENT_SITE}")
        logging.info(f"✅ Valid options: {list(WEBSITE_CONFIG.keys())}")
        logging.info("💡 Set MONITOR_SITE environment variable to change site")
        return

    logging.info("💡 To change site: Update MONITOR_SITE environment variable in Railway")
    logging.info(f"📋 Available sites: {', '.join(WEBSITE_CONFIG.keys())}")

    # Schedule checks every 2 hours during business hours
    schedule.every(SCHEDULE_CONFIG['check_interval']).hours.do(check_for_updates)

    # Also run immediately when script starts (if within hours)
    if is_within_schedule():
        logging.info("🚀 Starting immediate check...")
        check_for_updates()
    else:
        logging.info(f"⏰ Outside schedule hours. Next check at {SCHEDULE_CONFIG['start_time']}.")

    logging.info(
        f"📅 Monitor scheduled: {SCHEDULE_CONFIG['start_time']} - {SCHEDULE_CONFIG['end_time']} every {SCHEDULE_CONFIG['check_interval']} hours")

    while True:
        schedule.run_pending()
        time_module.sleep(60)  # Check every minute for scheduled tasks


def main():
    """Main function"""
    run_scheduler()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("🛑 Monitor stopped by user")
    except Exception as e:
        logging.error(f"❌ Monitor error: {e}")