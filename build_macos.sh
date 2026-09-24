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
stage="$(mktemp -d "${TMPDIR:-/tmp}/Hastings Chess Portable.XXXXXXXX")"
ditto 'dist/Hastings Chess.app' "$stage/Hastings Chess.app"
(
  cd /
  HASTINGS_SMOKE_MARKER="$stage/smoke-result.txt" "$stage/Hastings Chess.app/Contents/MacOS/HastingsChess" --smoke-test
  test "$(cat "$stage/smoke-result.txt")" = engine-ok
  rm "$stage/smoke-result.txt"
  HASTINGS_SMOKE_MARKER="$stage/smoke-result.txt" "$stage/Hastings Chess.app/Contents/MacOS/HastingsChess" --gui-smoke
  test "$(cat "$stage/smoke-result.txt")" = gui-ok
)
rm -rf "$stage"
stage=""
ditto -c -k --sequesterRsrc --keepParent 'dist/Hastings Chess.app' "dist/HastingsChess_macOS_${machine}.zip"
guide='Honestly, you should probably read this at some point.txt'
/usr/bin/zip -j -q "dist/HastingsChess_macOS_${machine}.zip" "$guide"
unzip -p "dist/HastingsChess_macOS_${machine}.zip" "$guide" | cmp - "$guide"
echo "Built and smoke-tested dist/HastingsChess_macOS_${machine}.zip"
