import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from datetime import datetime

# 📧 EMAIL CONFIGURATION
SENDER_EMAIL = "tvaalioth26@gmail.com"
SENDER_PASSWORD = "afyt pegw jzcg qyho"
RECIPIENT_EMAIL = "tvaalioth26@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 🎯 WEBSITE CONFIGURATION - CHANGE THIS!
WEBSITE_CONFIG = {
    # Option 1: Medical Admission Site
    "medical": {
        "url": "https://www.medadmgujarat.org/ga/home.aspx",
        "name": "Medical Admission Gujarat",
        "scraper_type": "medical"
    },

    # Option 2: Hacker News
    "hackernews": {
        "url": "https://news.ycombinator.com/newest",
        "name": "Hacker News",
        "scraper_type": "hackernews"
    },

    # Option 3: BBC News
    "bbc": {
        "url": "https://www.bbc.com/news",
        "name": "BBC News",
        "scraper_type": "bbc"
    },

    # Option 4: Reddit
    "reddit": {
        "url": "https://old.reddit.com/r/all",
        "name": "Reddit",
        "scraper_type": "reddit"
    }
}

# 🔧 CHANGE THIS TO SWITCH WEBSITES!
CURRENT_SITE = "hackernews"  # Change to: "medical", "hackernews", "bbc", "reddit"


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
                </div>

                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from your Website Monitor.<br>
                    Please check the official website for complete details.
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

        print("✅ Email notification sent successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def scrape_medical_site(url):
    """Scraper for medical admission websites"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        updates_found = []

        # Look for divs containing "Updated On:" pattern
        all_divs = soup.find_all("div")
        for div in all_divs:
            text = div.get_text(strip=True)
            if "Updated On:" in text and len(text) > 20:
                updates_found.append(text)

        # Check marquee tags
        marquees = soup.find_all("marquee")
        for marquee in marquees:
            text = marquee.get_text(strip=True)
            if text and len(text) > 20:
                updates_found.append(text)

        # Look for update containers
        update_containers = soup.find_all(["div", "td", "span"], class_=re.compile(r"update|notice|news", re.I))
        for container in update_containers:
            text = container.get_text(strip=True)
            if text and len(text) > 20:
                updates_found.append(text)

        # Remove duplicates and filter relevant updates
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
        print(f"Error scraping medical site: {e}")
        return None


def scrape_hackernews(url):
    """Scraper for Hacker News"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Get the top story title
        top_story = soup.find("span", class_="titleline")
        if top_story:
            title_link = top_story.find("a")
            if title_link:
                return title_link.get_text(strip=True)

        return "No top story found"

    except Exception as e:
        print(f"Error scraping Hacker News: {e}")
        return None


def scrape_bbc_news(url):
    """Scraper for BBC News"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Look for main headline
        headline = soup.find("h2", {"data-testid": "card-headline"})
        if not headline:
            headline = soup.find("h2") or soup.find("h1")

        if headline:
            return headline.get_text(strip=True)

        return "No headline found"

    except Exception as e:
        print(f"Error scraping BBC News: {e}")
        return None


def scrape_reddit(url):
    """Scraper for Reddit"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Get the top post title
        top_post = soup.find("a", class_="title")
        if top_post:
            return top_post.get_text(strip=True)

        return "No top post found"

    except Exception as e:
        print(f"Error scraping Reddit: {e}")
        return None


def scrape_website(config):
    """Main scraper function that routes to appropriate scraper"""
    url = config["url"]
    scraper_type = config["scraper_type"]

    print(f"🔍 Scraping {config['name']}...")

    if scraper_type == "medical":
        latest_update = scrape_medical_site(url)
    elif scraper_type == "hackernews":
        latest_update = scrape_hackernews(url)
    elif scraper_type == "bbc":
        latest_update = scrape_bbc_news(url)
    elif scraper_type == "reddit":
        latest_update = scrape_reddit(url)
    else:
        print(f"❌ Unknown scraper type: {scraper_type}")
        return None

    if latest_update:
        # Clean up text
        latest_update = re.sub(r'\s+', ' ', latest_update).strip()
        return latest_update

    return None


def main():
    """Main function to check for updates and send notifications"""

    # Get current website config
    if CURRENT_SITE not in WEBSITE_CONFIG:
        print(f"❌ Unknown site: {CURRENT_SITE}")
        print(f"Available sites: {list(WEBSITE_CONFIG.keys())}")
        return

    config = WEBSITE_CONFIG[CURRENT_SITE]
    site_name = config["name"]

    print(f"🔍 Checking {site_name} for updates... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

    # Scrape for updates
    latest_update = scrape_website(config)

    if not latest_update:
        print("❌ Could not fetch updates from website")
        return

    print("Latest Update Found:", latest_update[:100] + "..." if len(latest_update) > 100 else latest_update)

    # Check against previous update
    filename = f"last_update_{CURRENT_SITE}.txt"

    try:
        with open(filename, "r", encoding='utf-8') as f:
            last_seen = f.read().strip()

        if latest_update != last_seen:
            print("🚨 NEW UPDATE DETECTED!")

            # Send email notification
            subject = f"🚨 New Update from {site_name}!"
            body = f"New update detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            email_sent = send_email_notification(subject, body, latest_update, site_name, config["url"])

            if email_sent:
                # Save new update only if email was sent successfully
                with open(filename, "w", encoding='utf-8') as f:
                    f.write(latest_update)
                print("📝 Update saved to file")
            else:
                print("⚠️  Update not saved due to email failure")

        else:
            print("✅ No new updates since last check")

    except FileNotFoundError:
        # First run
        with open(filename, "w", encoding='utf-8') as f:
            f.write(latest_update)
        print("📝 First run - baseline saved")

        # Send initial notification
        subject = f"📋 {site_name} Monitor Started"
        body = f"Your {site_name} monitor is now active!"
        send_email_notification(subject, body, f"Current status: {latest_update}", site_name, config["url"])


if __name__ == "__main__":
    main()