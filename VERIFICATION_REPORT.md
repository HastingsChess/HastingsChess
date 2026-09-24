# Hastings Chess — difficulty release verification

24 September 2026. Source commit [`3a1407b`](https://github.com/dfntrecords-ui/Hastings-Chess/commit/3a1407bd561c8baa5dbfaf5b88bca07986374689), native workflow [run #36009251673](https://github.com/dfntrecords-ui/Hastings-Chess/actions/runs/36009251673). This pass changed only the public difficulty curve, explicit simulation preset metadata, a pre-existing simulation CLI argument error, and the final full stop in the main-window title. The approved Rules text, rating system, replay analysis, Hastings rules and Python/Fairy-Stockfish architecture were retained.

## Difficulty calibration

- **New Level 4 exactly preserves the preceding release's Level 1:** 0.10-second default budget, MultiPV 2, 250 recorded base nodes, numeric search level 1 (including compound beam and endpoint limits), 250-centipawn selection tolerance, and the same deterministic seed stream. This was compared directly with the preceding release's actual `hybrid.py` using the real Fairy-Stockfish process in five positions: opening, Black ordinary move, pre-charge preview, Norman response and Game 5 bonus-first rescue. All five first actions matched with fixed node budgets.
- **Benchmark Level 3 remains unchanged:** old numeric level 3, 1.6 seconds, MultiPV 5 and 10,000 recorded base nodes; the old compound widths, endpoint behaviour and charge preview use the same numeric search level. It remains an explicit simulation/testing preset, separate from public Level 3.
- **Public Levels 1–3** use progressively more search time and progressively less tolerance for inferior legal, Hastings-evaluated candidates. They consider six, five and four Fairy MultiPV candidates respectively, with 700, 430 and 300-centipawn selection tolerances. The same controlled selection applies to ordinary moves and complete Norman compound paths. Legal move validation and forced rescues remain authoritative in Python.
- **Public Levels 4–10** increase strictly in time, MultiPV count, node budget and numeric compound search level. Level 10 retains the previous maximum: 12 seconds, MultiPV 14, 200,000 recorded base nodes and numeric compound level 10.
- A small 11-position real-engine smoke comparison, using fixed engine nodes and a deeper reference analysis, recorded total candidate-score loss of 2058, 1872, 1615 and 1007 centipawns for Levels 1, 2, 3 and 4 respectively, with best-move counts of 1, 1, 3 and 5. This is a diagnostic sample, **not** a human-strength calibration or statistically reliable match result. Human playtesting is needed to establish whether Level 1 feels beginner-friendly.
- Simulation output identifies `difficulty_preset: public` versus `difficulty_preset: benchmark_level_3` and retains the explicit level value. Both command-line entries were smoke-tested. The earlier 100-game balance figures were not rerun or used to rebalance the game.

## Native packages

| Verification | Windows x64 | macOS Apple Silicon |
| --- | --- | --- |
| Native runner | Windows Server 2022, x64 | macOS 15, arm64 |
| Applicable automated suite | 96 passed | 96 passed |
| Packaged app | `HastingsChess.exe` in portable folder | `Hastings Chess.app` |
| Packaged engine and visible Tk GUI smoke | Passed | Passed |
| UCI, Hastings variant, Housecarl mapping, legal AI move | Passed | Passed |
| Ten-level selector, clean Elo 1066/1066, Rules window | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Exact title ending `Also Axes.` | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Replay-only evaluation and rated Elo persistence | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Path with spaces and unrelated working directory | Passed | Passed |
| Bundled engine architecture | Windows x64 executable | `file` and `lipo` confirmed arm64 |
| Distributable | `HastingsChess_Windows_Portable.zip` | `HastingsChess_macOS_arm64.zip` |
| SHA-256 of distributable ZIP | `430fd0ffbcee4cd5bda5b317f8566abab6f97ec3e9238a4b8609da82c4adf249` | `ba988e1a139f4b4ab13732fdba24a81dccf268fa7c4681ce9c1a2dfe0f78a529` |

The packaged GUI smoke opens the Rules window, verifies the fresh Elo display and all ten selector choices, makes a human move and waits for a bundled Fairy response, confirms the absence of live analysis, finishes a rated game and verifies persistent Norman rating changes, then enters and exits post-game Replay. The native build scripts require positive engine and GUI smoke markers before archiving. The Windows job copies the folder to a path with spaces and launches it from an unrelated working directory; the macOS job similarly copies the `.app` and launches its executable from `/`.

The local Linux environment ran 82 headless tests with real Fairy-Stockfish. It has no display; the GUI tests ran on native CI. The **new** Windows artifact has not yet been personally tested on the user's machine, although its predecessor was. The macOS artifact has not been tested on personal Mac hardware or launched through Finder. The native `.app` passed local/ad-hoc `codesign --verify --deep`, but it is not Developer ID signed or notarised. Gatekeeper behaviour after an internet download remains unverified. A separate clean Windows machine without Python was not available.

Known limits are unchanged: threefold repetition and insufficient-material draws are not adjudicated; historical old-rule replays are not analysed under the present rules; explicitly unrestricted bonus-mode replays are rejected; bounded hybrid search can miss tactics. Evaluations and mate information remain hidden during live play. Batch simulations never update local ratings.
