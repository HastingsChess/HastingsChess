# Windows Python/Tkinter launch fix

## The new screenshot's error

`ModuleNotFoundError: No module named 'tkinter'` appears at line 4 of `app.py` **before the application starts or tries to launch Fairy-Stockfish**. It is unrelated to the earlier Fairy-Stockfish configuration-path fix.

The previous `START_HASTINGS.bat` unconditionally chose `py -3`, which can select a different, newer Python installation from the interpreter used to launch the earlier working GUI. Some Windows Python installations omit the optional `tcl/tk and IDLE` component.

## Launcher change

`START_HASTINGS.bat` now checks `py -3.15` through `py -3.10`, in descending order, and then `python` from PATH. It runs a separate `import tkinter` probe for each and chooses the first supported interpreter that succeeds. It displays which interpreter it selected. `RUN_TESTS.bat` makes the same choice so the GUI tests use an interpreter with Tkinter.

The Python source, Fairy-Stockfish engine, configuration-path fix, gameplay rules, saved replays, and simulations remain unchanged.

## If the launcher still reports no suitable interpreter

Use the official **Windows installer from python.org** to repair/modify your Python installation. Under the optional features, enable **tcl/tk and IDLE**. Make sure you install a full Python 3.10+ distribution, not an embeddable/minimal package. Then reopen `START_HASTINGS.bat`.

For diagnosis, in Command Prompt run:

```bat
py -0p
py -3 -m tkinter
```

The first lists Python installations known to the launcher. The second should open a small Tk window if the default interpreter has Tk installed. It may still fail if the default interpreter lacks Tk; in that case try a specific installed version reported by `py -0p`, e.g. `py -3.12 -m tkinter`.

## Verification limit

This fix is targeted at interpreter selection. Windows execution must be confirmed on your machine. Once the GUI opens, choose Fairy-Stockfish hybrid and make an ordinary move to verify that the earlier Fairy-Stockfish configuration-path fix also works on Windows.
