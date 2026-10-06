from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import time

# ── Shared utilities (single source of truth) ─────────────────────────────────
from features.steps.common.utils import load_config, aid, find_fast

# ── Load credentials from config.env ──────────────────────────────────────────
CONFIG      = load_config()
LOGIN_URL   = CONFIG.get("LOGIN_URL", "")
COMPANY     = CONFIG.get("COMPANY", "")
TENANT_CODE = CONFIG.get("TENANT_CODE", "T1001")
USERNAME    = CONFIG.get("USERNAME", "")
PASSWORD    = CONFIG.get("PASSWORD", "")

if not USERNAME or not PASSWORD:
    raise RuntimeError("USERNAME and PASSWORD must be set in config.env")

print("[LOGIN] URL: " + LOGIN_URL + " | Company: " + (COMPANY or "not set") + " | User: " + USERNAME)

# ── OPEN LOGIN PAGE ───────────────────────────────────────────────────────────
@given('I open the login page')
def open_login_page(context):
    context.driver.get(LOGIN_URL)
    print("Opened: " + LOGIN_URL)
    context.short_wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

# ── ENTER TENANT CODE ───────────────────────────────────────────────────────
@when('I enter the tenantCode')
def enter_tenant_code(context):
    candidates = [
        aid("inp_tenantcode"),
        (By.XPATH, "//input[contains(@placeholder,'Tenant') or contains(@placeholder,'tenant') or contains(@placeholder,'code') or contains(@placeholder,'ACME') or contains(@placeholder,'e.g.')]"),
        (By.XPATH, "//label[contains(normalize-space(.),'Tenant code')]/following::input[1]"),
        (By.ID, "tenantCode"),
        (By.NAME, "tenantCode"),
        (By.XPATH, "//input[@type='text' or @type='email']"),
    ]
    el = find_fast(context, candidates)
    if el:
        try:
            el.clear()
        except Exception:
            pass
        el.send_keys(TENANT_CODE)
        print("Entered tenant code: " + TENANT_CODE)
        return
    raise Exception("Tenant code field not found!")

# ── SELECT COMPANY ────────────────────────────────────────────────────────────
@when('I select the company "{company_name}"')
def select_company(context, company_name):
    try:
        # Search for company using inp_search automation ID
        search = find_fast(context, [
            aid("inp_search"),
            (By.XPATH, "//input[@placeholder='Search companies...']"),
            (By.XPATH, "//input[contains(@placeholder,'Search')]"),
        ])
        if search:
            search.clear()
            search.send_keys(company_name)
            time.sleep(0.5)

        # Click company row: row_item_company_{code}
        row = find_fast(context, [
            aid("row_item_company_" + TENANT_CODE),
            (By.XPATH, "//*[contains(@data-testid,'row_item_company')]"
                       "[contains(.,'" + company_name + "')]"),
            (By.XPATH, "//*[contains(text(),'" + company_name + "')]"
                       "[contains(@class,'company') or contains(@class,'workspace') or "
                       "contains(@class,'row') or contains(@class,'item')]"),
            (By.XPATH, "//*[contains(text(),'" + company_name + "')]"),
        ])
        if row:
            row.click()
            print("Selected company: " + company_name)
            time.sleep(0.8)
        else:
            # Try typing tenant code directly
            inp = find_fast(context, [
                aid("inp_tenantcode"),
                (By.XPATH, "//input[contains(@placeholder,'code') or contains(@placeholder,'tenant')]"),
            ])
            if inp:
                inp.clear()
                inp.send_keys(TENANT_CODE)
                print("Typed tenant code: " + TENANT_CODE)
                time.sleep(0.5)
    except Exception as e:
        raise Exception("Company selection failed: " + str(e))

# ── CLICK CONTINUE (STEP 1 → STEP 2) ─────────────────────────────────────────
@then('I click on the Continue button')
def click_continue(context):
    el = find_fast(context, [
        aid("btn_next"),
        (By.XPATH, "//button[contains(text(),'Continue')]"),
        (By.XPATH, "//button[normalize-space()='Continue →']"),
        (By.XPATH, "//button[contains(.,'Continue')]"),
    ])
    if el:
        el.click()
        print("Clicked Continue")
        context.short_wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "input")) > 0)
        return
    raise Exception("Continue button not found!")

