# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Test runner for More Colors! — executed inside Blender.

Usage::

    blender -b --factory-startup -P Tests/run_tests.py --python-exit-code 1

Discovers and runs all ``test_*.py`` files in the Tests/ directory using
Python's built-in ``unittest`` framework.  No mocking required — tests
have full access to ``bpy``, ``numpy``, and real Blender data.
"""

import sys
import unittest
from pathlib import Path

# ---- sys.path ----------------------------------------------------------------
# Make the add-on package importable so ``from utilities.color_utilities import …``
# works from inside the test files.

_tests_dir = Path(__file__).resolve().parent
_repo_root = _tests_dir.parent
_addon_root = _repo_root / "More_Colors"

for p in (_tests_dir, _repo_root, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

# ---- Run tests ---------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(str(_tests_dir), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)
