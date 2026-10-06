"""
helpers.py — Higher-level action helpers built on top of utils.py
=================================================================
All low-level primitives (resolve_value, find_fast, aid, load_config, etc.)
are now in utils.py.  This module provides composite helpers used by step files.
"""

import os
import time
import glob
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ── Import shared primitives from single source of truth ──────────────────────
from features.steps.common.utils import (
    load_config,
    resolve_value,
    find_fast as find_element_fast,   # alias for backward compat
    aid as by_id,                      # alias for backward compat
    safe_click,
    BASE,
    DOWNLOADS_DIR,
    UPLOADS_DIR,
    SCREENSHOTS_DIR,
)

# Convenience alias so any code doing find_by_aid() still works
def find_by_aid(context, automation_id: str):
    """Find element by data-testid automation ID."""
    return find_element_fast(
        context,
        [(By.CSS_SELECTOR, '[data-testid="' + automation_id + '"]')]
    )

# ── CLICK ─────────────────────────────────────────────────────────────────────
def click(context, name):
    """Click by automation ID first, then fallback to text/label"""
    # Try automation ID directly
    el = find_by_aid(context, name)
    if el:
        el.click()
        print("Clicked [" + name + "]")
        time.sleep(0.5)
        return True

    # Fallback: try common button patterns
    selectors = [
        (By.CSS_SELECTOR, '[data-testid="' + name + '"]'),
        (By.XPATH, "//button[@id='btn_add']"),
        (By.XPATH, "//mat-icon[text()='add']"),
        (By.XPATH, "//mat-icon[text()='" + name + "']"),
        (By.XPATH, "//button[normalize-space()='" + name + "']"),
        (By.XPATH, "//button[contains(text(),'" + name + "')]"),
        (By.XPATH, "//a[normalize-space()='" + name + "']"),
        (By.XPATH, "//a[contains(text(),'" + name + "')]"),
        (By.XPATH, "//input[@value='" + name + "']"),
        (By.XPATH, "//*[@title='" + name + "']"),
        (By.XPATH, "//*[@aria-label='" + name + "']"),
        (By.XPATH, "//*[contains(text(),'" + name + "')]"),
    ]
    el = find_element_fast(context, selectors)
    if el:
        el.click()
        print("Clicked: " + name)
        time.sleep(0.5)
        return True
    raise Exception("Click target not found: " + name)

# ── TYPE TEXT ─────────────────────────────────────────────────────────────────
def type_text(context, field_name, text):
    """Type into field by automation ID or label"""
    text = resolve_value(text)

    # Try automation ID first (inp_fieldname pattern)
    aid_guess = "inp_" + field_name.lower().replace(" ", "").replace("*", "").replace("/", "")
    el = find_by_aid(context, aid_guess)
    if not el:
        el = find_by_aid(context, field_name)

    if not el:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="inp_' + field_name.lower().replace(" ", "") + '"]'),
            (By.XPATH, "//input[@placeholder='" + field_name + "']"),
            (By.XPATH, "//textarea[@placeholder='" + field_name + "']"),
            (By.XPATH, "//label[contains(text(),'" + field_name + "')]/..//input"),
            (By.XPATH, "//label[contains(text(),'" + field_name + "')]/..//textarea"),
            (By.XPATH, "//input[@name='" + field_name + "']"),
            (By.XPATH, "//input[@id='" + field_name + "']"),
            (By.XPATH, "//mat-form-field[.//label[contains(.,'" + field_name + "')]]//input"),
        ]
        el = find_element_fast(context, selectors)

    if el:
        el.clear()
        el.send_keys(text)
        print("Typed '" + text + "' in '" + field_name + "'")
        return True
    raise Exception("Input field not found: " + field_name)

