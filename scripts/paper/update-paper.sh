#!/usr/bin/env bash
# Install or update Paper Desktop (paper.design) on Linux from the official
# AppImage "latest" URL. Idempotent: replaces the AppImage only when the
# remote ETag (MD5 of the file) changes.
#
# Usage: update-paper.sh [--prefix DIR] [--bindir DIR] [--install-timer] [--no-desktop] [--status]
#
# Official latest URLs:
#   https://download.paper.design/linux/appImage/x64
#   https://download.paper.design/linux/appImage/arm64
# Version is in the Content-Disposition filename; the ETag is the file MD5.
# The AppImage has no AppImageUpdate info. ToDesktop may self-update only
# while the GUI is running as an AppImage (electron-updater against
# https://download.todesktop.com/2601167vjw8xe).
#
# Do not install a "paper" shim on PATH: on Arch, /usr/bin/paper is libpaper.

set -euo pipefail

PREFIX="${PAPER_PREFIX:-}"
BINDIR="${PAPER_BINDIR:-${HOME}/.local/bin}"
INSTALL_TIMER=0
INSTALL_DESKTOP=1
STATUS_ONLY=0

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="${2:?}" ; shift 2 ;;
    --bindir) BINDIR="${2:?}" ; shift 2 ;;
    --install-timer) INSTALL_TIMER=1 ; shift ;;
    --no-desktop) INSTALL_DESKTOP=0 ; shift ;;
    --status) STATUS_ONLY=1 ; shift ;;
    -h|--help) usage 0 ;;
    *) echo "unknown argument: $1" >&2 ; usage 1 ;;
  esac
done

default_prefix() {
  if [ -n "${PREFIX}" ]; then
    return
  fi
  if [ -x "${HOME}/opt/paper/paper.AppImage" ]; then
    PREFIX="${HOME}/opt/paper"
  else
    PREFIX="${HOME}/.local/opt/paper"
  fi
}

arch_asset() {
  case "$(uname -m)" in
    x86_64) echo x64 ;;
    aarch64|arm64) echo arm64 ;;
    *) echo "unsupported architecture: $(uname -m)" >&2 ; exit 1 ;;
  esac
}

parse_header() {
  # $1 = header name, case-insensitive; reads headers on stdin
  local name="$1"
  awk -v name="$(printf '%s' "$name" | tr 'A-Z' 'a-z')" '
    BEGIN { IGNORECASE=1 }
    tolower($1) == name ":" {
      sub(/^[^:]*:[[:space:]]*/, "")
      sub(/\r$/, "")
      print
      exit
    }
  '
}

version_from_filename() {
  local filename="$1"
  if printf '%s' "$filename" | grep -Eq 'paper-desktop-([0-9]+\.[0-9]+\.[0-9]+)'; then
    printf '%s' "$filename" | sed -n 's/.*paper-desktop-\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p'
  elif printf '%s' "$filename" | grep -Eq '[0-9]+\.[0-9]+\.[0-9]+'; then
    printf '%s' "$filename" | sed -n 's/.*\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p'
  else
    echo unknown
  fi
}

strip_etag() {
  printf '%s' "$1" | tr -d '"' | sed 's/^W\///'
}

install_icon() {
  local appimage="$1"
  local dest_dir="${HOME}/.local/share/icons"
  local dest="${dest_dir}/paper-desktop.png"
  if [ -f "$dest" ]; then
    return 0
  fi
  local tmp
  tmp="$(mktemp -d)"
  if (cd "$tmp" && "$appimage" --appimage-extract 'usr/share/icons/hicolor/256x256/apps/paper-desktop.png' >/dev/null 2>&1); then
    mkdir -p "$dest_dir"
    cp "$tmp/squashfs-root/usr/share/icons/hicolor/256x256/apps/paper-desktop.png" "$dest"
  fi
  rm -rf "$tmp"
}

install_desktop_entry() {
  local appimage="$1"
  local apps_dir="${HOME}/.local/share/applications"
  local desktop="${apps_dir}/paper-desktop.desktop"
  mkdir -p "$apps_dir"
  install_icon "$appimage" || true
  cat > "$desktop" <<DESKTOP
[Desktop Entry]
Name=Paper
Exec=${appimage} --no-sandbox %U
Terminal=false
Type=Application
Icon=paper-desktop
StartupWMClass=Paper
Comment=Paper Desktop
MimeType=x-scheme-handler/paper;x-scheme-handler/paper-dev;
Categories=Utility;
DESKTOP
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$apps_dir" >/dev/null 2>&1 || true
  fi
}

install_timer() {
  local script="$1"
  local unit_dir="${HOME}/.config/systemd/user"
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl not found; skipped systemd user timer" >&2
    return 1
  fi
  if ! systemctl --user is-system-running >/dev/null 2>&1; then
    echo "systemd --user is not available; skipped timer (install units in ${unit_dir} only if you enable a user session later)" >&2
    return 1
  fi
  mkdir -p "$unit_dir"
  cat > "${unit_dir}/paper-update.service" <<UNIT
[Unit]
Description=Update Paper Desktop AppImage
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=${script}
UNIT
  cat > "${unit_dir}/paper-update.timer" <<UNIT
[Unit]
Description=Daily Paper Desktop AppImage update

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=1h

[Install]
WantedBy=timers.target
UNIT
  systemctl --user daemon-reload
  systemctl --user enable --now paper-update.timer
  echo "enabled systemd user timer paper-update.timer (daily)"
}

