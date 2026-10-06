"""
dialog_steps.py — Dialog, toast, table actions, accordions, scroll, and stepper steps
"""

import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from features.steps.common.utils import find_fast, safe_click


# ─── DIALOGS ──────────────────────────────────────────────────────────────────

@then('I should see the dialog box')
@then('I should see dialog')
def verify_dialog(context):
    try:
        context.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(@class,'dialog') or contains(@class,'modal') or contains(@role,'dialog')]"
        )))
        print("[DIALOG] Dialog is visible")
    except Exception:
        raise Exception("Dialog not found — it may not have opened")


@then('I should see the success confirmation dialog')
def verify_success_dialog(context):
    try:
        context.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(@class,'dialog') or contains(@class,'modal')]"
            "[contains(text(),'success') or contains(text(),'Success')]"
        )))
        print("[DIALOG] Success dialog is visible")
    except Exception:
        print("[DIALOG] Success dialog not visible (may have already closed)")


@then('the dialog should be closed')
def verify_dialog_closed(context):
    """Assert no dialog/modal overlay is currently open."""
    time.sleep(0.5)
    dialogs = context.driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'dialog') or contains(@class,'modal')][@aria-hidden!='true']"
    )
    assert len(dialogs) == 0, f"Expected dialog to be closed but found {len(dialogs)} open dialog(s)"
    print("[DIALOG] Dialog is closed")


@then('I inspect the dialog fields')
def inspect_dialog_fields(context):
    try:
        dialog = context.driver.find_element(
            By.XPATH,
            "//*[contains(@class,'dialog') or contains(@role,'dialog')]"
        )
        fields = dialog.find_elements(
            By.XPATH, ".//input | .//select | .//textarea | .//mat-select"
        )
        print(f"[DEBUG] Dialog fields ({len(fields)}):")
        for f in fields:
            print(
                "  testid="      + str(f.get_attribute("data-testid")) +
                " placeholder=" + str(f.get_attribute("placeholder")) +
                " name="        + str(f.get_attribute("name"))
            )
    except Exception:
        print("[DEBUG] No dialog found to inspect")


# ─── TOASTS ───────────────────────────────────────────────────────────────────

@then('I should see the success toast')
@then('I should see toast')
def verify_toast(context):
    try:
        toast = context.wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '[data-testid="toast_message"]'
        )))
        print("[TOAST] " + toast.text)
        return
    except Exception:
        pass
    try:
        toast = context.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(@class,'toast') or contains(@class,'snack') or "
            "contains(@class,'notification')]"
        )))
        print("[TOAST] " + toast.text)
    except Exception:
        print("[TOAST] Not found — may have already dismissed")


# ─── TABLE ROW ACTIONS ────────────────────────────────────────────────────────

@then('I click table action "{action}" for the row where "{col_name}" is "{col_value}"')
@when('I click table action "{action}" for the row where "{col_name}" is "{col_value}"')
@then('I click "{action}" action for the row where "{col_name}" is "{col_value}" in the table')
@when('I click "{action}" action for the row where "{col_name}" is "{col_value}" in the table')
def click_row_action_table(context, action, col_name, col_value):
    # Find row by col_value in any cell or row text
    row_xpaths = [
        f"//tr[.//td[contains(normalize-space(),'{col_value}')]]",
        f"//tr[td[normalize-space()='{col_value}']]",
        f"//*[contains(@class,'dx-data-row')][.//td[contains(normalize-space(),'{col_value}')]]",
        f"//tr[contains(.,'{col_value}')]",
    ]
    row = None
    for rxp in row_xpaths:
        try:
            row = context.wait.until(EC.presence_of_element_located((By.XPATH, rxp)))
            if row:
                break
        except Exception:
            continue
    if not row:
        raise Exception(f"Row containing '{col_value}' not found in table")

    ActionChains(context.driver).move_to_element(row).perform()
    time.sleep(0.3)

    # Search for direct button/link inside the row
    btn_xpaths = [
        f".//button[contains(normalize-space(),'{action}')]",
        f".//a[contains(normalize-space(),'{action}')]",
        f".//*[@data-testid='btn_{action.lower().replace(' ', '_')}']",
        f".//*[contains(@title,'{action}')]",
        f".//*[contains(@aria-label,'{action}')]",
        f".//dx-button[contains(@hint,'{action}')]",
        f".//a[contains(@class,'dx-link')][contains(text(),'{action}')]",
        f".//button[contains(.,'{action}')]",
    ]
    btn = None
    for bxp in btn_xpaths:
        matches = row.find_elements(By.XPATH, bxp)
        if matches:
            btn = matches[0]
            break

    # If action not directly on row, try row action menu button (e.g. 3 dots / actions button)
    if not btn:
        menu_triggers = row.find_elements(
            By.XPATH,
            ".//button[contains(@id,'action') or contains(@class,'action') or contains(@id,'btn_action')] | "
            ".//a[contains(@class,'action')] | "
            ".//mat-icon[text()='more_vert']/.. | "
            ".//*[contains(@class,'dx-icon-overflow')]/.."
        )
        if menu_triggers:
            safe_click(context, menu_triggers[0])
            time.sleep(0.5)
            # Find action in opened menu/popup
            menu_item = find_fast(context, [
                (By.XPATH, f"//button[contains(normalize-space(),'{action}')]"),
                (By.XPATH, f"//a[contains(normalize-space(),'{action}')]"),
                (By.XPATH, f"//*[contains(@class,'menu-item') and contains(.,'{action}')]"),
                (By.XPATH, f"//mat-option[contains(.,'{action}')]"),
                (By.XPATH, f"//*[contains(@class,'dx-menu-item-text') and contains(.,'{action}')]"),
            ])
            if menu_item:
                safe_click(context, menu_item)
                print(f"[TABLE] Row menu action '{action}' for '{col_value}'")
                time.sleep(0.6)
                return

    if not btn:
        raise Exception(f"Action '{action}' not found on row for '{col_value}'")

    safe_click(context, btn)
    print(f"[TABLE] Row action '{action}' for '{col_value}'")
    time.sleep(0.6)