# ── SELECT DROPDOWN ───────────────────────────────────────────────────────────
def select_dropdown(context, dropdown_label, option_text):
    """Select from dropdown by automation ID (sel_fieldname) or label"""
    option_text = resolve_value(option_text)
    label_clean = dropdown_label.lower().replace(" *", "").replace(" ", "_").replace("/", "")

    # Try automation ID: sel_fieldname
    aid = "sel_" + label_clean
    trigger = find_by_aid(context, aid)

    if not trigger:
        trigger = find_by_aid(context, dropdown_label)

    if not trigger:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="sel_' + label_clean + '"]'),
            (By.ID,    "sel_" + label_clean),
            (By.XPATH, "//mat-select[contains(@id,'sel_" + label_clean + "')]"),
            (By.XPATH, "//mat-form-field[.//label[contains(.,'" + dropdown_label + "')]]//mat-select"),
            (By.XPATH, "//mat-form-field[.//mat-label[contains(.,'" + dropdown_label + "')]]//mat-select"),
            (By.XPATH, "//label[contains(.,'" + dropdown_label + "')]/..//mat-select"),
            (By.XPATH, "//select[@id='sel_" + label_clean + "']"),
        ]
        trigger = find_element_fast(context, selectors)

    if not trigger:
        raise Exception("Dropdown not found: " + dropdown_label)

    trigger.click()
    time.sleep(0.5)

    option_selectors = [
        (By.XPATH, "//mat-option[normalize-space()='" + option_text + "']"),
        (By.XPATH, "//mat-option[contains(.,'" + option_text + "')]"),
        (By.XPATH, "//mat-option//span[contains(text(),'" + option_text + "')]"),
        (By.XPATH, "//*[contains(@class,'mat-option')][contains(.,'" + option_text + "')]"),
        (By.XPATH, "//option[contains(text(),'" + option_text + "')]"),
        (By.XPATH, "//li[contains(text(),'" + option_text + "')]"),
    ]
    option = find_element_fast(context, option_selectors)
    if not option:
        raise Exception("Option not found: " + option_text + " in: " + dropdown_label)

    option.click()
    print("Selected: " + option_text + " from: " + dropdown_label)
    time.sleep(0.3)

# ── UPLOAD ────────────────────────────────────────────────────────────────────
def upload(context, filename):
    base = os.getcwd()
    locations = [
        os.path.join(base, "uploads", filename),
        os.path.join(base, "downloads", filename),
        os.path.join(r"C:\Automatio_EXE", "uploads", filename),
    ]
    file_path = next((p for p in locations if os.path.exists(p)), None)
    if not file_path:
        raise Exception("File not found: " + filename)
    try:
        upload_input = context.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        upload_input.send_keys(file_path)
        print("Uploaded: " + filename)
        time.sleep(1)
    except:
        raise Exception("Upload input not found for: " + filename)

# ── SELECT DATE ───────────────────────────────────────────────────────────────
def select_date(context, date_value):
    date_value = resolve_value(date_value)
    selectors = [
        (By.XPATH, "//input[@matdatepicker]"),
        (By.XPATH, "//input[contains(@class,'mat-date')]"),
        (By.XPATH, "//input[@type='date']"),
        (By.XPATH, "//input[contains(@placeholder,'date') or contains(@placeholder,'Date')]"),
    ]
    el = find_element_fast(context, selectors)
    if el:
        el.clear()
        el.send_keys(date_value)
        print("Date selected: " + date_value)
        time.sleep(0.3)
        return True
    raise Exception("Date picker not found")

# ── CHECK checkbox ────────────────────────────────────────────────────────────
def check(context, name):
    """Check checkbox by automation ID (chk_name) or label"""
    aid = "chk_" + name.lower().replace(" ", "_")
    el = find_by_aid(context, aid)
    if not el:
        el = find_by_aid(context, name)

    if not el:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="chk_' + name.lower().replace(" ", "_") + '"]'),
            (By.XPATH, "//mat-checkbox[contains(.,'" + name + "')]//input"),
            (By.XPATH, "//label[contains(text(),'" + name + "')]/..//input[@type='checkbox']"),
            (By.XPATH, "//input[@type='checkbox'][@name='" + name + "']"),
            (By.XPATH, "//input[@type='checkbox'][@id='" + name + "']"),
        ]
        el = find_element_fast(context, selectors)

    if el:
        if not el.is_selected():
            el.click()
        print("Checked: " + name)
        time.sleep(0.3)
        return True
    raise Exception("Checkbox not found: " + name)

# ── UNCHECK checkbox ──────────────────────────────────────────────────────────
def uncheck(context, name):
    """Uncheck checkbox by automation ID or label"""
    aid = "chk_" + name.lower().replace(" ", "_")
    el = find_by_aid(context, aid)
    if not el:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="chk_' + name.lower().replace(" ", "_") + '"]'),
            (By.XPATH, "//mat-checkbox[contains(.,'" + name + "')]//input"),
            (By.XPATH, "//label[contains(text(),'" + name + "')]/..//input[@type='checkbox']"),
            (By.XPATH, "//input[@type='checkbox'][@name='" + name + "']"),
        ]
        el = find_element_fast(context, selectors)

    if el:
        if el.is_selected():
            el.click()
        print("Unchecked: " + name)
        time.sleep(0.3)
        return True
    raise Exception("Checkbox not found: " + name)

# ── VERIFY DIALOG ─────────────────────────────────────────────────────────────
def verify_dialog(context):
    try:
        context.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(@class,'dialog') or contains(@class,'modal') or contains(@role,'dialog')]"
        )))
        print("Dialog visible")
        return True
    except:
        raise Exception("Dialog not found!")

