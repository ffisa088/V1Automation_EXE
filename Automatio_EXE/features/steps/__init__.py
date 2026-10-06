import importlib.util
import os
import sys

_steps_dir = os.path.dirname(__file__)

for folder_name in sorted(os.listdir(_steps_dir)):
    folder_path = os.path.join(_steps_dir, folder_name)
    if not os.path.isdir(folder_path):
        continue
    for filename in sorted(os.listdir(folder_path)):
        if not filename.endswith('.py') or filename == '__init__.py':
            continue
        full_path = os.path.join(folder_path, filename)
        module_name = f"behave_steps_{folder_name}_{os.path.splitext(filename)[0]}"
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            if attr_name.startswith('__'):
                continue
            globals()[attr_name] = getattr(module, attr_name)
