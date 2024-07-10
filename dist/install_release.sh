#!/bin/sh

[ "$UID" -eq 0 ] || exec sudo "$0" "$@"

echo "Installing Steam Deck Plugin Loader release..."

USER_DIR="$(getent passwd $SUDO_USER | cut -d: -f6)"
HOMEBREW_FOLDER="${USER_DIR}/.unofficial_homebrew"

# Create folder structure
rm -rf "${HOMEBREW_FOLDER}/services"
sudo -u $SUDO_USER mkdir -p "${HOMEBREW_FOLDER}/services"
sudo -u $SUDO_USER mkdir -p "${HOMEBREW_FOLDER}/plugins"
touch "${USER_DIR}/.steam/steam/.cef-enable-remote-debugging"

# Download latest release and install it
RELEASE=$(curl -s 'https://api.github.com/repos/aarron-lee/decky-loader/releases' | jq -r "first(.[] | select(.prerelease == "false"))")
VERSION=$(jq -r '.tag_name' <<< ${RELEASE} )
DOWNLOADURL=$(jq -r '.assets[].browser_download_url | select(endswith("UnofficialPluginLoader"))' <<< ${RELEASE})

printf "Installing version %s...\n" "${VERSION}"
curl -L $DOWNLOADURL --output ${HOMEBREW_FOLDER}/services/UnofficialPluginLoader
chmod +x ${HOMEBREW_FOLDER}/services/UnofficialPluginLoader

echo "Check for SELinux presence and if it is present, set the correct permission on the binary file..."
hash getenforce 2>/dev/null && getenforce | grep "Enforcing" >/dev/null && chcon -t bin_t ${HOMEBREW_FOLDER}/services/UnofficialPluginLoader

echo $VERSION > ${HOMEBREW_FOLDER}/services/.loader.version

systemctl --user stop plugin_loader 2> /dev/null
systemctl --user disable plugin_loader 2> /dev/null

systemctl stop plugin_loader 2> /dev/null
systemctl disable plugin_loader 2> /dev/null

curl -L https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/unofficial_plugin_loader-release.service  --output ${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service

cat > "${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-backup.service" <<- EOM
[Unit]
Description=Unofficial SteamDeck Plugin Loader
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=root
Restart=always
ExecStart=${HOMEBREW_FOLDER}/services/UnofficialPluginLoader
WorkingDirectory=${HOMEBREW_FOLDER}/services
KillSignal=SIGKILL
Environment=PLUGIN_PATH=${HOMEBREW_FOLDER}/plugins
Environment=LOG_LEVEL=INFO
[Install]
WantedBy=multi-user.target
EOM

if [[ -f "${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service" ]]; then
    printf "Grabbed latest release service.\n"
    sed -i -e "s|\${HOMEBREW_FOLDER}|${HOMEBREW_FOLDER}|" "${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service"
    cp -f "${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service" "/etc/systemd/system/unofficial_plugin_loader.service"
else
    printf "Could not curl latest release systemd service, using built-in service as a backup!\n"
    rm -f "/etc/systemd/system/unofficial_plugin_loader.service"
    cp "${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-backup.service" "/etc/systemd/system/unofficial_plugin_loader.service"
fi

mkdir -p ${HOMEBREW_FOLDER}/services/.systemd
cp ${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service ${HOMEBREW_FOLDER}/services/.systemd/unofficial_plugin_loader-release.service
cp ${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-backup.service ${HOMEBREW_FOLDER}/services/.systemd/unofficial_plugin_loader-backup.service
rm ${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-backup.service ${HOMEBREW_FOLDER}/services/unofficial_plugin_loader-release.service

systemctl daemon-reload
systemctl start unofficial_plugin_loader
systemctl enable unofficial_plugin_loader
