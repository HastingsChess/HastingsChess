# Hastings Chess — final packaging verification

24 September 2026. The private native build [run #12](https://github.com/dfntrecords-ui/Hastings-Chess/actions/runs/36032589122) checked out isolated branch `release-build-2026-09-24` at commit `19209342c1c1833d5285e3f066479987d0be1e71`. The repository's `main` branch was not changed for this pass. The branch exists only to run native packaging CI.

## Scope

- The main-window title remains `Hastings Chess: Catastrophic Military Stupidity Simulator. Also Axes.`
- The short in-game Rules text now explains that one Norman pawn can use both sequential bonus actions to advance one square each time, when legal. The prohibition on a single bonus double advance, en passant, and promotion remains explicit.
- The visible Simulate button and Norman knight counter were removed from the game window. Simulation code, command-line simulation tools, and internal knight analytics remain.
- The approved long-form player text was extracted from the supplied DOCX in paragraph/table order into `Honestly, you should probably read this at some point.txt` without editorial rewriting. Its UTF-8 SHA-256 is `1812cc732fa27bed7dbee87ed11e49cbd9b1d7ca75613f667ab393e9a2cb91e1`. A `.gitattributes` rule preserves LF bytes on Windows checkout. Both platform packages include the same bytes.
- Game rules, AI difficulty configuration, rating calculation, replay analysis, and the Python/Fairy-Stockfish hybrid were not changed in this pass.

## Native verification

| Check | Windows x64 | macOS Apple Silicon | macOS Intel (secondary) |
| --- | --- | --- | --- |
| Native job | Windows Server 2022, x64: passed | macOS 15, arm64: passed | macOS 15 Intel, x86_64: passed |
| Applicable automated tests | 98 passed | 98 passed | 98 passed |
| Packaged application | `HastingsChess.exe` produced | `Hastings Chess.app` produced | `Hastings Chess.app` produced |
| Bundled Fairy-Stockfish and Hastings variant | Packaged engine smoke passed | Packaged engine smoke passed | Packaged engine smoke passed |
| Visible Tk GUI smoke | Passed | Passed | Passed |
| Housecarl mapping and legal level-3 AI response | Packaged smoke passed | Packaged smoke passed | Packaged smoke passed |
| Replay-only analysis and Elo smoke | Passed | Passed | Passed |
| App moved to path with spaces, unrelated working directory | Passed | Passed | Passed |
| Bundled engine architecture | Windows x64 | `file` confirmed arm64 | `file` confirmed x86_64 |
| Exact player guide bytes and ZIP integrity | Verified after download | Verified after download | Verified after download |
| ZIP SHA-256 | `0e1aeb8dbaebdfcc4bee4b4959ad49583085d840b8c7d79ad21232b89c1e81a0` | `c17fd33f789ceca706f60ddfca245e67b35c1c3d17f486a2d6a2e710a5326170` | `1c5f9c64a8b3d71f0927fda06578a9c3146764a6b550ff8c8228c0afba0ffb01` |

The native build scripts require positive packaged engine and GUI smoke markers before archiving. Their smoke checks open the GUI and Rules window, verify the title, ratings, difficulty choices and hidden live evaluation, make a human move and obtain a bundled Fairy-Stockfish response, then exercise a completed game's Elo and Replay. The Windows folder and both Mac apps were copied to locations containing spaces and run from unrelated working directories. The Mac builds verified the bundled engine architecture; the apps passed local/ad-hoc `codesign --verify --deep` on their respective runners. The long-form text sits beside `HastingsChess.exe` in the Windows portable folder and at the ZIP root beside `Hastings Chess.app` on Mac.

The local Linux source environment passed 83 headless tests using real Fairy-Stockfish. Native runners passed 98 tests each, including display-capable GUI tests. The downloaded ZIPs were inspected for structure, CRC integrity, and exact guide bytes. No physical end-user Windows or Mac computer was available for this final pass. The Mac apps were not Developer ID signed or notarised, and Finder/Gatekeeper behaviour after an internet download was not tested. A separate clean Windows computer without Python was not available; the packaged runner smoke used the bundled executable and engine from the moved folder.

Known game limits inherited from the authoritative application remain: threefold repetition and insufficient-material draws are not adjudicated; historical old-rule replays are not analysed under the present rules; explicitly unrestricted bonus-mode replays are rejected; bounded hybrid search can miss tactics. Live play never displays replay evaluation or mate information, and batch simulations never update local ratings.
