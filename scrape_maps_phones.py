import time
import csv
import re
import os
import logging
import random
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def setup_browser():
    """Set up Playwright Chromium browser, headless for production."""
    logging.info("Initializing Chromium browser...")
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        logging.info("Chromium browser initialized successfully.")
        return browser, context
    except Exception as e:
        logging.error(f"Error initializing browser: {str(e)}")
        return None, None

def clean_url(url):
    """Clean URL to remove query strings and fragments."""
    if not url:
        return ""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def clean_phone(phone):
    """Clean and validate phone number."""
    if not phone:
        return ""
    phone = re.sub(r'[^\d+]', '', phone)
    if re.match(r'^\+?\d{7,}$', phone):
        return phone
    return ""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(PlaywrightTimeoutError)
)
def scroll_and_paginate(page, scroll_pane_selector, max_time=300):
    """Scroll and paginate Google Maps results until no more pages."""
    logging.info("Scrolling and paginating Google Maps results...")
    try:
        start_time = time.time()
        while time.time() - start_time < max_time:
            try:
                page.wait_for_selector(scroll_pane_selector, timeout=5000)
                page.evaluate("selector => document.querySelector(selector).scrollTo(0, document.querySelector(selector).scrollHeight)", scroll_pane_selector)
                time.sleep(random.uniform(1, 3))
            except PlaywrightTimeoutError:
                logging.warning("Timeout scrolling results pane.")
            
            try:
                next_button = page.query_selector("button[aria-label*='Next']")
                if not next_button or next_button.get_attribute("disabled"):
                    logging.info("No more pages to load.")
                    return True
                logging.info("Clicking 'Next' to load more results...")
                next_button.click()
                time.sleep(random.uniform(1, 3))
            except Exception:
                logging.info("No 'Next' button found. End of results.")
                return True
        logging.info("Max pagination time reached.")
        return False
    except Exception as e:
        logging.error(f"Error scrolling/paginating: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(PlaywrightTimeoutError)
)
def get_business_links(page, results_selector):
    """Extract links to business details pages."""
    logging.info("Extracting business detail page links...")
    try:
        page.wait_for_selector(results_selector, timeout=5000)
        links = page.query_selector_all(results_selector)
        business_links = [link.get_attribute("href") for link in links if link.get_attribute("href") and "https://www.google.com/maps/place/" in link.get_attribute("href")]
        logging.info(f"Found {len(business_links)} business links.")
        return business_links
    except PlaywrightTimeoutError:
        logging.warning("Timeout while loading business results.")
        return []
    except Exception as e:
        logging.error(f"Error extracting business links: {str(e)}")
        return []

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(PlaywrightTimeoutError)
)
def extract_business_info(page, url):
    """Extract business name, website URL, and phone number from a business details page."""
    logging.info(f"Visiting business page: {url}")
    try:
        page.goto(url)
        page.wait_for_selector("h1", timeout=5000)
        
        business_name = ""
        try:
            business_name = page.query_selector("h1").inner_text().strip()
            logging.info(f"Business name: {business_name}")
        except Exception:
            logging.warning("No business name found.")
        
        website = ""
        try:
            website_element = page.query_selector("a[data-item-id*='authority']")
            if website_element:
                website = clean_url(website_element.get_attribute("href"))
                logging.info(f"Found website: {website}")
        except Exception:
            logging.info("No website link found.")
        
        phone = ""
        try:
            phone_element = page.query_selector("button[data-item-id*='phone']")
            if phone_element:
                phone = clean_phone(phone_element.get_attribute("aria-label").replace("Phone:", "").strip())
                logging.info(f"Found phone: {phone}")
        except Exception:
            logging.info("No phone number found.")
        
        time.sleep(random.uniform(1, 2))
        return business_name, website, phone
    except PlaywrightTimeoutError:
        logging.warning(f"Timeout loading business page: {url}.")
        return "", "", ""
    except Exception as e:
        logging.error(f"Error processing business page {url}: {str(e)}")
        return "", "", ""

