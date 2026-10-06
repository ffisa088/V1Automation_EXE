# AcSys ERP BDD Automation — Guidance & Step Bindings Reference

> Comprehensive reference guide for QA engineers and developers creating and running automated BDD feature files in the AcSys ERP project.

---

## Table of Contents
1. [Architecture & Lifecycle](#architecture--lifecycle)
2. [Directory Layout](#directory-layout)
3. [Complete Step Bindings Reference](#complete-step-bindings-reference)
   - [1. Authentication & Login](#1-authentication--login)
   - [2. Navigation, Menus & Tabs](#2-navigation-menus--tabs)
   - [3. Waits & Page Render State](#3-waits--page-render-state)
   - [4. Buttons & Clicks](#4-buttons--clicks)
   - [5. Input Fields & Search](#5-input-fields--search)
   - [6. Dropdowns & Selection](#6-dropdowns--selection)
   - [7. Date Pickers & Range](#7-date-pickers--range)
   - [8. Checkboxes, Radios & Chips](#8-checkboxes-radios--chips)
   - [9. DevExtreme Grid (DevX)](#9-devextreme-grid-devx)
   - [10. File Uploads & Downloads](#10-file-uploads--downloads)
   - [11. Dialogs, Modals, Toasts & Icons](#11-dialogs-modals-toasts--icons)
   - [12. Dynamic Value Resolvers](#12-dynamic-value-resolvers)
4. [How to Run Tests](#how-to-run-tests)
5. [Artifacts & Diagnostic Outputs](#artifacts--diagnostic-outputs)

---

## Architecture & Lifecycle

* **BDD Framework**: Built with Python and **Behave** (Gherkin syntax: `Given`, `When`, `Then`).
* **Browser Driver**: Selenium WebDriver controls Google Chrome.
* **Singleton Browser Session**: `features/environment.py` manages a single browser instance that stays open across scenarios to eliminate repeated login overhead.
* **Master Login**: `features/login.feature` executes first to authenticate and expand sidebar toolbar menus.
* **Automatic Diagnostics**: If any step fails, `environment.py` immediately saves a timestamped screenshot in `screenshots/` and logs the failure in `screenshot_index.json`.
* **Visual Reports**: `generate_report.py` converts Behave's raw JSON telemetry into standalone, color-coded HTML dashboards in `reports/`.

---

## Directory Layout

```text
Automatio_EXE/
├── config.env                 # Credentials, URLs, and browser settings
├── BehaveTestRunner.py        # Central CLI runner with auto-reporting
├── run_tests.bat              # One-click interactive Windows launcher
├── setup.bat                  # One-click installer for dependencies & folders
├── generate_report.py         # Generates interactive HTML test reports
├── ARTIFACTS_GUIDE.html       # Searchable HTML reference with copy-to-clipboard
├── ARTIFACTS_GUIDE.md         # Markdown reference guide
├── PRESENTATION.html          # Interactive slide deck for stakeholders
├── features/
│   ├── login.feature          # Master authentication flow
│   ├── environment.py         # Hooks (before_all, after_scenario, etc.)
│   ├── Forms/                 # Business feature test files
│   │   ├── User_Management (2).feature
│   │   ├── ticket_manager.feature
│   │   └── Demo.feature
│   └── steps/
│       ├── auth/
│       │   └── login_steps.py # Authentication step bindings
│       └── common/
│           ├── all_steps.py   # Universal UI interaction step bindings
│           └── helpers.py     # Low-level Selenium locators and utilities
├── reports/                   # HTML & JSON test execution results
├── screenshots/               # Failure evidence PNG captures
├── downloads/                 # Browser auto-download target
└── uploads/                   # Test attachments for import/upload
```

---

## Complete Step Bindings Reference

Use these exact step definitions when writing `.feature` files inside `features/Forms/`.

### 1. Authentication & Login
*File: `features/steps/auth/login_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `Given` | `I open the login page` | Navigates to `LOGIN_URL` from `config.env`. |
| `When` | `I enter the tenantCode` | Enters tenant code from `config.env` into tenant field. |
| `When` | `I select the company "{company_name}"` | Searches and selects company from tenant list. |
| `Then` | `I click on the Continue button` | Clicks Continue button after tenant entry. |
| `When` | `I enter the username` | Enters username from `config.env`. |
| `When` | `I enter the password` | Enters password from `config.env`. |
| `Then` | `I click on the Sign In button` | Clicks Sign In button. |
| `Then` | `I should see the dashboard page` | Verifies dashboard has rendered. |
| `Then` | `I expand all menus in the toolbar` | Expands all navigation menus in toolbar. |

---

### 2. Navigation, Menus & Tabs
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `Given` | `I am on the "{page_name}" page` | Verifies or waits until page header matches. |
| `Given` | `I am on the dashboard page` | Verifies user is on main dashboard. |
| `When`/`Then` | `I click on "{menu_item}" from the menu` | Clicks sidebar menu item (e.g. `"User Management"`). |
| `Given` | `I am on the "{tab_name}" menu tab` | Verifies designated upper workspace tab is active. |
| `When`/`Then` | `I switch to the "{tab_name}" menu tab` | Switches view to designated upper tab. |
| `When`/`Then` | `I switch to tab "{tab_name}"` | Switches tab (e.g. `"My Request"`, `"Common Task"`). |
| `Then` | `I should see the "{tab_name}" menu tab is active` | Asserts tab has active CSS highlight. |
| `When`/`Then` | `I close the "{tab_name}" menu tab` | Clicks close 'X' on designated workspace tab. |
| `Then` | `the "{tab_name}" menu tab should not exist` | Asserts tab is no longer present in DOM. |

---

### 3. Waits & Page Render State
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `Then` | `I wait for the page to be fully loaded` | Waits for complete document state & no spinners. |
| `Given`/`When`/`Then`| `I wait for the page to be rendered` | Waits for Angular/DevExtreme controls to finish rendering. |
| `Then` | `the page is ready` | Synonym for render completion. |
| `When`/`Then` | `I wait for {seconds:d} seconds` | Explicit sleep for N seconds (e.g. `I wait for 2 seconds`). |
| `Then` | `I debug the page` | Prints console diagnostics of all visible elements. |
| `Then` | `I close any open notifications` | Dismisses lingering toast messages. |

---

### 4. Buttons & Clicks
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I click on the Add button` | Clicks primary Add button (`btn_add`, `Add`). |
| `When`/`Then` | `I click on the Save button` | Clicks primary Save button. |
| `When`/`Then` | `I click on the Cancel button` | Clicks Cancel button to abort dialog. |
| `When`/`Then` | `I click on the Close button` | Clicks dialog Close / 'X' button. |
| `When`/`Then` | `I close the dialog` | Smart dismiss: clicks Close button or backdrop. |
| `When`/`Then` | `I click on the Submit button` | Clicks Submit button. |
| `When`/`Then` | `I click on the Clear button` | Clicks filter/form reset button. |
| `When`/`Then` | `I click on the Next button` | Advances to next step in wizard dialogs. |
| `When`/`Then` | `I click on the Back button` | Returns to previous step in wizard dialogs. |
| `When`/`Then` | `I click on the Export button` | Triggers export action. |
| `When`/`Then` | `I click on the Import button` | Opens import file dialog. |
| `When`/`Then` | `I click on the "{button_name}" button` | Clicks any button by text (e.g. `"Create User"`). |
| `When`/`Then` | `I click on Yes in the delete confirmation dialog` | Confirms destructive action. |
| `When`/`Then` | `I click on No in the delete confirmation dialog` | Aborts destructive action. |
| `When`/`Then` | `I click "{name}"` | Generic click by visible text or automation ID. |

---

### 5. Input Fields & Search
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I type "{text}" in the input "{field_name}"` | Types into input field matching placeholder, ID, or `inp_{name}`. |
| `When`/`Then` | `I type "{value}" in "{field}"` | Short alias to type text into any field. |
| `When`/`Then` | `I clear the input "{field_name}"` | Clears text from input field. |
| `When`/`Then` | `I type "{text}" in the search bar` | Types query into active page search input. |
| `When`/`Then` | `I clear the search bar` | Clears page search input. |

---

### 6. Dropdowns & Selection
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I select "{option_text}" from the "{dropdown_label}" dropdown` | Selects option from standard dropdown (e.g. `"Active"` from `"status"`). |
| `When`/`Then` | `I select "{option_text}" from the "{dropdown_label}" searchable dropdown` | Selects option from searchable/filtered select dropdown. |
| `When` | `I select "{option}" from "{dropdown}"` | Short alias for dropdown selection. |
| `When`/`Then` | `I select "{options}" from the "{dropdown_label}" multi-select dropdown` | Selects multiple comma-separated items. |
| `When`/`Then` | `I clear all selections from the "{dropdown_label}" multi-select` | Deselects all checked items. |
| `When`/`Then` | `I type and select "{option_text}" in the autocomplete input "{field_name}"` | Types into autocomplete and clicks matching suggestion. |

---

### 7. Date Pickers & Range
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I open the date picker calendar and select "{date}"` | Picks date (supports `today`, `today+3`, `YYYY-MM-DD`). |
| `When`/`Then` | `I select the date range from "{start_date}" to "{end_date}" in the start-end date picker calender` | Selects dual start and end dates. |
| `When`/`Then` | `I clear the start-end date picker` | Resets date range picker. |
| `When`/`Then` | `I select "{month_year}" in the "{picker_id}" month year picker calendar` | Selects month and year view. |

---

### 8. Checkboxes, Radios & Chips
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I check the checkbox labelled "{label}"` | Checks checkbox by label text (e.g. `"Enable access"`). |
| `When`/`Then` | `I uncheck the checkbox labelled "{label}"` | Unchecks checkbox if selected. |
| `When`/`Then` | `I select "{option}" for the radio group "{group_name}"` | Selects radio button in named group. |
| `When`/`Then` | `I select "{options}" from the "{dropdown_label}" chip input` | Adds one or more tags/chips. |
| `When`/`Then` | `I remove "{chip_name}" chip from the "{dropdown_label}" chip input` | Removes specific chip tag. |

---

### 9. DevExtreme Grid (DevX)
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I click on the devx Add button` | Clicks '+' icon in DevExtreme grid toolbar. |
| `When`/`Then` | `I click the devx inline Save button` | Saves an inline-edited row. |
| `When`/`Then` | `I click the devx inline Cancel button` | Cancels inline editing. |
| `When`/`Then` | `I type "{value}" in the devx input "{col_name}" column` | Types value into column cell during edit. |
| `When`/`Then` | `I type "{text}" in devx search bar` | Searches inside DevExtreme search box. |
| `When`/`Then` | `I clear the devx search bar` | Clears DevExtreme search box. |
| `When`/`Then` | `I click on the Export to Excel devx button` | Exports grid data to Excel via toolbar button. |
| `When`/`Then` | `I check the devx row where "{col_name}" is "{col_value}"` | Selects row checkbox matching column value. |
| `When`/`Then` | `I select all devx rows` | Checks 'Select All' header checkbox. |

---

### 10. File Uploads & Downloads
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `When`/`Then` | `I click on the Export to Excel button` | Triggers Excel download. |
| `Then` | `the excel file should download successfully` | Asserts `.xlsx` / `.xls` appears in `downloads/`. |
| `Then` | `the csv file should download successfully` | Asserts `.csv` appears in `downloads/`. |
| `Then` | `the file {filename} should exist in downloads` | Verifies specific file was downloaded. |
| `When`/`Then` | `I upload "{filename}"` | Uploads file from `uploads/` folder. |
| `Then` | `I clean up the downloaded files` | Deletes temporary test downloads. |

---

### 11. Dialogs, Modals, Toasts & Icons
*File: `features/steps/common/all_steps.py`*

| Keyword | Step Pattern | Description |
| :--- | :--- | :--- |
| `Then` | `I should see the dialog box` | Asserts modal dialog is currently visible. |
| `Then` | `I should see the success toast` | Waits for green confirmation notification toast. |
| `When` | `I scroll down the "{panel_name}" panel` | Scrolls modal settings/body panel downwards. |
| `Then` | `I scroll up the "{panel_name}" panel` | Scrolls modal settings/body panel upwards. |
| `When` | `I click row actions for user "{username}"` | Clicks 3-dots action menu for table row user. |
| `When` | `I click "{action}" from the action menu` | Clicks item inside opened action menu (e.g. `"Edit User"`). |
| `When`/`Then` | `I click the "{icon}" icon` | Clicks icon button (e.g. `"toggle_password_visibility"`). |
| `When`/`Then` | `I toggle the "{header_text}" accordion` | Expands/collapses collapsible panel accordion. |

---

### 12. Dynamic Value Resolvers
*File: `features/steps/common/helpers.py`*

You can insert dynamic placeholders inside any quoted string value:

| Placeholder | Resolves To | Example |
| :--- | :--- | :--- |
| `{timestamp}` | Current timestamp | `TestUser_{timestamp}` → `TestUser_2026-09-21 11:30:00` |
| `{date}` | Current ISO date | `Doc_{date}` → `Doc_2026-09-21` |
| `{time}` | Current time | `11:30:00` |
| `{unix}` | Unix epoch seconds | `User_{unix}` → `User_1789972200` |
| `{year}` | Current 4-digit year | `2026` |
| `today+1` / `today-2` | Relative future/past dates | `today+3` → Date 3 days from now |

---

## How to Run Tests

### Method 1: Interactive Windows Launcher (Easiest)
Double-click `run_tests.bat` in Windows Explorer:
```text
  AcSys ERP BDD Automation Runner
  ----------------------------------------------------------------
   1. Run ALL feature files
   2. Run tests by TAG (e.g. @smoke)
   3. Browse and select a feature file
   4. Exit
  ----------------------------------------------------------------
```

### Method 2: Python Command Line Runner
```powershell
# Run interactive menu:
python BehaveTestRunner.py

# Run all features:
python BehaveTestRunner.py --run-all

# Run single feature:
python BehaveTestRunner.py --feature features/Forms/Demo.feature

# Run tagged scenarios:
python BehaveTestRunner.py --tag @smoke
```

### Method 3: Validate Without Opening Browser (Dry Run)
```powershell
python -m behave --dry-run
```

---

## Artifacts & Diagnostic Outputs

* **HTML Reports**: Saved in `reports/` (e.g. `reports/Forms/Demo_20260921_113000.html`). Open in any browser to review passed/failed steps, timing metrics, and error logs.
* **Failure Screenshots**: Saved in `screenshots/` on any scenario failure (`screenshots/FAIL_{scenario}_{timestamp}.png`).
* **Screenshot Index**: `screenshots/screenshot_index.json` links scenarios to screenshot filepaths so reports embed images automatically.
