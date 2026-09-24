# Hastings Chess Phase 4 — native verification

24 September 2026. The authoritative Phase 4 archive was committed to the private `dfntrecords-ui/Hastings-Chess` repository without altering Hastings game rules or the Fairy-Stockfish hybrid planner. Level 3 remains 1.6 seconds, MultiPV 5 and 10,000 fixed nodes. Native packaging run [#4](https://github.com/dfntrecords-ui/Hastings-Chess/actions/runs/35982182405), commit `d3cfd6c08c7ea0c321cf749f2199f82a13b8b1fb`, passed on all three target runners.

| Check | Windows x64 | macOS Apple Silicon | macOS Intel |
| --- | --- | --- | --- |
| Native runner | Windows Server 2022, x64 | macOS 15, arm64 | macOS 15, x86_64 |
| Full applicable suite | 93 tests passed | 93 tests passed | 93 tests passed |
| Native package produced | `HastingsChess.exe` folder ZIP | `Hastings Chess.app` ZIP | `Hastings Chess.app` ZIP |
| Packaged engine/Tk smoke | Passed with explicit success markers | Passed with explicit success markers | Passed with explicit success markers |
| Fairy UCI and Hastings variant | Passed | Passed | Passed |
| Housecarl legal-move mapping | Passed | Passed | Passed |
| Level-3 AI legal move | Passed | Passed | Passed |
| Visible Tk GUI initialised | Passed | Passed | Passed |
| Moved folder, path containing spaces and unrelated working directory | Passed | Passed | Passed |
| Engine architecture | Bundled Windows x64 executable | `file`/`lipo` confirmed arm64 | `file`/`lipo` confirmed x86_64 |
| Runtime bundled | Python 3.12 DLL, Tcl/Tk DLLs and scripts | Python.framework and Tk in `.app` | Python.framework and Tk in `.app` |
| Artifact | `HastingsChess_Windows_Portable.zip` | `HastingsChess_macOS_arm64.zip` | `HastingsChess_macOS_x86_64.zip` |
| SHA-256 of inner distributable ZIP | `9b738568e3602858de8ab1b37fcd322f102112535f4ad997755bfc97e27cf723` | `35824749de339137fe983964ffd20a6793ef585e95bf726b17c27142a7508a96` | `338923061d7038d84f92fc5047e85941f07eeb7a9a55e2443c16a16821eba937` |

The packaged smoke opened a visible 1100×800 Tk window, checked the board and ten difficulty choices, made a human move, waited for the bundled Fairy-based opponent's response, confirmed the absence of a live evaluation bar, exercised local Norman Elo persistence and fixed Saxon 1066 in an isolated test profile, opened completed-game Replay, confirmed the evaluation bar and returned to live view. The tests also cover Game 5 rescue, both counterattack modes, replay-only analysis, ratings, variant mapping and resource discovery. The executable smoke verified bundled piece assets and `hastings.ini`, actual Fairy search, a legal level-3 move and Housecarl move mapping. The tests and application did not silently use the lightweight fallback in these checks.

On macOS, `codesign --verify --deep` passed for PyInstaller's local/ad-hoc signature. **No Apple Developer ID signing or notarisation was performed.** Gatekeeper handling of an internet-downloaded ZIP, double-click launch on a personal Mac, and visual layout on a user's monitor were not tested. The native runners launched the packaged binaries through their build scripts, not through Finder or Explorer. The Windows runner had Python installed for building, but the resulting one-folder ZIP contains its own Python/Tk runtime and Fairy executable; the portable process was launched from a copied path with spaces and an unrelated working directory. A separate clean Windows computer without Python was not available for testing.

Known game/analysis limits remain: no threefold repetition or insufficient-material adjudication; historical old-rule replays cannot safely be evaluated under revised rules; compound charge estimates are bounded and can miss tactics. Difficulty labels are not calibrated human Elo estimates. Batch simulations never update the local ratings. The new 100-game level-3 and level-1 figures supplied by the user (51–40–8–1 and 50–45–5 respectively) were not rerun in this packaging pass. No full-game level-10 performance claim is made.

Initial native runs revealed and resolved two packaging defects: the pinned Fairy-Stockfish source included an obsolete Clang flag rejected by Xcode 16, and the original Windows smoke script failed to wait reliably for a GUI executable and copied Tk incompletely. The final run requires explicit engine and GUI success markers before archiving. Game logic, hybrid search, charge probabilities and level-3 parameters were not changed.
