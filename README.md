<h1 align="center">
  Unofficial Decky Loader
</h1>

## 📖 About

This is a fork of Decky Loader intended to be used solely with [SimpleDeckyTDP-Desktop](https://github.com/aarron-lee/SimpleDeckyTDP-Desktop) and [PowerControl-Electron](https://github.com/aarron-lee/PowerControl-Electron)

Unofficial decky loader can be used alongside regular Decky loader, they do not interfere with each other.

This uses an older version of decky loader without websocket-related changes. Upstream Decky's new websocket functionality completely breaks the desktop apps.

This fork also does not inject any js into the Steam BPM frontend, it is purely the python backend without any GUI/UI components.

All files for unofficialy decky loader can be found in `$HOME/.unofficial_homebrew`, and the systemd service is called `unofficial_plugin_loader.service`. This uses port 1338 for the backend

## Installation

Run in terminal and type your password when prompted.

```bash
curl -L https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/install_release.sh | sh
```

### 👋 Uninstallation

Run in terminal and type your password when prompted.

```
curl -L https://raw.githubusercontent.com/aarron-lee/decky-loader/main/dist/uninstall.sh | sh
```

## 📜 Credits

Thanks to the Decky team for the awesome plugin system
