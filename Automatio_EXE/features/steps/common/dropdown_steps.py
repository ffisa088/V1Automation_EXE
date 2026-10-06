"""
dropdown_steps.py — Dropdown, autocomplete, checkbox, radio, and chip step definitions
"""

import re
import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from features.steps.common.utils import find_fast, aid, safe_click, resolve_value


# ─── CORE DROPDOWN HELPER ─────────────────────────────────────────────────────

def _get_dropdown_label_variants(dropdown_label: str):
    """
    Generate normalized search variations for any dropdown identifier/label generically.
    No field-specific names are hardcoded.
    """
    raw = dropdown_label.strip()
    clean = (
        raw.lower()
        .replace(" *", "")
        .replace("*", "")
        .replace(" ", "_")
        .replace("/", "")
        .replace("-", "")
        .strip()
    )

    variants = []
    seen = set()

    def add(v):
        v = (v or "").strip()
        if v and v not in seen:
            seen.add(v)
            variants.append(v)

    add(raw)
    add(clean)
    add(raw.lower())

    # Split camelCase, snake_case, or spaced strings into words generically
    words = re.findall(r'[A-Za-z0-9]+', re.sub(r'([a-z])([A-Z])', r'\1 \2', raw))
    if words:
        spaced = " ".join(words)
        add(spaced)
        add(spaced.lower())
        add(spaced.title())
        add("".join(words).lower())
        add("_".join(w.lower() for w in words))

        # If identifier starts with a common prefix (e.g. 'user', 'sel', 'ddl', 'drp', 'cmb', 'inp', 'txt', 'opt')
        # also include core words without the prefix (e.g. 'userStatus' -> 'Status', 'sel_company' -> 'company')
        if len(words) > 1 and words[0].lower() in ('user', 'sel', 'ddl', 'drp', 'cmb', 'inp', 'txt', 'opt', 'form'):
            core = words[1:]
            core_spaced = " ".join(core)
            add(core_spaced)
            add(core_spaced.lower())
            add(core_spaced.title())
            add("".join(core).lower())
            add("_".join(w.lower() for w in core))

    return variants


