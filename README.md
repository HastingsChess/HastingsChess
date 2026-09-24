# Hastings Chess

**Fairy chess. Now with added random catastrophes!**

## Playing

The included Python source runs with `app.py` and Python 3.10+ with Tkinter. On Windows, `START_HASTINGS.bat` probes installed interpreters for Tkinter. A **native portable build** produced by `build_windows.ps1` runs `HastingsChess.exe` without installed Python; a macOS build produced by `build_macos.sh` runs `Hastings Chess.app`. Native builds have to be created and checked on their respective operating systems; this source ZIP does not pretend to contain those unbuilt applications.

Choose a side, **Fairy-Stockfish hybrid** or **Lightweight custom**, difficulty 1–10 (level 3 is the established testing setting), and **Knights + pawns** or **Experimental: any piece** Norman bonuses. Press **New battle**. Click a piece and highlighted destination. Use Save, Open replay, Flip, Undo, Pause, Computer vs computer and Simulate as before. Simulate exports seeded statistics and full replays; its games never affect ratings. Engine errors pause play with a visible diagnosis; no silent switch to the lightweight opponent occurs.

Normans begin at Elo 1100 and change by K=32 after a completed human-playable game. Saxons remain Elo 1066 whatever happens. The ratings are stored in your account's app-data folder. Computer-versus-computer, batch simulations, cancelled and unfinished games do not affect them. Hover over the rating display for the historical explanation. The selected difficulty is remembered between sessions.

After a game ends, choose **Review finished**, or use **Open replay** on a saved completed v3 game. The Black-at-top/White-at-bottom bar and numerical score are visible **only in Replay**; live games show no evaluation or mate warning. White advantage is positive. Each visited replay step is analysed asynchronously and cached. After-charge and Norman bonus positions use the Hastings compound planner; interim positions *inside* a multi-piece charge are labelled provisional. The bar is hidden again on returning to live view. Older v1/v2 replay chronicles remain viewable, but are not analysed using the revised rules.

## Game, engine and limitations

Housecarls move/capture one square in any direction as nonroyal kings; in the compulsory charge they attempt two directly forward without gaining a two-square capture. The Saxon charge probabilities are conditional from White move 20 to certain activation on move 30. A Norman ordinary response and two bonus actions follow; knight/pawn and any-piece modes and Game 5 bonus-first rescue are preserved. `RULE_DECISIONS.md` gives the complete operational rules.

Python owns all Hastings-specific legality, the charge and the compound counterattack. Real Fairy-Stockfish v14 evaluates/searches compatible positions with a custom housecarl definition. A bounded Hastings beam and legality bridge handle special positions. No chess engine gets to overrule Python's move validation. The ten levels increase time, search nodes (for fixed-node runs), candidate count and compound beam/endpoint budget; no uncalibrated human Elo claim is attached to their labels. The hybrid can still miss tactics. Threefold repetition and insufficient-material draws are not adjudicated; the fifty-move rule is.

The official Fairy-Stockfish Windows and Linux binaries, corresponding source and GPL licence are in `engine/`; the macOS build compiles that pinned source for its own processor. The original source snapshot and historical reports are retained. See `BUILDING.md` and `VERIFICATION_REPORT.md` for portable-build status, tests and limitations.
