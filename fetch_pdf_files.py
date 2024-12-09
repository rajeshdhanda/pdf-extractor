import os
import json
import time
import shutil
import logging
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging with visuals
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("download_logs.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

def log_visual_separator():
    """
    Log a visual separator for better readability.
    """
    logging.info("===================================================")

def clean_downloads_directory(base_download_dir):
    """
    Clean the downloads directory before starting.
    """
    if os.path.exists(base_download_dir):
        shutil.rmtree(base_download_dir)
        logging.info("🧹 Cleaned downloads directory: %s", base_download_dir)
    os.makedirs(base_download_dir, exist_ok=True)
    logging.info("📂 Created fresh downloads directory: %s", base_download_dir)

def wait_for_download(download_dir, timeout=600, check_interval=5):
    """
    Wait for a download to complete by monitoring the directory for valid files.
    Ensures no temporary files remain.
    """
    logging.info("📂 Monitoring downloads in: %s with timeout %ds", download_dir, timeout)
    elapsed_time = 0
    while elapsed_time < timeout:
        files = os.listdir(download_dir)
        # Check for valid PDF and ensure no temporary files remain
        if any(file.endswith(".pdf") for file in files) and not any(
            file.endswith(".crdownload") or file.startswith(".com.google.Chrome") for file in files
        ):
            logging.info("✅ PDF detected! Monitoring complete.")
            return True
        time.sleep(check_interval)
        elapsed_time += check_interval
    logging.warning("⏰ Timeout reached: No PDF found after %ds in %s", timeout, download_dir)
    return False

def download_pdf(url, resource_name, base_download_dir, retries=3, retry_delay=10):
    """
    Download a PDF from the given URL into a resource-specific folder.
    """
    download_dir = os.path.join(base_download_dir, resource_name)
    os.makedirs(download_dir, exist_ok=True)

    # Generate a unique temporary file name prefix
    temp_prefix = str(uuid.uuid4())

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Configure download settings
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    service = Service('./chromedriver-linux64/chromedriver')  # Update path if needed

    attempt = 0
    while attempt < retries:
        try:
            log_visual_separator()
            logging.info("🌐 Attempting to download: %s (Attempt %d/%d)", url, attempt + 1, retries)
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(600)  # Set high page load timeout
            driver.get(url)

            # Wait for the download button to be clickable
            download_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "downlode-pdf"))
            )

            # Scroll into view and click the button
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            driver.execute_script("arguments[0].click();", download_button)

            # Wait for the download to complete
            if wait_for_download(download_dir):
                logging.info("🎉 PDF download completed successfully for: %s", url)
                log_visual_separator()
                return True  # Success
            else:
                logging.warning("⚠️ Download timed out for: %s", url)

        except Exception as e:
            logging.error("❌ Error during download attempt %d/%d for %s - %s", attempt + 1, retries, url, e)

        finally:
            driver.quit()
            attempt += 1
            if attempt < retries:
                logging.info("🔄 Retrying download after %d seconds...", retry_delay)
                time.sleep(retry_delay)

    logging.error("❌ Failed to download after %d attempts for: %s", retries, url)
    return False  # Failure

def download_all_pdfs_from_json(json_file_path, base_download_dir):
    """
    Download PDFs for all resources listed in a JSON file.
    """
    # Clean downloads directory before starting
    clean_downloads_directory(base_download_dir)

    with open(json_file_path, 'r') as file:
        resources = json.load(file)

    failed_downloads = []  # Track failed downloads
    total_downloads = 0  # Counter for successful downloads

    for resource_name, urls in resources.items():
        log_visual_separator()
        logging.info("📖 Starting downloads for resource: %s", resource_name)
        resource_success_count = 0
        for url in urls:
            success = download_pdf(url, resource_name, base_download_dir)
            if success:
                total_downloads += 1
                resource_success_count += 1
            else:
                failed_downloads.append((url, resource_name))
        logging.info("📊 Successfully downloaded %d files for resource: %s", resource_success_count, resource_name)

    # Retry failed downloads
    if failed_downloads:
        log_visual_separator()
        logging.info("🔁 Retrying %d failed downloads after processing all files...", len(failed_downloads))
        time.sleep(30)  # Wait before retrying
        for url, resource_name in failed_downloads:
            logging.info("🔄 Retrying download for: %s", url)
            success = download_pdf(url, resource_name, base_download_dir)
            if success:
                total_downloads += 1
            else:
                logging.error("❌ Final failure for: %s", url)

    log_visual_separator()
    logging.info("🏁 All downloads completed. Total successful downloads: %d", total_downloads)

# Example usage
if __name__ == "__main__":
    json_file_path = 'resources.json'  # Path to your JSON file
    base_download_dir = os.path.join(os.getcwd(), "downloads")
    download_all_pdfs_from_json(json_file_path, base_download_dir)