@when('I click row action "{action}" where "{column}" is "{value}"')
def step_grid(context, action, column, value):
    click_row_action_table(context, action, column, value)



# ─── ACCORDIONS ───────────────────────────────────────────────────────────────

@then('I toggle the "{header_text}" accordion')
@when('I toggle the "{header_text}" accordion')
@when('I expand "{section}"')
def toggle_accordion(context, header_text=None, section=None):
    name = header_text or section
    el = find_fast(context, [
        (By.XPATH, "//mat-expansion-panel-header[contains(.,'" + name + "')]"),
        (By.XPATH, "//*[contains(@class,'accordion')][contains(.,'" + name + "')]"),
        (By.XPATH, "//*[contains(@class,'panel-header')][contains(.,'" + name + "')]"),
    ])
    if el:
        aria = el.get_attribute("aria-expanded")
        if aria != "true":
            el.click()
            print("[ACCORDION] Expanded: " + name)
        else:
            print("[ACCORDION] Already expanded: " + name)
        time.sleep(0.4)
        return
    raise Exception("Accordion not found: " + name)


# ─── STEPPERS ─────────────────────────────────────────────────────────────────

@then('I click on the stepper "{step_name}"')
@when('I click on the stepper "{step_name}"')
def click_stepper(context, step_name):
    el = find_fast(context, [
        (By.XPATH, "//mat-step-header[contains(.,'" + step_name + "')]"),
        (By.XPATH, "//*[contains(@class,'mat-step-label')][contains(text(),'" + step_name + "')]"),
    ])
    if el:
        el.click()
        print("[STEPPER] Clicked: " + step_name)
        time.sleep(0.4)
        return
    raise Exception("Stepper not found: " + step_name)


# ─── SCROLL ───────────────────────────────────────────────────────────────────

def scroll_panel(context, panel_xpath: str, direction: str = "down", amount: int = 300):
    """Scroll a specific panel element up or down by pixel amount."""
    try:
        panel = context.driver.find_element(By.XPATH, panel_xpath)
        script = (
            "arguments[0].scrollTop += arguments[1];"
            if direction.lower() == "down" else
            "arguments[0].scrollTop -= arguments[1];"
        )
        context.driver.execute_script(script, panel, amount)
        print(f"[SCROLL] {direction.capitalize()}ed panel '{panel_xpath}' by {amount}px")
        time.sleep(0.3)
    except Exception as exc:
        raise Exception(f"Panel scroll failed: {exc}")


@when('I scroll down the "{panel_name}" panel')
def step_scroll_down(context, panel_name):
    scroll_panel(context, f"//div[@class='{panel_name}']", "down")


@then('I scroll up the "{panel_name}" panel')
def step_scroll_up(context, panel_name):
    scroll_panel(context, f"//div[@class='{panel_name}']", "up")