# ── ENTER USERNAME ────────────────────────────────────────────────────────────
@when('I enter the username')
def enter_username(context):
    el = find_fast(context, [
        aid("inp_email"),
        (By.XPATH, "//input[@placeholder='you@company.com']"),
        (By.XPATH, "//input[contains(@placeholder,'Email') or contains(@placeholder,'Username')]"),
        (By.ID, "mat-input-0"),
        (By.XPATH, "//input[contains(@class,'mat-input-element')]"),
        (By.XPATH, "(//input[@type='text'])[1]"),
    ])
    if el:
        el.clear()
        el.send_keys(USERNAME)
        print("Entered username: " + USERNAME)
        return
    raise Exception("Username field not found!")

# ── ENTER PASSWORD ────────────────────────────────────────────────────────────
@when('I enter the password')
def enter_password(context):
    el = find_fast(context, [
        aid("inp_password"),
        (By.XPATH, "//input[@placeholder='Enter your password']"),
        (By.XPATH, "//input[@type='password']"),
        (By.ID, "mat-input-1"),
    ])
    if el:
        el.clear()
        el.send_keys(PASSWORD)
        print("Entered password")
        return
    raise Exception("Password field not found!")

# ── CLICK SIGN IN ─────────────────────────────────────────────────────────────
@then('I click on the Sign In button')
def click_sign_in(context):
    el = find_fast(context, [
        aid("btn_submit"),
        (By.ID,    'btn_submit'),
        (By.XPATH, "//button[normalize-space()='Sign in' or normalize-space()='Sign In' or normalize-space()='Sign in to acSysERP']"),
        (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]"),
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//input[@type='submit']")
    ])
    if el:
        el.click()
        print("Clicked Sign In")
        context.wait.until(lambda d: "/app" in d.current_url)
        return

    # Debug snapshot for the real app markup when the selector still misses.
    try:
        buttons = context.driver.find_elements(By.XPATH, "//button")
        names = [b.text.strip() for b in buttons if b.text and b.text.strip()]
        print("Available buttons: " + str(names[:20]))
    except Exception:
        pass
    raise Exception("Sign In button not found!")

# ── OLD PRIMARY BUTTON (kept for compatibility) ───────────────────────────────
@then('I click on the primary button in the login page')
def click_primary_button(context):
    el = find_fast(context, [
        aid("btn_next"),
        aid("btn_submit"),
        (By.XPATH, "//button[contains(text(),'Continue')]"),
        (By.XPATH, "//button[contains(text(),'Sign In')]"),
        (By.XPATH, "//button[@type='submit']"),
    ])
    if el:
        el.click()
        print("Clicked primary button")
        time.sleep(2)
        return
    raise Exception("Primary button not found!")

# ── VERIFY DASHBOARD ──────────────────────────────────────────────────────────
@then('I should see the dashboard page')
def verify_dashboard(context):
    context.wait.until(lambda d: "/app" in d.current_url)
    print("Dashboard URL: " + context.driver.current_url)



