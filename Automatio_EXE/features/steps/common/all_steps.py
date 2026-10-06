"""
all_steps.py — Backward-compatible re-export shim
==================================================
This file is kept so that any existing feature file or Behave
configuration that references "all_steps" continues to work.

All step implementations have been split into focused modules:

  navigation_steps.py  — Page navigation, waits, debug
  menu_steps.py        — Sidebar menu, tabs
  button_steps.py      — Button and icon clicks
  input_steps.py       — Text inputs, search bar
  dropdown_steps.py    — Dropdowns, autocomplete, checkboxes, radio, chips
  date_steps.py        — Date / date-range pickers
  devx_steps.py        — DevExtreme grid, treeview, export
  file_steps.py        — File export, download verification, upload
  dialog_steps.py      — Dialogs, toasts, table actions, accordions, scroll

Shared utilities live in:

  utils.py             — resolve_value, find_fast, aid, safe_click,
                         load_config, get_base, directory constants

Importing all modules here registers their @given/@when/@then
decorators with the Behave step registry automatically.
"""

# ── Re-import all sub-modules so their step decorators are registered ──────────
import features.steps.common.navigation_steps   # noqa: F401
import features.steps.common.menu_steps         # noqa: F401
import features.steps.common.button_steps       # noqa: F401
import features.steps.common.input_steps        # noqa: F401
import features.steps.common.dropdown_steps     # noqa: F401
import features.steps.common.date_steps         # noqa: F401
import features.steps.common.devx_steps         # noqa: F401
import features.steps.common.file_steps         # noqa: F401
import features.steps.common.dialog_steps       # noqa: F401

# ── Re-export shared utilities for any code that imports from all_steps ────────
from features.steps.common.utils import (       # noqa: F401
    resolve_value,
    resolve_date,
    find_fast,
    aid,
    safe_click,
    get_base,
    load_config,
    BASE,
    DOWNLOADS_DIR,
    UPLOADS_DIR,
    SCREENSHOTS_DIR,
)