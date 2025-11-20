from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Firefox()

try:
    driver.get("http://testphp.vulnweb.com/guestbook.php")
    print("Page loaded")
    
    time.sleep(2)
    
    print(f"Title: {driver.title}")
    print(f"URL: {driver.current_url}")
    
    forms = driver.find_elements(By.TAG_NAME, "form")
    print(f"\nFound {len(forms)} form")
    
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\nFound {len(all_inputs)} input field:")
    for i, inp in enumerate(all_inputs):
        try:
            name = inp.get_attribute('name')
            input_type = inp.get_attribute('type')
            visible = inp.is_displayed()
            print(f"  Input {i+1}: name='{name}', type='{input_type}', visible={visible}")
        except:
            pass
    
    all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
    print(f"\nFound {len(all_textareas)} textarea:")
    for i, ta in enumerate(all_textareas):
        try:
            name = ta.get_attribute('name')
            visible = ta.is_displayed()
            print(f"  Textarea {i+1}: name='{name}', visible={visible}")
        except:
            pass
    
    all_buttons = driver.find_elements(By.TAG_NAME, "button")
    all_submit_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
    print(f"\nFound {len(all_buttons)} button(s) and {len(all_submit_inputs)} submit input(s)")
    
    wait = WebDriverWait(driver, 10)
    
    # Look for textarea by any means
    try:
        comment_field = driver.find_element(By.TAG_NAME, "textarea")
        print("\n Found textarea")
        comment_field.send_keys("This is a test comment for learning Selenium")
        print(" Text entered in textarea")
    except Exception as e:
        print(f"\n Could not find or fill textarea: {e}")
    
    # Look for any visible text input
    try:
        text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        for inp in text_inputs:
            if inp.is_displayed():
                inp.send_keys("Test User")
                print(" Text entered in visible input field")
                break
    except Exception as e:
        print(f"Could not fill text input: {e}")
    
    # Find and click submit button
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        print("Found submit button")
        
        time.sleep(1) 
        submit_btn.click()
        print("Submit button clicked")
        
        time.sleep(3)
        print(f"Final URL: {driver.current_url}")
        
    except Exception as e:
        print(f" Could not find or click submit button: {e}")
    
    time.sleep(3)
    
except Exception as e:
    print(f"\n An error occurred: {e}")
    print(f"Current URL: {driver.current_url}")
    
    # Take a screenshot for debugging
    try:
        driver.save_screenshot("error_screenshot.png")
        print("Screenshot saved as error_screenshot.png")
    except:
        pass
    
finally:
    driver.quit()
    print("\n Browser closed")