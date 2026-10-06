import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
screenshots = root / 'screenshots'
screenshots.mkdir(exist_ok=True)

feature = root / 'features' / 'temp_fail.feature'
step = root / 'features' / 'steps' / 'temp_fail_steps.py'

feature.write_text(
    "Feature: Temp failing screenshot\n\n"
    "  Scenario: Should fail\n"
    "    Given I open the login page\n"
    "    Then I fail intentionally\n",
    encoding='utf-8'
)

step.write_text(
    "from behave import then\n\n"
    "@then('I fail intentionally')\n"
    "def fail_intentionally(context):\n"
    "    raise AssertionError('intentional failure')\n",
    encoding='utf-8'
)

try:
    result = subprocess.run(
        [sys.executable, '-m', 'behave', str(feature), '--no-capture', '-f', 'plain'],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    print('EXIT', result.returncode)
    print(result.stdout)
    print(result.stderr)
    files = sorted(screenshots.glob('FAIL_*.png'))
    print('SCREENSHOTS_FOUND', len(files))
    for f in files:
        print('FILE', f)
finally:
    if feature.exists():
        feature.unlink()
    if step.exists():
        step.unlink()
