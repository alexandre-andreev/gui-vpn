#!/usr/bin/env bash
# install.sh — install awg-gui PolicyKit policy and helper script.
#
# Usage:
#   sudo bash install.sh
#
# What it does:
#   1. Copies awg-gui-helper to /usr/local/lib/awg-gui/ (mode 0755, owned root)
#   2. Copies org.awg-gui.policy to /usr/share/polkit-1/actions/
#
# After installation the application will request the admin password once per
# session (~5 min cache) when performing privileged VPN operations.

set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "This script must be run as root: sudo bash install.sh" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing helper script to /usr/local/lib/awg-gui/"
install -d /usr/local/lib/awg-gui
install -m 0755 -o root -g root \
    "$SCRIPT_DIR/policy/awg-gui-helper" \
    /usr/local/lib/awg-gui/awg-gui-helper

echo "==> Installing PolicyKit policy to /usr/share/polkit-1/actions/"
install -m 0644 -o root -g root \
    "$SCRIPT_DIR/policy/org.awg-gui.policy" \
    /usr/share/polkit-1/actions/org.awg-gui.policy

echo ""
echo "Installation complete."
echo "Run 'awg-gui' (after 'pip install -e .') to start the application."