# ── VERIFY TOAST ──────────────────────────────────────────────────────────────
def verify_toast(context):
    try:
        toast = context.wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '[data-testid="toast_message"]'
        )))
        print("Toast: " + toast.text)
        return True
    except:
        try:
            toast = context.wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//*[contains(@class,'toast') or contains(@class,'snack') or contains(@class,'notification')]"
            )))
            print("Toast: " + toast.text)
            return True
        except:
            print("Toast not found - may have disappeared")
            return False

# ── VERIFY DOWNLOAD ───────────────────────────────────────────────────────────
def verify_download(context):
    base = os.getcwd()
    downloads_dir = os.path.join(base, "downloads")
    time.sleep(3)
    files = [f for f in glob.glob(os.path.join(downloads_dir, '*'))
             if not f.endswith('.tmp') and not f.endswith('.crdownload')]
    if len(files) > 0:
        print("Download verified: " + os.path.basename(files[-1]))
        return True
    raise Exception("No downloaded file found!")

# ── SWITCH TAB ────────────────────────────────────────────────────────────────
def switch_tab(context, tab_name):
    """Switch tab by automation ID (tab_name) or text"""
    aid = "tab_" + tab_name.lower().replace(" ", "_")
    el = find_by_aid(context, aid)
    if not el:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="tab_' + tab_name.lower().replace(" ", "_") + '"]'),
            (By.XPATH, "//a[contains(text(),'" + tab_name + "')]"),
            (By.XPATH, "//button[contains(text(),'" + tab_name + "')]"),
            (By.XPATH, "//*[@role='tab'][contains(text(),'" + tab_name + "')]"),
            (By.XPATH, "//*[contains(@class,'tab')][contains(text(),'" + tab_name + "')]"),
        ]
        el = find_element_fast(context, selectors)

    if el:
        el.click()
        print("Switched to tab: " + tab_name)
        time.sleep(0.8)
        return True
    raise Exception("Tab not found: " + tab_name)

# ── EXPAND SECTION ────────────────────────────────────────────────────────────
def expand_section(context, section):
    """Expand accordion/panel section"""
    selectors = [
        (By.XPATH, "//mat-expansion-panel-header[contains(.,'" + section + "')]"),
        (By.XPATH, "//*[contains(@class,'accordion')][contains(.,'" + section + "')]"),
        (By.XPATH, "//*[contains(@class,'panel-header')][contains(.,'" + section + "')]"),
        (By.XPATH, "//*[contains(@class,'section-header')][contains(.,'" + section + "')]"),
    ]
    el = find_element_fast(context, selectors)
    if el:
        aria = el.get_attribute("aria-expanded")
        if aria != "true":
            el.click()
            print("Expanded: " + section)
            time.sleep(0.5)
        else:
            print("Already expanded: " + section)
        return True
    raise Exception("Section not found: " + section)

# ── CLICK ROW ACTION ──────────────────────────────────────────────────────────
def click_row_action(context, action, col_name, col_value):
    """Click action button on a table row"""
    try:
        row = context.wait.until(EC.presence_of_element_located((
            By.XPATH, "//tr[.//td[normalize-space()='" + col_value + "']]"
        )))
        ActionChains(context.driver).move_to_element(row).perform()
        time.sleep(0.3)
        btn = row.find_element(
            By.XPATH,
            ".//button[contains(text(),'" + action + "')] | "
            ".//a[contains(text(),'" + action + "')] | "
            ".//*[@data-testid='btn_" + action.lower() + "']"
        )
        btn.click()
        print("Row action: " + action + " where " + col_name + "=" + col_value)
        time.sleep(0.8)
    except:
        raise Exception("Row action not found: " + action + " where " + col_name + "=" + col_value)

# ── CLICK ROW BY ID ───────────────────────────────────────────────────────────
def click_row(context, row_id):
    """Click a table row by automation ID (row_item_{id})"""
    aid = "row_item_" + str(row_id)
    el = find_by_aid(context, aid)
    if not el:
        el = find_element_fast(context, [
            (By.CSS_SELECTOR, '[data-testid="row_item_' + str(row_id) + '"]'),
            (By.XPATH, "//tr[@data-testid='row_item_" + str(row_id) + "']"),
        ])
    if el:
        el.click()
        print("Clicked row: " + str(row_id))
        time.sleep(0.5)
        return True
    raise Exception("Row not found: " + str(row_id))

