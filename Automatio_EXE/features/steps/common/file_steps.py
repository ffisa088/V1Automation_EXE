"""
file_steps.py — Export, import, upload, and download step definitions
"""

import os
import glob
import time

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from features.steps.common.utils import find_fast, safe_click, DOWNLOADS_DIR, UPLOADS_DIR
from features.steps.common.button_steps import _click_btn


# ─── EXPORT ───────────────────────────────────────────────────────────────────

@then('I click on the Export to Excel button')
@when('I click on the Export to Excel button')
def click_export_excel(context):
    _click_btn(context, 'Export to Excel', 'Excel', 'Export Excel')


# ─── DOWNLOAD VERIFICATION ────────────────────────────────────────────────────

@then('the excel file should download successfully')
def verify_excel_download(context):
    time.sleep(3)
    files = (
        glob.glob(os.path.join(DOWNLOADS_DIR, '*.xlsx')) +
        glob.glob(os.path.join(DOWNLOADS_DIR, '*.xls'))
    )
    assert len(files) > 0, "Excel file not downloaded!"
    print("[FILE] Excel downloaded: " + os.path.basename(files[-1]))


@then('the csv file should download successfully')
def verify_csv_download(context):
    time.sleep(3)
    files = glob.glob(os.path.join(DOWNLOADS_DIR, '*.csv'))
    assert len(files) > 0, "CSV file not downloaded!"
    print("[FILE] CSV downloaded: " + os.path.basename(files[-1]))


@then('the download should complete successfully')
@then('file should download')
def verify_download(context):
    time.sleep(3)
    files = [
        f for f in os.listdir(DOWNLOADS_DIR)
        if not f.endswith('.tmp') and not f.endswith('.crdownload')
    ]
    assert len(files) > 0, "No file was downloaded!"
    print("[FILE] Download complete: " + files[-1])


@then('the file {filename} should exist in downloads')
def verify_file_exists(context, filename):
    path = os.path.join(DOWNLOADS_DIR, filename)
    assert os.path.exists(path), "File not found in downloads: " + filename
    print("[FILE] File exists: " + filename)


@then('I wait for {seconds:d} seconds for the download')
def wait_for_download(context, seconds):
    time.sleep(seconds)


@then('I clean up the downloaded files')
def clean_downloads(context):
    files = glob.glob(os.path.join(DOWNLOADS_DIR, '*'))
    removed = 0
    for f in files:
        try:
            os.remove(f)
            removed += 1
        except Exception as exc:
            print(f"[FILE] Could not remove {f}: {exc}")
    print(f"[FILE] Cleaned {removed} file(s) from downloads/")


# ─── UPLOAD ───────────────────────────────────────────────────────────────────

@then('I upload the file "{filename}" to the import')
@when('I upload the file "{filename}" to the import')
@then('I upload the file "{filename}" to the import via upload button')
@when('I upload the file "{filename}" to the import via upload button')
@when('I upload "{filename}"')
def upload_file(context, filename):
    # Look in downloads first (exported files), then uploads
    path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(path):
        raise Exception(f"File not found for upload: {filename}\n"
                        f"  Checked: {DOWNLOADS_DIR}\n"
                        f"           {UPLOADS_DIR}")
    el = context.wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )
    el.send_keys(path)
    print("[FILE] Uploaded: " + filename)
    time.sleep(1)
