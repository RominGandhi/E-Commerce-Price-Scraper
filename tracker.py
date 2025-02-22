import os
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Enable Debug Mode (Set to False to disable logging)
DEBUG_MODE = True

# ✅ Path to ChromeDriver (Modify this to your actual path)
CHROME_DRIVER_PATH = "C:/Users/Romin/Downloads/chromedriver-win64/chromedriver.exe"

# ✅ Path to `selectors.json` (inside the `selectors` folder)
SELECTORS_FILE = os.path.join(os.path.dirname(__file__), "selectors", "selectors.json")

# ✅ Configure Chrome options
options = Options()

options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--log-level=3")  # Suppress unnecessary logs
options.add_argument("--disable-logging")
options.add_argument("--disable-webgl")  # Ignore WebGL warnings
options.add_argument("--disable-usb")  # Ignore USB warnings

# ✅ Load selectors from JSON file
def load_selectors():
    if not os.path.exists(SELECTORS_FILE):
        print(f"❌ ERROR: {SELECTORS_FILE} not found!")
        return {}

    try:
        with open(SELECTORS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print("❌ ERROR: Failed to parse selectors.json! Check JSON format.")
        return {}

selectors = load_selectors()  # Load selectors at startup


# ✅ Function to fetch the product price dynamically
def fetch_price_dynamic(url, store):
    """
    Fetch the price dynamically from a given URL using Selenium.
    :param url: URL of the product page.
    :param store: Store name to fetch the correct selector from selectors.json.
    :return: Extracted price as a float or None if not found.
    """

    # ✅ Get selector from selectors.json
    if store not in selectors:
        print(f"❌ ERROR: No selector found for {store} in selectors.json!")
        return None

    # ✅ Special handling for Amazon (combine whole + fraction)
    if store == "amazon.ca":
        whole_xpath = selectors[store].get("price_whole")
        fraction_xpath = selectors[store].get("price_fraction")

        if not whole_xpath or not fraction_xpath:
            print(f"❌ ERROR: Missing price selectors for Amazon in selectors.json!")
            return None
    else:
        xpath = selectors[store].get("price")
        if not xpath:
            print(f"❌ ERROR: No price selector found for {store} in selectors.json!")
            return None

    # ✅ Initialize Chrome WebDriver
    try:
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"⚠️ ChromeDriver failed to start at {CHROME_DRIVER_PATH}, trying auto-install...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print(f"🔍 Fetching URL: {url}")
        driver.get(url)

        # ✅ Allow JavaScript elements to load
        time.sleep(3)

        # ✅ Scroll down to ensure price elements are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # ✅ Extract price
        if store == "amazon.ca":
            try:
                whole_part = driver.find_element(By.XPATH, whole_xpath).text.strip()
                fraction_part = driver.find_element(By.XPATH, fraction_xpath).text.strip()

                # ✅ Handle cases where Amazon's price might be empty
                whole_part = "".join(filter(str.isdigit, whole_part)) if whole_part else "0"
                fraction_part = "".join(filter(str.isdigit, fraction_part)) if fraction_part else "00"

                product_price = f"{whole_part}.{fraction_part}"  # Combine whole and fraction
            except Exception as e:
                print(f"❌ Error extracting Amazon price: {e}")
                return None

        elif store == "walmart.ca":
            try:
                price_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                product_price = price_element.text.strip()
            except Exception as e:
                print(f"❌ Walmart price extraction failed: {e}")
                print(f"⚠️ Retrying with JavaScript extraction...")

                # Fallback: Extract price using JavaScript if XPath fails
                try:
                    product_price = driver.execute_script(
                        "return document.querySelector('[itemprop=price]').textContent;"
                    ).strip()
                except:
                    product_price = None

        else:
            price_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            product_price = price_element.text.strip()

        # ✅ Debug Mode Logging
        if DEBUG_MODE:
            print(f"💰 Raw Price Text: {product_price}")

        # ✅ Clean and format the extracted price
        cleaned_price = re.sub(r"[^\d\.]", "", product_price)  # Remove non-numeric characters

        # ✅ Ensure price is valid
        return round(float(cleaned_price), 2) if cleaned_price else None

    except Exception as e:
        print(f"❌ Error extracting price: {e}")
        return None

    finally:
        # ✅ Close the browser
        driver.quit()
