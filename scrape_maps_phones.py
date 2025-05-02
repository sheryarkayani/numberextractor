import time
import csv
import re
import os
import logging
import random
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
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

def setup_driver():
    """Set up Chrome driver, headless for production, visible for local."""
    logging.info("Initializing Chrome browser...")
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    
    is_headless = os.getenv("HEADLESS", "false").lower() == "true"
    if is_headless:
        logging.info("Running in headless mode for production.")
        chrome_options.add_argument("--headless=new")
    
    try:
        service = Service(ChromeDriverManager().install())
        logging.info("Starting ChromeDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        if not is_headless:
            driver.maximize_window()
        logging.info("Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error initializing Chrome driver: {str(e)}")
        return None

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
    retry=retry_if_exception_type((TimeoutException, StaleElementReferenceException))
)
def scroll_and_paginate(driver, scroll_pane_selector, max_time=300):
    """Scroll and paginate Google Maps results until no more pages."""
    logging.info("Scrolling and paginating Google Maps results...")
    try:
        start_time = time.time()
        while time.time() - start_time < max_time:
            try:
                scroll_pane = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, scroll_pane_selector))
                )
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_pane)
                time.sleep(random.uniform(1, 3))  # Random delay
            except TimeoutException:
                logging.warning("Timeout scrolling results pane.")
            
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Next']")
                if next_button.get_attribute("disabled"):
                    logging.info("No more pages to load.")
                    return True
                logging.info("Clicking 'Next' to load more results...")
                next_button.click()
                WebDriverWait(driver, 5).until(EC.staleness_of(next_button))
                time.sleep(random.uniform(1, 3))
            except NoSuchElementException:
                logging.info("No 'Next' button found. End of results.")
                return True
            except TimeoutException:
                logging.warning("Timeout loading next page.")
        logging.info("Max pagination time reached.")
        return False
    except Exception as e:
        logging.error(f"Error scrolling/paginating: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(TimeoutException)
)
def get_business_links(driver, results_selector):
    """Extract links to business details pages."""
    logging.info("Extracting business detail page links...")
    try:
        results = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, results_selector))
        )
        links = []
        for result in results:
            try:
                link = result.get_attribute("href")
                if link and "https://www.google.com/maps/place/" in link:
                    links.append(link)
            except StaleElementReferenceException:
                continue
        logging.info(f"Found {len(links)} business links.")
        return links
    except TimeoutException:
        logging.warning("Timeout while loading business results.")
        return []
    except Exception as e:
        logging.error(f"Error extracting business links: {str(e)}")
        return []

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((TimeoutException, StaleElementReferenceException))
)
def extract_business_info(driver, url):
    """Extract business name, website URL, and phone number from a business details page."""
    logging.info(f"Visiting business page: {url}")
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        business_name = ""
        try:
            name_element = driver.find_element(By.TAG_NAME, "h1")
            business_name = name_element.text.strip()
            logging.info(f"Business name: {business_name}")
        except NoSuchElementException:
            logging.warning("No business name found.")
        
        website = ""
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-item-id*='authority']")
            website = clean_url(website_element.get_attribute("href"))
            logging.info(f"Found website: {website}")
        except NoSuchElementException:
            logging.info("No website link found.")
        
        phone = ""
        try:
            phone_element = driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
            phone = clean_phone(phone_element.get_attribute("aria-label").replace("Phone:", "").strip())
            logging.info(f"Found phone: {phone}")
        except NoSuchElementException:
            logging.info("No phone number found.")
        
        time.sleep(random.uniform(1, 2))  # Random delay
        return business_name, website, phone
    except TimeoutException:
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
    driver = setup_driver()
    if not driver:
        logging.error("Failed to initialize driver. Aborting scrape.")
        return []

    start_time = time.time()
    businesses = set()
    try:
        logging.info("Navigating to Google Maps...")
        driver.get("https://www.google.com/maps")
        time.sleep(random.uniform(2, 4))
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            logging.info(f"Searching for: {search_term}")
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.ENTER)
            time.sleep(random.uniform(2, 4))
        except TimeoutException:
            logging.error("Timeout waiting for search box. Possible CAPTCHA or network issue.")
            driver.quit()
            return []
        
        scroll_pane_selector = "div[role='feed']"
        results_selector = "a[href*='/maps/place/']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, scroll_pane_selector))
        )
        
        if not scroll_and_paginate(driver, scroll_pane_selector, max_time):
            logging.warning("Pagination incomplete due to timeout or error.")
        
        business_links = get_business_links(driver, results_selector)
        if not business_links:
            logging.warning("No business links found.")
        
        for i, link in enumerate(business_links, 1):
            if time.time() - start_time > max_time:
                logging.info(f"Stopping scrape: Time limit reached after {len(businesses)} businesses.")
                break
            logging.info(f"Processing business {i}/{len(business_links)}...")
            name, website, phone = extract_business_info(driver, link)
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
        logging.info("Closing Chrome browser...")
        try:
            driver.quit()
        except:
            pass
    
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