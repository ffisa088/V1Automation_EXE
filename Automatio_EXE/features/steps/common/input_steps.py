"""
input_steps.py — Text input and search bar step definitions
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from features.steps.common.utils import find_fast, aid, resolve_value


# ─── CORE TYPE HELPER ─────────────────────────────────────────────────────────

def _type_in(context, field_name: str, text: str):
    """Locate an input/textarea by data-testid, placeholder, label, name, or id
    and send the resolved text value."""
    text = resolve_value(text)
    clean = field_name.lower().replace(" ", "").replace("*", "").replace("/", "")
    el = find_fast(context, [
        aid("inp_" + clean),
        aid(field_name),
        (By.ID, "inp_" + field_name.lower()),
        (By.XPATH, "//input[@placeholder='" + field_name + "']"),
        (By.XPATH, "//input[@formcontrolname='" + field_name + "']"),
        (By.XPATH, "//textarea[@placeholder='" + field_name + "']"),
        (By.XPATH, "//label[normalize-space()='" + field_name + "']/..//input"),
        (By.XPATH, "//label[contains(text(),'" + field_name + "')]/..//input"),
        (By.XPATH, "//label[normalize-space()='" + field_name + "']/..//textarea"),
        (By.XPATH, "//input[@name='" + field_name + "']"),
        (By.XPATH, "//input[@id='" + field_name + "']"),
        (By.XPATH, "//mat-form-field[.//mat-label[contains(.,'" + field_name + "')]]//input"),
        (By.XPATH, "//mat-form-field[.//label[contains(.,'" + field_name + "')]]//input"),
    ])
    if el:
        el.clear()
        el.send_keys(text)
        print(f"[INPUT] Typed '{text}' in '{field_name}'")
        return
    raise Exception("Input not found: " + field_name)


# ─── TYPE STEPS ───────────────────────────────────────────────────────────────

@then('I type "{text}" in the input "{field_name}"')
@when('I type "{text}" in the input "{field_name}"')
def type_in_input(context, text, field_name):
    _type_in(context, field_name, text)


@then('I type "{value}" in "{field}"')
@when('I type "{value}" in "{field}"')
def step_type(context, value, field):
    _type_in(context, field, value)


@then('I clear the input "{field_name}"')
@when('I clear the input "{field_name}"')
def clear_input(context, field_name):
    clean = field_name.lower().replace(" ", "").replace("*", "")
    el = find_fast(context, [
        aid("inp_" + clean),
        (By.XPATH, "//input[@placeholder='" + field_name + "']"),
        (By.XPATH, "//label[contains(text(),'" + field_name + "')]/..//input"),
        (By.XPATH, "//input[@name='" + field_name + "']"),
    ])
    if el:
        el.clear()
        print("[INPUT] Cleared: " + field_name)
        return
    print("[INPUT] Clear target not found: " + field_name)


# ─── SEARCH BAR ───────────────────────────────────────────────────────────────

def _find_search_bar(context):
    return find_fast(context, [
        aid("inp_search"),
        (By.ID, "inp_search"),
        (By.NAME, "inp_search"),
        (By.XPATH, "//input[(@data-testid='inp_search' or @id='inp_search' or @name='inp_search') and not(contains(translate(@placeholder, 'QUICK', 'quick'), 'quick')) and not(contains(translate(@id, 'QUICK', 'quick'), 'quick'))]"),
        (By.XPATH, "//input[(contains(@data-testid, 'inp_search') or contains(@id, 'inp_search') or contains(@name, 'inp_search')) and not(contains(translate(@placeholder, 'QUICK', 'quick'), 'quick')) and not(contains(translate(@id, 'QUICK', 'quick'), 'quick'))]"),
        (By.XPATH, "//input[(contains(translate(@data-testid,'SEARCH','search'),'inp_search') or contains(translate(@id,'SEARCH','search'),'inp_search') or contains(translate(@name,'SEARCH','search'),'inp_search')) and not(contains(translate(@placeholder, 'QUICK', 'quick'), 'quick'))]"),
    ])


@then('I type "{text}" in the search bar')
@when('I type "{text}" in the search bar')
def type_in_search_bar(context, text):
    text = resolve_value(text)
    el = _find_search_bar(context)
    if el:
        el.clear()
        el.send_keys(text)
        el.send_keys(Keys.ENTER)
        print("[INPUT] Searched: " + text)
        time.sleep(0.25)
        return
    raise Exception("Search bar not found!")


@then('I clear the search bar')
@when('I clear the search bar')
def clear_search_bar(context):
    el = _find_search_bar(context)
    if el:
        el.clear()
        el.send_keys(Keys.CONTROL + 'a')
        el.send_keys(Keys.DELETE)
        print("[INPUT] Search bar cleared")
        return
    print("[INPUT] Search bar not found for clearing")