def _select_dropdown(context, dropdown_label: str, option_text: str):
    """Open a mat-select, native select, or custom combobox by label/ID and pick the target option."""
    option_text = resolve_value(option_text)
    variants = _get_dropdown_label_variants(dropdown_label)

    candidates = []
    for v in variants:
        # ID and Name attributes
        candidates.append((By.ID, "sel_" + v))
        candidates.append((By.ID, v))
        candidates.append((By.NAME, v))
        candidates.append((By.NAME, "sel_" + v))
        candidates.append(aid("sel_" + v))
        candidates.append(aid(v))

        # XPath by ID, Name, FormControlName, or data attribute
        candidates.append((By.XPATH, f"//select[@id='sel_{v}' or @id='{v}' or @name='{v}' or @formcontrolname='{v}']"))
        candidates.append((By.XPATH, f"//mat-select[@id='sel_{v}' or @id='{v}' or @name='{v}' or @formcontrolname='{v}']"))
        candidates.append((By.XPATH, f"//*[self::select or self::mat-select or @role='combobox'][@id='sel_{v}' or @id='{v}' or @name='{v}' or @formcontrolname='{v}']"))

        # Associated by label (parent container, following sibling, or aria-label)
        candidates.append((By.XPATH, f"//label[contains(normalize-space(),'{v}')]/..//select"))
        candidates.append((By.XPATH, f"//label[contains(normalize-space(),'{v}')]/..//mat-select"))
        candidates.append((By.XPATH, f"//label[contains(normalize-space(),'{v}')]/following::select[1]"))
        candidates.append((By.XPATH, f"//label[contains(normalize-space(),'{v}')]/following::mat-select[1]"))
        candidates.append((By.XPATH, f"//label[contains(normalize-space(),'{v}')]/following::*[@role='combobox'][1]"))
        candidates.append((By.XPATH, f"//mat-form-field[.//mat-label[contains(normalize-space(),'{v}')]]//mat-select"))
        candidates.append((By.XPATH, f"//mat-form-field[.//label[contains(normalize-space(),'{v}')]]//mat-select"))
        candidates.append((By.XPATH, f"//div[contains(@class,'form-group') and .//label[contains(normalize-space(),'{v}')]]//select"))
        candidates.append((By.XPATH, f"//div[contains(@class,'form-group') and .//label[contains(normalize-space(),'{v}')]]//mat-select"))
        candidates.append((By.XPATH, f"//div[contains(@class,'form-group') and .//label[contains(normalize-space(),'{v}')]]//*[@role='combobox']"))
        candidates.append((By.XPATH, f"//div[contains(@class,'dx-selectbox') and .//label[contains(normalize-space(),'{v}')]]"))
        candidates.append((By.XPATH, f"//*[@aria-label='{v}' or @placeholder='{v}']"))

    trigger = find_fast(context, candidates)
    if not trigger:
        raise Exception("Dropdown not found: " + dropdown_label)

    # If trigger is a native HTML <select>, handle with Selenium Select
    if trigger.tag_name.lower() == "select":
        try:
            sel = Select(trigger)
            sel.select_by_visible_text(option_text)
            print(f"[DD] Native Selected '{option_text}' from '{dropdown_label}'")
            return
        except Exception:
            pass

    context.driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", trigger
    )
    try:
        trigger.click()
    except Exception as exc:
        print(f"[DD] JS click fallback: {exc}")
        context.driver.execute_script("arguments[0].click();", trigger)

    time.sleep(0.3)

    option = find_fast(context, [
        (By.XPATH, "//option[normalize-space()='" + option_text + "']"),
        (By.XPATH, "//option[contains(text(),'" + option_text + "')]"),
        (By.XPATH, "//mat-option[normalize-space()='" + option_text + "']"),
        (By.XPATH, "//mat-option[contains(.,'" + option_text + "')]"),
        (By.XPATH, "//mat-option//span[contains(text(),'" + option_text + "')]"),
        (By.XPATH, "//*[contains(@class,'mat-option')][contains(.,'" + option_text + "')]"),
        (By.XPATH, "//div[contains(@class,'mat-select-panel')]//mat-option[normalize-space()='" + option_text + "']"),
        (By.XPATH, "//*[@role='option'][normalize-space()='" + option_text + "' or contains(.,'" + option_text + "')]"),
        (By.XPATH, "//*[contains(@class,'dx-list-item')][contains(.,'" + option_text + "')]"),
    ])
    if not option:
        raise Exception(f"Option '{option_text}' not found in dropdown '{dropdown_label}'")

    context.driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", option
    )
    try:
        option.click()
    except Exception as exc:
        print(f"[DD] Option JS click fallback: {exc}")
        context.driver.execute_script("arguments[0].click();", option)

    print(f"[DD] Selected '{option_text}' from '{dropdown_label}'")



# ─── DROPDOWN STEPS ───────────────────────────────────────────────────────────

@then('I select "{option_text}" from the "{dropdown_label}" dropdown')
@when('I select "{option_text}" from the "{dropdown_label}" dropdown')
@then('I select "{option_text}" from the "{dropdown_label}" searchable dropdown')
@when('I select "{option_text}" from the "{dropdown_label}" searchable dropdown')
def select_dropdown(context, option_text, dropdown_label):
    _select_dropdown(context, dropdown_label, option_text)


@when('I select "{option}" from "{dropdown}"')
def step_select(context, option, dropdown):
    _select_dropdown(context, dropdown, option)


@then('I select "{option_text}" from the "{dropdown_label}" dropdown by label')
@when('I select "{option_text}" from the "{dropdown_label}" dropdown by label')
def select_dropdown_by_label(context, option_text, dropdown_label):
    _select_dropdown(context, dropdown_label, option_text)


# ─── MULTI-SELECT DROPDOWN ────────────────────────────────────────────────────

@then('I select "{options}" from the "{dropdown_label}" multi-select dropdown')
@when('I select "{options}" from the "{dropdown_label}" multi-select dropdown')
def select_multi_dropdown(context, options, dropdown_label):
    items = [o.strip() for o in options.split(',')]
    clean = dropdown_label.lower().replace(" *", "").replace(" ", "_")
    trigger = find_fast(context, [
        aid("sel_" + clean),
        (By.XPATH, "//mat-select[contains(@id,'sel_" + clean + "')]"),
        (By.XPATH, "//label[contains(.,'" + dropdown_label + "')]/..//mat-select"),
    ])
    if not trigger:
        raise Exception("Multi-select not found: " + dropdown_label)
    trigger.click()
    time.sleep(0.4)
    for item in items:
        item = resolve_value(item)
        opt = find_fast(context, [
            (By.XPATH, "//mat-option[contains(.,'" + item + "')]"),
            (By.XPATH, "//li[contains(text(),'" + item + "')]"),
        ])
        if opt:
            opt.click()
            time.sleep(0.15)
            print("[DD] Multi-selected: " + item)
        else:
            print(f"[DD] WARNING: option '{item}' not found in multi-select")
    context.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)


