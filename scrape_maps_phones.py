import time
import csv
import re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

def setup_driver():
    """Set up visible Chrome driver with compatible ChromeDriver."""
    print("Initializing Chrome browser (visible mode)...")
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        # Attempt to get the latest compatible ChromeDriver
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        print("Chrome browser opened successfully.")
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        print("Attempting to use a fallback ChromeDriver version...")
        try:
            # Fallback to a known compatible version (e.g., for Chrome 126)
            service = Service(ChromeDriverManager(version="126.0.6478.126").install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.maximize_window()
            print("Fallback ChromeDriver initialized successfully.")
            return driver
        except Exception as fallback_e:
            print(f"Fallback failed: {fallback_e}")
            print("Ensure Google Chrome is installed and compatible with webdriver-manager.")
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

def scroll_and_paginate(driver, scroll_pane_selector, max_time=120):
    """Scroll and paginate Google Maps results to load more businesses."""
    print("Scrolling and paginating Google Maps results...")
    try:
        start_time = time.time()
        while time.time() - start_time < max_time:
            try:
                scroll_pane = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, scroll_pane_selector))
                )
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_pane)
                time.sleep(1)
            except TimeoutException:
                print("Timeout scrolling results pane.")
            
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
                if next_button.get_attribute("disabled"):
                    print("No more pages to load.")
                    break
                print("Clicking 'Next' to load more results...")
                next_button.click()
                WebDriverWait(driver, 5).until(
                    EC.staleness_of(next_button)
                )
                time.sleep(2)
            except NoSuchElementException:
                print("No 'Next' button found.")
                break
            except TimeoutException:
                print("Timeout loading next page.")
                break
    except Exception as e:
        print(f"Error scrolling/paginating: {e}")

def get_business_links(driver, results_selector):
    """Extract links to business details pages."""
    print("Extracting business detail page links...")
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
            except:
                continue
        print(f"Found {len(links)} business links.")
        return links
    except TimeoutException:
        print("Timeout while loading business results.")
        return []
    except Exception as e:
        print(f"Error extracting business links: {e}")
        return []

def extract_business_info(driver, url):
    """Extract business name, website URL, and phone number from a business details page."""
    print(f"Visiting business page: {url}")
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        business_name = ""
        try:
            name_element = driver.find_element(By.TAG_NAME, "h1")
            business_name = name_element.text.strip()
            print(f"Business name: {business_name}")
        except NoSuchElementException:
            print("No business name found.")
        
        website = ""
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, "a[data-item-id*='authority']")
            website = clean_url(website_element.get_attribute("href"))
            print(f"Found website: {website}")
        except NoSuchElementException:
            print("No website link found.")
        
        phone = ""
        try:
            phone_element = driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
            phone = clean_phone(phone_element.get_attribute("aria-label").replace("Phone:", "").strip())
            print(f"Found phone: {phone}")
        except NoSuchElementException:
            print("No phone number found.")
        
        return business_name, website, phone
    except TimeoutException:
        print(f"Timeout loading business page: {url}.")
        return "", "", ""
    except Exception as e:
        print(f"Error processing business page {url}: {e}")
        return "", "", ""

def save_to_csv(businesses, filename="phones.csv"):
    """Save business names, websites, and phone numbers to a CSV file."""
    print(f"Saving {len(businesses)} businesses to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Business Name', 'Website', 'Phone'])
            for name, website, phone in businesses:
                writer.writerow([name, website or 'N/A', phone or 'N/A'])
        print(f"Businesses successfully saved to {filename}.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def save_websites_to_csv(businesses, filename="websites.csv"):
    """Save business names and website URLs to a CSV file."""
    print(f"Saving {len(businesses)} businesses to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Business Name', 'Website'])
            for name, website, _ in businesses:
                if website:
                    writer.writerow([name, website])
        print(f"Websites successfully saved to {filename}.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def scrape_google_maps(search_term, max_time=300):
    """Scrape business names, website URLs, and phone numbers from Google Maps."""
    driver = setup_driver()
    if not driver:
        return []

    start_time = time.time()
    businesses = set()
    try:
        print("Navigating to Google Maps...")
        driver.get("https://www.google.com/maps")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
        
        print(f"Searching for: {search_term}")
        search_box = driver.find_element(By.ID, "searchboxinput")
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.ENTER)
        
        scroll_pane_selector = "div[role='feed']"
        results_selector = "a[href*='/maps/place/']"
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, scroll_pane_selector))
        )
        
        scroll_and_paginate(driver, scroll_pane_selector)
        
        business_links = get_business_links(driver, results_selector)
        
        target_businesses = 150
        for i, link in enumerate(business_links, 1):
            if time.time() - start_time > max_time or len(businesses) >= target_businesses:
                print(f"Stopping scrape: {len(businesses)} businesses collected or time limit reached.")
                break
            print(f"Processing business {i}/{len(business_links)}...")
            name, website, phone = extract_business_info(driver, link)
            if name or website or phone:
                businesses.add((name, website, phone))
        
    except KeyboardInterrupt:
        print("\nUser interrupted scraping (Ctrl+C). Saving progress...")
        save_to_csv(businesses)
        save_websites_to_csv(businesses)
        raise
    except TimeoutException:
        print("Timeout during Google Maps search.")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        print("Closing Chrome browser...")
        try:
            driver.quit()
        except:
            pass
    
    businesses = list(businesses)
    elapsed_time = time.time() - start_time
    print(f"Scraping completed in {elapsed_time:.2f} seconds. Collected {len(businesses)} businesses.")
    return businesses

def main(search_term):
    """Main function to run the Google Maps scraper."""
    print(f"\n=== Starting Google Maps Scrape for: {search_term} ===")
    try:
        businesses = scrape_google_maps(search_term)
        if businesses:
            print(f"\nFound {len(businesses)} unique businesses:")
            for i, (name, website, phone) in enumerate(businesses, 1):
                print(f"{i}. {name}: {website or 'N/A'}, {phone or 'N/A'}")
            save_to_csv(businesses)
            save_websites_to_csv(businesses)
        else:
            print("No businesses found.")
        return businesses
    except KeyboardInterrupt:
        print("\nScraping stopped by user.")
        return []

if __name__ == "__main__":
    search_term = input("Enter the search term (e.g., dental clinics in London): ").strip()
    main(search_term)