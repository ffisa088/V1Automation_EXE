from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

service = Service("chromedriver.exe")
driver  = webdriver.Chrome(service=service)
driver.get("http://qa-erp.acsyserp.com/login")
time.sleep(3)

inputs = driver.find_elements(By.XPATH, "//input")
print(f"\nFound {len(inputs)} input fields:\n")
for i, inp in enumerate(inputs, 1):
    print(f"  [{i}]")
    print(f"       type        : {inp.get_attribute('type')}")
    print(f"       name        : {inp.get_attribute('name')}")
    print(f"       id          : {inp.get_attribute('id')}")
    print(f"       placeholder : {inp.get_attribute('placeholder')}")
    print(f"       class       : {inp.get_attribute('class')}")
    print()

input("\nPress ENTER to close...")
driver.quit()