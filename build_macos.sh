#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
builddir=""
stage=""
cleanup() {
  status=$?
  if [[ $status -ne 0 ]]; then
    echo "Native build failed (exit $status)" >&2
    log="$HOME/Library/Application Support/Hastings Chess/launch-errors.log"
    if [[ -f "$log" ]]; then tail -80 "$log" >&2; fi
  fi
  if [[ -n "$stage" ]]; then rm -rf "$stage"; fi
  if [[ -n "$builddir" ]]; then rm -rf "$builddir"; fi
}
trap cleanup EXIT
if [[ "$(uname -s)" != Darwin ]]; then echo 'Build the macOS application on macOS.' >&2; exit 1; fi
machine="$(uname -m)"
case "$machine" in arm64) target=apple-silicon;; x86_64) target=x86-64;; *) echo 'Unsupported Mac CPU' >&2; exit 1;; esac
python3 -c 'import sys, tkinter; assert sys.version_info >= (3,10)'
python3 -m pip install --disable-pip-version-check 'pyinstaller==6.22.3'
builddir="$(mktemp -d)"
tar -xzf engine/Fairy-Stockfish-fairy_sf_14.tar.gz -C "$builddir"
source_dir="$(find "$builddir" -maxdepth 1 -type d -name 'fairy-stockfish-*' -print -quit)"
test -n "$source_dir"
# The pinned Fairy-Stockfish release predates Xcode 16: its obsolete Clang
# pass-manager switch is rejected by current Apple compilers. Patch only the
# temporary build copy, leaving the corresponding source archive untouched.
python3 - "$source_dir/src/Makefile" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
flag = '-fexperimental-new-pass-manager'
assert flag in s, 'Unexpected Fairy-Stockfish Makefile version'
p.write_text(s.replace(flag, ''))
PY
make -C "$source_dir/src" -j 2 build ARCH="$target" COMP=clang
cp "$source_dir/src/stockfish" "engine/fairy-stockfish-macos-$machine"
chmod +x "engine/fairy-stockfish-macos-$machine"
file "engine/fairy-stockfish-macos-$machine"
if ! lipo -archs "engine/fairy-stockfish-macos-$machine" | grep -qw "$machine"; then
  echo "Compiled engine is not $machine" >&2; exit 1
fi
python3 -m unittest -q tests test_engine test_features test_resources test_gui
python3 -m PyInstaller --clean --noconfirm hastings.spec
codesign --verify --deep --verbose=2 'dist/Hastings Chess.app'
python3 - <<'PY'
from pathlib import Path
import subprocess
app=Path('dist/Hastings Chess.app').resolve()
frameworks=app/'Contents'/'Frameworks'
resources=app/'Contents'/'Resources'
for name in ('_tcl_data/init.tcl','_tk_data/tk.tcl','_tk_data/ttk/altTheme.tcl','engine/hastings.ini'):
    assert (resources/name).is_file(), f'Missing bundled resource: {name}'
for link in app.rglob('*'):
    if link.is_symlink():
        assert link.resolve().is_relative_to(app), f'External bundle symlink: {link}'
tkinter=next(frameworks.rglob('_tkinter*.so'))
for binary in (app/'Contents/MacOS/HastingsChess', tkinter,
               frameworks/'libtcl8.6.dylib', frameworks/'libtk8.6.dylib'):
    assert binary.is_file(), f'Missing bundled runtime: {binary}'
    result=subprocess.check_output(['otool','-L',str(binary)],text=True)
    for path in ('/opt/homebrew/','/usr/local/','/Users/runner/',
                 '/Library/Frameworks/Python.framework/',
                 '/System/Library/Frameworks/Tcl.framework/',
                 '/System/Library/Frameworks/Tk.framework/'):
        assert path not in result, f'External runtime dependency in {binary}: {result}'
PY
stage="$(mktemp -d "${TMPDIR:-/tmp}/Hastings Chess Portable.XXXXXXXX")"
ditto -c -k --sequesterRsrc --keepParent 'dist/Hastings Chess.app' "dist/HastingsChess_macOS_${machine}.zip"
guide='Honestly, you should probably read this at some point.txt'
/usr/bin/zip -j -q "dist/HastingsChess_macOS_${machine}.zip" "$guide"
unzip -p "dist/HastingsChess_macOS_${machine}.zip" "$guide" | cmp - "$guide"
ditto -x -k "dist/HastingsChess_macOS_${machine}.zip" "$stage"
codesign --verify --deep --verbose=2 "$stage/Hastings Chess.app"
test -f "$stage/Hastings Chess.app/Contents/Resources/_tcl_data/init.tcl"
test -f "$stage/Hastings Chess.app/Contents/Resources/_tk_data/tk.tcl"
mkdir "$stage/clean-home"
(
  cd /
  env -i HOME="$stage/clean-home" USER="${USER:-runner}" LOGNAME="${USER:-runner}" \
    TMPDIR="${TMPDIR:-/tmp}" PATH='/usr/bin:/bin:/usr/sbin:/sbin' LANG=en_US.UTF-8 \
    HASTINGS_SMOKE_MARKER="$stage/smoke-result.txt" \
    "$stage/Hastings Chess.app/Contents/MacOS/HastingsChess" --smoke-test
  test "$(cat "$stage/smoke-result.txt")" = engine-ok
  rm "$stage/smoke-result.txt"
  env -i HOME="$stage/clean-home" USER="${USER:-runner}" LOGNAME="${USER:-runner}" \
    TMPDIR="${TMPDIR:-/tmp}" PATH='/usr/bin:/bin:/usr/sbin:/sbin' LANG=en_US.UTF-8 \
    HASTINGS_SMOKE_MARKER="$stage/smoke-result.txt" \
    "$stage/Hastings Chess.app/Contents/MacOS/HastingsChess" --gui-smoke
  test "$(cat "$stage/smoke-result.txt")" = gui-ok
)
rm -rf "$stage"
stage=""
echo "Built and smoke-tested dist/HastingsChess_macOS_${machine}.zip"
