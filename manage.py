#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Compatibility shim for missing pkgutil functions in Python 3.14+
import importlib.util
import os
import pkgutil

if not hasattr(pkgutil, 'find_loader'):
    def _find_loader(name):
        spec = importlib.util.find_spec(name)
        return spec.loader if spec is not None else None
    pkgutil.find_loader = _find_loader

if not hasattr(pkgutil, 'iter_modules'):
    def _iter_modules(path=None, prefix=""):
        if path is None:
            path = sys.path
        for entry in path:
            if not os.path.isdir(entry):
                continue
            for name in os.listdir(entry):
                if name.startswith('.'):
                    continue
                full = os.path.join(entry, name)
                if os.path.isdir(full) and os.path.isfile(os.path.join(full, '__init__.py')):
                    yield (None, prefix + name, True)
                elif name.endswith('.py'):
                    mod_name = name[:-3]
                    yield (None, prefix + mod_name, False)
    pkgutil.iter_modules = _iter_modules

if not hasattr(pkgutil, 'walk_packages'):
    pkgutil.walk_packages = pkgutil.iter_modules



def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
