#!/usr/bin/env bash
# install.sh — install awg-gui PolicyKit policy, helper script, and system launcher.
#
# Usage:
#   sudo bash install.sh
#
# What it does:
#   1. Copies awg-gui-helper to /usr/local/lib/awg-gui/ (mode 0755, owned root)
#   2. Copies org.awg-gui.policy to /usr/share/polkit-1/actions/
#   3. Creates /usr/local/bin/awg-gui launcher pointing to the venv binary
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

echo "==> Creating system launcher at /usr/local/bin/awg-gui"
VENV_BIN="$SCRIPT_DIR/.venv/bin/awg-gui"
if [[ ! -f "$VENV_BIN" ]]; then
    echo "ERROR: $VENV_BIN not found." >&2
    echo "       Run 'python3 -m venv .venv && .venv/bin/pip install -e .' first." >&2
    exit 1
fi

# The launcher detaches from the terminal when run interactively so the shell
# prompt returns immediately. Autostart and keyboard shortcuts (no tty) exec
# directly. Logs always go to ~/.local/share/awg-gui/awg-gui.log.
cat > /usr/local/bin/awg-gui << LAUNCHER
#!/bin/bash
REAL="$VENV_BIN"
if [ -t 1 ]; then
    nohup "\$REAL" "\$@" </dev/null >/dev/null 2>&1 &
    disown
else
    exec "\$REAL" "\$@"
fi
LAUNCHER
chmod 0755 /usr/local/bin/awg-gui

echo ""
echo "Installation complete."
echo "Run 'awg-gui' to start the application."
echo "Logs: ~/.local/share/awg-gui/awg-gui.log"
