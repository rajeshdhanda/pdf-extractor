import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# --- Configurations and Constants ---
# DRIVER : https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.58/linux64/chromedriver-linux64.zip 
CHROMEDRIVER_PATH = './chromedriver-linux64/chromedriver'  # Path to the chromedriver executable
MAX_PAGES = 30  # Maximum number of pages to visit per resource
OUTPUT_FILE = 'pdf_configs.json'  # Output file for saving the collected links


# --- List of Resources ---
vision_domain = "https://www.visionias.in"
resources = [
    { 'name': 'Toppers Answer Copy', 'link': '/resources/toppers-answer-copy/' }, 
    { 'name': 'Quick Revision Material', 'link': '/resources/quick-revision-material/' },
    { 'name': 'UPSC Paper Solution', 'link': '/resources/upsc-paper-solution/' },
    { 'name': 'Research and Analysis', 'link': '/resources/research-and-analysis/' },
    { 'name': 'Preparation Strategy', 'link': '/resources/preparation-strategy/' },
    { 'name': 'Value Added Material - GS', 'link': '/resources/vam.php' },
    { 'name': 'Value Addition Optional Subject', 'link': '/resources/vam.php?type=1' },
    { "name": 'Current Affairs', "link": '/resources/current-affairs/' }
]


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --- Function to configure WebDriver ---
def configure_driver():
    """
    Configures the Selenium WebDriver with headless options for scraping.
    """
    logger.info("Configuring WebDriver with headless options...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    logger.info("WebDriver configured successfully.")
    return driver

# --- Function to collect links from a page ---
def collect_links_from_page(driver, url, page_number, resource_name):
    """
    Collects filtered links from a given URL, with pagination support.
    
    Args:
    - driver: Selenium WebDriver instance
    - url: URL of the resource
    - page_number: Current page number being scraped
    - resource_name: Name of the resource for logging
    """
    logger.info(f"Visiting URL: {url} (Page {page_number}) - Resource: {resource_name}")
    driver.get(url)
    links = []

    while True:
        if page_number > MAX_PAGES:  # Break if page number exceeds the limit
            logger.info(f"Exceeded {MAX_PAGES} pages. Stopping the collection for {resource_name}.")
            break

        logger.info(f"Collecting links from Page {page_number} - Resource: {resource_name}")
        link_elements = driver.find_elements(By.TAG_NAME, 'a')
        page_links = []

        # Collect links that match the filter criteria
        for link in link_elements:
            href = link.get_attribute('href')
            if href and href.startswith("https://www.visionias.in/resources/material"):
                page_links.append(href)

        if not page_links:  # If no filtered links were found
            logger.info(f"No valid links found on Page {page_number} for {resource_name}. Breaking loop.")
            break

        links.extend(page_links)
        logger.info(f"Found {len(page_links)} valid links on Page {page_number} for {resource_name}.")

        # Check for the 'Next' button to go to the next page
        if not click_next_button(driver, page_number):
            logger.info("No 'Next' button found, stopping.")
            break

        page_number += 1  # Increment page number after clicking next
    
    links = list(set(links))
    logger.info(f"Collected {len(links)} links from {resource_name}.")
    return links

# --- Function to click 'Next' button ---
def click_next_button(driver, page_number):
    """
    Clicks the 'Next' button to navigate to the next page of the resource.
    
    Args:
    - driver: Selenium WebDriver instance
    - page_number: Current page number
    """
    try:
        logger.info(f"Checking for 'Next' button on Page {page_number}...")
        next_button = driver.find_element(By.CLASS_NAME, 'next')
        actions = ActionChains(driver)
        actions.move_to_element(next_button).click().perform()
        time.sleep(2)  # Wait for the page to load
        logger.info(f"Clicked 'Next' on Page {page_number}.")
        return True
    except Exception as e:
        logger.warning(f"Next button not found or clickable: {e}")
        return False

# --- Function to process URLs and save links ---
def process_urls(resources):
    """
    Processes multiple resource URLs and collects the links for each resource.
    
    Args:
    - resources: List of resources containing name and URL information
    """
    global vision_domain
    all_links = {}
    total_links_collected = 0
    total_pages_visited = 0

    logger.info("Starting to process URLs...")
    driver = configure_driver()

    for resource in resources:
        url = vision_domain + resource['link']
        page_number = 1  # Start from page 1
        logger.info(f"Starting collection from {resource['name']} ({url})...")
        links = collect_links_from_page(driver, url, page_number, resource['name'])
        
        all_links[resource['name']] = links
        total_links_collected += len(links)
        total_pages_visited += len(links) > 0

    logger.info(f"Total Links Collected: {total_links_collected}")
    logger.info(f"Total Pages Visited: {total_pages_visited}")
    logger.info("Saving collected links to JSON...")
    save_links_to_json(all_links)
    driver.quit()

# --- Function to save collected links to JSON ---
def save_links_to_json(all_links):
    """
    Saves the collected links to a JSON file.
    
    Args:
    - all_links: Dictionary containing resource names as keys and collected links as values
    """
    with open(OUTPUT_FILE, 'w') as file:
        json.dump(all_links, file, indent=4)
    logger.info(f"Saved collected links to '{OUTPUT_FILE}'.")

# --- Start the process ---
process_urls(resources)
