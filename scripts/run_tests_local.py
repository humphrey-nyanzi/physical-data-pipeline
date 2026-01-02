"""Lightweight local test runner for cleaning tests (works without pytest).

Runs the simple test functions in `tests/test_cleaning.py` and reports pass/fail.
"""

import importlib
import sys
import os

# Ensure project root is on sys.path so 'tests' package is importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

mod = importlib.import_module("tests.test_cleaning")

tests = [
    mod.test_normalize_clubs,
    mod.test_compute_derived_metrics,
    mod.test_drop_sparse_columns,
]

failed = []
for t in tests:
    try:
        t()
        print(f"PASS: {t.__name__}")
    except AssertionError as e:
        print(f"FAIL: {t.__name__}: {e}")
        failed.append((t.__name__, str(e)))
    except Exception as e:
        print(f"ERROR: {t.__name__}: {e}")
        failed.append((t.__name__, str(e)))

if failed:
    print(f"{len(failed)} tests failed.")
    sys.exit(1)
else:
    print("All tests passed.")
    sys.exit(0)
