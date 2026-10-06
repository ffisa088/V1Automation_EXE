from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

service = Service("chromedriver.exe")
driver  = webdriver.Chrome(service=service)
driver.get("https://qa.acsyscrm.com")
time.sleep(3)

input("Login manually then press ENTER...")

# Navigate to Ticket Manager
time.sleep(2)

# Find ALL dropdowns on page
print("\n=== ALL DROPDOWNS FOUND ===\n")

# Check mat-select
mat_selects = driver.find_elements(By.XPATH, "//mat-select")
print("mat-select count: " + str(len(mat_selects)))
for i, s in enumerate(mat_selects, 1):
    print("  [" + str(i) + "] class: " + str(s.get_attribute("class")))
    print("       id   : " + str(s.get_attribute("id")))
    print("       aria : " + str(s.get_attribute("aria-label")))
    print()

# Check ng-select
ng_selects = driver.find_elements(By.XPATH, "//ng-select")
print("ng-select count: " + str(len(ng_selects)))
for i, s in enumerate(ng_selects, 1):
    print("  [" + str(i) + "] class: " + str(s.get_attribute("class")))
    print()

# Check dx-select-box
dx_selects = driver.find_elements(By.XPATH, "//dx-select-box")
print("dx-select-box count: " + str(len(dx_selects)))

# Check regular select
selects = driver.find_elements(By.XPATH, "//select")
print("select count: " + str(len(selects)))

# Check labels
labels = driver.find_elements(By.XPATH, "//label")
print("\nAll labels:")
for l in labels:
    print("  - " + l.text)

input("\nPress ENTER to close...")
driver.quit()