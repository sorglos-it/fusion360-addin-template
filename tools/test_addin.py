# -*- coding: utf-8 -*-
"""Compatibility: the check moved to apps/desktop/tests/test_addin.py.

This file only forwards, so commands written against the old path keep
working - for example in projects built from this template:

    python ../fusion360-addin-template/tools/test_addin.py --path MyAddIn

Same arguments, same output, same exit code.
"""
import os
import sys
import runpy

TARGET = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'apps', 'desktop', 'tests', 'test_addin.py')

sys.argv[0] = TARGET
runpy.run_path(TARGET, run_name='__main__')
