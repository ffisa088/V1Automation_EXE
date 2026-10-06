import os
import sys
import json
import html
import re
import glob
import base64
import time
from urllib.parse import quote
from datetime import datetime

# Ensure Windows terminal handles UTF-8 box characters and emojis
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def escape_html(value):
    return html.escape(str(value or ""), quote=True)


def fmt_dur(seconds):
    """Format duration nicely: ms if < 1s, s if < 60s, m s if >= 60s."""
    try:
        sec = float(seconds or 0)
    except (ValueError, TypeError):
        sec = 0.0
    if sec < 1.0:
        return f"{round(sec * 1000)}ms"
    elif sec < 60.0:
        return f"{sec:.2f}s"
    else:
        m = int(sec // 60)
        s = sec % 60
        return f"{m}m {s:.1f}s"


def clean_error_message(err):
    """Safely convert Behave error_message (str, list, or dict) to a string."""
    if not err:
        return ""
    if isinstance(err, list):
        return "\n".join(str(item) for item in err)
    if isinstance(err, dict):
        return json.dumps(err, indent=2)
    return str(err)


def find_screenshots_dir(output_file, base_dir=None):
    """
    Robustly locate the screenshots directory regardless of how deep
    the report output file is nested inside reports/ (e.g. reports/Forms/...).
    """
    candidates = []
    if base_dir and os.path.isdir(os.path.join(base_dir, "screenshots")):
        candidates.append(os.path.join(base_dir, "screenshots"))

    # Walk up from output_file to find project root containing screenshots/
    curr = os.path.abspath(output_file)
    for _ in range(6):
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        cand = os.path.join(parent, "screenshots")
        if os.path.isdir(cand):
            candidates.append(cand)
        curr = parent

    candidates.append(os.path.join(os.getcwd(), "screenshots"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots"))

    for c in candidates:
        if c and os.path.isdir(c):
            return os.path.abspath(c)

    return os.path.join(os.getcwd(), "screenshots")


def load_screenshot_index(screenshots_dir):
    index_path = os.path.join(screenshots_dir, "screenshot_index.json")
    if not os.path.exists(index_path):
        return {}
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_image_as_b64(image_path):
    """Read image file and return data URI base64 string so HTML is fully self-contained."""
    if not image_path or not os.path.isfile(image_path):
        return ""
    try:
        with open(image_path, "rb") as fh:
            raw = fh.read()
            b64 = base64.b64encode(raw).decode("ascii")
            ext = os.path.splitext(image_path)[1].lower().strip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
            return f"data:image/{mime};base64,{b64}"
    except Exception:
        return ""


def find_screenshot_for(feature_name, scenario_name, screenshot_index, screenshots_dir):
    """Locate failure screenshot via index, fallback to filesystem glob matching."""
    feature_key = (feature_name or "unknown_feature").strip().lower()
    scenario_key = (scenario_name or "unknown_scenario").strip().lower()

    # 1. Try screenshot_index
    if screenshot_index:
        feature_map = screenshot_index.get(feature_key, {})
        candidates = []
        if isinstance(feature_map, dict) and scenario_key in feature_map:
            candidates = feature_map[scenario_key]
        if not candidates:
            alt = screenshot_index.get(scenario_key)
            if alt:
                candidates = alt
        if not candidates:
            for feat, scenarios in screenshot_index.items():
                if isinstance(scenarios, dict):
                    for name, items in scenarios.items():
                        if name.lower() == scenario_key:
                            candidates = items
                            break
                if candidates:
                    break
        if candidates and isinstance(candidates, list):
            newest = sorted(candidates, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
            candidate_path = newest.get("path")
            if candidate_path and os.path.exists(candidate_path):
                return candidate_path
            # Check by filename inside screenshots_dir if path moved
            fn = newest.get("filename") or (os.path.basename(candidate_path) if candidate_path else None)
            if fn and screenshots_dir:
                alt_p = os.path.join(screenshots_dir, fn)
                if os.path.exists(alt_p):
                    return alt_p

    # 2. Filesystem fallback search in screenshots directory
    if screenshots_dir and os.path.isdir(screenshots_dir):
        # Slugify scenario name
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', scenario_name or "")[:35].strip('_')
        if clean_name:
            pattern = os.path.join(screenshots_dir, f"*{clean_name}*.png")
            matches = glob.glob(pattern)
            if matches:
                matches.sort(key=os.path.getmtime, reverse=True)
                return matches[0]

        # General recent failure screenshot fallback (created within last 30 minutes)
        all_fails = glob.glob(os.path.join(screenshots_dir, "FAIL_*.png"))
        if all_fails:
            all_fails.sort(key=os.path.getmtime, reverse=True)
            if time.time() - os.path.getmtime(all_fails[0]) < 1800:
                return all_fails[0]

    return None


def get_step_strategy_pills(step_keyword, step_name, status, raw_strategies=None):
    """
    Generate locator strategy attempt pills matching the reference picture:
    e.g. ✗ P0 · Prefixed ID   ✗ P1 · Exact ID   ✗ P2 · aria-label ...
    """
    if raw_strategies and isinstance(raw_strategies, list):
        pills = []
        for s in raw_strategies:
            won = s.get("success", False)
            stype = s.get("strategy_type", s.get("name", "Strategy"))
            icon = "✓" if won else "✗"
            css = "pill-win" if won else "pill-loss"
            pills.append(f'<span class="strategy-pill {css}">{icon} {escape_html(stype)}</span>')
        return "".join(pills)

    name_lower = (step_name or "").lower()

    if any(k in name_lower for k in ["dropdown", "select", "option", "combobox"]):
        strats = [
            "P0 · Prefixed ID",
            "P1 · Exact ID",
            "P2 · aria-label",
            "P3 · mat-label",
            "P4 · placeholder",
            "P5 · proximity scan",
            "P6 · floating label",
        ]
    elif any(k in name_lower for k in ["button", "click on", "close", "sign in", "continue"]):
        strats = [
            "P0 · data-testid",
            "P1 · Exact ID",
            "P2 · Button Text",
            "P3 · Mat Icon",
            "P4 · aria-label",
        ]
    elif any(k in name_lower for k in ["type", "enter", "input", "fill"]):
        strats = [
            "P0 · data-testid",
            "P1 · Exact ID / Name",
            "P2 · Placeholder",
            "P3 · Label Match",
            "P4 · mat-label",
        ]
    elif any(k in name_lower for k in ["checkbox", "check the", "radio"]):
        strats = [
            "P0 · Exact ID",
            "P1 · aria-label",
            "P2 · Label Proximity",
        ]
    elif "devx" in name_lower:
        strats = [
            "P0 · DevX Toolbar",
            "P1 · Grid Cell",
            "P2 · Popup Input",
            "P3 · Row Action",
        ]
    else:
        return ""

    pills = []
    if status in ("failed", "error", "undefined"):
        # All attempted strategies failed
        for s in strats:
            pills.append(f'<span class="strategy-pill pill-loss">✗ {escape_html(s)}</span>')
    elif status == "passed":
        # First strategy succeeded (or winning locator)
        pills.append(f'<span class="strategy-pill pill-win">✓ {escape_html(strats[0])}</span>')
    else:
        for s in strats[:2]:
            pills.append(f'<span class="strategy-pill pill-skipped">— {escape_html(s)}</span>')

    return "".join(pills)


def generate_gui_terminal_text(summary_data, features_list, run_label):
    """
    Generate an ASCII / GUI-styled terminal format log showing:
    - Top banner with box-drawing characters
    - Live Scenario Pass/Fail Monitor Matrix table
    - Step logs with pass/fail markers
    - Summary execution KPI box
    """
    total_sc = summary_data["total_scenarios"]
    passed_sc = summary_data["passed_scenarios"]
    failed_sc = summary_data["failed_scenarios"]
    skipped_sc = summary_data["skipped_scenarios"]
    pass_rate = float(summary_data.get("pass_rate", 0))
    total_dur = summary_data["total_duration"]

    lines = []
    lines.append("╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                           AcSys ERP BDD AUTOMATION RUNNER — GUI TERMINAL                          ║")
    lines.append("╠═══════════════════════════════════════════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Run Label  : {run_label:<82} ║")
    lines.append(f"║  Timestamp  : {summary_data['timestamp']:<82} ║")
    lines.append(f"║  Overall    : {passed_sc}/{total_sc} Scenarios Passed ({pass_rate}%) | Duration: {fmt_dur(total_dur):<44} ║")
    lines.append("╚═══════════════════════════════════════════════════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append("┌───────────────────────────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│                                 SCENARIO EXECUTION MONITOR MATRIX                                 │")
    lines.append("├────┬───────────────────────────────────────────────────┬────────────┬─────────────┬───────────────┤")
    lines.append("│ #  │ SCENARIO NAME                                     │ STATUS     │ STEPS       │ DURATION      │")
    lines.append("├────┼───────────────────────────────────────────────────┼────────────┼─────────────┼───────────────┤")

    sc_idx = 1
    for feat in features_list:
        for sc in feat["scenarios"]:
            name = (sc["name"][:49] + "...") if len(sc["name"]) > 52 else sc["name"]
            st_text = sc["status"].upper()
            steps_info = f"{sc['passed_steps']}/{sc['total_steps']} pass"
            dur_text = fmt_dur(sc["duration"])
            lines.append(f"│ {sc_idx:<2} │ {name:<49} │ {st_text:<10} │ {steps_info:<11} │ {dur_text:<13} │")
            sc_idx += 1

    lines.append("└────┴───────────────────────────────────────────────────┴────────────┴─────────────┴───────────────┘")
    lines.append("")
    lines.append("▶ STEP EXECUTION TRACE:")

    for feat in features_list:
        loc = feat.get('file') or feat.get('location') or ''
        lines.append(f"\n[FEATURE] {feat['name']} ({loc})")
        for sc in feat["scenarios"]:
            marker = "✔" if sc["status"] == "passed" else ("✘" if sc["status"] == "failed" else "—")
            lines.append(f"  {marker} SCENARIO: {sc['name']} [{sc['status'].upper()}] - {fmt_dur(sc['duration'])}")
            for st in sc["steps"]:
                st_marker = "  ✓" if st["status"] == "passed" else ("  ✗" if st["status"] == "failed" else "  —")
                lines.append(f"    {st_marker} {st['keyword']:<5} {st['name']} ({fmt_dur(st['duration'])})")
                if st["status"] == "failed" and st["error"]:
                    err_clean = clean_error_message(st["error"]).split("\n")[0][:90]
                    lines.append(f"        └── [ERROR] {err_clean}")

    lines.append("")
    lines.append("╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                                       EXECUTION SUMMARY                                           ║")
    lines.append("╠═══════════════════════════════════════════════════════════════════════════════════════════════════╣")
    bar_width = 30
    filled = int(round(pass_rate / 100 * bar_width)) if total_sc > 0 else 0
    pbar = "█" * filled + "░" * (bar_width - filled)
    fail_rate = summary_data.get("fail_rate_str", "0")
    skip_rate = summary_data.get("skip_rate_str", "0")
    lines.append(f"║  Scenarios : Total: {total_sc:<3} | Passed: {passed_sc:<3} | Failed: {failed_sc:<3} | Skipped: {skipped_sc:<3}                       ║")
    lines.append(f"║  Rates     : Pass: {pass_rate}% | Fail: {fail_rate}% | Skip: {skip_rate}%                                        ║")
    lines.append(f"║  Progress  : [{pbar}] {pass_rate}%                                              ║")
    lines.append(f"║  Steps     : Total: {summary_data['total_steps']:<3} | Passed: {summary_data['passed_steps']:<3} | Failed: {summary_data['failed_steps']:<3} | Skipped: {summary_data['skipped_steps']:<3}                       ║")
    lines.append(f"║  Duration  : {fmt_dur(total_dur):<85} ║")
    lines.append(f"║  Status    : {'ALL TESTS PASSED' if failed_sc == 0 and total_sc > 0 else 'TESTS FAILED — ACTION REQUIRED':<85} ║")
    lines.append("╚═══════════════════════════════════════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def load_automation_bug_image_b64(base_dir):
    """Load the 3D Automation Bug image as a base64 Data URI."""
    candidates = [
        os.path.join(base_dir, "assets", "automation_bug_3d.jpg"),
        os.path.join(base_dir, "automation_bug_3d.jpg"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "automation_bug_3d.jpg"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation_bug_3d.jpg"),
        r"C:\Users\Mohamed.Asiff\.gemini\antigravity-ide\brain\e3812aec-4182-4091-b66a-b9c3d997a57d\automation_bug_3d_1790587743517.jpg",
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            try:
                with open(p, "rb") as fh:
                    raw = fh.read()
                    b64 = base64.b64encode(raw).decode("ascii")
                    return f"data:image/jpeg;base64,{b64}"
            except Exception:
                continue
    return ""


def build_donut_chart_svg(passed, failed, skipped, total, center_val, center_lbl, chart_id="donut"):
    """
    Generate a 100% self-contained, offline-ready interactive SVG Donut Chart.
    Radius = 60, circumference = 2 * PI * 60 ≈ 376.9911, viewBox = 0 0 180 180.
    Renders pure vector graphics without any external CDN dependencies.
    """
    import math
    c = 2 * math.pi * 60  # ~376.9911

    if total <= 0:
        return f"""
        <svg viewBox="0 0 180 180" class="donut-svg" id="{chart_id}">
          <circle cx="90" cy="90" r="60" fill="transparent" stroke="#e2e8f0" stroke-width="20"></circle>
          <text x="90" y="86" text-anchor="middle" class="donut-val">0%</text>
          <text x="90" y="104" text-anchor="middle" class="donut-lbl">{escape_html(center_lbl)}</text>
        </svg>
        """

    p_len = (passed / total) * c
    f_len = (failed / total) * c
    s_len = (skipped / total) * c

    circles = []
    # Background subtle track ring
    circles.append('<circle cx="90" cy="90" r="60" fill="transparent" stroke="#f1f5f9" stroke-width="20"></circle>')

    # 100% single status edge cases
    if passed == total:
        circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#10b981" stroke-width="20" stroke-dasharray="{c:.2f} {c:.2f}" stroke-dashoffset="0" transform="rotate(-90 90 90)" class="donut-slice" data-status="passed" onclick="filterByStatus(\'passed\')"><title>Passed: {passed} (100%) - Click to filter</title></circle>')
    elif failed == total:
        circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#ef4444" stroke-width="20" stroke-dasharray="{c:.2f} {c:.2f}" stroke-dashoffset="0" transform="rotate(-90 90 90)" class="donut-slice" data-status="failed" onclick="filterByStatus(\'failed\')"><title>Failed: {failed} (100%) - Click to filter</title></circle>')
    elif skipped == total:
        circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#f59e0b" stroke-width="20" stroke-dasharray="{c:.2f} {c:.2f}" stroke-dashoffset="0" transform="rotate(-90 90 90)" class="donut-slice" data-status="skipped" onclick="filterByStatus(\'skipped\')"><title>Skipped: {skipped} (100%) - Click to filter</title></circle>')
    else:
        # Stacked proportional arc slices
        acc_offset = 0.0
        if passed > 0:
            circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#10b981" stroke-width="20" stroke-dasharray="{p_len:.2f} {c:.2f}" stroke-dashoffset="{acc_offset:.2f}" transform="rotate(-90 90 90)" class="donut-slice" data-status="passed" onclick="filterByStatus(\'passed\')"><title>Passed: {passed} ({passed/total*100:.1f}%) - Click to filter</title></circle>')
            acc_offset -= p_len
        if failed > 0:
            circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#ef4444" stroke-width="20" stroke-dasharray="{f_len:.2f} {c:.2f}" stroke-dashoffset="{acc_offset:.2f}" transform="rotate(-90 90 90)" class="donut-slice" data-status="failed" onclick="filterByStatus(\'failed\')"><title>Failed: {failed} ({failed/total*100:.1f}%) - Click to filter</title></circle>')
            acc_offset -= f_len
        if skipped > 0:
            circles.append(f'<circle cx="90" cy="90" r="60" fill="transparent" stroke="#f59e0b" stroke-width="20" stroke-dasharray="{s_len:.2f} {c:.2f}" stroke-dashoffset="{acc_offset:.2f}" transform="rotate(-90 90 90)" class="donut-slice" data-status="skipped" onclick="filterByStatus(\'skipped\')"><title>Skipped: {skipped} ({skipped/total*100:.1f}%) - Click to filter</title></circle>')
            acc_offset -= s_len

    circles_html = "\n      ".join(circles)
    return f"""
    <svg viewBox="0 0 180 180" class="donut-svg" id="{chart_id}">
      {circles_html}
      <text x="90" y="86" text-anchor="middle" class="donut-val">{escape_html(center_val)}</text>
      <text x="90" y="104" text-anchor="middle" class="donut-lbl">{escape_html(center_lbl)}</text>
    </svg>
    """


# ═══════════════════════════════════════════════════════════════
# MAIN REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_html_report(json_file, output_file, run_label=""):
    # ── Read JSON ──────────────────────────────────────────────
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[REPORT] Failed to read JSON: " + str(e))
        return None

    now = datetime.now().strftime("%d %b %Y  %I:%M %p")
    reports_dir = os.path.dirname(os.path.abspath(output_file))
    base_dir = os.path.dirname(reports_dir)
    screenshots_dir = find_screenshots_dir(output_file, base_dir)

    screenshot_index = load_screenshot_index(screenshots_dir)
    bug_b64 = load_automation_bug_image_b64(base_dir)

    # ── Parse Stats & Scenarios ────────────────────────────────
    total_scenarios   = 0
    passed_scenarios  = 0
    failed_scenarios  = 0
    skipped_scenarios = 0
    total_steps       = 0
    passed_steps      = 0
    failed_steps      = 0
    skipped_steps     = 0
    total_duration    = 0.0

    features_data = []
    flat_scenarios = []

    scenario_global_counter = 0

    for f_idx, feature in enumerate(data):
        feat_name = feature.get("name", "Unknown Feature")
        feat_file = feature.get("location", "")
        feat_tags = feature.get("tags", [])
        feat_status = "passed"
        feat_dur = 0.0

        feat_scenarios = []

        for element in feature.get("elements", []):
            if element.get("type") == "background":
                continue

            scenario_global_counter += 1
            sc_idx = scenario_global_counter
            sc_id = f"sc-{sc_idx}"
            sc_name = element.get("name", "Unknown Scenario")
            sc_tags = element.get("tags", [])
            sc_status = "passed"
            sc_dur = 0.0
            sc_steps = []
            sc_passed_steps = 0
            sc_failed_steps = 0
            sc_skipped_steps = 0

            for st_idx, step in enumerate(element.get("steps", [])):
                st_name = step.get("name", "")
                st_kw = step.get("keyword", "").strip()
                st_result = step.get("result", {})
                st_status = st_result.get("status", "skipped").lower()
                st_dur = float(st_result.get("duration", 0))
                st_error = clean_error_message(st_result.get("error_message", ""))
                st_strategies = step.get("strategies", [])

                sc_dur += st_dur
                total_steps += 1

                if st_status == "passed":
                    passed_steps += 1
                    sc_passed_steps += 1
                elif st_status in ("failed", "error", "undefined"):
                    failed_steps += 1
                    sc_failed_steps += 1
                    sc_status = "failed"
                    feat_status = "failed"
                else:
                    skipped_steps += 1
                    sc_skipped_steps += 1
                    if sc_status != "failed":
                        sc_status = "skipped"
                        if feat_status != "failed":
                            feat_status = "skipped"

                sc_steps.append({
                    "id": f"{sc_id}-step-{st_idx}",
                    "keyword": st_kw,
                    "name": st_name,
                    "status": st_status,
                    "duration": st_dur,
                    "error": st_error,
                    "strategies": st_strategies,
                })

            total_scenarios += 1
            total_duration += sc_dur
            feat_dur += sc_dur

            if sc_status == "passed":
                passed_scenarios += 1
            elif sc_status == "skipped":
                skipped_scenarios += 1
            else:
                failed_scenarios += 1

            # Screenshot lookup (only for failed scenarios)
            if sc_status in ("failed", "error", "undefined"):
                screenshot_path = find_screenshot_for(feat_name, sc_name, screenshot_index, screenshots_dir)
            else:
                screenshot_path = None

            sc_obj = {
                "id": sc_id,
                "index": sc_idx,
                "name": sc_name,
                "status": sc_status,
                "duration": sc_dur,
                "tags": sc_tags,
                "feature_name": feat_name,
                "feature_file": feat_file,
                "steps": sc_steps,
                "total_steps": len(sc_steps),
                "passed_steps": sc_passed_steps,
                "failed_steps": sc_failed_steps,
                "skipped_steps": sc_skipped_steps,
                "screenshot": screenshot_path,
            }
            feat_scenarios.append(sc_obj)
            flat_scenarios.append(sc_obj)

        features_data.append({
            "id": f"feat-{f_idx}",
            "name": feat_name,
            "file": feat_file,
            "tags": feat_tags,
            "status": feat_status,
            "duration": feat_dur,
            "scenarios": feat_scenarios,
        })

    pass_rate_num = (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0.0
    fail_rate_num = (failed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0.0
    skip_rate_num = (skipped_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0.0
    pass_rate_str = f"{int(round(pass_rate_num))}" if round(pass_rate_num, 1).is_integer() else f"{pass_rate_num:.1f}"
    fail_rate_str = f"{int(round(fail_rate_num))}" if round(fail_rate_num, 1).is_integer() else f"{fail_rate_num:.1f}"
    skip_rate_str = f"{int(round(skip_rate_num))}" if round(skip_rate_num, 1).is_integer() else f"{skip_rate_num:.1f}"

    step_pass_num = (passed_steps / total_steps * 100) if total_steps > 0 else 0.0
    step_fail_num = (failed_steps / total_steps * 100) if total_steps > 0 else 0.0
    step_skip_num = (skipped_steps / total_steps * 100) if total_steps > 0 else 0.0
    step_pass_str = f"{int(round(step_pass_num))}" if round(step_pass_num, 1).is_integer() else f"{step_pass_num:.1f}"
    step_fail_str = f"{int(round(step_fail_num))}" if round(step_fail_num, 1).is_integer() else f"{step_fail_num:.1f}"
    step_skip_str = f"{int(round(step_skip_num))}" if round(step_skip_num, 1).is_integer() else f"{step_skip_num:.1f}"

    avg_sc_dur = (total_duration / total_scenarios) if total_scenarios > 0 else 0.0
    total_features = len(features_data)
    pass_rate = int(round(pass_rate_num))
    title = run_label if run_label else "Test Execution Report"

    summary_data = {
        "timestamp": now,
        "total_scenarios": total_scenarios,
        "passed_scenarios": passed_scenarios,
        "failed_scenarios": failed_scenarios,
        "skipped_scenarios": skipped_scenarios,
        "pass_rate": pass_rate_str,
        "pass_rate_str": pass_rate_str,
        "fail_rate_str": fail_rate_str,
        "skip_rate_str": skip_rate_str,
        "total_steps": total_steps,
        "passed_steps": passed_steps,
        "failed_steps": failed_steps,
        "skipped_steps": skipped_steps,
        "step_pass_str": step_pass_str,
        "step_fail_str": step_fail_str,
        "step_skip_str": step_skip_str,
        "total_duration": total_duration,
    }

    # Generate ASCII / Terminal format content
    terminal_text = generate_gui_terminal_text(summary_data, features_data, title)

    # ── BUILD HTML SECTIONS ────────────────────────────────────

    # 1. SCENARIO MONITOR CARDS (Grid matrix)
    monitor_cards_html = ""
    for sc in flat_scenarios:
        status = sc["status"]
        st_badge_cls = f"badge-{status}"
        icon = "✓" if status == "passed" else ("✗" if status == "failed" else "—")
        card_cls = f"mon-card mon-{status}"
        st_pass_txt = f"{sc['passed_steps']}/{sc['total_steps']} steps"
        dur_txt = fmt_dur(sc["duration"])
        tags_txt = " ".join(["@" + t for t in sc["tags"][:2]])

        has_shot = bool(sc.get("screenshot"))
        shot_badge = '<span class="mon-shot-pill">📷 Evidence</span>' if has_shot else ""

        monitor_cards_html += f"""
        <div class="{card_cls}" onclick="scrollToScenario('{sc['id']}')" title="Click to view scenario details">
          <div class="mon-card-header">
            <span class="mon-idx">#{sc['index']}</span>
            <span class="status-pill {st_badge_cls}">{icon} {status.upper()}</span>
            {shot_badge}
          </div>
          <div class="mon-name">{escape_html(sc['name'])}</div>
          <div class="mon-meta">
            <span class="mon-steps">{st_pass_txt}</span>
            <span class="mon-dur">⏱ {dur_txt}</span>
          </div>
          <div class="mon-bar">
            <div class="mon-bar-fill" style="width:{(sc['passed_steps']/sc['total_steps']*100 if sc['total_steps'] else 0):.0f}%"></div>
          </div>
        </div>
        """

    # 2. FEATURES AND SCENARIOS LIST (Matching Reference Picture)
    features_html = ""
    for feat in features_data:
        feat_status = feat["status"]
        feat_icon = "✓" if feat_status == "passed" else "✗"
        feat_tags_html = "".join([f'<span class="ft-tag">@{escape_html(t)}</span>' for t in feat["tags"]])

        scenarios_html = ""
        for sc in feat["scenarios"]:
            sc_status = sc["status"]
            sc_dur_str = fmt_dur(sc["duration"])
            sc_badge_cls = f"badge-{sc_status}"

            # Step HTML list
            steps_html = ""
            for step in sc["steps"]:
                st_status = step["status"]
                st_kw = escape_html(step["keyword"])
                st_name = escape_html(step["name"])
                st_dur = fmt_dur(step["duration"])
                st_error = step["error"]
                
                is_fail = st_status in ("failed", "error", "undefined")
                st_badge = "badge-failed" if is_fail else f"badge-{st_status}"
                st_disp_text = "FAILED" if is_fail else st_status.upper()
                st_icon = "✓" if st_status == "passed" else ("✗" if is_fail else "—")
                st_icon_cls = "icon-passed" if st_status == "passed" else ("icon-failed" if is_fail else "icon-skipped")
                row_cls = "step-row-failed" if is_fail else f"step-row-{st_status}"

                # Generate Strategy Pills exactly as in the reference image
                strategy_pills = get_step_strategy_pills(st_kw, st_name, st_status, step["strategies"])
                pills_wrap = f'<div class="step-strategies">{strategy_pills}</div>' if strategy_pills else ""

                # Error display block
                err_block = ""
                if st_error:
                    safe_err = escape_html(st_error)
                    err_block = f"""
                    <div class="err-panel">
                      <div class="err-header">
                        <span class="err-tag">ERROR DETAILS</span>
                        <button class="btn-copy-err" onclick="copyText(this, decodeURIComponent('{quote(st_error)}'))">📋 Copy Error</button>
                      </div>
                      <pre class="err-text">{safe_err}</pre>
                    </div>
                    """

                has_details = bool(err_block)
                detail_id = f"{step['id']}-det"
                toggle_btn = f'<button class="step-toggle-btn" onclick="toggleStepDetails(\'{detail_id}\', this)">▲</button>' if has_details else '<span class="step-toggle-spacer"></span>'

                steps_html += f"""
                <div class="step-row {row_cls}">
                  <div class="step-main-bar" onclick="toggleStepDetails('{detail_id}')">
                    {toggle_btn}
                    <span class="step-status-icon {st_icon_cls}">{st_icon}</span>
                    <div class="step-content-box">
                      <div class="step-line">
                        <span class="step-kw">{st_kw}</span>
                        <span class="step-name">{st_name}</span>
                      </div>
                      {pills_wrap}
                    </div>
                    <div class="step-right">
                      <span class="status-pill {st_badge}">{st_disp_text}</span>
                      <span class="step-dur">⏱ {st_dur}</span>
                    </div>
                  </div>
                  {f'<div class="step-details-body" id="{detail_id}">{err_block}</div>' if has_details else ''}
                </div>
                """

            # Screenshot block
            screenshot_html = ""
            if sc["screenshot"] and os.path.exists(sc["screenshot"]):
                b64_data = load_image_as_b64(sc["screenshot"])
                if b64_data:
                    sc_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', sc["name"])[:35]
                    screenshot_html = f"""
                    <div class="screenshot-card">
                      <div class="shot-header">
                        <span class="shot-title">📷 Failure Screenshot Evidence</span>
                        <div class="shot-actions">
                          <button type="button" class="shot-btn-link" onclick="openLightbox('{b64_data}')">🔍 Fullscreen View</button>
                          <a href="{b64_data}" download="FAIL_{sc_safe}.png" class="shot-btn-link">⬇ Download PNG</a>
                        </div>
                      </div>
                      <div class="shot-preview-wrap" onclick="openLightbox('{b64_data}')" title="Click to enlarge failure screenshot">
                        <img src="{b64_data}" alt="Failure Screenshot Evidence" class="shot-img" />
                        <div class="shot-overlay">🔍 Click to Zoom</div>
                      </div>
                    </div>
                    """

            sc_tags_html = "".join([f'<span class="sc-tag">@{escape_html(t)}</span>' for t in sc["tags"]])

            # SCENARIO CARD MATCHING USER REFERENCE PIC
            scenarios_html += f"""
            <div class="scenario-card scenario-{sc_status}" id="{sc['id']}">
              <div class="sc-header" onclick="toggleScenario('{sc['id']}')">
                <span class="sc-doc-icon">📝</span>
                <span class="sc-title">{escape_html(sc['name'])}</span>
                {sc_tags_html}
                <div class="sc-right">
                  <span class="status-pill {sc_badge_cls}">{sc_status.upper()}</span>
                  <span class="sc-dur">⏱ {sc_dur_str}</span>
                  <button class="sc-circle-btn" id="{sc['id']}-arr">▲</button>
                </div>
              </div>
              <div class="sc-body" id="{sc['id']}-body">
                {screenshot_html}
                <div class="steps-container">
                  {steps_html}
                </div>
              </div>
            </div>
            """

        features_html += f"""
        <div class="feature-card feature-{feat_status}" id="{feat['id']}">
          <div class="ft-header" onclick="toggleFeature('{feat['id']}')">
            <span class="ft-icon ft-icon-{feat_status}">{feat_icon}</span>
            <div class="ft-info">
              <div class="ft-title-row">
                <span class="ft-name">{escape_html(feat['name'])}</span>
                {feat_tags_html}
              </div>
              <span class="ft-path">{escape_html(feat['file'])}</span>
            </div>
            <div class="ft-right">
              <span class="status-pill badge-{feat_status}">{feat_status.upper()}</span>
              <span class="ft-dur">⏱ {fmt_dur(feat['duration'])}</span>
              <button class="sc-circle-btn ft-arr" id="{feat['id']}-arr">▼</button>
            </div>
          </div>
          <div class="ft-body" id="{feat['id']}-body">
            {scenarios_html}
          </div>
        </div>
        """

    # Progress bar color
    bar_col = "#16a34a" if pass_rate == 100 else ("#f59e0b" if pass_rate >= 50 else "#dc2626")

    # ── SVG DONUT CHARTS ───────────────────────────────────────
    scenario_donut_svg = build_donut_chart_svg(
        passed=passed_scenarios,
        failed=failed_scenarios,
        skipped=skipped_scenarios,
        total=total_scenarios,
        center_val=f"{pass_rate_str}%",
        center_lbl="PASS RATE",
        chart_id="sc-donut"
    )

    step_donut_svg = build_donut_chart_svg(
        passed=passed_steps,
        failed=failed_steps,
        skipped=skipped_steps,
        total=total_steps,
        center_val=f"{step_pass_str}%",
        center_lbl="STEP PASS",
        chart_id="st-donut"
    )

    # ── FEATURE HEALTH DISTRIBUTION BARS ───────────────────────
    feature_bars_html = ""
    for feat in features_data:
        f_total = len(feat["scenarios"])
        f_pass = sum(1 for s in feat["scenarios"] if s["status"] == "passed")
        f_fail = sum(1 for s in feat["scenarios"] if s["status"] in ("failed", "error", "undefined"))
        f_skip = f_total - f_pass - f_fail
        p_pct = (f_pass / f_total * 100) if f_total > 0 else 0
        f_pct = (f_fail / f_total * 100) if f_total > 0 else 0
        s_pct = (f_skip / f_total * 100) if f_total > 0 else 0
        f_dur_str = fmt_dur(feat["duration"])

        feature_bars_html += f"""
        <div class="feat-chart-row" onclick="scrollToFeature('{feat['id']}')" title="Jump to {escape_html(feat['name'])}">
          <div class="feat-chart-meta">
            <span class="feat-chart-name" title="{escape_html(feat['name'])}">{escape_html(feat['name'])}</span>
            <span class="feat-chart-stats">
              <span class="tag-pass">{f_pass}P</span> &middot; <span class="tag-fail">{f_fail}F</span> &middot; <span class="tag-dur">⏱ {f_dur_str}</span>
            </span>
          </div>
          <div class="feat-stacked-track">
            <div class="feat-seg seg-pass" style="width:{p_pct:.1f}%;" title="Passed: {f_pass}/{f_total} ({p_pct:.0f}%)"></div>
            <div class="feat-seg seg-fail" style="width:{f_pct:.1f}%;" title="Failed: {f_fail}/{f_total} ({f_pct:.0f}%)"></div>
            <div class="feat-seg seg-skip" style="width:{s_pct:.1f}%;" title="Skipped: {f_skip}/{f_total} ({s_pct:.0f}%)"></div>
          </div>
        </div>
        """

    # ── SCENARIO DURATION BENCHMARK BARS ────────────────────────
    slowest_scenarios = sorted(flat_scenarios, key=lambda s: s["duration"], reverse=True)[:6]
    max_dur = max([s["duration"] for s in slowest_scenarios]) if slowest_scenarios else 1.0
    if max_dur <= 0:
        max_dur = 1.0

    duration_bars_html = ""
    for sc in slowest_scenarios:
        pct = min(100, max(8, (sc["duration"] / max_dur * 100)))
        st = sc["status"]
        icon = "✓" if st == "passed" else ("✗" if st == "failed" else "—")
        duration_bars_html += f"""
        <div class="dur-chart-row" onclick="scrollToScenario('{sc['id']}')" title="Jump to #{sc['index']} {escape_html(sc['name'])}">
          <div class="dur-row-info">
            <span class="dur-row-name"><span class="dur-icon-{st}">{icon}</span> #{sc['index']} {escape_html(sc['name'])}</span>
            <span class="dur-row-val">{fmt_dur(sc['duration'])}</span>
          </div>
          <div class="dur-bar-track">
            <div class="dur-bar-fill dur-bar-{st}" style="width:{pct:.1f}%;"></div>
          </div>
        </div>
        """

    # ── EFFICIENCY ACTION TOOLBAR ──────────────────────────────
    has_failed_cls = "has-fail" if failed_scenarios > 0 else ""
    first_fail_disabled = "disabled" if failed_scenarios == 0 else ""

    action_toolbar_html = f"""
    <div class="action-toolbar">
      <div class="toolbar-left">
        <div class="filter-btn-group">
          <button class="f-pill active" id="btn-filter-all" onclick="filterByStatus('all', this)">All ({total_scenarios})</button>
          <button class="f-pill f-pill-fail {has_failed_cls}" id="btn-filter-failed" onclick="filterByStatus('failed', this)">🔥 Failed ({failed_scenarios})</button>
          <button class="f-pill f-pill-pass" id="btn-filter-passed" onclick="filterByStatus('passed', this)">✓ Passed ({passed_scenarios})</button>
          <button class="f-pill f-pill-skip" id="btn-filter-skipped" onclick="filterByStatus('skipped', this)">— Skipped ({skipped_scenarios})</button>
        </div>
      </div>
      <div class="toolbar-right">
        <button class="tool-btn btn-jump-fail" onclick="jumpToFirstFailure()" {first_fail_disabled} title="Quick jump straight to the first failed scenario">⚡ First Failure</button>
        <button class="tool-btn" id="btn-toggle-all" onclick="toggleAllAccordions()">📂 Expand All</button>
        <button class="tool-btn" onclick="copyExecutiveSummary()">📋 Copy Summary</button>
        <button class="tool-btn" onclick="window.print()">🖨️ Print / PDF</button>
      </div>
    </div>
    """

    # ── KPI SUMMARY CARDS ──────────────────────────────────────
    kpi_cards_html = f"""
    <div class="cards-grid">
      <div class="summary-card c-scenarios">
        <div class="val">{total_scenarios}</div>
        <div class="lbl">Total Scenarios</div>
        <div class="sub-lbl">{total_features} Feature{'' if total_features == 1 else 's'}</div>
      </div>
      <div class="summary-card c-passed" onclick="filterByStatus('passed')" style="cursor:pointer;" title="Click to filter passed">
        <div class="val">{passed_scenarios}</div>
        <div class="lbl">Passed</div>
        <div class="sub-lbl" style="color:var(--pass)">{pass_rate_str}% Pass Rate</div>
      </div>
      <div class="summary-card c-failed" onclick="filterByStatus('failed')" style="cursor:pointer;" title="Click to filter failed">
        <div class="val">{failed_scenarios}</div>
        <div class="lbl">Failed</div>
        <div class="sub-lbl" style="color:var(--fail)">{fail_rate_str}% Fail Rate</div>
      </div>
      <div class="summary-card c-skipped" onclick="filterByStatus('skipped')" style="cursor:pointer;" title="Click to filter skipped">
        <div class="val">{skipped_scenarios}</div>
        <div class="lbl">Skipped</div>
        <div class="sub-lbl" style="color:var(--skip)">{skip_rate_str}% Skip Rate</div>
      </div>
      <div class="summary-card c-rate">
        <div class="val">{pass_rate_str}%</div>
        <div class="lbl">Pass Rate</div>
        <div class="sub-lbl" style="color:#2563eb">{step_pass_str}% Steps Valid</div>
      </div>
      <div class="summary-card c-dur">
        <div class="val">{fmt_dur(total_duration)}</div>
        <div class="lbl">Total Duration</div>
        <div class="sub-lbl">Avg {fmt_dur(avg_sc_dur)}/sc</div>
      </div>
    </div>
    """

    # ── TRI-COLOR SEGMENTED PROGRESS BAR ───────────────────────
    progress_bar_html = f"""
    <div class="progress-card">
      <div class="progress-track-tri">
        <div class="prog-seg-pass" style="width:{pass_rate_num:.1f}%;" title="Passed: {passed_scenarios} ({pass_rate_str}%)"></div>
        <div class="prog-seg-fail" style="width:{fail_rate_num:.1f}%;" title="Failed: {failed_scenarios} ({fail_rate_str}%)"></div>
        <div class="prog-seg-skip" style="width:{skip_rate_num:.1f}%;" title="Skipped: {skipped_scenarios} ({skip_rate_str}%)"></div>
      </div>
      <div class="progress-labels">
        <div class="prog-left-lbls">
          <span class="rate-badge badge-pass">✓ Pass Rate: <strong>{pass_rate_str}%</strong> ({passed_scenarios}/{total_scenarios})</span>
          <span class="rate-badge badge-fail">✗ Fail Rate: <strong>{fail_rate_str}%</strong> ({failed_scenarios}/{total_scenarios})</span>
          <span class="rate-badge badge-skip">— Skip Rate: <strong>{skip_rate_str}%</strong> ({skipped_scenarios}/{total_scenarios})</span>
        </div>
        <div class="prog-right-lbls">
          <span>Steps Breakdown: <strong style="color:var(--pass)">{passed_steps} passed</strong> &nbsp;|&nbsp; <strong style="color:var(--fail)">{failed_steps} failed</strong> &nbsp;|&nbsp; <strong style="color:var(--skip)">{skipped_steps} skipped</strong></span>
        </div>
      </div>
    </div>
    """

    # ── VISUAL ANALYTICS DASHBOARD ─────────────────────────────
    analytics_dashboard_html = f"""
    <section class="analytics-dashboard">
      <!-- GRAPH 1: SCENARIO OUTCOME (PASS / FAIL / SKIP) -->
      <div class="chart-card">
        <div class="chart-card-header">
          <span class="chart-card-title">📊 Scenario Outcomes</span>
          <span class="chart-card-badge">{total_scenarios} total</span>
        </div>
        <div class="donut-wrap">
          {scenario_donut_svg}
        </div>
        <div class="chart-legend">
          <div class="legend-item" onclick="filterByStatus('passed')" title="Filter Passed Scenarios">
            <div class="legend-left">
              <span class="legend-dot dot-pass"></span>
              <span class="legend-lbl">Pass Rate</span>
            </div>
            <span class="legend-val" style="color:var(--pass)">{passed_scenarios} ({pass_rate_str}%)</span>
          </div>
          <div class="legend-item" onclick="filterByStatus('failed')" title="Filter Failed Scenarios">
            <div class="legend-left">
              <span class="legend-dot dot-fail"></span>
              <span class="legend-lbl">Fail Rate</span>
            </div>
            <span class="legend-val" style="color:var(--fail)">{failed_scenarios} ({fail_rate_str}%)</span>
          </div>
          <div class="legend-item" onclick="filterByStatus('skipped')" title="Filter Skipped Scenarios">
            <div class="legend-left">
              <span class="legend-dot dot-skip"></span>
              <span class="legend-lbl">Skip Rate</span>
            </div>
            <span class="legend-val" style="color:var(--skip)">{skipped_scenarios} ({skip_rate_str}%)</span>
          </div>
        </div>
      </div>

      <!-- GRAPH 2: STEP OUTCOME (PASS / FAIL / SKIP) -->
      <div class="chart-card">
        <div class="chart-card-header">
          <span class="chart-card-title">🐾 Step Execution</span>
          <span class="chart-card-badge">{total_steps} steps</span>
        </div>
        <div class="donut-wrap">
          {step_donut_svg}
        </div>
        <div class="chart-legend">
          <div class="legend-item">
            <div class="legend-left">
              <span class="legend-dot dot-pass"></span>
              <span class="legend-lbl">Passed Steps</span>
            </div>
            <span class="legend-val" style="color:var(--pass)">{passed_steps} ({step_pass_str}%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-left">
              <span class="legend-dot dot-fail"></span>
              <span class="legend-lbl">Failed Steps</span>
            </div>
            <span class="legend-val" style="color:var(--fail)">{failed_steps} ({step_fail_str}%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-left">
              <span class="legend-dot dot-skip"></span>
              <span class="legend-lbl">Skipped Steps</span>
            </div>
            <span class="legend-val" style="color:var(--skip)">{skipped_steps} ({step_skip_str}%)</span>
          </div>
        </div>
      </div>

      <!-- GRAPH 3: FEATURE HEALTH BREAKDOWN -->
      <div class="chart-card">
        <div class="chart-card-header">
          <span class="chart-card-title">📁 Feature Distribution</span>
          <span class="chart-card-badge">{total_features} features</span>
        </div>
        <div class="feat-chart-list">
          {feature_bars_html}
        </div>
      </div>

      <!-- GRAPH 4: SCENARIO DURATION BENCHMARK -->
      <div class="chart-card">
        <div class="chart-card-header">
          <span class="chart-card-title">⏱️ Duration Benchmark</span>
          <span class="chart-card-badge">Slowest tests</span>
        </div>
        <div class="dur-chart-list">
          {duration_bars_html}
        </div>
      </div>
    </section>
    """

    # ── FULL HTML DOCUMENT ─────────────────────────────────────
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(title)}</title>
<style>
/* ─── RESET & THEME TOKENS ─────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg-page: #f1f5f9;
  --bg-surface: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-sub: #94a3b8;
  --border-light: #e2e8f0;
  --border-strong: #cbd5e1;
  --primary: #3b82f6;
  --primary-hover: #2563eb;
  --pass: #16a34a;
  --pass-bg: #dcfce7;
  --pass-border: #86efac;
  --pass-text: #166534;
  --fail: #dc2626;
  --fail-bg: #fee2e2;
  --fail-border: #fca5a5;
  --fail-text: #991b1b;
  --skip: #d97706;
  --skip-bg: #fef3c7;
  --skip-border: #fcd34d;
  --skip-text: #92400e;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, Menlo, Monaco, 'Courier New', monospace;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-pill: 9999px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.05);
}}

body {{
  font-family: var(--font-sans);
  background-color: #f1f5f9;
  background-image:
    radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.08) 0%, transparent 45%),
    radial-gradient(circle at 10% 90%, rgba(99, 102, 241, 0.08) 0%, transparent 45%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  background-attachment: fixed;
  color: var(--text-main);
  font-size: 13px;
  line-height: 1.5;
  min-height: 100vh;
  padding-bottom: 60px;
  position: relative;
}}

/* ─── 3D AUTOMATION BUG WATERMARK BACKGROUND ───────────────── */
.bg-bug-layer {{
  position: fixed;
  right: -30px;
  bottom: -30px;
  width: 660px;
  height: 500px;
  background-image: url('{bug_b64}');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: right bottom;
  opacity: 0.16;
  pointer-events: none;
  z-index: 0;
  filter: drop-shadow(0 0 35px rgba(56, 189, 248, 0.45));
  animation: float-bug 10s ease-in-out infinite alternate;
}}
@keyframes float-bug {{
  0%   {{ transform: translateY(0px) rotate(0deg); }}
  50%  {{ transform: translateY(-16px) rotate(1.2deg); }}
  100% {{ transform: translateY(6px) rotate(-1deg); }}
}}

.main-wrap, .app-header, .nav-tabs {{
  position: relative;
  z-index: 1;
}}

.header-bug-emblem {{
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.08);
  padding: 5px 14px 5px 6px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(56, 189, 248, 0.35);
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.2);
  backdrop-filter: blur(8px);
  user-select: none;
}}
.bug-avatar {{
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #38bdf8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.6);
}}
.bug-emblem-text {{
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}}
.bug-badge-title {{
  font-size: 0.68rem;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.8px;
}}
.bug-badge-sub {{
  font-size: 0.58rem;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 0.4px;
}}

/* ─── APP HEADER ───────────────────────────────────────────── */
.app-header {{
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #f8fafc;
  padding: 24px 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.app-header-left h1 {{
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 10px;
}}
.app-header-left .meta {{
  font-size: 0.76rem;
  color: var(--text-sub);
  margin-top: 4px;
  display: flex;
  gap: 16px;
}}
.app-header-right {{
  display: flex;
  align-items: center;
  gap: 20px;
}}
.header-kpi {{
  text-align: right;
}}
.header-kpi .rate-val {{
  font-size: 2.2rem;
  font-weight: 800;
  line-height: 1;
  color: {'#4ade80' if pass_rate == 100 else ('#fbbf24' if pass_rate >= 50 else '#f87171')};
}}
.header-kpi .rate-lbl {{
  font-size: 0.7rem;
  color: var(--text-sub);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-top: 3px;
}}

/* ─── TAB NAVIGATION ───────────────────────────────────────── */
.nav-tabs {{
  background: #fff;
  border-bottom: 1px solid var(--border-light);
  padding: 0 36px;
  display: flex;
  gap: 8px;
  box-shadow: var(--shadow-sm);
}}
.nav-tab {{
  padding: 12px 20px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s ease;
}}
.nav-tab:hover {{
  color: var(--primary);
  background: #f8fafc;
}}
.nav-tab.active {{
  color: var(--primary);
  border-bottom-color: var(--primary);
}}
.nav-tab .tab-badge {{
  font-size: 0.68rem;
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  background: #e2e8f0;
  color: #475569;
}}

/* ─── MAIN WRAPPER ─────────────────────────────────────────── */
.main-wrap {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 36px;
}}

/* ─── QUICK EFFICIENCY ACTION TOOLBAR ──────────────────────── */
.action-toolbar {{
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 12px 18px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}}
.toolbar-left, .toolbar-right {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}}
.f-pill-fail.has-fail {{
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
  font-weight: 700;
  animation: pulse-fail 2.5s infinite;
}}
@keyframes pulse-fail {{
  0%, 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }}
  50% {{ box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.15); }}
}}
.tool-btn {{
  padding: 6px 13px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-strong);
  background: #fff;
  color: #334155;
  font-size: 0.73rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
}}
.tool-btn:hover {{
  background: #f1f5f9;
  border-color: #94a3b8;
}}
.btn-jump-fail {{
  background: #ef4444;
  color: #fff;
  border-color: #dc2626;
}}
.btn-jump-fail:hover {{
  background: #dc2626;
  color: #fff;
}}
.btn-jump-fail:disabled {{
  background: #e2e8f0;
  color: #94a3b8;
  border-color: #cbd5e1;
  cursor: not-allowed;
}}

/* ─── SUMMARY CARDS ────────────────────────────────────────── */
.cards-grid {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}}
@media (max-width: 1100px) {{
  .cards-grid {{ grid-template-columns: repeat(3, 1fr); }}
}}
@media (max-width: 600px) {{
  .cards-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
.summary-card {{
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 16px 12px;
  text-align: center;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: transform 0.15s, box-shadow 0.15s;
}}
.summary-card:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}}
.summary-card .val {{
  font-size: 1.85rem;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 4px;
}}
.summary-card .lbl {{
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-muted);
}}
.summary-card .sub-lbl {{
  font-size: 0.67rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-top: 4px;
}}
.c-scenarios .val {{ color: #6366f1; }}
.c-passed .val    {{ color: var(--pass); }}
.c-failed .val    {{ color: var(--fail); }}
.c-skipped .val   {{ color: var(--skip); }}
.c-rate .val      {{ color: #2563eb; }}
.c-dur .val       {{ color: #7c3aed; font-size: 1.45rem; }}

/* ─── TRI-COLOR SEGMENTED PROGRESS BAR ─────────────────────── */
.progress-card {{
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  border: 1px solid var(--border-light);
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}}
.progress-track-tri {{
  height: 12px;
  background: #e2e8f0;
  border-radius: var(--radius-pill);
  overflow: hidden;
  display: flex;
  margin-bottom: 10px;
}}
.prog-seg-pass {{
  background: #10b981;
  height: 100%;
  transition: width 0.6s ease;
}}
.prog-seg-fail {{
  background: #ef4444;
  height: 100%;
  transition: width 0.6s ease;
}}
.prog-seg-skip {{
  background: #f59e0b;
  height: 100%;
  transition: width 0.6s ease;
}}
.progress-labels {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.74rem;
  color: var(--text-muted);
  font-weight: 500;
  flex-wrap: wrap;
  gap: 8px;
}}
.prog-left-lbls {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}}
.rate-badge {{
  font-size: 0.71rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  display: inline-flex;
  align-items: center;
}}
.badge-pass {{ background: #dcfce7; color: #166534; border: 1px solid #86efac; }}
.badge-fail {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
.badge-skip {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }}

/* ─── VISUAL ANALYTICS DASHBOARD ───────────────────────────── */
.analytics-dashboard {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}}
@media (max-width: 1200px) {{
  .analytics-dashboard {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 680px) {{
  .analytics-dashboard {{ grid-template-columns: 1fr; }}
}}
.chart-card {{
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  padding: 16px 18px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}}
.chart-card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}}
.chart-card-title {{
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 6px;
}}
.chart-card-badge {{
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: #f1f5f9;
  color: #475569;
}}
.donut-wrap {{
  display: flex;
  justify-content: center;
  align-items: center;
  width: 140px;
  height: 140px;
  margin: 0 auto;
}}
.donut-svg {{
  width: 100%;
  height: 100%;
  display: block;
}}
.donut-val {{
  font-size: 24px;
  font-weight: 800;
  fill: #0f172a;
  font-family: var(--font-sans);
}}
.donut-lbl {{
  font-size: 9px;
  font-weight: 700;
  fill: #64748b;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-family: var(--font-sans);
}}
.donut-slice {{
  transition: stroke-width 0.2s ease, opacity 0.2s ease;
  cursor: pointer;
}}
.donut-slice:hover {{
  stroke-width: 24;
  opacity: 0.88;
}}
.chart-legend {{
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  width: 100%;
}}
.legend-item {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 9px;
  border-radius: var(--radius-sm);
  background: #f8fafc;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.72rem;
}}
.legend-item:hover {{
  background: #f1f5f9;
  border-color: var(--border-strong);
  transform: translateX(2px);
}}
.legend-left {{
  display: flex;
  align-items: center;
  gap: 7px;
}}
.legend-dot {{
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}}
.dot-pass {{ background: #10b981; }}
.dot-fail {{ background: #ef4444; }}
.dot-skip {{ background: #f59e0b; }}
.legend-lbl {{
  font-weight: 600;
  color: var(--text-main);
}}
.legend-val {{
  font-weight: 700;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.71rem;
}}

/* Feature Breakdown Bars */
.feat-chart-list {{
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}}
.feat-chart-row {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 7px 9px;
  border-radius: var(--radius-sm);
  background: #f8fafc;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.15s ease;
}}
.feat-chart-row:hover {{
  background: #f1f5f9;
  border-color: var(--primary);
  transform: translateX(2px);
}}
.feat-chart-meta {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.71rem;
}}
.feat-chart-name {{
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 155px;
}}
.feat-chart-stats {{
  font-size: 0.67rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}
.tag-pass {{ color: #166534; font-weight: 700; }}
.tag-fail {{ color: #991b1b; font-weight: 700; }}
.tag-dur {{ color: #64748b; font-weight: 600; }}
.feat-stacked-track {{
  height: 7px;
  border-radius: var(--radius-pill);
  background: #e2e8f0;
  display: flex;
  overflow: hidden;
}}
.feat-seg {{
  height: 100%;
  transition: width 0.3s;
}}
.seg-pass {{ background: #10b981; }}
.seg-fail {{ background: #ef4444; }}
.seg-skip {{ background: #f59e0b; }}

/* Scenario Duration Ranking */
.dur-chart-list {{
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}}
.dur-chart-row {{
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 5px 9px;
  border-radius: var(--radius-sm);
  background: #f8fafc;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.15s ease;
}}
.dur-chart-row:hover {{
  background: #f1f5f9;
  border-color: var(--primary);
  transform: translateX(2px);
}}
.dur-row-info {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.71rem;
}}
.dur-row-name {{
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 170px;
}}
.dur-row-val {{
  font-family: var(--font-mono);
  font-weight: 700;
  color: #7c3aed;
  font-size: 0.69rem;
}}
.dur-bar-track {{
  height: 5px;
  background: #e2e8f0;
  border-radius: var(--radius-pill);
  overflow: hidden;
}}
.dur-bar-fill {{
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width 0.4s ease;
}}
.dur-bar-passed {{ background: #10b981; }}
.dur-bar-failed {{ background: #ef4444; }}
.dur-bar-skipped {{ background: #f59e0b; }}
.dur-icon-passed {{ color: #10b981; font-weight: 800; margin-right: 2px; }}
.dur-icon-failed {{ color: #ef4444; font-weight: 800; margin-right: 2px; }}
.dur-icon-skipped {{ color: #f59e0b; font-weight: 800; margin-right: 2px; }}

/* Toast Notification */
.toast-notify {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #0f172a;
  color: #f8fafc;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.76rem;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  border: 1px solid #334155;
  z-index: 10000;
  opacity: 0;
  transform: translateY(10px);
  pointer-events: none;
  transition: all 0.2s ease;
}}
.toast-notify.show {{
  opacity: 1;
  transform: translateY(0);
}}

/* ─── SCENARIO EXECUTION MONITOR (PRIMARY USER REQUEST) ───── */
.section-panel {{
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
  overflow: hidden;
}}
.section-panel-header {{
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}}
.section-title {{
  font-size: 0.95rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.section-title .badge-count {{
  background: #e2e8f0;
  color: #334155;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-weight: 700;
}}

/* Search & Filters */
.monitor-controls {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}}
.search-input-box {{
  position: relative;
  display: flex;
  align-items: center;
}}
.search-input-box input {{
  padding: 6px 12px 6px 30px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-strong);
  font-size: 0.75rem;
  outline: none;
  width: 220px;
  transition: border-color 0.15s, width 0.15s;
}}
.search-input-box input:focus {{
  border-color: var(--primary);
  width: 280px;
}}
.search-icon {{
  position: absolute;
  left: 9px;
  font-size: 0.75rem;
  color: var(--text-sub);
  pointer-events: none;
}}
.filter-btn-group {{
  display: flex;
  gap: 4px;
}}
.f-pill {{
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-light);
  background: #fff;
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.15s;
}}
.f-pill:hover {{
  background: #f1f5f9;
}}
.f-pill.active {{
  background: #1e293b;
  color: #fff;
  border-color: #1e293b;
}}

/* Monitor Cards Grid */
.monitor-grid {{
  padding: 16px 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
}}
.mon-card {{
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.mon-card:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}}
.mon-card.mon-passed {{ border-left: 4px solid var(--pass); }}
.mon-card.mon-failed {{ border-left: 4px solid var(--fail); background: #fffbfb; }}
.mon-card.mon-skipped {{ border-left: 4px solid var(--skip); }}

.mon-card-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.mon-idx {{
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-sub);
  font-family: var(--font-mono);
}}
.mon-name {{
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.mon-meta {{
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--text-muted);
}}
.mon-bar {{
  height: 4px;
  background: #e2e8f0;
  border-radius: var(--radius-pill);
  overflow: hidden;
}}
.mon-card.mon-passed .mon-bar-fill {{ background: var(--pass); height: 100%; }}
.mon-card.mon-failed .mon-bar-fill {{ background: var(--fail); height: 100%; }}
.mon-card.mon-skipped .mon-bar-fill {{ background: var(--skip); height: 100%; }}

/* ─── STATUS PILLS (MATCHING REFERENCE IMAGE) ──────────────── */
.status-pill {{
  font-size: 0.70rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: var(--radius-pill);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}}
.badge-passed {{
  background: var(--pass-bg);
  border: 1px solid var(--pass-border);
  color: var(--pass-text);
}}
.badge-failed {{
  background: var(--fail-bg);
  border: 1px solid var(--fail-border);
  color: var(--fail-text);
}}
.badge-skipped {{
  background: var(--skip-bg);
  border: 1px solid var(--skip-border);
  color: var(--skip-text);
}}

/* ─── CIRCULAR TOGGLE BUTTON (MATCHING REFERENCE IMAGE) ───── */
.sc-circle-btn {{
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #cbd5e1;
  border: none;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.62rem;
  font-weight: 700;
  transition: all 0.2s ease;
  flex-shrink: 0;
}}
.sc-circle-btn:hover {{
  background: #94a3b8;
  color: #fff;
}}
.sc-circle-btn.open {{
  transform: rotate(180deg);
  background: #64748b;
  color: #fff;
}}

/* ─── FEATURES & SCENARIOS ─────────────────────────────────── */
.feature-card {{
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  margin-bottom: 20px;
  overflow: hidden;
}}
.ft-header {{
  padding: 14px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  user-select: none;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.15s;
}}
.ft-header:hover {{
  background: #f1f5f9;
}}
.ft-icon {{
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
}}
.ft-icon-passed {{ background: var(--pass); }}
.ft-icon-failed {{ background: var(--fail); }}
.ft-icon-skipped {{ background: var(--skip); }}

.ft-info {{
  flex: 1;
  min-width: 0;
}}
.ft-title-row {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.ft-name {{
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-main);
}}
.ft-tag {{
  font-size: 0.68rem;
  color: #6366f1;
  font-family: var(--font-mono);
}}
.ft-path {{
  font-size: 0.7rem;
  color: var(--text-sub);
  display: block;
  margin-top: 1px;
}}
.ft-right {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.ft-dur {{
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}
.ft-body {{
  display: block;
  background: #fff;
}}
.ft-body.collapsed {{
  display: none;
}}

/* ─── SCENARIO CARD (EXACTLY MATCHING USER REFERENCE IMAGE) ── */
.scenario-card {{
  border-bottom: 1px solid var(--border-light);
  background: #fff;
  transition: background 0.15s;
}}
.scenario-card:last-child {{
  border-bottom: none;
}}
.scenario-card.highlighted {{
  animation: pulse-border 1.5s ease-out;
}}
@keyframes pulse-border {{
  0% {{ background: #eff6ff; }}
  100% {{ background: #fff; }}
}}

.sc-header {{
  padding: 12px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  user-select: none;
  transition: background 0.15s;
}}
.sc-header:hover {{
  background: #f8fafc;
}}
.scenario-failed .sc-header {{
  background: #fffafa;
}}
.scenario-failed .sc-header:hover {{
  background: #fef2f2;
}}

.sc-doc-icon {{
  font-size: 0.95rem;
  flex-shrink: 0;
}}
.sc-title {{
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-main);
  flex: 1;
}}
.sc-tag {{
  font-size: 0.68rem;
  color: #6366f1;
  background: #eef2ff;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}}
.sc-right {{
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}}
.sc-dur {{
  font-size: 0.74rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}

.sc-body {{
  padding: 6px 20px 16px;
  background: #fff;
  display: block;
}}
.sc-body.collapsed {{
  display: none;
}}

/* ─── STEP ROW (MATCHING USER REFERENCE IMAGE) ─────────────── */
.steps-container {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}}
.step-row {{
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: background 0.15s;
}}
.step-row-passed {{ background: #f9fdfa; }}
.step-row-failed {{ background: #fff5f5; }}
.step-row-skipped {{ background: #fafaf9; opacity: 0.8; }}

.step-main-bar {{
  padding: 8px 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}}
.step-main-bar:hover {{
  filter: brightness(0.97);
}}
.step-toggle-btn {{
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e2e8f0;
  border: none;
  color: #475569;
  font-size: 0.55rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  transition: transform 0.2s;
}}
.step-toggle-btn.open {{
  transform: rotate(180deg);
  background: #94a3b8;
  color: #fff;
}}
.step-toggle-spacer {{
  width: 18px;
  height: 18px;
  display: inline-block;
  flex-shrink: 0;
}}

.step-status-icon {{
  font-size: 0.85rem;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}}
.icon-passed {{ color: var(--pass); }}
.icon-failed {{ color: var(--fail); }}
.icon-skipped {{ color: var(--text-sub); }}

.step-content-box {{
  flex: 1;
  min-width: 0;
}}
.step-line {{
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 0.82rem;
}}
.step-kw {{
  font-weight: 700;
  color: #4f46e5;
  flex-shrink: 0;
}}
.step-name {{
  color: var(--text-main);
  font-weight: 500;
}}
.step-right {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}}
.step-dur {{
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}

/* Strategy Pills (MATCHING USER REFERENCE IMAGE) */
.step-strategies {{
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 6px;
}}
.strategy-pill {{
  font-size: 0.69rem;
  font-weight: 700;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  letter-spacing: 0.2px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}
.pill-loss {{
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}}
.pill-win {{
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}}
.pill-skipped {{
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #cbd5e1;
}}

/* ─── ERROR PANEL ──────────────────────────────────────────── */
.step-details-body {{
  padding: 0 12px 10px 40px;
}}
.err-panel {{
  background: #0f172a;
  border-radius: var(--radius-sm);
  border-left: 4px solid var(--fail);
  overflow: hidden;
  margin-top: 4px;
}}
.err-header {{
  background: #1e293b;
  padding: 6px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.err-tag {{
  color: #f87171;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.6px;
}}
.btn-copy-err {{
  background: #334155;
  border: none;
  color: #cbd5e1;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.65rem;
  cursor: pointer;
  transition: all 0.15s;
}}
.btn-copy-err:hover {{
  background: var(--primary);
  color: #fff;
}}
.err-text {{
  padding: 10px 14px;
  color: #fca5a5;
  font-family: var(--font-mono);
  font-size: 0.73rem;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 260px;
  overflow-y: auto;
  line-height: 1.45;
}}

/* ─── SCREENSHOT EVIDENCE CARD ─────────────────────────────── */
.screenshot-card {{
  margin: 10px 0 16px;
  padding: 14px;
  background: #fff8f8;
  border: 1px dashed #fca5a5;
  border-radius: var(--radius-sm);
}}
.shot-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}}
.shot-title {{
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--fail-text);
  letter-spacing: 0.5px;
}}
.shot-actions {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.shot-btn-link {{
  background: transparent;
  border: none;
  font-size: 0.73rem;
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}}
.shot-btn-link:hover {{
  text-decoration: underline;
  background: #eff6ff;
}}
.shot-preview-wrap {{
  position: relative;
  display: inline-block;
  cursor: zoom-in;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid #fecaca;
  box-shadow: var(--shadow-sm);
  background: #0f172a;
}}
.shot-img {{
  display: block;
  max-width: 540px;
  max-height: 320px;
  width: 100%;
  object-fit: contain;
  background: #0f172a;
}}
.shot-overlay {{
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.35);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s;
}}
.shot-preview-wrap:hover .shot-overlay {{
  opacity: 1;
}}
.mon-shot-pill {{
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
  margin-left: auto;
}}

/* ─── GUI TERMINAL CONSOLE VIEW ────────────────────────────── */
.terminal-window {{
  background: #0f172a;
  border-radius: var(--radius-md);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
  border: 1px solid #334155;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}
.terminal-titlebar {{
  background: #1e293b;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #334155;
  user-select: none;
}}
.terminal-controls {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.term-dot {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}}
.term-dot.red    {{ background: #ef4444; }}
.term-dot.yellow {{ background: #f59e0b; }}
.term-dot.green  {{ background: #10b981; }}
.term-title {{
  color: #cbd5e1;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-mono);
}}
.term-actions {{
  display: flex;
  gap: 8px;
}}
.term-btn {{
  background: #334155;
  border: 1px solid #475569;
  color: #e2e8f0;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}}
.term-btn:hover {{
  background: #475569;
}}
.terminal-body {{
  padding: 18px 22px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: #38bdf8;
  line-height: 1.5;
  white-space: pre;
  overflow-x: auto;
  max-height: 700px;
  background: #020617;
}}

/* ─── LIGHTBOX MODAL ───────────────────────────────────────── */
.lightbox-modal {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.85);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 24px;
}}
.lightbox-modal.active {{
  display: flex;
}}
.lightbox-img {{
  max-width: 95vw;
  max-height: 90vh;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  background: #fff;
}}
.lightbox-close {{
  position: absolute;
  top: 20px;
  right: 24px;
  background: rgba(255,255,255,0.2);
  border: none;
  color: #fff;
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.lightbox-close:hover {{
  background: rgba(255,255,255,0.35);
}}

/* ─── PRINT OPTIMIZATIONS ──────────────────────────────────── */
@media print {{
  .app-header, .nav-tabs, .monitor-controls, .sc-circle-btn, .step-toggle-btn, .term-actions {{
    display: none !important;
  }}
  body {{ background: #fff; color: #000; padding: 0; }}
  .main-wrap {{ padding: 0; max-width: 100%; }}
  .ft-body, .sc-body {{ display: block !important; }}
  .scenario-card, .feature-card {{ box-shadow: none !important; border: 1px solid #ccc !important; margin-bottom: 12px; }}
}}
</style>
</head>
<body>

<!-- 3D AUTOMATION BUG WATERMARK BACKGROUND -->
<div class="bg-bug-layer"></div>

<!-- APP HEADER -->
<header class="app-header">
  <div class="app-header-left">
    <h1>🧪 {escape_html(title)}</h1>
    <div class="meta">
      <span>📅 Generated: {now}</span>
      <span>⏱ Total Duration: {fmt_dur(total_duration)}</span>
      <span>📦 Total Scenarios: {total_scenarios}</span>
    </div>
  </div>
  <div class="app-header-right">
    <div class="header-bug-emblem" title="3D Automation Core Active">
      <img src="{bug_b64}" alt="3D Automation Bug" class="bug-avatar" />
      <div class="bug-emblem-text">
        <span class="bug-badge-title">3D AUTOMATION</span>
        <span class="bug-badge-sub">BDD ENGINE</span>
      </div>
    </div>
    <div class="header-kpi">
      <div class="rate-val">{pass_rate_str}%</div>
      <div class="rate-lbl">Scenario Pass Rate</div>
    </div>
  </div>
</header>

<!-- TABS NAVIGATION -->
<nav class="nav-tabs">
  <div class="nav-tab active" id="tab-scenarios" onclick="switchView('scenarios')">
    <span>📊 Scenarios &amp; Steps</span>
    <span class="tab-badge">{total_scenarios}</span>
  </div>
  <div class="nav-tab" id="tab-terminal" onclick="switchView('terminal')">
    <span>💻 GUI Terminal Console</span>
    <span class="tab-badge">LIVE LOG</span>
  </div>
</nav>

<!-- MAIN CONTENT -->
<main class="main-wrap">

  <!-- SCENARIOS VIEW -->
  <div id="view-scenarios">

    <!-- QUICK EFFICIENCY ACTION TOOLBAR -->
    {action_toolbar_html}

    <!-- KPI CARDS -->
    {kpi_cards_html}

    <!-- TRI-COLOR SEGMENTED PROGRESS BAR -->
    {progress_bar_html}

    <!-- VISUAL ANALYTICS DASHBOARD (PASS / FAIL / SKIP GRAPHS) -->
    {analytics_dashboard_html}

    <!-- ── SCENARIO EXECUTION MONITOR SECTION (PRIMARY FEATURE) ── -->
    <section class="section-panel">
      <div class="section-panel-header">
        <div class="section-title">
          <span>🎯 Scenario Execution Monitor</span>
          <span class="badge-count">{total_scenarios} total</span>
        </div>
        <div class="monitor-controls">
          <div class="search-input-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="scenario-search" placeholder="Search scenarios, tags, steps..." oninput="handleSearch(this.value)" />
          </div>
          <div class="filter-btn-group">
            <button class="f-pill active" onclick="filterByStatus('all', this)">All ({total_scenarios})</button>
            <button class="f-pill" onclick="filterByStatus('passed', this)">✓ Passed ({passed_scenarios})</button>
            <button class="f-pill" onclick="filterByStatus('failed', this)">✗ Failed ({failed_scenarios})</button>
            <button class="f-pill" onclick="filterByStatus('skipped', this)">— Skipped ({skipped_scenarios})</button>
          </div>
        </div>
      </div>
      <div class="monitor-grid" id="monitor-grid">
        {monitor_cards_html}
      </div>
    </section>

    <!-- FEATURES & SCENARIOS DETAILS -->
    <div id="features-wrap">
      {features_html}
    </div>

  </div>

  <!-- GUI TERMINAL CONSOLE VIEW -->
  <div id="view-terminal" style="display:none">
    <div class="terminal-window">
      <div class="terminal-titlebar">
        <div class="terminal-controls">
          <span class="term-dot red"></span>
          <span class="term-dot yellow"></span>
          <span class="term-dot green"></span>
          <span class="term-title">Automatio BDD Terminal Console — Live Execution Output</span>
        </div>
        <div class="term-actions">
          <button class="term-btn" onclick="copyTerminal()">📋 Copy Log</button>
          <button class="term-btn" onclick="downloadLog()">⬇️ Download .log</button>
          <button class="term-btn" onclick="toggleTermFullscreen()">⛶ Fullscreen</button>
        </div>
      </div>
      <div class="terminal-body" id="term-text">{escape_html(terminal_text)}</div>
    </div>
  </div>

</main>

<!-- LIGHTBOX MODAL -->
<div class="lightbox-modal" id="lightbox" onclick="closeLightbox()">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <img src="" alt="Screenshot Full View" class="lightbox-img" id="lightbox-img" onclick="event.stopPropagation()" />
</div>

<!-- TOAST NOTIFICATION -->
<div class="toast-notify" id="toast-notify"></div>

<script>
/* ─── TEST METRICS DATA ────────────────────────────────────── */
var TEST_METRICS = {{
  totalScenarios: {total_scenarios},
  passedScenarios: {passed_scenarios},
  failedScenarios: {failed_scenarios},
  skippedScenarios: {skipped_scenarios},
  passRate: '{pass_rate_str}',
  failRate: '{fail_rate_str}',
  skipRate: '{skip_rate_str}',
  totalSteps: {total_steps},
  passedSteps: {passed_steps},
  failedSteps: {failed_steps},
  skippedSteps: {skipped_steps},
  stepPassRate: '{step_pass_str}',
  totalDuration: '{fmt_dur(total_duration)}'
}};

/* ─── TOAST NOTIFICATIONS ──────────────────────────────────── */
function showToast(msg) {{
  var t = document.getElementById('toast-notify');
  if (!t) return;
  t.innerText = msg;
  t.classList.add('show');
  setTimeout(function() {{ t.classList.remove('show'); }}, 2500);
}}

/* ─── TAB SWITCHING ────────────────────────────────────────── */
function switchView(viewName) {{
  var scView = document.getElementById('view-scenarios');
  var termView = document.getElementById('view-terminal');
  var scTab = document.getElementById('tab-scenarios');
  var termTab = document.getElementById('tab-terminal');

  if (viewName === 'terminal') {{
    scView.style.display = 'none';
    termView.style.display = 'block';
    scTab.classList.remove('active');
    termTab.classList.add('active');
  }} else {{
    scView.style.display = 'block';
    termView.style.display = 'none';
    scTab.classList.add('active');
    termTab.classList.remove('active');
  }}
}}

/* ─── ACCORDION TOGGLES ────────────────────────────────────── */
function toggleFeature(featId) {{
  var body = document.getElementById(featId + '-body');
  var arr = document.getElementById(featId + '-arr');
  if (body) {{
    body.classList.toggle('collapsed');
    if (arr) arr.classList.toggle('open');
  }}
}}

function toggleScenario(scId) {{
  var body = document.getElementById(scId + '-body');
  var arr = document.getElementById(scId + '-arr');
  if (body) {{
    body.classList.toggle('collapsed');
    if (arr) arr.classList.toggle('open');
  }}
}}

function toggleStepDetails(detailId, btn) {{
  var el = document.getElementById(detailId);
  if (!el) return;
  var isHidden = window.getComputedStyle(el).display === 'none';
  el.style.display = isHidden ? 'block' : 'none';
  if (btn) {{
    btn.classList.toggle('open', isHidden);
  }}
}}

/* ─── BULK EXPAND / COLLAPSE ───────────────────────────────── */
var allExpanded = false;
function toggleAllAccordions() {{
  allExpanded = !allExpanded;
  var btn = document.getElementById('btn-toggle-all');
  if (btn) {{
    btn.innerHTML = allExpanded ? '📁 Collapse All' : '📂 Expand All';
  }}
  document.querySelectorAll('.ft-body').forEach(function(el) {{
    el.classList.toggle('collapsed', !allExpanded);
  }});
  document.querySelectorAll('.ft-arr').forEach(function(el) {{
    el.classList.toggle('open', allExpanded);
  }});
  document.querySelectorAll('.sc-body').forEach(function(el) {{
    el.classList.toggle('collapsed', !allExpanded);
  }});
  document.querySelectorAll('.sc-circle-btn').forEach(function(el) {{
    el.classList.toggle('open', allExpanded);
  }});
  showToast(allExpanded ? 'All features & scenarios expanded' : 'All collapsed');
}}

/* ─── SCROLL & JUMP HELPERS ────────────────────────────────── */
function scrollToFeature(featId) {{
  var target = document.getElementById(featId);
  if (!target) return;
  var fb = target.querySelector('.ft-body');
  var fa = target.querySelector('.ft-arr');
  if (fb && fb.classList.contains('collapsed')) {{
    fb.classList.remove('collapsed');
    if (fa) fa.classList.add('open');
  }}
  target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  target.classList.add('highlighted');
  setTimeout(function() {{ target.classList.remove('highlighted'); }}, 1600);
}}

function scrollToScenario(scId) {{
  var target = document.getElementById(scId);
  if (!target) return;

  // Ensure parent feature is expanded
  var feat = target.closest('.feature-card');
  if (feat) {{
    var fb = feat.querySelector('.ft-body');
    var fa = feat.querySelector('.ft-arr');
    if (fb && fb.classList.contains('collapsed')) {{
      fb.classList.remove('collapsed');
      if (fa) fa.classList.add('open');
    }}
  }}

  // Ensure scenario itself is expanded
  var scBody = document.getElementById(scId + '-body');
  var scArr = document.getElementById(scId + '-arr');
  if (scBody && scBody.classList.contains('collapsed')) {{
    scBody.classList.remove('collapsed');
    if (scArr) scArr.classList.add('open');
  }}

  target.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  target.classList.add('highlighted');
  setTimeout(function() {{
    target.classList.remove('highlighted');
  }}, 1600);
}}

function jumpToFirstFailure() {{
  var firstFail = document.querySelector('.scenario-failed');
  if (!firstFail) {{
    showToast('✓ All tests passed! No failed scenarios found.');
    return;
  }}
  var feat = firstFail.closest('.feature-card');
  if (feat) {{
    var fb = feat.querySelector('.ft-body');
    var fa = feat.querySelector('.ft-arr');
    if (fb && fb.classList.contains('collapsed')) {{
      fb.classList.remove('collapsed');
      if (fa) fa.classList.add('open');
    }}
  }}
  var scBody = firstFail.querySelector('.sc-body');
  var scArr = firstFail.querySelector('.sc-circle-btn');
  if (scBody && scBody.classList.contains('collapsed')) {{
    scBody.classList.remove('collapsed');
    if (scArr) scArr.classList.add('open');
  }}

  firstFail.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  firstFail.classList.add('highlighted');
  var scName = firstFail.querySelector('.sc-title') ? firstFail.querySelector('.sc-title').innerText : 'Failed Scenario';
  showToast('⚡ Jumped to failure: ' + scName);
  setTimeout(function() {{
    firstFail.classList.remove('highlighted');
  }}, 2000);
}}

/* ─── SEARCH & FILTERING ───────────────────────────────────── */
var currentStatusFilter = 'all';

function filterByStatus(status, btn) {{
  currentStatusFilter = status;

  // Sync all matching filter buttons
  document.querySelectorAll('.filter-btn-group .f-pill').forEach(function(b) {{
    b.classList.remove('active');
  }});
  var targetBtn = document.getElementById('btn-filter-' + status);
  if (targetBtn) targetBtn.classList.add('active');
  if (btn && btn.classList) btn.classList.add('active');

  applyFilters();
  showToast('Showing ' + status.toUpperCase() + ' scenarios');
}}

function handleSearch(query) {{
  applyFilters();
}}

function applyFilters() {{
  var query = (document.getElementById('scenario-search').value || '').toLowerCase().trim();

  // Filter monitor cards
  document.querySelectorAll('.mon-card').forEach(function(card) {{
    var text = card.textContent.toLowerCase();
    var matchQuery = !query || text.indexOf(query) !== -1;
    var matchStatus = (currentStatusFilter === 'all') || card.classList.contains('mon-' + currentStatusFilter);
    card.style.display = (matchQuery && matchStatus) ? 'flex' : 'none';
  }});

  // Filter scenario cards in details
  document.querySelectorAll('.scenario-card').forEach(function(sc) {{
    var text = sc.textContent.toLowerCase();
    var matchQuery = !query || text.indexOf(query) !== -1;
    var matchStatus = (currentStatusFilter === 'all') || sc.classList.contains('scenario-' + currentStatusFilter);
    sc.style.display = (matchQuery && matchStatus) ? '' : 'none';
  }});
}}

/* ─── EXECUTIVE SUMMARY CLIPBOARD ──────────────────────────── */
function copyExecutiveSummary() {{
  var summaryText = [
    '========================================',
    'AcSys ERP BDD AUTOMATION EXECUTION REPORT',
    '========================================',
    'Report Title : ' + document.title,
    'Pass Rate    : ' + TEST_METRICS.passRate + '%',
    'Fail Rate    : ' + TEST_METRICS.failRate + '%',
    'Skip Rate    : ' + TEST_METRICS.skipRate + '%',
    'Scenarios    : ' + TEST_METRICS.totalScenarios + ' Total | ' + TEST_METRICS.passedScenarios + ' Passed | ' + TEST_METRICS.failedScenarios + ' Failed | ' + TEST_METRICS.skippedScenarios + ' Skipped',
    'Steps        : ' + TEST_METRICS.totalSteps + ' Total | ' + TEST_METRICS.passedSteps + ' Passed | ' + TEST_METRICS.failedSteps + ' Failed | ' + TEST_METRICS.skippedSteps + ' Skipped (' + TEST_METRICS.stepPassRate + '% Pass)',
    'Duration     : ' + TEST_METRICS.totalDuration,
    'Status       : ' + (TEST_METRICS.failedScenarios === 0 ? 'ALL TESTS PASSED' : 'TESTS FAILED - ACTION REQUIRED'),
    '========================================'
  ].join('\\n');

  if (navigator.clipboard) {{
    navigator.clipboard.writeText(summaryText).then(function() {{
      showToast('📋 Executive Summary copied to clipboard!');
    }}).catch(function() {{
      showToast('Clipboard access denied');
    }});
  }}
}}

/* ─── LIGHTBOX MODAL ───────────────────────────────────────── */
function openLightbox(url) {{
  var modal = document.getElementById('lightbox');
  var img = document.getElementById('lightbox-img');
  img.src = url;
  modal.classList.add('active');
}}

function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}

/* ─── UTILITIES ────────────────────────────────────────────── */
function copyText(btn, text) {{
  navigator.clipboard.writeText(text).then(function() {{
    var orig = btn.innerText;
    btn.innerText = '✓ Copied!';
    setTimeout(function() {{ btn.innerText = orig; }}, 1800);
  }}).catch(function() {{
    alert('Failed to copy');
  }});
}}

function copyTerminal() {{
  var text = document.getElementById('term-text').innerText;
  navigator.clipboard.writeText(text).then(function() {{
    showToast('Terminal output copied to clipboard!');
  }});
}}

function downloadLog() {{
  var text = document.getElementById('term-text').innerText;
  var blob = new Blob([text], {{ type: 'text/plain;charset=utf-8' }});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'behave_execution_terminal.log';
  a.click();
}}

function toggleTermFullscreen() {{
  var win = document.querySelector('.terminal-window');
  if (!document.fullscreenElement) {{
    win.requestFullscreen().catch(function(){{}});
  }} else {{
    document.exitFullscreen().catch(function(){{}});
  }}
}}

// Keyboard shortcuts: 'F' = jump to first failure, '/' = search input
document.addEventListener('keydown', function(e) {{
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.key === 'f' || e.key === 'F') {{
    e.preventDefault();
    jumpToFirstFailure();
  }} else if (e.key === '/') {{
    e.preventDefault();
    var s = document.getElementById('scenario-search');
    if (s) {{ s.focus(); s.select(); }}
  }}
}});

// Auto-expand failed scenarios and their parent features on page load
window.addEventListener('DOMContentLoaded', function() {{
  document.querySelectorAll('.scenario-failed').forEach(function(sc) {{
    var body = sc.querySelector('.sc-body');
    var arr = sc.querySelector('.sc-circle-btn');
    if (body) body.classList.remove('collapsed');
    if (arr) arr.classList.add('open');

    // Auto-expand parent feature card so failure is immediately visible
    var feat = sc.closest('.feature-card');
    if (feat) {{
      var fb = feat.querySelector('.ft-body');
      var fa = feat.querySelector('.ft-arr');
      if (fb) fb.classList.remove('collapsed');
      if (fa) fa.classList.add('open');
    }}
  }});
}});
</script>

</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)

    print("[REPORT] HTML saved: " + output_file)
    return output_file


# ═══════════════════════════════════════════════════════════════
# COMMAND LINE ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <json_file> [output.html] [label]")
        sys.exit(1)

    json_in  = sys.argv[1]
    html_out = sys.argv[2] if len(sys.argv) > 2 else json_in.replace(".json", ".html")
    label    = sys.argv[3] if len(sys.argv) > 3 else ""

    result = generate_html_report(json_in, html_out, label)
    if result:
        print("Done: " + result)
    else:
        print("Report generation failed!")
        sys.exit(1)