def save_to_csv(businesses, filename="phones.csv"):
    """Save business names, websites, and phone numbers to a CSV file."""
    logging.info(f"Saving {len(businesses)} businesses to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Business Name', 'Website', 'Phone'])
            for name, website, phone in businesses:
                writer.writerow([name, website or 'N/A', phone or 'N/A'])
        logging.info(f"Businesses successfully saved to {filename}.")
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")

def save_websites_to_csv(businesses, filename="websites.csv"):
    """Save business names and website URLs to a CSV file."""
    logging.info(f"Saving {len(businesses)} businesses to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Business Name', 'Website'])
            for name, website, _ in businesses:
                if website:
                    writer.writerow([name, website])
        logging.info(f"Websites successfully saved to {filename}.")
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")

def scrape_google_maps(search_term, max_time=600):
    """Scrape business names, website URLs, and phone numbers from Google Maps."""
    browser, context = setup_browser()
    if not browser or not context:
        logging.error("Failed to initialize browser. Aborting scrape.")
        return []
    
    page = context.new_page()
    start_time = time.time()
    businesses = set()
    try:
        logging.info("Navigating to Google Maps...")
        page.goto("https://www.google.com/maps")
        time.sleep(random.uniform(2, 4))
        try:
            page.wait_for_selector("#searchboxinput", timeout=10000)
            page.fill("#searchboxinput", search_term)
            page.keyboard.press("Enter")
            time.sleep(random.uniform(2, 4))
        except PlaywrightTimeoutError:
            logging.error("Timeout waiting for search box. Possible CAPTCHA or network issue.")
            page.close()
            browser.close()
            return []
        
        scroll_pane_selector = "div[role='feed']"
        results_selector = "a[href*='/maps/place/']"
        page.wait_for_selector(scroll_pane_selector, timeout=10000)
        
        if not scroll_and_paginate(page, scroll_pane_selector, max_time):
            logging.warning("Pagination incomplete due to timeout or error.")
        
        business_links = get_business_links(page, results_selector)
        if not business_links:
            logging.warning("No business links found.")
        
        for i, link in enumerate(business_links, 1):
            if time.time() - start_time > max_time:
                logging.info(f"Stopping scrape: Time limit reached after {len(businesses)} businesses.")
                break
            logging.info(f"Processing business {i}/{len(business_links)}...")
            name, website, phone = extract_business_info(page, link)
            if name or website or phone:
                businesses.add((name, website, phone))
        
    except KeyboardInterrupt:
        logging.info("User interrupted scraping. Saving progress...")
        save_to_csv(businesses)
        save_websites_to_csv(businesses)
        raise
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
    finally:
        logging.info("Closing browser...")
        page.close()
        browser.close()
    
    businesses = list(businesses)
    elapsed_time = time.time() - start_time
    logging.info(f"Scraping completed in {elapsed_time:.2f} seconds. Collected {len(businesses)} businesses.")
    return businesses

def main(search_term):
    """Main function to run the Google Maps scraper."""
    logging.info(f"\n=== Starting Google Maps Scrape for: {search_term} ===")
    try:
        businesses = scrape_google_maps(search_term)
        if businesses:
            logging.info(f"\nFound {len(businesses)} unique businesses:")
            for i, (name, website, phone) in enumerate(businesses, 1):
                logging.info(f"{i}. {name}: {website or 'N/A'}, {phone or 'N/A'}")
            save_to_csv(businesses)
            save_websites_to_csv(businesses)
        else:
            logging.info("No businesses found.")
        return businesses
    except KeyboardInterrupt:
        logging.info("\nScraping stopped by user.")
        return []

if __name__ == "__main__":
    search_term = input("Enter the search term (e.g., dental clinics in Lahore): ").strip()
    main(search_term)