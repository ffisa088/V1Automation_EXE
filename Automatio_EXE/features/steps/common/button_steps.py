"""
button_steps.py — Button click step definitions
"""

import re
import time

from behave import given, when, then
from selenium.webdriver.common.by import By

from features.steps.common.utils import find_fast, aid, safe_click


# ─── CORE CLICK HELPER ────────────────────────────────────────────────────────

def _click_btn(context, *names):
    """Universal button locator: tries data-testid first, then ID, then text/label strategies."""
    for name in names:
        raw = str(name).strip().strip('"').strip("'")
        if not raw:
            continue

        clean = (
            raw.lower()
            .replace(" ", "_")
            .replace("+", "")
            .replace(":", "")
            .strip()
        )

        snake = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', raw).lower()
        spaced = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', raw).replace("_", " ").strip()
        title_text = spaced.title()
        lower_text = spaced.lower()

        selectors = []

        # ── 1. Specific data-testid (P0 · data-testid) ──
        for tid in [f"btn_{clean}", f"btn_{snake}", f"btn_{raw}", clean, snake, raw]:
            selectors.append(aid(tid))

        # ── 2. Specific ID & Name (P1 · Exact ID) ──
        for elem_id in [f"btn_{clean}", f"btn_{snake}", f"btn_{raw}", clean, snake, raw]:
            selectors.append((By.ID, elem_id))
            selectors.append((By.NAME, elem_id))

        id_match = f"@id='{raw}' or @id='{clean}' or @id='{snake}' or @id='btn_{clean}' or @id='btn_{snake}' or @id='btn_{raw}'"
        tid_match = f"@data-testid='{raw}' or @data-testid='{clean}' or @data-testid='{snake}' or @data-testid='btn_{clean}' or @data-testid='btn_{snake}' or @data-testid='btn_{raw}'"
        selectors.append((By.XPATH, f"//button[{id_match} or {tid_match}]"))
        selectors.append((By.XPATH, f"//a[{id_match} or {tid_match}]"))
        selectors.append((By.XPATH, f"//*[@id and ({id_match})]"))
        selectors.append((By.XPATH, f"//*[@data-testid and ({tid_match})]"))

        # ── 3. Button Text & Value (P2 · Button Text) ──
        for txt in [raw, title_text, lower_text]:
            if txt:
                selectors.append((By.XPATH, f"//button[normalize-space()='{txt}']"))
                selectors.append((By.XPATH, f"//button[contains(normalize-space(),'{txt}')]"))
                selectors.append((By.XPATH, f"//a[normalize-space()='{txt}']"))
                selectors.append((By.XPATH, f"//a[contains(normalize-space(),'{txt}')]"))
                selectors.append((By.XPATH, f"//input[@value='{txt}']"))

        # ── 4. Mat Icon & Icon elements (P3 · Mat Icon) ──
        for icon_id in [clean, snake, raw]:
            selectors.append((By.XPATH, f"//button[.//mat-icon[normalize-space()='{icon_id}']]"))
            selectors.append((By.XPATH, f"//mat-icon[normalize-space()='{icon_id}']/ancestor::button"))
            selectors.append((By.XPATH, f"//button[.//i[contains(@class,'{icon_id}')]]"))

        # ── 5. aria-label & title (P4 · aria-label) ──
        for lbl in [raw, title_text, lower_text, clean, snake]:
            if lbl:
                selectors.append((By.XPATH, f"//*[@aria-label='{lbl}']"))
                selectors.append((By.XPATH, f"//*[@title='{lbl}']"))

        # ── 6. Close Button Handlers (e.g. closeView, CloseView, close, btn_close) ──
        if "close" in clean:
            close_selectors = [
                aid("btn_close"),
                aid("close"),
                (By.ID, "btn_close"),
                (By.ID, "close"),
                (By.XPATH, "//button[@aria-label='Close' or @aria-label='close' or @title='Close' or @title='close']"),
                (By.XPATH, "//button[normalize-space()='Close' or normalize-space()='close']"),
                (By.XPATH, "//button[.//mat-icon[translate(normalize-space(),'CLOSE','close')='close']]"),
                (By.XPATH, "//mat-icon[translate(normalize-space(),'CLOSE','close')='close']/ancestor::button"),
                (By.XPATH, "//mat-icon[translate(normalize-space(),'CLOSE','close')='close']"),
                (By.XPATH, "//button[contains(@class,'close') or contains(@class,'btn-close') or @mat-dialog-close]"),
                (By.XPATH, "//*[contains(@class,'dialog') or contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'offcanvas') or @role='dialog']//button[contains(@class,'close') or contains(@class,'btn-close') or .//mat-icon[translate(normalize-space(),'CLOSE','close')='close'] or @aria-label='Close' or @title='Close']"),
                (By.XPATH, "//*[contains(@class,'dialog') or contains(@class,'modal') or contains(@class,'drawer') or contains(@class,'detail')]//button[normalize-space()='Close' or normalize-space()='close' or normalize-space()='Cancel' or normalize-space()='×' or normalize-space()='✕']"),
                (By.XPATH, "//*[contains(@class,'dialog') or contains(@class,'modal') or contains(@class,'drawer')]//button[last()]"),
            ]
            selectors.extend(close_selectors)

        # ── 7. Filter Button Handlers (e.g. openFilters, userApplyFilters) ──
        if "filter" in clean:
            filter_selectors = [
                (By.XPATH, "//button[.//mat-icon[normalize-space()='filter_list' or normalize-space()='tune' or contains(normalize-space(),'filter')]]"),
                (By.XPATH, "//button[contains(@id,'filter') or contains(@data-testid,'filter')]"),
                (By.XPATH, "//button[contains(normalize-space(),'Filter') or contains(normalize-space(),'Filters')]"),
            ]
            selectors.extend(filter_selectors)

        el = find_fast(context, selectors)
        if el:
            safe_click(context, el)
            print("[BTN] Clicked: " + raw)
            time.sleep(0.25)
            return
    raise Exception("Button not found: " + str(names))



