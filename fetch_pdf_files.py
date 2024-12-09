import os
import time
import json
import uuid
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_id_from_url(url):
    """
    Extract the 'id' parameter from the URL to use in the filename.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("id", ["unknown"])[0]

def validate_url(url):
    """
    Validate if the URL is accessible by sending a HEAD request.
    """
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logging.info("🌐 URL is valid: %s", url)
            return True
        else:
            logging.warning("⚠️ URL returned status code %d: %s", response.status_code, url)
    except Exception as e:
        logging.error("❌ Error validating URL %s - %s", url, e)
    return False

def wait_for_download(download_dir, timeout=600, check_interval=5):
    """
    Wait for a download to complete by monitoring for new files.
    """
    logging.info("📂 Monitoring downloads in: %s with timeout %ds", download_dir, timeout)
    start_time = time.time()
    elapsed_time = 0

    while elapsed_time < timeout:
        files = os.listdir(download_dir)
        # Get only newly created PDF files
        pdf_files = [
            file for file in files
            if file.endswith(".pdf") and os.path.getmtime(os.path.join(download_dir, file)) > start_time
        ]
        
        if pdf_files:
            logging.info("✅ New PDF detected! Monitoring complete.")
            return pdf_files[0]  # Return the first detected file
        time.sleep(check_interval)
        elapsed_time = time.time() - start_time

    logging.warning("⏰ Timeout reached: No new PDF found after %ds in %s", timeout, download_dir)
    return None

def download_and_rename_pdf(url, resource_name, base_download_dir, retries=3, retry_delay=10):
    """
    Download a PDF and rename it after ensuring completion.
    """
    download_dir = os.path.join(base_download_dir, resource_name)
    os.makedirs(download_dir, exist_ok=True)

    file_id = extract_id_from_url(url)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    service = Service('./chromedriver-linux64/chromedriver')

    for attempt in range(retries):
        try:
            logging.info("🌐 Attempt %d/%d: Starting download for URL: %s", attempt + 1, retries, url)
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            download_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "downlode-pdf"))
            )
            driver.execute_script("arguments[0].click();", download_button)

            downloaded_file = wait_for_download(download_dir)
            if downloaded_file:
                downloaded_filepath = os.path.join(download_dir, downloaded_file)
                logging.info("📥 Download complete: %s", downloaded_filepath)
                downloaded_filepath_renamed = downloaded_filepath.split(".pdf")[0] + f"{file_id}.pdf"
                os.rename(downloaded_filepath, downloaded_filepath_renamed)
                logging.info("🎉 File renamed to: %s", downloaded_filepath_renamed)
                return True
            else:
                logging.warning("⚠️ No new PDF file found after waiting.")

        except Exception as e:
            logging.error("❌ Download attempt %d/%d failed for URL %s - %s", attempt + 1, retries, url, e)

        finally:
            if 'driver' in locals():
                driver.quit()

        if attempt < retries - 1:
            logging.info("🔄 Retrying download after %d seconds...", retry_delay)
            time.sleep(retry_delay)

    logging.error("❌ Failed to download after %d attempts for URL: %s", retries, url)
    return False

def download_all_pdfs_from_json(json_file_path, base_download_dir):
    """
    Download PDFs for all resources listed in a JSON file, ensuring sequential downloads.
    """
    with open(json_file_path, 'r') as file:
        resources = json.load(file)

    for resource_name, urls in resources.items():
        logging.info("📖 Starting downloads for resource: %s", resource_name)
        for url in urls:
            if validate_url(url):
                success = download_and_rename_pdf(url, resource_name, base_download_dir)
                if not success:
                    logging.error("🚫 Skipping URL due to repeated failures: %s", url)

if __name__ == "__main__":
    json_file_path = "resources.json"
    base_download_dir = os.path.join(os.getcwd(), "downloads")
    download_all_pdfs_from_json(json_file_path, base_download_dir)