print_status() {
  local prefix="$1"
  local appimage="${prefix}/paper.AppImage"
  local version_file="${prefix}/version"
  local etag_file="${prefix}/etag"
  echo "prefix:  ${prefix}"
  if [ -e "$appimage" ]; then
    echo "appimage: ${appimage}"
    echo "size:    $(wc -c < "$appimage" | tr -d ' ') bytes"
  else
    echo "appimage: missing"
  fi
  [ -f "$version_file" ] && echo "version: $(cat "$version_file")" || echo "version: unknown"
  [ -f "$etag_file" ] && echo "etag:    $(cat "$etag_file")" || echo "etag:    unknown"
  if command -v paper-desktop >/dev/null 2>&1; then
    echo "path:    $(command -v paper-desktop)"
  else
    echo "path:    paper-desktop not on PATH"
  fi
}

default_prefix
ASSET="$(arch_asset)"
URL="https://download.paper.design/linux/appImage/${ASSET}"
APPIMAGE="${PREFIX}/paper.AppImage"
ETAG_FILE="${PREFIX}/etag"
VERSION_FILE="${PREFIX}/version"
SCRIPT_COPY="${PREFIX}/update-paper.sh"
BIN_LINK="${BINDIR}/paper-desktop"
UPDATER_LINK="${BINDIR}/update-paper"

if [ "$STATUS_ONLY" -eq 1 ]; then
  print_status "$PREFIX"
  exit 0
fi

mkdir -p "$PREFIX" "$BINDIR"

HEADERS="$(curl -fsSI --retry 3 --retry-delay 2 "$URL")"
REMOTE_ETAG="$(printf '%s' "$HEADERS" | parse_header etag | tail -1)"
REMOTE_ETAG="$(strip_etag "$REMOTE_ETAG")"
DISPOSITION="$(printf '%s' "$HEADERS" | parse_header content-disposition | tail -1)"
FILENAME="$(printf '%s' "$DISPOSITION" | sed -n 's/.*filename="\([^"]*\)".*/\1/p')"
[ -n "$FILENAME" ] || FILENAME="paper-desktop.AppImage"
VERSION="$(version_from_filename "$FILENAME")"

if [ -z "$REMOTE_ETAG" ]; then
  echo "failed to read remote ETag from ${URL}" >&2
  exit 1
fi

LOCAL_ETAG=""
if [ -f "$ETAG_FILE" ]; then
  LOCAL_ETAG="$(tr -d '[:space:]' < "$ETAG_FILE")"
elif [ -f "$APPIMAGE" ]; then
  LOCAL_ETAG="$(md5sum "$APPIMAGE" | awk '{print $1}')"
fi

UPDATED=0
if [ "$LOCAL_ETAG" = "$REMOTE_ETAG" ] && [ -x "$APPIMAGE" ]; then
  echo "Paper ${VERSION} already up to date (etag ${REMOTE_ETAG})"
else
  TMP="${APPIMAGE}.part"
  echo "downloading Paper ${VERSION} from ${URL}"
  curl -fL --retry 3 --retry-delay 2 --output "$TMP" "$URL"
  ACTUAL_MD5="$(md5sum "$TMP" | awk '{print $1}')"
  if [ "$ACTUAL_MD5" != "$REMOTE_ETAG" ]; then
    echo "downloaded file MD5 ${ACTUAL_MD5} does not match ETag ${REMOTE_ETAG}" >&2
    rm -f "$TMP"
    exit 1
  fi
  chmod 0755 "$TMP"
  mv -f "$TMP" "$APPIMAGE"
  UPDATED=1
  echo "installed Paper ${VERSION} to ${APPIMAGE}"
fi

printf '%s\n' "$REMOTE_ETAG" > "$ETAG_FILE"
printf '%s\n' "$VERSION" > "$VERSION_FILE"

# Keep a copy of this script next to the AppImage, then link it on PATH.
if [ -f "$0" ]; then
  if [ "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")" != "$(readlink -f "$SCRIPT_COPY" 2>/dev/null || echo "")" ]; then
    cp -f "$0" "$SCRIPT_COPY"
    chmod 0755 "$SCRIPT_COPY"
  fi
fi
ln -sfn "$APPIMAGE" "$BIN_LINK"
if [ -f "$SCRIPT_COPY" ]; then
  ln -sfn "$SCRIPT_COPY" "$UPDATER_LINK"
fi

if [ "$INSTALL_DESKTOP" -eq 1 ]; then
  install_desktop_entry "$APPIMAGE"
fi

if [ "$INSTALL_TIMER" -eq 1 ]; then
  install_timer "$UPDATER_LINK"
fi

if [ "$UPDATED" -eq 1 ]; then
  echo "Paper ${VERSION} ready at ${BIN_LINK}"
else
  echo "links and metadata refreshed for Paper ${VERSION}"
fi
