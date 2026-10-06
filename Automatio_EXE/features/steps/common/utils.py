"""
utils.py — shared utilities for ALL Behave step modules
========================================================
Single source of truth for:
  - resolve_value()  : expand {date}, {timestamp}, today+N tokens
  - find_fast()      : try multiple selectors, return first match
  - aid()            : shorthand for data-testid CSS selector tuple
  - safe_click()     : scroll-into-view + JS fallback click
  - get_base()       : locate project root (works in EXE mode too)
  - load_config()    : parse config.env once, return dict
  - Directory constants: BASE, DOWNLOADS_DIR, UPLOADS_DIR, SCREENSHOTS_DIR
"""

import os
import re
import sys
import time
from datetime import datetime, timedelta

from selenium.webdriver.common.by import By


# ── Project root ──────────────────────────────────────────────────────────────

def get_base() -> str:
    """Locate project root by walking up from __file__ until config.env is found."""
    p = os.path.abspath(__file__)
    for _ in range(5):
        p = os.path.dirname(p)
        if os.path.exists(os.path.join(p, "config.env")):
            return p
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return r"C:\Automatio_EXE"


BASE            = get_base()
DOWNLOADS_DIR   = os.path.join(BASE, "downloads")
UPLOADS_DIR     = os.path.join(BASE, "uploads")
SCREENSHOTS_DIR = os.path.join(BASE, "screenshots")


# ── Config loader ─────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Parse config.env and return key/value dict.

    Search order:
      1. sys._MEIPASS (PyInstaller bundle)
      2. Project BASE directory
      3. Current working directory
      4. C:\\Automatio_EXE
    """
    search = [
        os.path.join(BASE, "config.env"),
        os.path.join(os.getcwd(), "config.env"),
        r"C:\Automatio_EXE\config.env",
    ]
    if hasattr(sys, "_MEIPASS"):
        search.insert(0, os.path.join(sys._MEIPASS, "config.env"))

    for path in search:
        if os.path.exists(path):
            config: dict = {}
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        config[key.strip()] = val.strip()
            print("[CONFIG] Loaded: " + path)
            return config

    print("[CONFIG] WARNING: config.env not found — using empty config")
    return {}


# ── Selector helpers ──────────────────────────────────────────────────────────

def aid(testid: str) -> tuple:
    """Return a (By.CSS_SELECTOR, ...) tuple targeting data-testid='testid'."""
    return (By.CSS_SELECTOR, '[data-testid="' + testid + '"]')


def find_fast(context, selectors: list, timeout: float = None):
    """Ultra-fast element finder across multiple selector candidates.
    1. Instant DOM check (Pass 1): Probes selectors immediately with 0 wait.
       If an element is already in the DOM, returns it in 1-5ms.
    2. Polling loop (Pass 2): If not immediately found, polls all selectors
       together up to a single total timeout (NOT per-selector timeout).
    """
    driver = getattr(context, "driver", None)
    if not driver:
        return None

    # Pass 1: Instant scan across all candidates (takes ~1-5ms total)
    for by, sel in selectors:
        try:
            els = driver.find_elements(by, sel)
            for el in els:
                if el.is_displayed():
                    return el
            if els:
                return els[0]
        except Exception:
            continue

    # Pass 2: Polling loop if element needs a moment to render / animate in
    if timeout is None:
        timeout = float(getattr(context, "short_timeout_sec", 2.0))

    end_time = time.time() + timeout
    while time.time() < end_time:
        time.sleep(0.06)
        for by, sel in selectors:
            try:
                els = driver.find_elements(by, sel)
                for el in els:
                    if el.is_displayed():
                        return el
                if els:
                    return els[0]
            except Exception:
                continue

    return None


def safe_click(context, element) -> None:
    """Scroll element into view then click; fall back to JS click if intercepted."""
    context.driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", element
    )
    time.sleep(0.08)
    try:
        element.click()
    except Exception as exc:
        print(f"[WARN] Normal click failed ({exc}), using JS click")
        context.driver.execute_script("arguments[0].click();", element)


# ── Value / date resolver ─────────────────────────────────────────────────────

def resolve_value(value: str) -> str:
    """Expand dynamic tokens in a string value.

    Supported tokens:
      {timestamp}   2025-01-15 09:30:00
      {date}        2025-01-15
      {time}        09:30:00
      {datetime}    January 15, 2025 09:30 AM
      {date_short}  01/15/2025
      {date_us}     15/01/2025
      {unix}        1736929800
      {year}        2025
      {month}       01
      {day}         15
      today         2025-01-15
      today+3       2025-01-18
      today-7       2025-01-08
    """
    now = datetime.now()
    tokens = {
        "{timestamp}":  now.strftime("%Y-%m-%d %H:%M:%S"),
        "{date}":       now.strftime("%Y-%m-%d"),
        "{time}":       now.strftime("%H:%M:%S"),
        "{datetime}":   now.strftime("%B %d, %Y %I:%M %p"),
        "{date_short}": now.strftime("%m/%d/%Y"),
        "{date_us}":    now.strftime("%d/%m/%Y"),
        "{unix}":       str(int(now.timestamp())),
        "{year}":       now.strftime("%Y"),
        "{month}":      now.strftime("%m"),
        "{day}":        now.strftime("%d"),
    }
    for token, replacement in tokens.items():
        value = value.replace(token, replacement)

    # today[+/-N] relative date
    value = re.sub(
        r"\btoday([+-]\d+)?",
        lambda m: (
            now + timedelta(days=int(m.group(1)) if m.group(1) else 0)
        ).strftime("%Y-%m-%d"),
        value,
    )
    return value


def resolve_date(value: str) -> str:
    """Convenience alias: resolve tokens and return a YYYY-MM-DD date string."""
    return resolve_value(value)
