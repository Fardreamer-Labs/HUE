# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for utilities/logging.py.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_tests_dir = Path(__file__).resolve().parent
_addon_root = _tests_dir.parent / "HUE"
for p in (_tests_dir, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import utilities.logging as hue_logging
from utilities.logging import debug


class TestDebug(unittest.TestCase):
    def test_suppressed_when_debug_mode_false(self):
        hue_logging.DEBUG_MODE = False
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            debug("should not appear")
            self.assertEqual(mock_out.getvalue(), "")

    def test_prints_when_debug_mode_true(self):
        hue_logging.DEBUG_MODE = True
        try:
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                debug("hello world")
                output = mock_out.getvalue()
                self.assertIn("[HUE Debug]", output)
                self.assertIn("hello world", output)
        finally:
            hue_logging.DEBUG_MODE = False

    def test_prefix_format(self):
        hue_logging.DEBUG_MODE = True
        try:
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                debug("test message")
                self.assertEqual(
                    mock_out.getvalue().strip(), "[HUE Debug] test message"
                )
        finally:
            hue_logging.DEBUG_MODE = False


if __name__ == "__main__":
    unittest.main()
