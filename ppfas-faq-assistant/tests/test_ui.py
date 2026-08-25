import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_ui_tests():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    print("Starting Selenium Chrome...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 1. Desktop Test
        print("=== Running Desktop Test ===")
        driver.set_window_size(1280, 900)
        driver.get("http://127.0.0.1:3000")
        
        # Verify disclaimer
        disclaimer = driver.find_element(By.CLASS_NAME, "disclaimer-banner")
        assert "Facts-only. No investment advice." in disclaimer.text
        print("✓ Disclaimer banner verified")
        
        # Test chat
        input_box = driver.find_element(By.ID, "chat-input")
        send_btn = driver.find_element(By.ID, "send-btn")
        
        input_box.send_keys("What is the expense ratio?")
        send_btn.click()
        print("✓ Sent question (Desktop)")
        
        # Wait for assistant response
        wait = WebDriverWait(driver, 10)
        # Wait until at least 2 assistant messages are present (welcome message + response)
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message.assistant-message:not(.typing-indicator)")) >= 2)
        assistant_msgs = driver.find_elements(By.CSS_SELECTOR, ".message.assistant-message:not(.typing-indicator)")
        
        text = assistant_msgs[-1].text
        print(f"TEXT RECEIVED: {text}")
        assert "Source:" in text
        print("✓ Assistant responded with Source link")
        print(f"Response snippet: {text[:60]}...")
        
        # 2. Mobile Test
        print("\n=== Running Mobile Test ===")
        driver.set_window_size(375, 667)
        driver.refresh()
        
        disclaimer = driver.find_element(By.CLASS_NAME, "disclaimer-banner")
        assert disclaimer.is_displayed()
        print("✓ Disclaimer banner is visible on mobile")
        
        input_box = wait.until(EC.visibility_of_element_located((By.ID, "chat-input")))
        assert input_box.is_displayed()
        print("✓ Input box is visible on mobile viewport")
        
        input_box.send_keys("What is the exit load?")
        send_btn = driver.find_element(By.ID, "send-btn")
        send_btn.click()
        print("✓ Sent question (Mobile)")
        
        # Wait for assistant response
        time.sleep(2) # brief delay
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message.assistant-message:not(.typing-indicator)")) >= 2)
        assistant_msgs = driver.find_elements(By.CSS_SELECTOR, ".message.assistant-message:not(.typing-indicator)")
        text = assistant_msgs[-1].text
        print("✓ Assistant responded on mobile")
        print(f"Response snippet: {text[:60]}...")
        
        print("\n✅ All UI tests passed successfully using Selenium!")
    except Exception as e:
        print(f"\n❌ UI Test Failed: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_ui_tests()
