# Hastings Chess v1.0.0 native packaging repair

27 September 2026. Source branch `repair/tcl-tk-portability`; native [build and published-Mac audit run #25](https://github.com/HastingsChess/HastingsChess/actions/runs/36345674867).

## Windows

The previous Windows ZIP was a PyInstaller one-folder build. Its `_internal/_tcl_data/init.tcl`, `_internal/_tk_data/tk.tcl`, Tcl/Tk DLLs and engine were present in the published ZIP, but the failure screenshot's Tcl search paths did not include `_internal`. The executable therefore could not see its required companion folder in that launch. The evidence does not establish whether extraction, copying, security software or another condition made the folder unavailable on that user's machine. It does establish the distribution's avoidable dependence on retaining the entire sibling tree.

The repaired Windows build is a single-file PyInstaller executable inside a ZIP with the unchanged player guide. Python, Tcl/Tk data and DLLs, Fairy-Stockfish, variant configuration and assets are embedded in that executable and extracted by its bootloader at launch. Its smoke tests assert that `TCL_LIBRARY` and `TK_LIBRARY` point at the bootloader's own `_tcl_data` and `_tk_data`, and that `init.tcl` and `tk.tcl` exist there.

A native Windows Server 2022 x64 runner passed **99 automated tests**. The build script extracted its own final ZIP to a path with spaces, ran from an unrelated working directory, removed Python from `PATH`, poisoned inherited Python/Tcl/Tk search paths, and ran packaged engine/Tk and visible GUI smoke modes. Those checks include Fairy-Stockfish UCI, Hastings variant/Housecarl mapping, a level-3 legal move, ratings and Replay. This is direct execution of the packaged EXE on Windows. It is not a personal clean Windows machine test. The corrected ZIP was downloaded and passed CRC and content checks. `Hastings.Chess.v1.0.0.Windows.zip` SHA-256: `619c90bf404c9729e03a9145bdce1ce09b3dce9061916f11ba5828b2844da6dc`.

## macOS Apple Silicon and Intel

Both existing public v1.0.0 ZIPs were downloaded anew on matching native macOS 15 runners, extracted to paths containing spaces, and run with a deliberately clean environment lacking Python, Tcl/Tk, Homebrew and developer search paths. **Both published assets passed** engine/Tk and visible GUI smoke, Fairy-Stockfish architecture checks, Tcl/Tk resource checks, internal symlink checks, `otool` checks against Homebrew and developer paths, and `codesign --verify --deep`. The existing macOS assets therefore do not need replacement for this Tcl/Tk repair.

Fresh arm64 and Intel build candidates also passed **99 automated tests each** and equivalent ZIP-extraction, clean-environment engine/GUI smoke checks. These are direct native execution tests on hosted Mac runners, not physical personal Mac/Finder launch tests. The apps are locally/ad-hoc signed, not Developer ID signed or notarised. Quarantine and Gatekeeper behaviour for an ordinary internet download remains unverified and may require Finder's Open approval; a guaranteed unprompted double-click launch cannot be claimed without signing/notarisation.

The existing published macOS ZIP checksums remain: Apple Silicon `c17fd33f789ceca706f60ddfca245e67b35c1c3d17f486a2d6a2e710a5326170`; Intel `1c5f9c64a8b3d71f0927fda06578a9c3146764a6b550ff8c8228c0afba0ffb01`.

## Scope and remaining checks

Only packaging configuration, native scripts, smoke assertions, related tests and technical documentation changed. Hastings rules, hybrid engine planning, difficulty settings, Elo, Replay and public-facing humour were not altered. Source headless tests passed locally (84); the native Windows and both Mac build jobs passed 99 each.

A separate personal Windows machine should download the replacement ZIP, extract it and launch the EXE. Apple Silicon and Intel users should likewise test ordinary Finder launch after download; Gatekeeper prompts remain possible. The CI runners cannot establish behaviour on every Windows installation or Apple security policy.
