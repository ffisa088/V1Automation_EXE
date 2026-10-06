
import os
import sys
import subprocess
import json
import glob
import re
from datetime import datetime

# Ensure Windows terminal handles UTF-8 box characters and emojis
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init(autoreset=True)
    HAS_COLOR = True
except Exception:
    HAS_COLOR = False

def _c(text, color_name="WHITE", bold=False):
    if not HAS_COLOR:
        return text
    col = getattr(Fore, color_name.upper(), "")
    bld = Style.BRIGHT if bold else ""
    return f"{bld}{col}{text}{Style.RESET_ALL}"

# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════

def get_base_path():
    """Always return the folder where this script lives."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(*parts):
    """Resolve bundled resources, falling back to the executable folder."""
    candidates = [BASE_PATH]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, sys._MEIPASS)
    for root in candidates:
        path = os.path.join(root, *parts)
        if os.path.exists(path):
            return path
    return os.path.join(BASE_PATH, *parts)

BASE_PATH     = get_base_path()
FEATURES_PATH = get_resource_path("features")
LOGIN_FEATURE = os.path.join(FEATURES_PATH, "login.feature")
REPORTS_DIR   = os.path.join(BASE_PATH, "reports")
REPORT_SCRIPT = get_resource_path("generate_report.py")

os.makedirs(REPORTS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# PYTHON FINDER
# ═══════════════════════════════════════════════════════════════════════

def find_python():
    """Locate Python executable — checks local project venv first, then system."""
    candidates = []
    venv_py = os.path.join(BASE_PATH, "venv", "Scripts", "python.exe")
    if os.path.isfile(venv_py):
        candidates.append(venv_py)
    if not getattr(sys, "frozen", False) and sys.executable:
        candidates.append(sys.executable)

    try:
        r = subprocess.run(["py", "-3", "-c", "import sys; print(sys.executable)"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            candidates.append(r.stdout.strip())
    except Exception:
        pass

    username = os.environ.get("USERNAME", "")
    for v in ["315", "314", "313", "312", "311", "310"]:
        if username:
            candidates.append(rf"C:\Users\{username}\AppData\Local\Programs\Python\Python{v}\python.exe")
        candidates.append(rf"C:\Program Files\Python{v}\python.exe")
        candidates.append(rf"C:\Program Files (x86)\Python{v}\python.exe")
        candidates.append(rf"C:\Python{v}\python.exe")

    for v in ["3.15", "3.14", "3.13", "3.12", "3.11", "3.10"]:
        if username:
            candidates.append(rf"C:\Users\{username}\AppData\Local\Python\pythoncore-{v}-64\python.exe")

    candidates.extend(["python", "python3"])

    for c in candidates:
        if not c:
            continue
        try:
            r = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    return None

PYTHON = find_python()

# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def divider(char="=", width=60):
    print(char * width)

def header(title):
    divider()
    print("  " + title)
    divider()

def get_report_meta(feature_path):
    """
    Given an absolute feature path, return:
      label   → human-readable "Forms / user_management"
      sub_dir → absolute path to report subfolder
      name    → bare file name without extension
    """
    rel   = os.path.relpath(feature_path, FEATURES_PATH)
    parts = rel.replace("\\", "/").split("/")
    name  = os.path.splitext(parts[-1])[0]

    if len(parts) > 1:
        folder_parts = parts[:-1]
        label   = " / ".join(folder_parts) + " / " + name
        sub_dir = os.path.join(REPORTS_DIR, *folder_parts)
    else:
        label   = name
        sub_dir = REPORTS_DIR

    os.makedirs(sub_dir, exist_ok=True)
    return label, sub_dir, name

def scan_all_features():
    """Return sorted list of all .feature files except login.feature."""
    found = []
    for root, dirs, files in os.walk(FEATURES_PATH):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".feature") and f.lower() != "login.feature":
                found.append(os.path.join(root, f))
    return found

def format_dur(sec):
    try:
        s = float(sec or 0)
    except Exception:
        s = 0.0
    if s < 1.0:
        return f"{round(s * 1000)}ms"
    elif s < 60.0:
        return f"{s:.2f}s"
    else:
        return f"{int(s // 60)}m {s % 60:.1f}s"

def print_gui_terminal_monitor(json_path, html_path, label, exit_code):
    """
    Renders a live GUI-styled terminal format in console showing:
    - Banner
    - Scenario Pass/Fail Monitor Matrix Table
    - Diagnostics for failed scenarios
    - KPI execution summary box
    """
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    scenarios = []
    total_steps = 0
    passed_steps = 0
    failed_steps = 0
    skipped_steps = 0
    total_duration = 0.0

    for feat in data:
        for el in feat.get("elements", []):
            if el.get("type") == "background":
                continue
            sc_name = el.get("name", "Unknown Scenario")
            sc_status = "passed"
            sc_dur = 0.0
            sc_passed = 0
            sc_failed = 0
            sc_skipped = 0
            failed_step_info = None

            for st in el.get("steps", []):
                res = st.get("result", {})
                st_stat = res.get("status", "skipped").lower()
                dur = float(res.get("duration", 0))
                sc_dur += dur
                total_steps += 1

                if st_stat == "passed":
                    passed_steps += 1
                    sc_passed += 1
                elif st_stat in ("failed", "error", "undefined"):
                    failed_steps += 1
                    sc_failed += 1
                    sc_status = "failed"
                    if not failed_step_info:
                        err = res.get("error_message", "")
                        if isinstance(err, list):
                            err = "\n".join(str(x) for x in err)
                        failed_step_info = {
                            "kw": st.get("keyword", "").strip(),
                            "name": st.get("name", "").strip(),
                            "error": str(err).split("\n")[0][:80]
                        }
                else:
                    skipped_steps += 1
                    sc_skipped += 1
                    if sc_status != "failed":
                        sc_status = "skipped"

            total_duration += sc_dur
            scenarios.append({
                "name": sc_name,
                "status": sc_status,
                "passed": sc_passed,
                "total": len(el.get("steps", [])),
                "dur": sc_dur,
                "failure": failed_step_info,
            })

    total_sc = len(scenarios)
    passed_sc = sum(1 for s in scenarios if s["status"] == "passed")
    failed_sc = sum(1 for s in scenarios if s["status"] == "failed")
    skipped_sc = sum(1 for s in scenarios if s["status"] == "skipped")
    rate = round((passed_sc / total_sc * 100) if total_sc > 0 else 0)
    fail_rate = round((failed_sc / total_sc * 100) if total_sc > 0 else 0)
    skip_rate = round((skipped_sc / total_sc * 100) if total_sc > 0 else 0)

    # 1. Top GUI Banner
    print("\n" + _c("╔══════════════════════════════════════════════════════════════════════════════════════════╗", "CYAN", True))
    title_str = f"AcSys ERP BDD RUNNER — SCENARIO MONITOR : {label}"[:88]
    print(_c(f"║ {title_str:<88} ║", "CYAN", True))
    print(_c("╠════╤══════════════════════════════════════════════════╤════════════╤═════════════╤═════════════╣", "CYAN", True))
    print(_c("║ #  │ SCENARIO NAME                                    │ STATUS     │ STEPS       │ TIME        ║", "CYAN", True))
    print(_c("╠════╪══════════════════════════════════════════════════╪════════════╪═════════════╪═════════════╣", "CYAN", True))

    for idx, sc in enumerate(scenarios, 1):
        name_disp = (sc["name"][:46] + "...") if len(sc["name"]) > 48 else sc["name"]
        st = sc["status"]
        if st == "passed":
            st_badge = _c("[ PASSED ] ", "GREEN", True)
        elif st == "failed":
            st_badge = _c("[ FAILED ] ", "RED", True)
        else:
            st_badge = _c("[ SKIPPED ]", "YELLOW", True)

        steps_disp = f"{sc['passed']}/{sc['total']} pass"
        time_disp = format_dur(sc["dur"])
        print(f"║ {idx:<2} │ {name_disp:<48} │ {st_badge} │ {steps_disp:<11} │ {time_disp:<11} ║")

    print(_c("╚════╧══════════════════════════════════════════════════╧════════════╧═════════════╧═════════════╝", "CYAN", True))

    # 2. Diagnostics if any failures
    failures = [s for s in scenarios if s["status"] == "failed" and s.get("failure")]
    if failures:
        print("\n" + _c("┌─ FAILURES & DIAGNOSTICS ─────────────────────────────────────────────────────────────────┐", "RED", True))
        for f_item in failures:
            info = f_item["failure"]
            print(_c(f"│ ✗ SCENARIO: {f_item['name']}", "RED", True))
            print(f"│   Step  : {info['kw']} {info['name']}")
            print(f"│   Error : {info['error']}")
        print(_c("└──────────────────────────────────────────────────────────────────────────────────────────┘", "RED", True))

    # 3. Execution KPI Dashboard Box
    bar_len = 28
    filled = int(round(rate / 100 * bar_len)) if total_sc > 0 else 0
    pbar = _c("█" * filled, "GREEN" if rate == 100 else ("YELLOW" if rate >= 50 else "RED"), True) + _c("░" * (bar_len - filled), "WHITE")
    rel_html = os.path.relpath(html_path, BASE_PATH) if html_path else "None"

    print("\n" + _c("╔══════════════════════════════════════════════════════════════════════════════════════════╗", "MAGENTA", True))
    print(_c("║                                  EXECUTION KPI DASHBOARD                                 ║", "MAGENTA", True))
    print(_c("╠══════════════════════════════════════════════════════════════════════════════════════════╣", "MAGENTA", True))
    print(f"║  Scenarios : Total: {total_sc:<3} | Passed: {_c(str(passed_sc), 'GREEN', True):<12} | Failed: {_c(str(failed_sc), 'RED', True):<12} | Skipped: {skipped_sc:<3}              ║")
    print(f"║  Rates     : Pass: {_c(str(rate)+'%', 'GREEN', True):<12} | Fail: {_c(str(fail_rate)+'%', 'RED', True):<12} | Skip: {_c(str(skip_rate)+'%', 'YELLOW', True):<12}         ║")
    print(f"║  Progress  : [{pbar}] {_c(str(rate)+'%', 'GREEN' if rate==100 else ('YELLOW' if rate>=50 else 'RED'), True):<18}                                     ║")
    print(f"║  Steps     : Total: {total_steps:<3} | Passed: {passed_steps:<3} | Failed: {failed_steps:<3} | Skipped: {skipped_steps:<3}                          ║")
    print(f"║  Duration  : {format_dur(total_duration):<86} ║")
    print(f"║  HTML Rep  : {rel_html:<86} ║")
    print(_c("╚══════════════════════════════════════════════════════════════════════════════════════════╝", "MAGENTA", True) + "\n")

# ═══════════════════════════════════════════════════════════════════════
# CORE: RUN ONE FEATURE + GENERATE REPORT
# ═══════════════════════════════════════════════════════════════════════

def run_feature(feature_path, extra_args=None):
    """
    Runs login.feature + feature_path in one Behave command
    (shared browser session).
    Captures JSON, converts to HTML report.
    Returns (exit_code, html_path | None)
    """
    if not PYTHON:
        print("[ERROR] Python not found — cannot run tests!")
        return 1, None

    if not os.path.exists(LOGIN_FEATURE):
        print("[ERROR] login.feature not found: " + LOGIN_FEATURE)
        return 1, None

    if not os.path.exists(feature_path):
        print("[ERROR] Feature not found: " + feature_path)
        return 1, None

    label, sub_dir, name = get_report_meta(feature_path)
    stamp    = timestamp()
    json_out = os.path.join(sub_dir, name + "_" + stamp + ".json")
    html_out = os.path.join(sub_dir, name + "_" + stamp + ".html")

    # Build behave command
    cmd = [
        PYTHON, "-m", "behave",
        "--no-capture",
        "--no-capture-stderr",
        "--no-skipped",
        "--format", "json",
        "--outfile", json_out,
        LOGIN_FEATURE,
        feature_path,
    ]
    if extra_args:
        cmd += extra_args

    print("")
    divider("-", 60)
    print("  Feature : " + label)
    print("  JSON    : " + os.path.relpath(json_out, BASE_PATH))
    print("  HTML    : " + os.path.relpath(html_out, BASE_PATH))
    divider("-", 60)

    result = subprocess.run(cmd, cwd=BASE_PATH)
    exit_code = result.returncode

    # Generate HTML report from JSON
    html_path = None
    if os.path.exists(json_out):
        if os.path.exists(REPORT_SCRIPT):
            report_result = subprocess.run(
                [PYTHON, REPORT_SCRIPT, json_out, html_out, label],
                cwd=BASE_PATH,
                capture_output=True,
                text=True,
            )
            if report_result.returncode != 0:
                print("[REPORT] Generation failed: " +
                      (report_result.stderr.strip() or "unknown error"))
        else:
            print("[REPORT] WARNING: Generator not found: " + REPORT_SCRIPT)
        if os.path.exists(html_out):
            html_path = html_out
            print("[REPORT] Saved: " + os.path.relpath(html_out, BASE_PATH))
        else:
            print("[REPORT] WARNING: HTML not generated for " + label)
        
        # Print GUI Terminal Monitor & Live Matrix
        print_gui_terminal_monitor(json_out, html_path, label, exit_code)
    else:
        print("[REPORT] WARNING: No JSON output — report skipped for " + label)

    status = "PASSED" if exit_code == 0 else "FAILED"
    print("[RESULT] " + status + " — " + label)

    return exit_code, html_path

# ═══════════════════════════════════════════════════════════════════════
# MODES
# ═══════════════════════════════════════════════════════════════════════

def mode_run_all():
    """Run every feature file — each gets its own report."""
    os.system("cls")
    header("BEHAVE TEST RUNNER  |  Run ALL Features")
    print("  Base    : " + BASE_PATH)
    print("  Python  : " + str(PYTHON))
    divider()

    features = scan_all_features()
    if not features:
        print("\n[ERROR] No feature files found in features\\")
        input("\nPress ENTER to exit...")
        return 1

    print("\nFound " + str(len(features)) + " feature file(s):\n")
    for i, f in enumerate(features, 1):
        rel = os.path.relpath(f, FEATURES_PATH)
        print("  [" + str(i) + "] " + rel)
    print("")

    all_reports    = []
    overall_passed = True

    for fpath in features:
        code, html = run_feature(fpath)
        if html:
            lbl, _, _ = get_report_meta(fpath)
            all_reports.append((lbl, html))
        if code != 0:
            overall_passed = False

    _print_summary(all_reports, overall_passed)
    return 0 if overall_passed else 1


def mode_run_feature(rel_or_abs_path):
    """Run a single feature file."""
    # resolve path
    if os.path.isabs(rel_or_abs_path):
        fpath = rel_or_abs_path
    else:
        fpath = os.path.join(BASE_PATH, rel_or_abs_path)

    os.system("cls")
    header("BEHAVE TEST RUNNER  |  Single Feature")
    print("  Base    : " + BASE_PATH)
    print("  Python  : " + str(PYTHON))
    print("  Feature : " + rel_or_abs_path)
    divider()

    code, html = run_feature(fpath)
    all_reports = []
    if html:
        lbl, _, _ = get_report_meta(fpath)
        all_reports.append((lbl, html))

    _print_summary(all_reports, code == 0)
    return 0 if code == 0 else 1


def mode_run_tag(tag):
    """Run all feature files filtered by a Behave tag."""
    os.system("cls")
    header("BEHAVE TEST RUNNER  |  Tag: " + tag)
    print("  Base    : " + BASE_PATH)
    print("  Python  : " + str(PYTHON))
    divider()

    features = scan_all_features()
    if not features:
        print("\n[ERROR] No feature files found!")
        input("\nPress ENTER to exit...")
        return 1

    all_reports    = []
    overall_passed = True

    for fpath in features:
        code, html = run_feature(
            fpath,
            extra_args=["--tags", "@always_login or " + tag],
        )
        if html:
            lbl, _, _ = get_report_meta(fpath)
            all_reports.append((lbl, html))
        if code != 0:
            overall_passed = False

    _print_summary(all_reports, overall_passed)
    return 0 if overall_passed else 1


def mode_interactive():
    """Interactive menu when no CLI args given."""
    os.system("cls")
    header("BEHAVE TEST RUNNER")
    print("  Base    : " + BASE_PATH)
    print("  Python  : " + str(PYTHON))
    divider()

    if not PYTHON:
        print("\n[ERROR] Python not found!")
        input("\nPress ENTER to exit...")
        sys.exit(1)

    features = scan_all_features()
    if not features:
        print("\n[ERROR] No feature files found in features\\")
        input("\nPress ENTER to exit...")
        sys.exit(1)

    print("\n  Login runs automatically first!\n")
    print("  Select feature to run after login:\n")

    last_folder = None
    for i, f in enumerate(features, 1):
        rel    = os.path.relpath(f, FEATURES_PATH)
        parts  = rel.replace("\\", "/").split("/")
        folder = "/".join(parts[:-1]) if len(parts) > 1 else "root"
        fname  = os.path.splitext(parts[-1])[0]
        if folder != last_folder:
            print("  [" + folder.upper() + "]")
            last_folder = folder
        print("    [" + str(i) + "] " + fname)

    print()
    print("  [0] Run ALL features")
    divider()

    try:
        choice = int(input("\n  Enter number: "))
    except Exception:
        print("  Invalid input!")
        input("  Press ENTER to exit...")
        sys.exit(1)

    all_reports    = []
    overall_passed = True

    if choice == 0:
        for fpath in features:
            code, html = run_feature(fpath)
            if html:
                lbl, _, _ = get_report_meta(fpath)
                all_reports.append((lbl, html))
            if code != 0:
                overall_passed = False

    elif 1 <= choice <= len(features):
        fpath = features[choice - 1]
        code, html = run_feature(fpath)
        if html:
            lbl, _, _ = get_report_meta(fpath)
            all_reports.append((lbl, html))
        if code != 0:
            overall_passed = False
    else:
        print("  Invalid choice!")
        input("  Press ENTER to exit...")
        sys.exit(1)

    _print_summary(all_reports, overall_passed)
    sys.exit(0 if overall_passed else 1)

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY PRINTER
# ═══════════════════════════════════════════════════════════════════════

def _print_summary(all_reports, overall_passed):
    print("")
    divider()
    if overall_passed:
        print("  ALL TESTS PASSED!")
    else:
        print("  SOME TESTS FAILED!")
        print("  Screenshots: " + os.path.join(BASE_PATH, "screenshots"))
    divider()

    if all_reports:
        print("\n  Generated " + str(len(all_reports)) + " report(s):\n")
        for i, (lbl, path) in enumerate(all_reports, 1):
            print("  " + str(i) + ". " + lbl)
            print("     " + path)
        print("")

        ans = input("  Open reports? [A]ll / [1-" +
                    str(len(all_reports)) + "] specific / [N]o: ").strip().upper()
        if ans == "A":
            for _, path in all_reports:
                try:
                    os.startfile(path)
                except Exception:
                    pass
        elif ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(all_reports):
                try:
                    os.startfile(all_reports[idx][1])
                except Exception:
                    pass

    print("\n  Reports folder: " + REPORTS_DIR)
    input("\n  Press ENTER to close...")

# ═══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mode_interactive()

    elif "--run-all" in args:
        sys.exit(mode_run_all())

    elif "--feature" in args:
        idx = args.index("--feature")
        if idx + 1 >= len(args):
            print("[ERROR] --feature requires a path argument")
            sys.exit(1)
        sys.exit(mode_run_feature(args[idx + 1]))

    elif "--tag" in args:
        idx = args.index("--tag")
        if idx + 1 >= len(args):
            print("[ERROR] --tag requires a tag argument (e.g. @smoke)")
            sys.exit(1)
        sys.exit(mode_run_tag(args[idx + 1]))

    else:
        print("[ERROR] Unknown arguments: " + str(args))
        print("Usage:")
        print("  python BehaveTestRunner.py")
        print("  python BehaveTestRunner.py --run-all")
        print("  python BehaveTestRunner.py --feature features\\Forms\\user.feature")
        print("  python BehaveTestRunner.py --tag @smoke")
        sys.exit(1)