@then('I clear all selections from the "{dropdown_label}" multi-select')
@when('I clear all selections from the "{dropdown_label}" multi-select')
def clear_multi_select(context, dropdown_label):
    el = find_fast(context, [
        (By.XPATH, "//label[contains(text(),'" + dropdown_label + "')]"
                   "/..//*[contains(@class,'clear') or contains(@aria-label,'Clear')]"),
    ])
    if el:
        el.click()
        print("[DD] Cleared multi-select: " + dropdown_label)
    else:
        print("[DD] Clear button not found for: " + dropdown_label)


# ─── AUTOCOMPLETE ─────────────────────────────────────────────────────────────

@then('I type and select "{option_text}" in the autocomplete input "{field_name}"')
@when('I type and select "{option_text}" in the autocomplete input "{field_name}"')
def type_and_select_autocomplete(context, option_text, field_name):
    option_text = resolve_value(option_text)
    clean = field_name.lower().replace(" ", "").replace("*", "")
    field = find_fast(context, [
        aid("inp_" + clean),
        (By.XPATH, "//input[@placeholder='" + field_name + "']"),
        (By.XPATH, "//label[contains(text(),'" + field_name + "')]/..//input"),
    ])
    if not field:
        raise Exception("Autocomplete field not found: " + field_name)
    field.clear()
    field.send_keys(option_text)
    time.sleep(0.8)
    option = find_fast(context, [
        (By.XPATH, "//mat-option[contains(.,'" + option_text + "')]"),
        (By.XPATH, "//li[contains(text(),'" + option_text + "')]"),
    ])
    if option:
        option.click()
        print("[AUTO] Selected: " + option_text)
    else:
        raise Exception("Autocomplete option not found: " + option_text)


@then('I select autocomplete option "{option_text}"')
@when('I select autocomplete option "{option_text}"')
def select_autocomplete_option(context, option_text):
    option_text = resolve_value(option_text)
    option = find_fast(context, [
        (By.XPATH, "//mat-option[contains(.,'" + option_text + "')]"),
        (By.XPATH, "//li[contains(text(),'" + option_text + "')]"),
    ])
    if option:
        option.click()
        print("[AUTO] Selected: " + option_text)
    else:
        raise Exception("Autocomplete option not found: " + option_text)


# ─── CHECKBOXES ───────────────────────────────────────────────────────────────

def _get_checkbox(context, label: str):
    label = label.strip()
    return find_fast(context, [
        (By.XPATH, f"//div[starts-with(@id,'chk_option')][contains(.,'{label}')]"),
        (By.XPATH, f"//div[contains(@class,'co-picker-toggle')][contains(normalize-space(.),'{label}')]"),
        (By.XPATH, f"//span[contains(text(),'{label}')]/ancestor::div[contains(@class,'co-picker-toggle')]"),
        (By.XPATH, f"//mat-checkbox[contains(.,'{label}')]//input"),
        (By.XPATH, f"//label[contains(text(),'{label}')]/..//input[@type='checkbox']"),
        (By.XPATH, f"//*[normalize-space(text())='{label}']"),
    ])


def _get_checkbox_by_id(context, elem_id: str):
    return find_fast(context, [
        (By.ID, elem_id),
        aid(elem_id),
        (By.XPATH, f"//*[@id='{elem_id}']"),
        (By.XPATH, f"//input[@id='{elem_id}']"),
        (By.XPATH, f"//*[@id='{elem_id}']//input[@type='checkbox']"),
    ])


@when('I check the checkbox labelled "{label}"')
@then('I check the checkbox labelled "{label}"')
def check_checkbox(context, label):
    el = _get_checkbox(context, label)
    if not el:
        raise Exception("Checkbox not found: " + label)
    safe_click(context, el)
    print("[CHK] Checked: " + label)


@when('I check the checkbox with id "{elem_id}"')
@then('I check the checkbox with id "{elem_id}"')
def check_checkbox_by_id(context, elem_id):
    el = _get_checkbox_by_id(context, elem_id)
    if not el:
        raise Exception("Checkbox not found with id: " + elem_id)
    safe_click(context, el)
    print("[CHK] Checked id: " + elem_id)


