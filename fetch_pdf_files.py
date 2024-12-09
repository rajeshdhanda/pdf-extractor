import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_pdf(url):
    # Extract "type" parameter from URL
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    folder_name = query_params.get("type", ["default"])[0]

    # Create a download directory for the specific type
    download_dir = os.path.join(os.getcwd(), "downloads", folder_name)
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Configure download settings
    prefs = {
        "download.default_directory": download_dir,  # Set specific download directory
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    service = Service('./chromedriver-linux64/chromedriver')  # Update path if needed
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        print(f"Processing URL: {url}")

        # Wait for the download button to be clickable
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "downlode-pdf"))
        )

        # Scroll into view and click the button
        driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
        driver.execute_script("arguments[0].click();", download_button)

        print(f"PDF download initiated. Monitoring downloads in: {download_dir}")

        # Monitor the download directory for completion
        while True:
            files = os.listdir(download_dir)
            if any(file.endswith(".pdf") for file in files):
                print(f"PDF download completed! Saved in: {download_dir}")
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()

# Example usage
url = "https://visionias.in/resources/material/?id=1372&type=mains_sol"
download_pdf(url)
