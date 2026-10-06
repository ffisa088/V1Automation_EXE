from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
steps = root / 'features' / 'steps'
common = steps / 'common'
auth = steps / 'auth'
common.mkdir(exist_ok=True)
auth.mkdir(exist_ok=True)

moves = [
    ('helpers.py', common / 'helpers.py'),
    ('all_steps.py', common / 'all_steps.py'),
    ('login_steps.py', auth / 'login_steps.py'),
]

for src_name, dest in moves:
    src = steps / src_name
    if src.exists() and not dest.exists():
        shutil.move(str(src), str(dest))

for pkg in (common, auth):
    init = pkg / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

print('reorganized')
