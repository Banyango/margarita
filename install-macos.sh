#!/usr/bin/env bash
set -euo pipefail

# install-macos.sh
# Usage: ./install-macos.sh [GITHUB_REPOSITORY]
# Installs the latest margarita macOS binary from the GitHub release to /usr/local/bin or Homebrew prefix.

REPO=${1:-${GITHUB_REPOSITORY:-}}

get_repo() {
  if [ -n "$REPO" ]; then
    echo "$REPO"
    return
  fi
  url=$(git config --get remote.origin.url 2>/dev/null || true)
  if [ -z "$url" ]; then
    echo ""
    return
  fi
  if [[ $url =~ git@github.com:(.+)/(.+)\.git ]]; then
    echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    return
  fi
  if [[ $url =~ https://github.com/(.+)/(.+)\.git ]]; then
    echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    return
  fi
  echo ""
}

repo=$(get_repo)
if [ -z "$repo" ]; then
  echo "Could not determine GitHub repository. Pass it as the first argument or set GITHUB_REPOSITORY (owner/repo)."
  exit 1
fi

echo "Using repository: $repo"

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
curl -sL "https://api.github.com/repos/$repo/releases/latest" -o "$tmpfile"

read download_url asset_name < <(python3 - <<PY
import sys, json
j=json.load(open(r"$tmpfile"))
for a in j.get("assets", []):
    n = a.get("name", "")
    if n.startswith("margarita-macos-"):
        print(a.get("browser_download_url"), n)
        sys.exit(0)
sys.exit(1)
PY
) || {
  echo "No macOS asset found in latest release for pattern 'margarita-macos-*'."
  exit 1
}

echo "Found asset: $asset_name"

echo "Downloading $download_url..."
curl -L "$download_url" -o "$asset_name"
chmod +x "$asset_name"

# Choose install dir: prefer Homebrew prefix if available and writable, else /usr/local/bin, else $HOME/.local/bin
install_dir=""
if command -v brew >/dev/null 2>&1; then
  prefix=$(brew --prefix)
  if [ -d "$prefix/bin" ] && [ -w "$prefix/bin" ]; then
    install_dir="$prefix/bin"
  fi
fi

if [ -z "$install_dir" ] && [ -w /usr/local/bin ]; then
  install_dir="/usr/local/bin"
fi

if [ -z "$install_dir" ]; then
  install_dir="$HOME/.local/bin"
  mkdir -p "$install_dir"
fi

if [ -w "$install_dir" ]; then
  mv "$asset_name" "$install_dir/$asset_name"
else
  echo "Need elevated permissions to write to $install_dir. You may be prompted for your password."
  sudo mv "$asset_name" "$install_dir/$asset_name"
fi

# Create symlink
if [ -w "$install_dir" ]; then
  ln -sf "$install_dir/$asset_name" "$install_dir/margarita"
else
  sudo ln -sf "$install_dir/$asset_name" "$install_dir/margarita"
fi


echo "Installed $asset_name -> $install_dir/$asset_name"
echo "Symlink created: $install_dir/margarita"

if ! echo ":$PATH:" | grep -q ":$install_dir:"; then
  echo
  echo "Note: $install_dir is not in your PATH for this session. Add to your shell profile (e.g. ~/.zshrc):"
  echo "  export PATH=\"$install_dir:\$PATH\""
  echo
fi

echo "Done. Run 'margarita --help' to verify."

