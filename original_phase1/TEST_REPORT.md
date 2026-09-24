# Test report — 23 September 2026

Environment: Linux x86-64, Python 3.12, no DISPLAY, Windows runtime, Wine, Windows runner or Fairy-Stockfish binary.

Passed locally:

- Ten targeted `unittest` cases for initial army, housecarl movement/attacks, charge ordering/obstructions, promotion, castling/en passant, displaced rook rights, one-roll hazard, two consecutive same-knight bonus actions, custom search and replay schema.
- Python compilation of all source files.
- Three seed-reproducible self-play examples (seed 42–44, 32-full-move cap, quick level 1) produced JSON replays. A further 20-game run (seed 230926, 40-full-move cap) yielded 8 White checkmates and 12 unfinished games. All 20 replay histories retained exactly one king per side; all games reached a charge. These are weak-bot outcomes, not competitive balance estimates.

Not tested: actual Tk window and click controls, narrow or high-DPI layout, Windows EXE build/launch, clean Windows machine, Fairy-Stockfish handshake or engine strength comparison. The attached ZIP is a **source and automated build package, not a Windows executable**. A Windows CI runner or Windows machine is required to generate and verify the portable EXE. The CI workflow's launch smoke check checks process survival, not GUI control functionality.

Known limitations: no Fairy-Stockfish integration; no repetition or insufficient-material draws; replay imports are structural rather than cryptographically or rules verified; weak AI at low depth; no sound or timed charge animation; simulation can take a long time at large counts; the batch output includes full per-game replays and can become large.
