#!/usr/bin/env bash
set -euo pipefail

# Simple installer for Margarita macOS binary.
# Edit VERSION at the top of this file before running to control which release is installed.
# Usage:
#   bash install-macos.sh owner/repo [asset-url-or-name]
# Examples:
#   bash install-macos.sh Banyango/margarita
#   bash install-macos.sh Banyango/margarita margarita-macos-0.3.3
#   bash install-macos.sh Banyango/margarita https://github.com/owner/repo/releases/download/v0.3.3/margarita-macos-0.3.3

VERSION=0.3.4
REPO=Banyango/margarita
ASSET_ARG=margarita-macos-$VERSION

# Try to infer repo from git remote if not provided
if [ -z "$REPO" ]; then
  url=$(git config --get remote.origin.url 2>/dev/null || true)
  if [ -n "$url" ]; then
    if [[ $url =~ git@github.com:(.+)/(.+)\.git ]]; then
      REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    elif [[ $url =~ https://github.com/(.+)/(.+)\.git ]]; then
      REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    fi
  fi
fi

if [ -z "$REPO" ]; then
  echo "Usage: $0 owner/repo [asset-url-or-name]"
  echo "Please provide the GitHub repository (owner/repo) or set GITHUB_REPOSITORY env var."
  exit 1
fi

if [ -z "$VERSION" ]; then
  echo "Please set VERSION at the top of this script before running."
  exit 1
fi

if [[ "$ASSET_ARG" =~ ^https?:// ]]; then
  DOWNLOAD_URL="$ASSET_ARG"
else
  if [ -n "$ASSET_ARG" ]; then
    ASSET_NAME="$ASSET_ARG"
  else
    ASSET_NAME="margarita-macos-$VERSION"
  fi
  DOWNLOAD_URL="https://github.com/$REPO/releases/download/v$VERSION/$ASSET_NAME"
fi

echo "Downloading: $DOWNLOAD_URL"

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
if ! curl -fSL --progress-bar "$DOWNLOAD_URL" -o "$tmpfile"; then
  echo "Failed to download: $DOWNLOAD_URL"
  echo "If the asset name differs, pass it as the second argument or set VERSION in this script."
  exit 1
fi

chmod +x "$tmpfile"

# Prefer system /usr/local/bin if writable, else install to $HOME/.local/bin
INSTALL_DIR="/usr/local/bin"
if [ ! -w "$INSTALL_DIR" ]; then
  INSTALL_DIR="$HOME/.local/bin"
  mkdir -p "$INSTALL_DIR"
fi

TARGET_PATH="$INSTALL_DIR/margarita"

if [ -w "$INSTALL_DIR" ]; then
  mv "$tmpfile" "$TARGET_PATH"
else
  sudo mv "$tmpfile" "$TARGET_PATH"
fi

chmod +x "$TARGET_PATH"

echo "Installed margarita -> $TARGET_PATH"

if ! echo ":$PATH:" | grep -q ":$INSTALL_DIR:"; then
  echo
  echo "Note: $INSTALL_DIR is not in your PATH for this session. Add it to your profile, e.g.:"
  echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
  echo
fi

echo "Done. Run 'margarita --help' to verify."