# ─── NAMED BUTTONS ────────────────────────────────────────────────────────────

@then('I click on the Add button')
@when('I click on the Add button')
def click_add(context):
    _click_btn(context, 'Add', '+ Add', 'Add New', 'New')


@then('I click on the Save button')
@when('I click on the Save button')
def click_save(context):
    _click_btn(context, 'Save', 'SAVE', 'Update', 'Create User')


@then('I click on the Cancel button')
@when('I click on the Cancel button')
def click_cancel(context):
    _click_btn(context, 'Cancel', 'CANCEL')


@then('I click on the Close button')
@when('I click on the Close button')
def click_close(context):
    el = find_fast(context, [
        aid("btn_close"),
        (By.ID, "btn_close"),
        (By.XPATH, "//button[@aria-label='Close' or @title='Close']"),
        (By.XPATH, "//button[normalize-space()='Close']"),
        (By.XPATH, "//mat-icon[normalize-space()='close']/.."),
        (By.XPATH, "//*[contains(@class,'dialog')]//button[last()]"),
        (By.XPATH, "//*[contains(@class,'modal')]//button[contains(@class,'close')]"),
    ])
    if el:
        safe_click(context, el)
        print("[BTN] Closed dialog")
        time.sleep(0.4)
        return
    raise Exception("Close button not found!")


@then('I close the dialog')
@when('I close the dialog')
def close_dialog(context):
    el = find_fast(context, [
        (By.ID, "btn_close"),
        (By.XPATH, "//button[contains(@class,'close-btn')]"),
        (By.XPATH, "//button[.//mat-icon[normalize-space()='close']]"),
        (By.XPATH, "//mat-icon[normalize-space()='close']/ancestor::button"),
    ])
    if el:
        safe_click(context, el)
        print("[BTN] Dialog closed")
        time.sleep(0.4)
        return
    raise Exception("Dialog close button not found")


