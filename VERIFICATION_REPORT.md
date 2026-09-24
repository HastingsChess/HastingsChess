# Hastings Chess — release verification

24 September 2026. Source commit [`4c470f9`](https://github.com/dfntrecords-ui/Hastings-Chess/commit/4c470f9c32be6acf7bb8ccdcbfc7f40414b67f05), native workflow [run #36004577528](https://github.com/dfntrecords-ui/Hastings-Chess/actions/runs/36004577528). The existing Python/Fairy-Stockfish hybrid, charge and knight/pawn counterattack were retained. This release changes the public difficulty ladder, removes the pre-release unrestricted bonus mode, migrates initial Norman Elo to 1066, and bundles the Rules window with the requested title and “Also Axes” text.

| Verification | Windows x64 | macOS Apple Silicon |
| --- | --- | --- |
| Native runner | Windows Server 2022, x64 | macOS 15, arm64 |
| Applicable automated suite | 94 passed | 94 passed |
| Packaged app | `HastingsChess.exe` in portable folder | `Hastings Chess.app` |
| Packaged engine and visible Tk GUI smoke | Passed | Passed |
| UCI, Hastings variant, Housecarl mapping, legal AI move | Passed | Passed |
| Rules window and bundled text, new title | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Public 1–10 selector, clean Elo 1066/1066 | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Replay-only evaluation bar and post-game analysis | Passed in packaged GUI smoke | Passed in packaged GUI smoke |
| Path with spaces and unrelated working directory | Passed | Passed |
| Bundled engine architecture | Windows x64 executable | `file` and `lipo` confirmed arm64 |
| Distributable | `HastingsChess_Windows_Portable.zip` | `HastingsChess_macOS_arm64.zip` |
| SHA-256 of distributable ZIP | `4563dba97fc33306ed4a0fc86786d6a41a001317ae8f9c3a569690ce957ca7bb` | `320c95833e5810372755bba55e51ba961e9c7b86e0810eede018b0621875451e` |

The native jobs executed the real Fairy-Stockfish tests and packaged application smoke checks. The GUI smoke opened a visible Tk window, checked all difficulty options and both initial ratings, opened and reopened the bundled Rules text, played a human move and waited for the bundled Fairy opponent, verified that the live evaluation bar remained absent, completed a rated game, checked persisted Norman Elo and fixed Saxon Elo, and opened Replay for the post-game evaluation bar. The scripts require explicit engine and GUI success markers before publishing an artifact. Windows copied the app to a path with spaces and launched it with the working directory elsewhere. macOS copied the `.app` to a path with spaces and ran its executable from `/`.

The public Level 4 uses precisely the former Level 1 configuration and deterministic best-move selection. `Benchmark Level 3` retains the former Level 3 resources, numeric beam width, endpoint count and search behaviour. The lower levels choose among already legal, Hastings-evaluated alternatives with increasing tolerance. A deterministic candidate-selection smoke found cumulative sample scores of -5480, -4200, -1620 and 0 centipawns for public Levels 1, 2, 3 and 4 over 80 sampled move numbers. This confirms the selection mechanism, **not** calibrated human strength or statistically established game performance. The previous 100-game figures supplied by the user were not rerun for this release.

The local Linux environment ran 80 headless tests with the real Fairy-Stockfish engine. It has no display, so GUI tests were executed on the native runners. The updated Windows artifact has **not** been personally tested by the user on their Windows machine; the previous portable version was. The macOS artifact has **not** been tested on a personal Mac or launched through Finder. The native `.app` passed its runner launch and local ad-hoc `codesign --verify --deep`; it is not Developer ID signed or notarised. Gatekeeper behaviour after internet download remains unverified. The bundled one-folder runtime was inspected, but no separate clean Windows computer without Python was available.

Known limits remain: threefold repetition and insufficient-material draws are not adjudicated; historical old-rule replays may be viewed as chronicles but are not analysed under the current rules; explicitly unrestricted bonus-mode replays are rejected; bounded hybrid search can miss tactics. The app does not expose evaluation or mate information during live play. Batch simulations never affect local ratings.
