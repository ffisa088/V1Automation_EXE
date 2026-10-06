import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

def load_config():
    config = {}
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base, "config.env")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
        print("Config loaded!")
    else:
        print("config.env not found! Using defaults.")
    return config

CONFIG = load_config()

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
DOWNLOADS_DIR  = os.path.join(BASE_DIR, "downloads")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR,  exist_ok=True)

CLOSE_BROWSER = CONFIG.get("CLOSE_BROWSER_AFTER_TEST", "false").lower() == "true"
WAIT_TIMEOUT  = int(CONFIG.get("WAIT_TIMEOUT", "10"))
SHORT_WAIT    = int(CONFIG.get("SHORT_WAIT", "2"))
MAXIMIZED     = CONFIG.get("BROWSER_MAXIMIZED", "true").lower() == "true"

_shared_driver = None
_shared_wait   = None
_short_wait    = None

def get_chromedriver_path():
    local = os.path.join(BASE_DIR, "chromedriver.exe")
    if os.path.isfile(local):
        return local
    from webdriver_manager.chrome import ChromeDriverManager
    return ChromeDriverManager().install()

def get_shared_driver():
    global _shared_driver, _shared_wait, _short_wait
    if _shared_driver is None:
        chromedriver = get_chromedriver_path()
        service  = Service(chromedriver)
        options  = webdriver.ChromeOptions()
        if MAXIMIZED:
            options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOADS_DIR,
            "download.prompt_for_download": False,
        })
        options.add_experimental_option("detach", True)
        _shared_driver = webdriver.Chrome(service=service, options=options)
        _shared_wait   = WebDriverWait(_shared_driver, WAIT_TIMEOUT)
        _short_wait    = WebDriverWait(_shared_driver, SHORT_WAIT)
        print("Browser started!")
    return _shared_driver, _shared_wait, _short_wait

def before_all(context):
    context.driver, context.wait, context.short_wait = get_shared_driver()
    context.config_data = CONFIG
    # ✅ This makes ALL scenarios continue even if one fails!
    context.config.stop_on_first_failure = False

def before_scenario(context, scenario):
    context.driver, context.wait, context.short_wait = get_shared_driver()
    context.config_data = CONFIG
    print("\n" + "="*40)
    print("Starting: " + scenario.name)
    print("="*40)

def after_scenario(context, scenario):
    # ✅ Always take screenshot on failure but NEVER stop
    if scenario.status == "failed":
        name = scenario.name.replace(" ", "_")
        path = os.path.join(SCREENSHOT_DIR, "FAIL_" + name + ".png")
        try:
            context.driver.save_screenshot(path)
            print("Screenshot saved: FAIL_" + name + ".png")
        except:
            pass
        print("Scenario FAILED - continuing to next scenario...")
    else:
        print("Scenario PASSED!")

def after_all(context):
    global _shared_driver
    if CLOSE_BROWSER and _shared_driver:
        print("Closing browser...")
        _shared_driver.quit()
        _shared_driver = None
    else:
        print("All tests done! Browser stays open.")
        _shared_driver = None