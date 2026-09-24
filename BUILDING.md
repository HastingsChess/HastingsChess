# Rebuilding Hastings Chess

Build on each target operating system. PyInstaller does not produce a Windows executable or a macOS application from this Linux workspace. The source `app.py` continues to work with Python 3.10+ and Tkinter. The build requires Python/Tkinter and build tools **only on the build machine**; end users of a completed portable build need none.

## Windows x64

With Python 3.10+ including Tkinter on the Windows build machine, run `powershell -ExecutionPolicy Bypass -File .\build_windows.ps1` from this source directory. The script installs pinned PyInstaller, executes the rules, real Fairy-Stockfish, replay and Tk tests, creates a one-folder `dist\HastingsChess\HastingsChess.exe`, copies it to a folder containing spaces, launches that packaged executable from an unrelated working directory with `--smoke-test` (real engine + variant + Tk + AI move) and `--gui-smoke` (visible window, human and AI move, replay bar and isolated Elo persistence), and writes `dist\HastingsChess_Windows_Portable.zip`. The source's original `START_HASTINGS.bat` still works independently.

The package embeds the official pinned Windows Fairy-Stockfish v14 executable, the exact variant configuration, GPL licence, corresponding source archive, assets, Tcl/Tk and Python runtime. In packaged mode the old Repair Engine control is labelled **Check engine**: it tests the embedded copy and reports failures, with instructions to re-extract the ZIP. It does not claim to modify a packaged program.

## Apple Silicon or Intel macOS

Run `bash ./build_macos.sh` on the corresponding Mac. It compiles the included pinned Fairy-Stockfish v14 source with `ARCH=apple-silicon` or `ARCH=x86-64`, checks the native architecture, verifies real UCI integration and Tk tests on that Mac, builds `dist/Hastings Chess.app` with PyInstaller, checks its code signature, copies it to a path containing spaces, and launches its actual executable in engine/Tk and visible-GUI smoke modes. It archives the `.app` with `ditto` as `dist/HastingsChess_macOS_arm64.zip` or `_x86_64.zip`. Apple Silicon is the priority; Intel is an independent native build, not an unverified universal binary.

The app is not Apple Developer signed or notarised. PyInstaller may add an ad-hoc signature required to run its native arm64 code; that is **not** Developer ID signing. A downloaded ZIP may trigger Gatekeeper. On first launch use Finder's Open context menu and approve the prompt, subject to your macOS version and policies. No Homebrew or Terminal command is needed by a recipient of a successfully built app.

## Native CI

`.github/workflows/native-builds.yml` has Windows x64, macOS arm64 and macOS Intel jobs, with native smoke checks before publishing each ZIP as an artifact. Put the contents of this source folder at repository root and run the workflow manually. A passing workflow is evidence of that runner's build/test, not physical Mac or arbitrary Windows machine coverage.

All paths to assets, variant and engine are relative to the packaged application's `__file__` resource root. The engine itself is started by absolute path with `cwd` set to its resource directory and `load hastings.ini`, preserving the working fix for directories with spaces. Ratings live under per-user app data, outside the executable folder, so moving the app or running from a removable drive does not affect persistence.

When a packaged launch fails before the interface can show an error, the PyInstaller runtime hook records platform, architecture, resource/engine/config paths and the traceback in `launch-errors.log` under the same per-user Hastings Chess application-data folder. Normal successful runs do not write debug output.

This Linux environment has run source-level tests and the real Linux engine only. See `VERIFICATION_REPORT.md` for exact outcomes and outstanding native-build checks.
