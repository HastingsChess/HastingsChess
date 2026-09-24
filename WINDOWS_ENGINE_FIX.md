# Windows engine startup fix

The initial Phase 3 app launched on Windows but sometimes reported “Engine did not load the Hastings custom-piece variant”. The official bundled engine binary was valid, so the Repair engine button's checksum check did not correct it.

**Cause (reproduced):** Fairy-Stockfish 14's `load` command splits its configuration path at spaces; when Hastings Chess was extracted to a directory such as `C:\Users\Name\My Games\Hastings Chess`, the engine failed to load `hastings.ini`.

**Fix:** `engine_uci.py` now starts Fairy-Stockfish from its own `engine` working directory with the argument `load hastings.ini`. This has been regression-tested using the actual bundled Linux engine in a directory containing spaces, alongside the 78 passing rules, real-engine and virtual-display GUI tests. Windows execution itself remains to be tested on your PC.

## How to use

Extract the **entire** fixed ZIP, ideally to a new folder so you retain the previous release as a backup. Double-click `START_HASTINGS.bat`. Select Fairy-Stockfish hybrid and make an ordinary move with the Saxons; the computer should respond without the variant error. You do not need to click Repair engine unless the engine executable itself is missing or corrupted.

If you prefer keeping the existing folder, replace **only** its `engine_uci.py` with the updated one from this ZIP, then close and reopen the application. The rules, replays, two counterattack options and bundled engine are unchanged.

`RUN_TESTS.bat` runs the automated tests on Windows and will print any remaining platform-specific errors.
