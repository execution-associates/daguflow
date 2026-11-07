#!/bin/sh
# Download one dagu release binary, verified against the release's checksums.txt.
#   tools/fetch-dagu.sh v2.24.0 /opt/dagu/v2.24.0   ->  /opt/dagu/v2.24.0/dagu
set -eu
version="${1:?usage: fetch-dagu.sh vX.Y.Z DEST_DIR}"
dest="${2:?usage: fetch-dagu.sh vX.Y.Z DEST_DIR}"
v="${version#v}"
case "$(uname -m)" in
  x86_64) arch=amd64 ;;
  aarch64|arm64) arch=arm64 ;;
  *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;;
esac
asset="dagu_${v}_linux_${arch}.tar.gz"
base="https://github.com/dagucloud/dagu/releases/download/v${v}"
[ -x "$dest/dagu" ] && exit 0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/$asset" "$base/$asset"
curl -fsSL -o "$tmp/checksums.txt" "$base/checksums.txt"
(cd "$tmp" && grep " $asset\$" checksums.txt | sha256sum -c - >/dev/null)
mkdir -p "$dest"
tar -xzf "$tmp/$asset" -C "$tmp" dagu
install -m 0755 "$tmp/dagu" "$dest/dagu"
