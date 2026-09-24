# Hastings Chess

**Fairy chess. Now with added random catastrophes!**

## Play

For a Windows portable build, unzip `HastingsChess-Windows-x64.zip`, open the `HastingsChess` folder, and double-click `HastingsChess.exe`. No Python or chess engine is needed **in a successfully built ZIP**. Choose a side or computer versus computer, set search depth (1–4), and press **New battle**. Click a piece and a highlighted destination. Use **Save** for a variant-aware JSON replay, and **Open replay** to inspect each charge action and Norman bonus move. **Simulate** runs seed-reproducible games in the background and exports detailed JSON, including the full replays. A 60-full-move limit is classified as unfinished.

The custom canvas renders an axe head for each Saxon housecarl. The SVG reference is included in `assets/dane_axe.svg`. Flip, undo, promotion choice, replay navigation and the event log are available. Save before quitting if you want to retain a game.

## Strength and limitations

The opponent is labelled **custom alpha-beta**, with bounded iterative deepening, capture ordering, a transposition cache, position evaluation, charge chance preview and joint search of Norman bonus actions. Its tactical strength is modest. Fairy-Stockfish is **not bundled or invoked**: its configurable variants cannot express this random compulsory multi-piece push and multiple Black actions through UCI settings, and a validated hybrid integration was not completed. The program works offline using only Python's standard library inside the packaged EXE. No Fairy-Stockfish licence or binary is included.

The search is most useful at depth 2–3. Depth 4 can take several seconds. Simulation uses a quick depth-1 configuration by default, so its outcomes measure these bots only. The GUI does not offer sound or detailed charge animation; instead its chronicle steps through each forced action. Repetition and insufficient-material draws are not adjudicated. Imported replay JSON is treated as a position chronicle; it validates the board alphabet/length but does not prove each historical action was legal.

## Developer build

From the `HastingsChess` directory, `python -m unittest -v tests` runs the rules/controller tests, `python app.py` starts the UI on a machine with a display, and `python simulate.py --games 20 --seed 42 --limit 60 --output batch.json` runs self-play. No external runtime packages are required for source execution except a Python installation with Tk.

The included `.github/workflows/windows-portable.yml` is a Windows x64 CI workflow. Put this `HastingsChess` directory at the root of a GitHub repository and run the workflow on Windows; it tests, packages, launches a smoke-test process, and uploads a portable ZIP. `build_windows.ps1` performs the equivalent local Windows build. Both use PyInstaller 6.22.3. Neither has been executed in this Linux workspace. A clean Windows click-through and DPI/resize test remain release gates.
