<h1 align="center">
  Unofficial Decky Loader
</h1>

## 📖 About

This is a fork of Decky Loader intended to be used solely with [SimpleDeckyTDP-Desktop](https://github.com/aarron-lee/SimpleDeckyTDP-Desktop) and [PowerControl-Electron](https://github.com/aarron-lee/PowerControl-Electron)

This fork uses an older version of decky loader without websocket-related changes. Upstream Decky's new websocket functionality completely breaks the desktop apps.

Unofficial decky loader can be used alongside regular Decky loader, they do not interfere with each other.

All files for unofficialy decky loader can be found in `$HOME/.unofficial_homebrew`, and the systemd service is called `unofficial_plugin_loader.service`

## Installation

Run in terminal and type your password when prompted.

```bash
curl -L https://github.com/aarron-lee/decky-installer/releases/latest/download/install_release.sh | sh
```

### 👋 Uninstallation

Run in terminal and type your password when prompted.

```
curl -L https://github.com/aarron-lee/decky-installer/releases/latest/download/uninstall.sh | sh
```

## 📜 Credits

Thanks to the Decky team for the awesome plugin system