@then('I click on the Delete button')
@when('I click on the Delete button')
def click_delete(context):
    _click_btn(context, 'Delete', 'DELETE')


@then('I click on the Edit button')
@when('I click on the Edit button')
def click_edit(context):
    _click_btn(context, 'Edit', 'EDIT', 'edit')


@then('I click on the Refresh button')
@when('I click on the Refresh button')
def click_refresh(context):
    _click_btn(context, 'Refresh', 'REFRESH')


@then('I click on the Search button')
@when('I click on the Search button')
def click_search_btn(context):
    _click_btn(context, 'Search', 'SEARCH')


@then('I click on the Submit button')
@when('I click on the Submit button')
def click_submit(context):
    _click_btn(context, 'Submit', 'SUBMIT')


@then('I click on the Clear button')
@when('I click on the Clear button')
def click_clear(context):
    _click_btn(context, 'Clear', 'CLEAR')


@then('I click on the Export button')
@when('I click on the Export button')
def click_export(context):
    _click_btn(context, 'Export', 'EXPORT')


@then('I click on the Import button')
@when('I click on the Import button')
def click_import(context):
    _click_btn(context, 'Import', 'IMPORT')


@then('I click on the Next button')
@when('I click on the Next button')
def click_next(context):
    _click_btn(context, 'Next', 'NEXT')


@then('I click on the Back button')
@when('I click on the Back button')
def click_back(context):
    _click_btn(context, 'Back', 'BACK', 'Previous')


@then('I click on the Download button')
@when('I click on the Download button')
def click_download_btn(context):
    _click_btn(context, 'Download', 'DOWNLOAD')


@then('I click on the Upload button')
@when('I click on the Upload button')
def click_upload_btn(context):
    _click_btn(context, 'Upload', 'UPLOAD')


@then('I click on the Confirm button')
@when('I click on the Confirm button')
def click_confirm(context):
    _click_btn(context, 'Confirm', 'Yes', 'OK')


@then('I click on the "{button_name}" button')
@when('I click on the "{button_name}" button')
def click_named_button(context, button_name):
    button_name = button_name.strip().strip('"').strip("'")
    _click_btn(context, button_name)


@then('I click on Yes in the delete confirmation dialog')
@when('I click on Yes in the delete confirmation dialog')
def click_yes_delete(context):
    _click_btn(context, 'Yes', 'Confirm', 'Delete')


@then('I click on No in the delete confirmation dialog')
@when('I click on No in the delete confirmation dialog')
def click_no_delete(context):
    _click_btn(context, 'No', 'Cancel')


@then('I click "{name}"')
@when('I click "{name}"')
def step_click(context, name):
    _click_btn(context, name)


# ─── ICON CLICKS ──────────────────────────────────────────────────────────────

def _click_icon(context, identifier):
    el = find_fast(context, [
        (By.ID, identifier),
        (By.XPATH, f"//i[@id='{identifier}']"),
        (By.XPATH, f"//i[contains(@class,'{identifier}')]"),
        (By.XPATH, f"//mat-icon[normalize-space()='{identifier}']"),
        (By.XPATH, f"//button[.//mat-icon[normalize-space()='{identifier}']]"),
    ])
    if el:
        safe_click(context, el)
        print("[BTN] Clicked icon: " + identifier)
        time.sleep(0.4)
        return
    raise Exception("Icon not found: " + identifier)


@then('I click the "{icon}" icon')
@when('I click the "{icon}" icon')
def click_icon(context, icon):
    _click_icon(context, icon)


@then('I should see the "{icon}" icon')
@when('I should see the "{icon}" icon')
def verify_icon(context, icon):
    el = find_fast(context, [
        (By.ID, icon),
        (By.XPATH, f"//i[@id='{icon}']"),
        (By.XPATH, f"//i[contains(@class,'{icon}')]"),
        (By.XPATH, f"//mat-icon[normalize-space()='{icon}']"),
    ])
    assert el and el.is_displayed(), f"Icon not visible: {icon}"
    print("[BTN] Verified icon: " + icon)
