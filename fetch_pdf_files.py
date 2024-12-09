import os
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("download_logs.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

def download_pdf(url, resource_name, base_download_dir, retries=3, retry_delay=5):
    """Download a PDF from the given URL into a resource-specific folder."""
    download_dir = os.path.join(base_download_dir, resource_name)
    os.makedirs(download_dir, exist_ok=True)

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
            logging.info(f"Attempting to download from URL: {url} (Attempt {attempt + 1}/{retries})")
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            # Wait for the download button to be clickable
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "downlode-pdf"))
            )

            # Scroll into view and click the button
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            driver.execute_script("arguments[0].click();", download_button)

            logging.info(f"PDF download initiated. Monitoring downloads in: {download_dir}")

            # Monitor the download directory for completion
            for _ in range(60):  # Wait up to 60 seconds for the download to complete
                files = os.listdir(download_dir)
                if any(file.endswith(".pdf") for file in files):
                    logging.info(f"PDF download completed! Saved in: {download_dir}")
                    return  # Exit the function if download succeeds
                time.sleep(1)

            logging.warning(f"Download timed out for URL: {url}")

        except Exception as e:
            logging.error(f"Error during download attempt {attempt + 1}/{retries} for URL: {url} - {e}")

        finally:
            driver.quit()
            attempt += 1
            if attempt < retries:
                logging.info(f"Retrying download after {retry_delay} seconds...")
                time.sleep(retry_delay)

    logging.error(f"Failed to download PDF after {retries} attempts for URL: {url}")


def download_all_pdfs_from_json(json_file_path, base_download_dir):
    """Download PDFs for all resources listed in a JSON file."""
    with open(json_file_path, 'r') as file:
        resources = json.load(file)

    for resource_name, urls in resources.items():
        logging.info(f"Starting downloads for resource: {resource_name}")
        for url in urls:
            download_pdf(url, resource_name, base_download_dir)


# Example usage
if __name__ == "__main__":
    json_file_path = 'resources.json'  
    base_download_dir = os.path.join(os.getcwd(), "downloads")
    download_all_pdfs_from_json(json_file_path, base_download_dir)
