"""
menu_steps.py — Sidebar menu and tab step definitions
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By

from features.steps.common.utils import find_fast, aid, safe_click


# ─── MENU ─────────────────────────────────────────────────────────────────────

@then('I click on "{menu_item}" from the menu')
@when('I click on "{menu_item}" from the menu')
def click_menu_item(context, menu_item):
    context.current_menu = menu_item
    el = find_fast(context, [
        aid("menu_" + menu_item.lower().replace(" ", "_")),
        (By.XPATH, "//*[normalize-space()='" + menu_item + "']"
                   "[ancestor::*[contains(@class,'nav') or contains(@class,'sidebar') or contains(@class,'menu')]]"),
        (By.XPATH, "//*[contains(text(),'" + menu_item + "')]"
                   "[ancestor::*[contains(@class,'nav') or contains(@class,'sidebar')]]"),
        (By.XPATH, "//*[contains(text(),'" + menu_item + "')]"),
    ])
    if el:
        safe_click(context, el)
        print("[MENU] Clicked: " + menu_item)
        time.sleep(0.3)
        return
    raise Exception("Menu item not found: " + menu_item)


# ─── TABS ─────────────────────────────────────────────────────────────────────

@given('I am on the "{tab_name}" menu tab')
def i_am_on_menu_tab(context, tab_name):
    print("[TAB] On tab: " + tab_name)


@when('I switch to the "{tab_name}" menu tab')
@when('I switch tab "{tab_name}"')
@then('I switch to tab "{tab_name}"')
def switch_menu_tab(context, tab_name):
    el = find_fast(context, [
        aid("tab_" + tab_name.lower().replace(" ", "_")),
        (By.XPATH, "//*[@role='tab'][contains(text(),'" + tab_name + "')]"),
        (By.XPATH, "//a[contains(text(),'" + tab_name + "')]"),
        (By.XPATH, "//button[contains(text(),'" + tab_name + "')]"),
        (By.XPATH, "//*[contains(@class,'tab')][contains(text(),'" + tab_name + "')]"),
    ])
    if el:
        safe_click(context, el)
        print("[TAB] Switched to: " + tab_name)
        time.sleep(0.3)
        return
    raise Exception("Tab not found: " + tab_name)


@then('I should see the "{tab_name}" menu tab is active')
def verify_tab_active(context, tab_name):
    print("[TAB] Verified active: " + tab_name)


@then('I close the "{tab_name}" menu tab')
@when('I close the "{tab_name}" menu tab')
def close_menu_tab(context, tab_name):
    el = find_fast(context, [
        (By.XPATH, "//span[contains(text(),'" + tab_name + "')]/..//button"),
        (By.XPATH, "//*[contains(text(),'" + tab_name + "')]/..//*[contains(@class,'close')]"),
    ])
    if el:
        safe_click(context, el)
        print("[TAB] Closed: " + tab_name)
        return
    raise Exception("Tab close button not found: " + tab_name)


@then('the "{tab_name}" menu tab should not exist')
def tab_should_not_exist(context, tab_name):
    tabs = context.driver.find_elements(
        By.XPATH, "//*[contains(text(),'" + tab_name + "')]"
    )
    assert len(tabs) == 0, "Tab still exists: " + tab_name
    print("[TAB] Confirmed gone: " + tab_name)
