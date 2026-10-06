"""
navigation_steps.py — Page, wait, and debug step definitions
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By

from features.steps.common.utils import find_fast, safe_click, aid


# ─── NAVIGATION / PAGE ────────────────────────────────────────────────────────

@given('I am on the "{page_name}" page')
def i_am_on_page(context, page_name):
    context.current_page = page_name
    print("On page: " + page_name)
    driver = getattr(context, "driver", None)
    if not driver:
        return
    try:
        # 1. If tab is already open, ensure it is selected
        tab = find_fast(context, [
            (By.XPATH, f"//*[contains(@class,'tab') or @role='tab'][contains(.,'{page_name}')][not(self::button)]"),
            (By.XPATH, f"//span[contains(text(),'{page_name}')][ancestor::*[contains(@class,'tab') or @role='tablist']]"),
        ], timeout=0.3)
        if tab and tab.is_displayed():
            safe_click(context, tab)
            return

        # 2. If screen is empty ("Select a menu item to open a tab") or tab missing, open it from menu
        empty_screen = driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'Select a menu item') or contains(text(),'Select a module')]"
        )
        if any(el.is_displayed() for el in empty_screen):
            from features.steps.common.menu_steps import click_menu_item
            click_menu_item(context, page_name)
    except Exception:
        pass


@given('I am on the dashboard page')
def i_am_on_dashboard(context):
    print("Dashboard: " + context.driver.current_url)


# ─── PAGE READY WAITS ────────────────────────────────────────────────────────

@then('I wait for the page to be fully loaded')
@then('I wait for the page to be rendered')
@when('I wait for the page to be rendered')
@given('I wait for the page to be rendered')
def wait_page_rendered(context):
    context.wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.4)
    print("[NAV] Page ready")


@then('the page is ready')
def page_is_ready(context):
    context.wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    print("[NAV] Page ready")


@then('I wait for {seconds:d} seconds')
@when('I wait for {seconds:d} seconds')
def wait_seconds(context, seconds):
    print(f"[NAV] Waiting {seconds}s…")
    time.sleep(seconds)


# ─── DEBUG HELPER ─────────────────────────────────────────────────────────────

@then('I debug the page')
def debug_page(context):
    print("[DEBUG] URL  : " + context.driver.current_url)
    print("[DEBUG] Title: " + context.driver.title)
    inputs = context.driver.find_elements(
        By.XPATH, "//input | //mat-select | //select"
    )
    print(f"[DEBUG] Inputs found: {len(inputs)}")
    for el in inputs[:10]:
        print(
            "  id="          + str(el.get_attribute("id")) +
            " placeholder=" + str(el.get_attribute("placeholder")) +
            " testid="      + str(el.get_attribute("data-testid"))
        )


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@then('I close any open notifications')
def close_notifications(context):
    try:
        context.driver.execute_script("document.body.click();")
        time.sleep(0.3)
        btns = context.driver.find_elements(
            By.XPATH,
            "//*[contains(@class,'notification')]//button | "
            "//*[contains(@class,'overlay')]//button"
        )
        for btn in btns:
            try:
                btn.click()
                time.sleep(0.2)
            except Exception:
                continue
        print("[NAV] Notifications closed")
    except Exception:
        print("[NAV] No notifications to close")