@when('I uncheck the checkbox labelled "{label}"')
@then('I uncheck the checkbox labelled "{label}"')
def uncheck_checkbox(context, label):
    el = _get_checkbox(context, label)
    if not el:
        raise Exception("Checkbox not found: " + label)
    safe_click(context, el)
    print("[CHK] Unchecked: " + label)


@when('I uncheck the checkbox with id "{elem_id}"')
@then('I uncheck the checkbox with id "{elem_id}"')
def uncheck_checkbox_by_id(context, elem_id):
    el = _get_checkbox_by_id(context, elem_id)
    if not el:
        raise Exception("Checkbox not found with id: " + elem_id)
    safe_click(context, el)
    print("[CHK] Unchecked id: " + elem_id)


@when('I uncheck "{name}"')
def step_uncheck(context, name):
    uncheck_checkbox(context, name)


# ─── RADIO BUTTONS ────────────────────────────────────────────────────────────

@then('I select "{option}" for the radio group "{group_name}"')
@when('I select "{option}" for the radio group "{group_name}"')
def select_radio(context, option, group_name):
    el = find_fast(context, [
        (By.XPATH, "//mat-radio-group//mat-radio-button[contains(.,'" + option + "')]"),
        (By.XPATH, "//label[contains(text(),'" + group_name + "')]/..//"
                   "input[@type='radio'][@value='" + option + "']"),
        (By.XPATH, "//mat-radio-button[contains(.,'" + option + "')]"),
    ])
    if el:
        el.click()
        print(f"[RADIO] Selected '{option}' in '{group_name}'")
        time.sleep(0.2)
        return
    raise Exception(f"Radio option '{option}' not found in group '{group_name}'")


# ─── CHIP INPUTS ──────────────────────────────────────────────────────────────

@then('I select "{options}" from the "{dropdown_label}" chip input')
@when('I select "{options}" from the "{dropdown_label}" chip input')
def select_chip_input(context, options, dropdown_label):
    items = [o.strip() for o in options.split(',')]
    chip_input = find_fast(context, [
        (By.XPATH, "//label[contains(text(),'" + dropdown_label + "')]/..//mat-chip-list//input"),
        (By.XPATH, "//mat-chip-list//input"),
    ])
    if not chip_input:
        raise Exception("Chip input not found: " + dropdown_label)
    for item in items:
        chip_input.clear()
        chip_input.send_keys(item)
        time.sleep(0.4)
        opt = find_fast(context, [
            (By.XPATH, "//mat-option[contains(.,'" + item + "')]"),
            (By.XPATH, "//li[contains(text(),'" + item + "')]"),
        ])
        if opt:
            opt.click()
            print("[CHIP] Selected: " + item)
        else:
            print("[CHIP] WARNING: option not found: " + item)
        time.sleep(0.2)


@then('I remove "{chip_name}" chip from the "{dropdown_label}" chip input')
@when('I remove "{chip_name}" chip from the "{dropdown_label}" chip input')
def remove_chip(context, chip_name, dropdown_label):
    el = find_fast(context, [
        (By.XPATH, "//mat-chip[contains(.,'" + chip_name + "')]//mat-icon[contains(.,'cancel')]"),
        (By.XPATH, "//mat-chip[contains(.,'" + chip_name + "')]//button"),
    ])
    if el:
        el.click()
        print("[CHIP] Removed: " + chip_name)
        return
    raise Exception("Chip not found: " + chip_name)


@then('I remove all chips from the "{dropdown_label}" chip input')
@when('I remove all chips from the "{dropdown_label}" chip input')
def remove_all_chips(context, dropdown_label):
    chips = context.driver.find_elements(
        By.XPATH,
        "//label[contains(text(),'" + dropdown_label + "')]/..//mat-chip//mat-icon | "
        "//label[contains(text(),'" + dropdown_label + "')]/..//mat-chip//button"
    )
    for chip in chips:
        try:
            chip.click()
            time.sleep(0.1)
        except Exception:
            continue
    print("[CHIP] Removed all chips from: " + dropdown_label)


@then('the "{dropdown_label}" chip input should contain "{expected_chips}"')
def verify_chips(context, dropdown_label, expected_chips):
    expected = [c.strip() for c in expected_chips.split(',')]
    chips = context.driver.find_elements(
        By.XPATH, "//label[contains(text(),'" + dropdown_label + "')]/..//mat-chip"
    )
    chip_texts = [c.text.strip() for c in chips]
    for exp in expected:
        assert any(exp in ct for ct in chip_texts), "Chip not found: " + exp
    print("[CHIP] Verified: " + expected_chips)
