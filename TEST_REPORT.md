# Phase 3 development and test report — 23 September 2026

## Changes and audit

The phase-two hybrid architecture was retained: Python owns legality, turn control and replay; a real Fairy-Stockfish UCI process searches ordinary positions using the custom `h:K` variant. The original phase-one source remains in `original_phase1/`. The phase-two reports in `reports/previous_rules/` describe superseded housecarl and knight-only rules; they are not evidence for this revision.

The source and five supplied historical games were audited. Original Game 1 exposed the illegal housecarl charge capture two squares ahead. The charge code now stops before that pawn if it cannot be pushed; the unit identity map and atomic per-unit update avoid duplicate/disappearing pieces. The new housecarl's ordinary move generation and attack detection both use exactly one-square king geometry without royal square-safety limits. Charge probabilities are conditional and the move-30 guarantee is tested. Promotion, king-safety exemption, push and multiple-unit interactions have targeted tests.

The recent Game 5 replay was reconstructed immediately before move 29. The charge leaves Black in check with zero legal *ordinary* moves. The only legal default bonus action is `f8f7`, a pawn capturing directly forward. It resolves check, then Black receives its ordinary action and remaining bonus action. The original Game 5 end condition is no longer prematurely applied to that reconstructed position. In unrestricted mode the same position has no legal ordinary or bonus response and remains checkmate, as expected because unrestricted bonus movement is ordinary movement.

The default Norman bonus is now knight or special pawn; experimental unrestricted bonuses are selectable before a new game. Both allow the same eligible piece twice. Every action is checked for king safety, and saved v3 replays record the ruleset and rescue phase. Historical v1/v2 files and batch formats remain viewable as position chronicles; old moves are not replayed under new legality.

The hybrid's Norman controller searches bounded sequences of ordinary and bonus actions, including the exceptional bonus-first ordering. It calls Fairy-Stockfish at representable endpoints; incompatible charge positions use the explicit Python bridge. Engine move legality is checked against Python before application. This is a heuristic bounded beam, not a complete game solver or proof of optimal counterattack. Charge chance preview and knight reserve remain implemented. The custom fallback is separate and labelled.

## Executed here

- `python3 -m unittest -q tests test_engine`: **65 passed** after the new rules, including real Fairy-Stockfish handshake, legal-move differential checks, UCI search, Game 5 rescue search, unrestricted compound endpoint search and saved replay checks.
- The official bundled Linux Fairy-Stockfish v14 was actually launched and contributed to ordinary move selection. Engine calls were recorded in the result JSON. The bundled Windows x64 binary is the pinned official release and its hash is in `engine/manifest.json`; it has **not** been executed in Windows here.
- Four matched-seed `fairy` self-play games per bonus mode, seeds 78–81, level 1, 1200 nodes/search, capped at White move 36: each set had 4 unfinished games, all four reaching a charge at moves 26, 27, 30, 30. The default mode made **759** real engine calls and averaged **0.5** Norman knights at charge; unrestricted made **780** calls and also averaged **0.5**. These tiny runs cannot estimate balance.
- Four matched-seed `light` versus `light` games in the default mode, capped at 36, also ended unfinished, averaged **2.0** Norman knights at charge, and made **0** Fairy calls. Its timing settings differ from the node-limited Fairy runs, so the knight contrast is not a controlled strength conclusion.
- At level 1, 1200–1500 nodes/search, seeds 42–43, Fairy as White beat light as Black twice before charge; Fairy as Black beat light as White twice before charge. This is a small tactical smoke comparison, not an Elo or statistical demonstration of superiority. Full records, timestamps, material and positional charge deltas, engine calls and per-game replays are in `reports/phase3_*.json`.
- Game 5's three response actions were also executed from the recorded board using the real hybrid search. The first returned `f8f7`; the later Black actions were legal. This particular line produced a Python-proven White mate without an engine endpoint call, as the detailed UCI tests elsewhere verify actual invocation.
- Python bytecode compilation and replay JSON structural validation pass. The earlier phase-two GUI build had ten native Tk control tests and screenshots under a virtual display (`reports/gui_tests.txt`, PNGs), before this ruleset selector was added.

## Remaining release verification

This current container has no Windows runtime. Its display socket policy prevented launching the local virtual X server for the updated Tk UI, so the *new* ruleset selector and Game 5 GUI click tests were added but **not executed** here. On Windows, double-click `RUN_TESTS.bat` to run the 65 headless tests and the twelve Tk tests, then launch `START_HASTINGS.bat` for a manual click-through at both rulesets. The Windows engine executable, launcher, Tk layout, process startup and operating-system specific behaviour require that validation. The source application and real Linux engine path are tested; no Windows executable is claimed.

Known limitations: no threefold repetition or insufficient-material adjudication; replay imports validate structure rather than cryptographic provenance or complete historic move legality; preview/beam pruning can miss tactics; short simulations should not be used as balance evidence. Large simulations include full replays and can produce large files.

## Windows custom-variant startup hotfix (23 September 2026)

After the initial package failed on a Windows installation with “Engine did not load the Hastings custom-piece variant”, the precise configuration-path bug was reproduced on Linux. Fairy-Stockfish v14's CLI `load` handler tokenizes a full config path containing spaces (even when correctly passed as a single subprocess argument); it prints “Unable to open file ...” and starts with its built-in variants, omitting `hastings`. The old engine repair function only verified the official executable's SHA-256, so it could not resolve that application-code bug.

`engine_uci.py` now starts the engine with `cwd=engine/` and `load hastings.ini`, avoiding whitespace in the filename supplied to Fairy-Stockfish. The executable retains its absolute path; Python correctly quotes that for Windows process creation. A new `test_engine_launch_from_directory_with_spaces` regression copied the actual bundled executable/config to a temporary folder with multiple spaces and verified the Hastings handshake and a real-engine search.

**Executed after this fix:** `xvfb-run -a python -m unittest -v tests test_engine test_gui` — **78 tests passed** including all 12 Tk GUI tests, the new whitespace-path test and real Fairy-Stockfish regression tests. This environment still does **not** run Windows executables; Windows startup must be verified on the user's machine. No rule, search or UI feature changes were made in this hotfix.
