from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- Setup ---
options = Options()
# These flags help the browser run smoothly in automation environments
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

try:
    # 1. Open the practice site (reliable alternative to vulnweb)
    print("Navigating to the vulnerable-style practice form...")
    driver.get("https://testautomationpractice.blogspot.com/")

    # 2. Setup Explicit Wait
    wait = WebDriverWait(driver, 10)

    # 3. Fill out the "Name" (Text Input)
    # This site uses IDs, which are much more stable for automation
    print("Entering Name...")
    name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
    name_field.send_keys("Ethical Hacker Test")

    # 4. Fill out the "Address" or "Comment" (Textarea)
    print("Writing the comment into the textarea...")
    # This field is a <textarea>, perfect for practicing comments/payloads
    comment_area = driver.find_element(By.ID, "textarea")
    
    # We can even send 'vulnerable-looking' payloads like HTML tags
    comment_area.send_keys("User Comment: This is a test post.\n<b>Testing HTML Bold Tag Support</b>")

    # 5. Click the Submit/Execute button
    # On this specific practice page, we can interact with various 'Submit' style elements
    print("Finding the submit button...")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button.start") # Example selector
    
    # Optional: Scroll to the element so you can see it
    driver.execute_script("arguments[0].scrollIntoView();", comment_area)
    
    time.sleep(2) # Pause so you can see the filled form
    print("Process complete!")

except Exception as e:
    print(f"An error occurred: {e}")
    # If the script fails, it takes a screenshot of the 'vulnerable' app state
    driver.save_screenshot("vulnerable_app_error.png")
finally:
    driver.quit()
    print("Browser closed.")