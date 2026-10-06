"""
environment.py
==============
Behave hooks for AcSys ERP Test Automation.

Responsibilities:
  - Load config.env
  - Start ONE shared Chrome browser for the entire test run
  - Inject context.driver, context.wait, context.short_wait into every scenario
  - Save screenshot on failure
  - Never close the browser mid-run (shared session)
  - Close browser only after all tests complete (if configured)
"""

import os
import sys
import json
import importlib.util
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# ══════════════════════════════════════════════════════════════════
# BASE PATH
# ══════════════════════════════════════════════════════════════════

def _base_dir():
    """Project root — works for both .py script and frozen EXE."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # environment.py lives in features/ → go up one level
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = _base_dir()


def _load_step_modules():
    """Import the organized step modules manually so nested folders work without raw __init__ execution."""
    steps_root = os.path.join(BASE_DIR, "features", "steps")
    if not os.path.isdir(steps_root):
        return

    for folder_name in sorted(os.listdir(steps_root)):
        folder_path = os.path.join(steps_root, folder_name)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(os.listdir(folder_path)):
            if not filename.endswith(".py") or filename == "__init__.py":
                continue
            full_path = os.path.join(folder_path, filename)
            module_name = "behave_step_" + folder_name + "_" + os.path.splitext(filename)[0]
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

# ══════════════════════════════════════════════════════════════════
# CONFIG LOADER  (single source of truth: utils.py)
# ══════════════════════════════════════════════════════════════════

from features.steps.common.utils import load_config as _load_config, find_fast, safe_click, aid

CONFIG = _load_config()
_load_step_modules()

# ══════════════════════════════════════════════════════════════════
# SETTINGS (from config.env with safe defaults)
# ══════════════════════════════════════════════════════════

CLOSE_AFTER   = CONFIG.get("CLOSE_BROWSER_AFTER_TEST", "false").lower() == "true"
WAIT_TIMEOUT  = int(CONFIG.get("WAIT_TIMEOUT",  "10"))
SHORT_TIMEOUT = int(CONFIG.get("SHORT_WAIT",    "2"))
MAXIMIZED     = CONFIG.get("BROWSER_MAXIMIZED", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════
# DIRECTORY SETUP
# ══════════════════════════════════════════════════════════════════

SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
DOWNLOADS_DIR  = os.path.join(BASE_DIR, "downloads")
UPLOADS_DIR    = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR    = os.path.join(BASE_DIR, "reports")
SCREENSHOT_INDEX = os.path.join(SCREENSHOT_DIR, "screenshot_index.json")

for _d in [SCREENSHOT_DIR, DOWNLOADS_DIR, UPLOADS_DIR, REPORTS_DIR]:
    os.makedirs(_d, exist_ok=True)


def _save_screenshot_reference(scenario_name, feature_name, screenshot_path):
    """Persist a lightweight mapping from scenario name to screenshot path."""
    data = {}
    if os.path.exists(SCREENSHOT_INDEX):
        try:
            with open(SCREENSHOT_INDEX, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    feature_key = (feature_name or "unknown_feature").strip().lower()
    scenario_key = (scenario_name or "unknown_scenario").strip().lower()
    data.setdefault(feature_key, {})
    data[feature_key].setdefault(scenario_key, [])
    data[feature_key][scenario_key].append({
        "path": screenshot_path,
        "filename": os.path.basename(screenshot_path),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    try:
        with open(SCREENSHOT_INDEX, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("[ENV] Failed to save screenshot index: " + str(e))

# ══════════════════════════════════════════════════════════════════
# CHROMEDRIVER FINDER
# ══════════════════════════════════════════════════════════════════

def _find_chromedriver():
    candidates = [
        os.path.join(BASE_DIR, "chromedriver.exe"),
        os.path.join(os.getcwd(), "chromedriver.exe"),
        r"C:\Automatio_EXE\chromedriver.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            print("[ENV] Driver  : " + p)
            return p

    # Auto-download via webdriver-manager as last resort
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        path = ChromeDriverManager().install()
        print("[ENV] Driver  : " + path + "  (auto-downloaded)")
        return path
    except Exception as e:
        raise RuntimeError(
            "[ENV] ChromeDriver not found and auto-download failed.\n"
            "Place chromedriver.exe in: " + BASE_DIR + "\n"
            "Error: " + str(e)
        )

# ══════════════════════════════════════════════════════════════════
# SHARED BROWSER — singleton, started once per test run
# ══════════════════════════════════════════════════════════════════

_driver     = None
_wait       = None
_short_wait = None


def _start_browser():
    """Create a new Chrome session with proper settings."""
    global _driver, _wait, _short_wait

    options = webdriver.ChromeOptions()

    if MAXIMIZED:
        options.add_argument("--start-maximized")

    # Keep browser open even after Python exits
    options.add_experimental_option("detach", True)

    # Auto-download to project downloads/ folder
    options.add_experimental_option("prefs", {
        "download.default_directory":   DOWNLOADS_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade":   True,
        "safebrowsing.enabled":         True,
    })

    # Let Selenium Manager select a driver matching the installed Chrome.
    _driver     = webdriver.Chrome(options=options)
    _wait       = WebDriverWait(_driver, WAIT_TIMEOUT)
    _short_wait = WebDriverWait(_driver, SHORT_TIMEOUT)

    print("[ENV] Browser : started  (timeout=" + str(WAIT_TIMEOUT) +
          "s, short=" + str(SHORT_TIMEOUT) + "s)")
    return _driver, _wait, _short_wait


def _get_browser():
    """Return existing browser or start a new one."""
    global _driver, _wait, _short_wait
    if _driver is None:
        return _start_browser()
    return _driver, _wait, _short_wait


def _scenario_failed(scenario):
    """Behave marks some failures as 'failed' and others as 'error'."""
    status = getattr(scenario.status, "name", str(scenario.status)).lower()
    return status in {"failed", "error", "undefined"}

# ══════════════════════════════════════════════════════════
# BEHAVE HOOKS
# ══════════════════════════════════════════════════

def before_all(context):
    """
    Called once before the entire test run.
    Start browser and attach to context.
    """
    context.driver, context.wait, context.short_wait = _get_browser()
    context.config_data = CONFIG
    context.base_dir    = BASE_DIR

    # Never stop on first failure — continue to next scenario always
    context.config.stop_on_first_failure = False

    print("[ENV] ======================================================")
    print("[ENV] Run start : " + datetime.now().strftime("%d %b %Y %H:%M:%S"))
    print("[ENV] URL       : " + CONFIG.get("LOGIN_URL", "not set"))
    print("[ENV] User      : " + CONFIG.get("USERNAME",  "not set"))
    print("[ENV] Company   : " + CONFIG.get("COMPANY",   "not set"))
    print("[ENV] Reports   : " + REPORTS_DIR)
    print("[ENV] ======================================================")


def before_feature(context, feature):
    """Called before each feature file."""
    print("\n[FEATURE] " + feature.name)


def before_scenario(context, scenario):
    """
    Called before each scenario.
    Reuse the existing browser — do NOT create a new session.
    """
    context.driver, context.wait, context.short_wait = _get_browser()
    context.config_data = CONFIG
    context.base_dir    = BASE_DIR
    context.scenario    = scenario
    context._failed_screenshot = None

    print("\n[SCENARIO] >>> " + scenario.name)


def after_step(context, step):
    """Called after each step — log pass/fail and capture failure screenshot immediately."""
    status = str(step.status).upper().replace("STATUS.", "")
    if status == "FAILED":
        print("[STEP]     FAILED : " + step.keyword + " " + step.name)
        try:
            driver = getattr(context, "driver", None)
            if driver:
                scenario = getattr(context, "scenario", None)
                sc_name = getattr(scenario, "name", "unknown_scenario") if scenario else "unknown_scenario"
                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', sc_name)[:60].strip('_')
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"FAIL_{clean_name}_{stamp}.png"
                path = os.path.join(SCREENSHOT_DIR, filename)
                ok = driver.get_screenshot_as_file(path)
                if ok:
                    print("[STEP]     Screenshot : " + path)
                    context._failed_screenshot = path
                    feat_name = getattr(getattr(scenario, "feature", None), "name", "") if scenario else ""
                    _save_screenshot_reference(sc_name, feat_name, path)
        except Exception as e:
            print("[STEP]     Screenshot failed : " + str(e))
    # passed steps are already printed by --no-capture


def after_scenario(context, scenario):
    """
    Called after each scenario.
    Save screenshot on any failure-like result. NEVER close the browser.
    """
    sc_name = scenario.name
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', sc_name)[:60].strip('_')

    if _scenario_failed(scenario):
        # If after_step didn't already capture the screenshot, take it now
        if not getattr(context, "_failed_screenshot", None):
            stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FAIL_{clean_name}_{stamp}.png"
            path     = os.path.join(SCREENSHOT_DIR, filename)
            try:
                driver = getattr(context, "driver", None)
                if driver is None:
                    print("[SCENARIO] Screenshot failed : no browser attached")
                else:
                    ok = driver.get_screenshot_as_file(path)
                    if ok:
                        print("[SCENARIO] Screenshot : " + path)
                        feature_name = getattr(getattr(scenario, "feature", None), "name", "")
                        _save_screenshot_reference(scenario.name, feature_name, path)
                    else:
                        print("[SCENARIO] Screenshot failed : file write returned False")
            except Exception as e:
                print("[SCENARIO] Screenshot failed : " + str(e))
        print("[SCENARIO] FAILED  — continuing to next scenario")

def _return_to_list_form(context, scenario=None, feature=None):
    """
    Recovery helper: When a scenario fails:
      1. Cancel Delete Dialog: If a delete/confirm modal is open, click Cancel / No.
      2. Close Add / Edit / View: Click 'Close' (or Cancel / closeView) on the form/drawer
         without ever touching the tab header close button.
      3. Clear Search & Filters: If search text or filter chips are active, click 'Clear'
         or the search '×' icon.
      4. Protect Tab: Never close the module tab (e.g. User Management). If the tab
         was missing or closed, automatically restore it from the sidebar menu.
    """
    driver = getattr(context, "driver", None)
    if not driver:
        return

    print("[RECOVERY] Scenario failed — executing automatic recovery flow...")

    # Strictly exclude buttons inside the tab bar/header (role='tab', role='tablist', tab-header)
    # Never match tab-content or tab-pane which are page containers!
    tab_header_exclusion = "[not(ancestor-or-self::*[@role='tab' or @role='tablist' or contains(@class,'tab-header') or contains(@class,'tab-strip') or contains(@class,'nav-tabs')])]"

    # 1. Dismiss any open native browser alerts (e.g. "Leave site? Changes you made may not be saved")
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        print(f"[RECOVERY] Dismissed browser alert: '{alert_text}'")
        time.sleep(0.4)
    except Exception:
        pass

    # 2. Cancel Delete / Confirmation dialogs if open
    delete_dialog_candidates = [
        (By.XPATH, f"//*[contains(@class,'modal') or contains(@class,'dialog') or contains(@class,'popup') or @role='dialog']//button[normalize-space()='Cancel' or normalize-space()='No' or contains(.,'Cancel') or contains(.,'No')]{tab_header_exclusion}"),
        (By.XPATH, f"//button[(normalize-space()='Cancel' or normalize-space()='No') and ancestor::*[contains(@class,'modal') or contains(@class,'dialog') or @role='dialog']]{tab_header_exclusion}"),
    ]
    for by, sel in delete_dialog_candidates:
        try:
            for el in driver.find_elements(by, sel):
                if el.is_displayed():
                    safe_click(context, el)
                    time.sleep(0.5)
                    print("[RECOVERY] Clicked Cancel on delete/confirmation dialog.")
                    break
        except Exception:
            pass

    # 3. Close Add / Edit / View form or drawer (finds 'Close', 'cancel', or 'closeView')
    form_close_candidates = [
        # Explicit View Details close button: id="closeView"
        (By.XPATH, "//button[@id='closeView']"),
        # Top-right or header 'Close' button on Add / Edit / View form (e.g. Create New User, Edit User)
        (By.XPATH, f"//button[contains(normalize-space(),'Close')]{tab_header_exclusion}"),
        # Form Cancel button (e.g. id="cancel" or text "Cancel" on form)
        (By.XPATH, f"//button[(@id='cancel' or normalize-space()='Cancel') and not(ancestor::*[contains(@class,'modal') or contains(@class,'dialog')])]{tab_header_exclusion}"),
        # Detail / Drawer slide-out close buttons
        (By.XPATH, f"//*[contains(@class,'drawer') or contains(@class,'detail') or contains(@class,'offcanvas')]//button[contains(.,'Close') or contains(.,'Cancel') or @id='closeView' or @aria-label='Close']{tab_header_exclusion}"),
        # DevExpress inline Cancel
        (By.XPATH, f"//a[contains(@class,'dx-link-cancel')]{tab_header_exclusion}"),
    ]

    for by, sel in form_close_candidates:
        try:
            clicked_form_close = False
            for el in driver.find_elements(by, sel):
                if el.is_displayed():
                    safe_click(context, el)
                    time.sleep(0.6)
                    clicked_form_close = True
                    print(f"[RECOVERY] Clicked Close/Cancel on Add/Edit/View form via: {sel}")
                    # If closing the form prompted an unsaved changes confirmation:
                    try:
                        discard_btns = driver.find_elements(
                            By.XPATH,
                            f"//button[normalize-space()='Discard' or normalize-space()='Yes' or normalize-space()='Leave']{tab_header_exclusion}"
                        )
                        for db in discard_btns:
                            if db.is_displayed():
                                safe_click(context, db)
                                time.sleep(0.4)
                                print("[RECOVERY] Confirmed discard unsaved changes.")
                                break
                    except Exception:
                        pass
                    break
            if clicked_form_close:
                break
        except Exception:
            pass

    # 4. Clear Search & Filters on List View
    try:
        # Click the "Clear" button next to Filters on the list view toolbar
        clear_btns = driver.find_elements(
            By.XPATH,
            f"//button[(normalize-space()='Clear' or @id='clear_filters')]{tab_header_exclusion}"
        )
        for cb in clear_btns:
            if cb.is_displayed():
                safe_click(context, cb)
                time.sleep(0.3)
                print("[RECOVERY] Clicked Clear button on search/filters toolbar.")
                break
    except Exception:
        pass

    try:
        # Clear search input text or click the '✕' icon inside search input box
        search_inputs = driver.find_elements(
            By.XPATH,
            f"//input[(contains(@placeholder,'Search') or contains(@class,'search') or @type='search')]{tab_header_exclusion}"
        )
        for sinp in search_inputs:
            if sinp.is_displayed() and sinp.get_attribute("value"):
                # Check for '✕' clear icon inside search input
                clear_x = driver.find_elements(
                    By.XPATH,
                    f"//input[contains(@placeholder,'Search')]/..//*[contains(@class,'close') or normalize-space()='×' or normalize-space()='✕' or @aria-label='Clear']"
                )
                cleared = False
                for cx in clear_x:
                    if cx.is_displayed():
                        safe_click(context, cx)
                        cleared = True
                        break
                if not cleared:
                    sinp.clear()
                time.sleep(0.3)
                print("[RECOVERY] Cleared search input bar.")
                break
    except Exception:
        pass

    # 5. Tab Verification: Ensure the module list tab is active and NOT closed
    target_page = getattr(context, "current_menu", None) or getattr(context, "current_page", None)
    if not target_page:
        feat = feature or (getattr(scenario, "feature", None) if scenario else None)
        target_page = getattr(feat, "name", None)

    if target_page:
        try:
            # Check if screen is empty ("Select a menu item to open a tab")
            empty_screen = driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'Select a menu item') or contains(text(),'Select a module')]"
            )
            is_empty = any(el.is_displayed() for el in empty_screen)

            # Check if list view grid is visible
            list_indicators = driver.find_elements(
                By.XPATH,
                f"//table | //dx-data-grid | //div[contains(@class,'grid')] | //button[contains(.,'Add') or @id='addUser']"
            )
            has_list = any(el.is_displayed() for el in list_indicators)

            if is_empty or not has_list:
                print(f"[RECOVERY] Tab missing or not on list view for '{target_page}'. Restoring...")
                # First check if tab header exists in the tab bar
                tab_el = find_fast(context, [
                    (By.XPATH, f"//*[contains(@class,'tab') or @role='tab'][contains(.,'{target_page}')][not(self::button)]"),
                    (By.XPATH, f"//span[contains(text(),'{target_page}')][ancestor::*[contains(@class,'tab') or @role='tablist']]"),
                ], timeout=0.5)

                if tab_el and tab_el.is_displayed():
                    safe_click(context, tab_el)
                    time.sleep(0.5)
                    print(f"[RECOVERY] Switched back to tab: '{target_page}'")
                else:
                    # Tab was closed — re-open it from sidebar menu
                    menu_el = find_fast(context, [
                        aid("menu_" + target_page.lower().replace(" ", "_")),
                        (By.XPATH, f"//*[normalize-space()='{target_page}'][ancestor::*[contains(@class,'nav') or contains(@class,'sidebar') or contains(@class,'menu')]]"),
                        (By.XPATH, f"//*[contains(text(),'{target_page}')][ancestor::*[contains(@class,'nav') or contains(@class,'sidebar')]]"),
                        (By.XPATH, f"//*[contains(text(),'{target_page}')]"),
                    ], timeout=2.0)
                    if menu_el:
                        safe_click(context, menu_el)
                        time.sleep(1.0)
                        print(f"[RECOVERY] Re-opened menu item from sidebar: '{target_page}'")
        except Exception as e:
            print("[RECOVERY] Notice during list view restoration: " + str(e))
def after_scenario(context, scenario):
    """
    Called after each scenario.
    Save screenshot on any failure-like result. NEVER close the browser.
    Automatically return to list form if scenario fails.
    """
    sc_name = scenario.name
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', sc_name)[:60].strip('_')

    if _scenario_failed(scenario):
        # If after_step didn't already capture the screenshot, take it now
        if not getattr(context, "_failed_screenshot", None):
            stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FAIL_{clean_name}_{stamp}.png"
            path     = os.path.join(SCREENSHOT_DIR, filename)
            try:
                driver = getattr(context, "driver", None)
                if driver is None:
                    print("[SCENARIO] Screenshot failed : no browser attached")
                else:
                    ok = driver.get_screenshot_as_file(path)
                    if ok:
                        print("[SCENARIO] Screenshot : " + path)
                        feature_name = getattr(getattr(scenario, "feature", None), "name", "")
                        _save_screenshot_reference(scenario.name, feature_name, path)
                    else:
                        print("[SCENARIO] Screenshot failed : file write returned False")
            except Exception as e:
                print("[SCENARIO] Screenshot failed : " + str(e))
        print("[SCENARIO] FAILED  — continuing to next scenario")

        # Cleanup & Recovery: Return page automatically back to the list form
        _return_to_list_form(context, scenario=scenario)
    else:
        print("[SCENARIO] PASSED  : " + scenario.name)


def after_feature(context, feature):
    """Called after each feature file — print summary and ensure clean return to list form."""
    passed  = sum(1 for s in feature.scenarios if s.status.name == "passed")
    failed  = sum(1 for s in feature.scenarios if s.status.name == "failed")
    skipped = sum(1 for s in feature.scenarios if s.status.name == "skipped")

    print("\n[FEATURE]  Done    : " + feature.name)
    print("[FEATURE]  Passed  : " + str(passed) +
          "  Failed : " + str(failed) +
          "  Skipped: " + str(skipped))

    if failed > 0:
        _return_to_list_form(context, feature=feature)


def after_all(context):
    """
    Called once after entire test run.
    Close browser only if CLOSE_BROWSER_AFTER_TEST=true in config.env.
    """
    global _driver

    print("\n[ENV] ======================================================")
    print("[ENV] Run end   : " + datetime.now().strftime("%d %b %Y %H:%M:%S"))
    print("[ENV] Screenshots: " + SCREENSHOT_DIR)
    print("[ENV] Reports    : " + REPORTS_DIR)

    if CLOSE_AFTER and _driver:
        try:
            _driver.quit()
            print("[ENV] Browser  : closed")
        except Exception:
            pass
        _driver = None
    else:
        print("[ENV] Browser  : stays open  (CLOSE_BROWSER_AFTER_TEST=false)")
        _driver = None

    print("[ENV] ======================================================")
