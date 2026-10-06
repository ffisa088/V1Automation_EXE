"""
date_steps.py — Date picker step definitions
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from features.steps.common.utils import find_fast, resolve_date


# ─── SINGLE DATE PICKER ───────────────────────────────────────────────────────

def _find_date_input(context):
    return find_fast(context, [
        (By.XPATH, "//input[@matdatepicker]"),
        (By.XPATH, "//input[contains(@class,'mat-date')]"),
        (By.XPATH, "//input[@type='date']"),
        (By.XPATH, "//input[contains(@placeholder,'date') or contains(@placeholder,'Date')]"),
    ])


@then('I open the date picker calendar and select "{date}"')
@when('I open the date picker calendar and select "{date}"')
def open_date_picker_and_select(context, date):
    date = resolve_date(date)
    el = _find_date_input(context)
    if el:
        el.clear()
        el.send_keys(date)
        print("[DATE] Set: " + date)
        return
    raise Exception("Date picker not found")


@when('I select date "{date}"')
def step_date(context, date):
    open_date_picker_and_select(context, date)


@then('I open the date picker by id "{picker_id}" and select "{date}"')
@when('I open the date picker by id "{picker_id}" and select "{date}"')
def open_date_picker_by_id(context, picker_id, date):
    date = resolve_date(date)
    el = find_fast(context, [
        (By.ID, picker_id),
        (By.CSS_SELECTOR, '[data-testid="' + picker_id + '"]'),
    ])
    if el:
        el.clear()
        el.send_keys(date)
        print(f"[DATE] '{picker_id}' = {date}")
        return
    raise Exception("Date picker not found: " + picker_id)


# ─── DATE RANGE PICKER ────────────────────────────────────────────────────────

@then('I select the date range from "{start_date}" to "{end_date}" in the start-end date picker calender')
@when('I select the date range from "{start_date}" to "{end_date}" in the start-end date picker calender')
def select_date_range(context, start_date, end_date):
    start_date = resolve_date(start_date)
    end_date   = resolve_date(end_date)
    inputs = context.wait.until(EC.presence_of_all_elements_located((
        By.XPATH, "//input[@matdatepicker] | //input[contains(@class,'mat-date')]"
    )))
    inputs[0].clear()
    inputs[0].send_keys(start_date)
    time.sleep(0.2)
    inputs[1].clear()
    inputs[1].send_keys(end_date)
    print(f"[DATE] Range: {start_date} → {end_date}")


@then('I clear the start-end date picker')
@when('I clear the start-end date picker')
def clear_date_picker(context):
    inputs = context.driver.find_elements(
        By.XPATH, "//input[@matdatepicker] | //input[contains(@class,'mat-date')]"
    )
    for inp in inputs:
        context.driver.execute_script("arguments[0].value = '';", inp)
        context.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", inp
        )
    print("[DATE] Date picker cleared")


@then('the start-end date picker should show "{start_date}" to "{end_date}"')
def verify_date_range(context, start_date, end_date):
    inputs = context.driver.find_elements(By.XPATH, "//input[@matdatepicker]")
    assert start_date in inputs[0].get_attribute('value'), "Start date mismatch"
    assert end_date   in inputs[1].get_attribute('value'), "End date mismatch"
    print(f"[DATE] Range verified: {start_date} → {end_date}")


# ─── MONTH / YEAR PICKER ──────────────────────────────────────────────────────

@then('I select "{month_year}" in the "{picker_id}" month year picker calendar')
@when('I select "{month_year}" in the "{picker_id}" month year picker calendar')
def select_month_year(context, month_year, picker_id):
    el = find_fast(context, [
        (By.ID, picker_id),
        (By.CSS_SELECTOR, '[data-testid="' + picker_id + '"]'),
    ])
    if el:
        el.clear()
        el.send_keys(month_year)
        print(f"[DATE] Month/Year '{picker_id}' = {month_year}")
        return
    raise Exception("Month/Year picker not found: " + picker_id)


# ─── RANGE RADIO PICKER ───────────────────────────────────────────────────────

@then('I open the range picker calendar and select "{date_range}"')
def open_range_picker(context, date_range):
    parts = [p.strip() for p in date_range.split('|')]
    el = find_fast(context, [
        (By.XPATH, "//mat-radio-button[contains(.,'" + parts[0] + "')]"),
    ])
    if el:
        el.click()
        time.sleep(0.3)
    if len(parts) > 1:
        inp = find_fast(context, [(By.XPATH, "//input[@matdatepicker]")])
        if inp:
            inp.send_keys(parts[1])
    print("[DATE] Range picker: " + date_range)
