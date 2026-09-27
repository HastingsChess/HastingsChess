"""Assertions used by native packaged smoke tests, never by live play."""
import os
import sys
from pathlib import Path


def verify_bundled_tk():
    if not getattr(sys, 'frozen', False):
        return
    root = Path(sys._MEIPASS)
    for folder, file, variable in (
        ('_tcl_data', 'init.tcl', 'TCL_LIBRARY'),
        ('_tk_data', 'tk.tcl', 'TK_LIBRARY'),
    ):
        expected = root / folder
        assert (expected / file).is_file(), f'Missing bundled {file}: {expected}'
        actual = os.environ.get(variable)
        assert actual and Path(actual).resolve() == expected.resolve(), (
            f'{variable} does not point to bundled {folder}: {actual!r}'
        )