# ── EXPAND ALL MENUS ──────────────────────────────────────────────────────────
@then('I expand all menus in the toolbar')
def expand_all_menus(context):
    print("Expanding all sidebar menu trees and child menus...")
    total_expanded = 0
    max_passes = 20

    for pass_num in range(1, max_passes + 1):
        # Find all closed expandable parent menus in the sidebar
        closed_buttons = context.driver.execute_script("""
            var sidebar = document.querySelector('nav.sidebar, .shell-sidebar, mat-sidenav') || document.body;
            var buttons = sidebar.querySelectorAll('button.nav-parent, .nav-parent, [role="treeitem"][aria-expanded="false"]');
            var closed = [];
            
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                // Must be visible
                var rect = btn.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                
                // Exclude company switcher or items outside sidebar menu body
                if (btn.classList.contains('company-switcher') || btn.closest('.menu-panel-company')) continue;
                
                // Determine if already expanded:
                var chevron = btn.querySelector('.nav-chevron, mat-icon');
                var isChevronOpen = chevron && (chevron.classList.contains('open') || 
                                                /expand_less|keyboard_arrow_up|arrow_drop_up/.test(chevron.textContent || ''));
                
                var parentNode = btn.closest('.menu-tree-node, app-menu-tree-node, [role="treeitem"]');
                var hasNavChildren = false;
                if (parentNode) {
                    var ch = parentNode.querySelector('.nav-children');
                    if (ch && ch.children.length > 0) hasNavChildren = true;
                }
                
                var ariaExp = btn.getAttribute('aria-expanded');
                var isExpanded = isChevronOpen || hasNavChildren || (ariaExp === 'true');
                
                // Only collect if strictly closed / not expanded
                if (!isExpanded) {
                    closed.push(btn);
                }
            }
            return closed;
        """)

        if not closed_buttons:
            print(f"Pass {pass_num}: No closed parent menus found. All menus expanded.")
            break

        print(f"Pass {pass_num}: Found {len(closed_buttons)} closed menu tree nodes")
        pass_expanded = 0

        for btn in closed_buttons:
            try:
                # Safely re-check and click only if still closed to prevent accidental collapse
                result = context.driver.execute_script("""
                    var btn = arguments[0];
                    if (!btn || !btn.isConnected) return null;
                    
                    var chevron = btn.querySelector('.nav-chevron, mat-icon');
                    if (chevron && (chevron.classList.contains('open') || 
                        /expand_less|keyboard_arrow_up|arrow_drop_up/.test(chevron.textContent || ''))) {
                        return null; // Already expanded, do NOT click (never collapse)
                    }
                    
                    var parentNode = btn.closest('.menu-tree-node, app-menu-tree-node, [role="treeitem"]');
                    if (parentNode) {
                        var ch = parentNode.querySelector('.nav-children');
                        if (ch && ch.children.length > 0) return null; // Already has children rendered
                    }
                    
                    if (btn.getAttribute('aria-expanded') === 'true') return null;
                    
                    var labelEl = btn.querySelector('.nav-text') || btn;
                    var label = (labelEl.textContent || '').trim().split('\\n')[0];
                    
                    btn.scrollIntoView({block: 'nearest'});
                    btn.click();
                    return label || 'menu';
                """, btn)

                if result:
                    pass_expanded += 1
                    total_expanded += 1
                    print(f"  Expanded: {result}")
                    time.sleep(0.15)
            except Exception as e:
                # Silently ignore stale element references during dynamic DOM updates
                pass

        if pass_expanded == 0:
            break

        # Short pause between passes for Angular tree rendering / DOM update
        time.sleep(0.3)

    print(f"All parent and child menu trees expanded successfully. Total expanded: {total_expanded}")
# ── OTHER STEPS ───────────────────────────────────────────────────────────────




@then('I should see error message "{expected_error}"')
def verify_error_message(context, expected_error):
    try:
        context.wait.until(EC.presence_of_element_located((
            By.XPATH, "//*[contains(text(),'" + expected_error + "')]"
        )))
        print("Error message found: " + expected_error)
    except:
        raise Exception("Error message not found: " + expected_error)

@when('I enter invalid username "{username}"')
def enter_invalid_username(context, username):
    el = find_fast(context, [
        aid("inp_email"),
        (By.XPATH, "//input[@placeholder='you@company.com']"),
        (By.ID, "mat-input-0"),
        (By.XPATH, "//input[contains(@class,'mat-input-element')]"),
    ])
    if el:
        el.clear()
        el.send_keys(username)
        print("Entered invalid username: " + username)
        return
    raise Exception("Username field not found!")

@when('I enter invalid password "{password}"')
def enter_invalid_password(context, password):
    el = find_fast(context, [
        aid("inp_password"),
        (By.XPATH, "//input[@type='password']"),
    ])
    if el:
        el.clear()
        el.send_keys(password)
        print("Entered invalid password")
        return
    raise Exception("Password field not found!")








