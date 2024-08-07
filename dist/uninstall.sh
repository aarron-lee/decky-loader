#!/bin/sh

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

echo "Uninstalling Steam Deck Plugin Loader..."

USER_DIR="$(getent passwd $SUDO_USER | cut -d: -f6)"
HOMEBREW_FOLDER="${USER_DIR}/.unofficial_homebrew"

# Disable and remove services
sudo systemctl disable --now unofficial_plugin_loader.service > /dev/null
sudo rm -f "${USER_DIR}/.config/systemd/user/unofficial_plugin_loader.service"
sudo rm -f "/etc/systemd/system/unofficial_plugin_loader.service"

# Remove temporary folder if it exists from the install process
rm -rf "/tmp/plugin_loader"

# Cleanup services folder
sudo rm "${HOMEBREW_FOLDER}/services/UnofficialPluginLoader"

