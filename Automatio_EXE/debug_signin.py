from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

service = Service("chromedriver.exe")
driver  = webdriver.Chrome(service=service)
driver.get("http://192.168.1.15/acSysERP/")
time.sleep(3)

input("Select company + Click Continue manually then press ENTER...")
time.sleep(1)

buttons = driver.find_elements(By.XPATH, "//button")
print("\nBUTTONS FOUND: " + str(len(buttons)))
for i, b in enumerate(buttons, 1):
    print("[" + str(i) + "] text='" + b.text + "' type='" + str(b.get_attribute("type")) + "' class='" + str(b.get_attribute("class"))[:50] + "'")

inputs = driver.find_elements(By.XPATH, "//input")
print("\nINPUTS FOUND: " + str(len(inputs)))
for i, inp in enumerate(inputs, 1):
    print("[" + str(i) + "] type='" + str(inp.get_attribute("type")) + "' placeholder='" + str(inp.get_attribute("placeholder")) + "' id='" + str(inp.get_attribute("id")) + "'")

input("\nPress ENTER to close...")
driver.quit()