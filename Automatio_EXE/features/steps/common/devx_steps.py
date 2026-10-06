"""
devx_steps.py — DevExtreme grid, treeview, and popup step definitions
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from features.steps.common.utils import find_fast, safe_click


# ─── TOOLBAR BUTTONS ──────────────────────────────────────────────────────────

@then('I click on the devx Add button')
@when('I click on the devx Add button')
def devx_click_add(context):
    el = find_fast(context, [
        (By.XPATH, ".//dx-button[@hint='Add']"),
        (By.XPATH, ".//div[contains(@class,'dx-toolbar')]//dx-button[contains(@hint,'Add')]"),
    ])
    if el:
        safe_click(context, el)
        print("[DEVX] Add clicked")
        time.sleep(0.6)
        return
    raise Exception("DevX Add button not found")


@then('I click the devx inline Save button')
@when('I click the devx inline Save button')
def devx_click_save(context):
    el = find_fast(context, [
        (By.XPATH, ".//a[contains(@class,'dx-link-save')]"),
        (By.XPATH, ".//dx-button[@hint='Save']"),
    ])
    if el:
        safe_click(context, el)
        print("[DEVX] Save clicked")
        time.sleep(0.6)
        return
    raise Exception("DevX Save button not found")


@then('I click the devx inline Cancel button')
@when('I click the devx inline Cancel button')
def devx_click_cancel(context):
    el = find_fast(context, [
        (By.XPATH, ".//a[contains(@class,'dx-link-cancel')]"),
        (By.XPATH, ".//dx-button[@hint='Cancel']"),
    ])
    if el:
        safe_click(context, el)
        time.sleep(0.3)
        return
    raise Exception("DevX Cancel button not found")


# ─── INLINE EDITING ───────────────────────────────────────────────────────────

@then('I type "{value}" in the devx input "{col_name}" column')
@when('I type "{value}" in the devx input "{col_name}" column')
def devx_type_in_column(context, value, col_name):
    el = find_fast(context, [
        (By.XPATH, ".//tr[contains(@class,'dx-edit-row')]//input"),
        (By.XPATH, ".//td[contains(@class,'dx-editor-cell')]//input"),
    ])
    if el:
        el.clear()
        el.send_keys(value)
        print(f"[DEVX] Typed '{value}' in column '{col_name}'")
        return
    raise Exception("DevX column input not found: " + col_name)


@then('I type "{value}" in the devx dialog column "{col_name}"')
@when('I type "{value}" in the devx dialog column "{col_name}"')
def devx_type_dialog_column(context, value, col_name):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-popup')]//label[contains(text(),'" + col_name + "')]/..//input"),
        (By.XPATH, ".//div[contains(@class,'dx-popup')]//input[@placeholder='" + col_name + "']"),
    ])
    if el:
        el.clear()
        el.send_keys(value)
        print(f"[DEVX] Dialog '{col_name}' = '{value}'")
        return
    raise Exception("DevX dialog column not found: " + col_name)


# ─── ROW ACTIONS ──────────────────────────────────────────────────────────────

@then('I click devx action "{action}" for row where "{col_name}" is "{col_value}"')
@when('I click devx action "{action}" for row where "{col_name}" is "{col_value}"')
def devx_click_row_action(context, action, col_name, col_value):
    row = context.wait.until(EC.presence_of_element_located((
        By.XPATH, ".//tr[.//td[normalize-space()='" + col_value + "']]"
    )))
    ActionChains(context.driver).move_to_element(row).perform()
    time.sleep(0.2)
    btn = row.find_element(
        By.XPATH,
        ".//a[contains(@class,'dx-link')][contains(text(),'" + action + "')] | "
        ".//dx-button[contains(@hint,'" + action + "')]"
    )
    btn.click()
    print(f"[DEVX] Action '{action}' for '{col_value}'")
    time.sleep(0.6)


@then('I double click the row where "{col_name}" is "{col_value}"')
@when('I double click the row where "{col_name}" is "{col_value}"')
def devx_double_click_row(context, col_name, col_value):
    row = context.wait.until(EC.presence_of_element_located((
        By.XPATH, ".//tr[.//td[normalize-space()='" + col_value + "']]"
    )))
    ActionChains(context.driver).double_click(row).perform()
    print("[DEVX] Double clicked row: " + col_value)
    time.sleep(0.6)


# ─── DATE / DROPDOWN IN GRID ──────────────────────────────────────────────────

@then('I select "{date_value}" in the devx "{col_name}" datepicker')
@when('I select "{date_value}" in the devx "{col_name}" datepicker')
def devx_select_date(context, date_value, col_name):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-datebox')]//input"),
    ])
    if el:
        el.clear()
        el.send_keys(date_value)
        print(f"[DEVX] Date '{col_name}' = {date_value}")
        return
    raise Exception("DevX datepicker not found: " + col_name)


@then('I select "{option_text}" from the devx "{col_name}" dropdown')
@when('I select "{option_text}" from the devx "{col_name}" dropdown')
def devx_select_dropdown(context, option_text, col_name):
    box = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-selectbox')]//input"),
        (By.XPATH, ".//dx-select-box//input"),
    ])
    if not box:
        raise Exception("DevX dropdown not found: " + col_name)
    box.click()
    time.sleep(0.3)
    opt = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-list-item')][contains(.,'" + option_text + "')]"),
    ])
    if opt:
        opt.click()
        print(f"[DEVX] Dropdown '{col_name}' = '{option_text}'")
    else:
        raise Exception("DevX option not found: " + option_text)


# ─── SEARCH ───────────────────────────────────────────────────────────────────

@then('I type "{text}" in the devx search bar')
@when('I type "{text}" in the devx search bar')
@then('I type "{text}" in devx search bar')
@when('I type "{text}" in devx search bar')
def devx_type_search(context, text):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-datagrid-search-panel')]//input"),
    ])
    if el:
        el.clear()
        el.send_keys(text)
        print("[DEVX] Search: " + text)
        time.sleep(0.7)
        return
    raise Exception("DevX search bar not found")


@then('I clear the devx search bar')
@when('I clear the devx search bar')
def devx_clear_search(context):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-datagrid-search-panel')]//input"),
    ])
    if el:
        el.clear()
        print("[DEVX] Search cleared")


# ─── ROW SELECTION ────────────────────────────────────────────────────────────

@then('I check the devx row where "{col_name}" is "{col_value}"')
@when('I check the devx row where "{col_name}" is "{col_value}"')
def devx_check_row(context, col_name, col_value):
    row = context.wait.until(EC.presence_of_element_located((
        By.XPATH, ".//tr[.//td[normalize-space()='" + col_value + "']]"
    )))
    cb = row.find_element(
        By.XPATH, ".//td[contains(@class,'dx-command-select')]//input[@type='checkbox']"
    )
    if not cb.is_selected():
        cb.click()
    print("[DEVX] Checked: " + col_value)


@then('I uncheck the devx row where "{col_name}" is "{col_value}"')
@when('I uncheck the devx row where "{col_name}" is "{col_value}"')
def devx_uncheck_row(context, col_name, col_value):
    row = context.wait.until(EC.presence_of_element_located((
        By.XPATH, ".//tr[.//td[normalize-space()='" + col_value + "']]"
    )))
    cb = row.find_element(
        By.XPATH, ".//td[contains(@class,'dx-command-select')]//input[@type='checkbox']"
    )
    if cb.is_selected():
        cb.click()
    print("[DEVX] Unchecked: " + col_value)


@then('I select all devx rows')
@when('I select all devx rows')
def devx_select_all(context):
    el = find_fast(context, [
        (By.XPATH, ".//th[contains(@class,'dx-command-select')]//input[@type='checkbox']"),
    ])
    if el and not el.is_selected():
        el.click()
    print("[DEVX] All rows selected")


@then('I unselect all devx rows')
@when('I unselect all devx rows')
def devx_unselect_all(context):
    el = find_fast(context, [
        (By.XPATH, ".//th[contains(@class,'dx-command-select')]//input[@type='checkbox']"),
    ])
    if el and el.is_selected():
        el.click()
    print("[DEVX] All rows unselected")


# ─── TREEVIEW ─────────────────────────────────────────────────────────────────

@then('I expand "{node_name}" in the treeview')
@when('I expand "{node_name}" in the treeview')
def devx_expand_treeview(context, node_name):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-treeview-item')][contains(.,'" + node_name + "')]"
                   "/..//div[contains(@class,'dx-treeview-toggle-item-visibility')]"),
    ])
    if el:
        el.click()
        print("[DEVX] Treeview expanded: " + node_name)
        time.sleep(0.4)
        return
    raise Exception("Treeview node not found: " + node_name)


@then('I check "{item_name}" in the treeview')
@when('I check "{item_name}" in the treeview')
def devx_check_treeview(context, item_name):
    el = find_fast(context, [
        (By.XPATH, ".//div[contains(@class,'dx-treeview-item')][contains(.,'" + item_name + "')]"
                   "//input[@type='checkbox']"),
    ])
    if el:
        if not el.is_selected():
            el.click()
        print("[DEVX] Treeview checked: " + item_name)
        return
    raise Exception("Treeview item not found: " + item_name)


# ─── EXPORT ───────────────────────────────────────────────────────────────────

@then('I click on the Export to Excel devx button')
@when('I click on the Export to Excel devx button')
def click_export_excel_devx(context):
    el = find_fast(context, [
        (By.XPATH, ".//dx-button[@hint='Export to Excel']"),
        (By.XPATH, ".//div[contains(@class,'dx-toolbar')]//dx-button[contains(@hint,'Excel')]"),
    ])
    if el:
        safe_click(context, el)
        print("[DEVX] Export to Excel clicked")
        time.sleep(2)
        return
    raise Exception("DevX Export button not found")