# ── CLICK BUTTON BY AUTOMATION ID ────────────────────────────────────────────
def click_btn(context, btn_id):
    """Click button by automation ID e.g. btn_save, btn_add"""
    el = find_by_aid(context, btn_id)
    if not el:
        el = find_element_fast(context, [
            (By.CSS_SELECTOR, '[data-testid="' + btn_id + '"]'),
            (By.ID, btn_id),
            
        ])
    if el:
        el.click()
        print("Clicked button: " + btn_id)
        time.sleep(0.5)
        return True
    raise Exception("Button not found: " + btn_id)

# ── SEARCH ────────────────────────────────────────────────────────────────────
def search(context, text):
    """Type in search field (inp_search automation ID)"""
    text = resolve_value(text)
    el = find_by_aid(context, "inp_search")
    if not el:
        selectors = [
            (By.ID, "inp_search"),
            (By.NAME, "inp_search"),
            (By.XPATH, "//input[(@data-testid='inp_search' or @id='inp_search' or @name='inp_search') and not(contains(translate(@placeholder, 'QUICK', 'quick'), 'quick')) and not(contains(translate(@id, 'QUICK', 'quick'), 'quick'))]"),
            (By.XPATH, "//input[(contains(@data-testid, 'inp_search') or contains(@id, 'inp_search') or contains(@name, 'inp_search')) and not(contains(translate(@placeholder, 'QUICK', 'quick'), 'quick')) and not(contains(translate(@id, 'QUICK', 'quick'), 'quick'))]"),
        ]
        el = find_element_fast(context, selectors)
    if el:
        el.clear()
        el.send_keys(text)
        el.send_keys(Keys.ENTER)
        
        print("Searched: " + text)
        time.sleep(1)
        return True
    raise Exception("Search field not found")

# ── VERIFY TABLE HAS ROW ──────────────────────────────────────────────────────
def verify_row_exists(context, col_value):
    """Verify a row with given value exists in the table"""
    try:
        table = context.wait.until(EC.presence_of_element_located((
            By.XPATH, "//tr[.//td[contains(normalize-space(),'" + col_value + "')]]"
        )))
        print("Row found: " + col_value)
        return True
    except:
        raise Exception("Row not found in table: " + col_value)

# ── TOGGLE ────────────────────────────────────────────────────────────────────
def toggle(context, toggle_id):
    """Click a toggle by automation ID (toggle_name)"""
    aid = "toggle_" + toggle_id.lower().replace(" ", "_")
    el = find_by_aid(context, aid)
    if not el:
        el = find_by_aid(context, toggle_id)
    if not el:
        selectors = [
            (By.CSS_SELECTOR, '[data-testid="toggle_' + toggle_id.lower().replace(" ", "_") + '"]'),
            (By.XPATH, "//mat-slide-toggle[contains(.,'" + toggle_id + "')]"),
            (By.XPATH, "//*[contains(@class,'toggle')][contains(.,'" + toggle_id + "')]"),
        ]
        el = find_element_fast(context, selectors)
    if el:
        el.click()
        print("Toggled: " + toggle_id)
        time.sleep(0.3)
        return True
    raise Exception("Toggle not found: " + toggle_id)

# ── SCREENSHOT ────────────────────────────────────────────────────────────────
def take_screenshot(context, name):
    try:
        base = os.getcwd()
        screenshot_dir = os.path.join(base, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, name + ".png")
        context.driver.save_screenshot(path)
        print("Screenshot: " + path)
    except Exception as e:
        print("Screenshot failed: " + str(e))

# ── WAIT FOR PAGE ─────────────────────────────────────────────────────────────
def wait_for_page(context):
    context.wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.3)

# ── ELEMENT EXISTS ────────────────────────────────────────────────────────────
def element_exists(context, xpath):
    try:
        context.driver.find_element(By.XPATH, xpath)
        return True
    except:
        return False

# ── GET TEXT ──────────────────────────────────────────────────────────────────
def get_text(context, xpath):
    try:
        return context.driver.find_element(By.XPATH, xpath).text
    except:
        return ""

# ── SCROLL TO ─────────────────────────────────────────────────────────────────
def scroll_to(context, xpath):
    try:
        el = context.driver.find_element(By.XPATH, xpath)
        context.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        time.sleep(0.2)
        return True
    except:
        return False

# ── PRESS KEY ─────────────────────────────────────────────────────────────────
def press_key(context, key):
    key_map = {
        'enter':  Keys.ENTER, 'escape': Keys.ESCAPE,
        'tab':    Keys.TAB,   'space':  Keys.SPACE,
        'delete': Keys.DELETE,'back':   Keys.BACK_SPACE,
    }
    k = key_map.get(key.lower(), key)
    context.driver.find_element(By.TAG_NAME, 'body').send_keys(k)
    time.sleep(0.2)
