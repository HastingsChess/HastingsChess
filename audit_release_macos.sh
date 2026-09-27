#!/usr/bin/env bash
# Check the already-published v1.0.0 ZIP on the matching native Mac runner.
set -euo pipefail
cd "$(dirname "$0")"
machine="$(uname -m)"
case "$machine" in arm64|x86_64) ;; *) echo "Unsupported Mac CPU: $machine" >&2; exit 1;; esac
stage="$(mktemp -d "${TMPDIR:-/tmp}/Hastings Published Mac Audit.XXXXXXXX")"
trap 'rm -rf "$stage"' EXIT
suffix="$machine"
if [[ "$machine" == x86_64 ]]; then suffix=x86.64; fi
url="https://github.com/HastingsChess/HastingsChess/releases/download/v1.0.0/Hastings.Chess.v1.0.0.macOS.${suffix}.zip"
curl --fail --location --retry 3 --output "$stage/published.zip" "$url"
ditto -x -k "$stage/published.zip" "$stage/extracted"
app="$stage/extracted/Hastings Chess.app"
exe="$app/Contents/MacOS/HastingsChess"
test -x "$exe"
test -f "$app/Contents/Resources/_tcl_data/init.tcl"
test -f "$app/Contents/Resources/_tk_data/tk.tcl"
test -f "$app/Contents/Resources/engine/hastings.ini"
test -x "$app/Contents/Frameworks/engine/fairy-stockfish-macos-$machine"
cmp 'Honestly, you should probably read this at some point.txt' \
  "$stage/extracted/Honestly, you should probably read this at some point.txt"
codesign --verify --deep --verbose=2 "$app"
lipo -archs "$app/Contents/Frameworks/engine/fairy-stockfish-macos-$machine" | grep -qw "$machine"
python3 - "$app" <<'PY'
from pathlib import Path
import subprocess,sys
app=Path(sys.argv[1]).resolve()
for link in app.rglob('*'):
    if link.is_symlink():
        assert link.resolve().is_relative_to(app), f'External bundle symlink: {link}'
frameworks=app/'Contents/Frameworks'
for binary in (app/'Contents/MacOS/HastingsChess', next(frameworks.rglob('_tkinter*.so')),
               frameworks/'libtcl8.6.dylib', frameworks/'libtk8.6.dylib'):
    deps='\n'.join(subprocess.check_output(['otool','-L',str(binary)],text=True).splitlines()[1:])
    for external in ('/opt/homebrew/','/usr/local/','/Users/runner/',
                     '/Library/Frameworks/Python.framework/',
                     '/System/Library/Frameworks/Tcl.framework/',
                     '/System/Library/Frameworks/Tk.framework/'):
        assert external not in deps, f'External dependency in {binary}: {deps}'
PY
mkdir "$stage/clean-home"
for mode in --smoke-test --gui-smoke; do
  marker="$stage/marker"
  (
    cd /
    env -i HOME="$stage/clean-home" USER="${USER:-runner}" LOGNAME="${USER:-runner}" \
      TMPDIR="${TMPDIR:-/tmp}" PATH='/usr/bin:/bin:/usr/sbin:/sbin' LANG=en_US.UTF-8 \
      HASTINGS_SMOKE_MARKER="$marker" "$exe" "$mode"
  )
  if [[ "$mode" == --smoke-test ]]; then test "$(cat "$marker")" = engine-ok
  else test "$(cat "$marker")" = gui-ok; fi
  rm "$marker"
done
echo "Published v1.0.0 macOS ${machine} ZIP: extracted and smoke-tested without external runtimes"
