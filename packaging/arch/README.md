# Arch packaging

[简体中文](README.zh-CN.md)

This directory is the first step towards an Arch-based NextKDE spin. It packages
NextKDE as a system package and adds a dedicated Wayland session entry; it does
not yet build an ISO or run an installer. See [PLAN.md](PLAN.md) for the phased
roadmap from this package to a published reference ISO.

NextKDE is **not** a standalone desktop environment. It is a user-space shell
that runs on a KDE Plasma 6 Wayland session and needs KWin 6.6+, Quickshell
0.3.x, Plasma's session services and the KWin plugins built from this tree. The
Arch spin is therefore a Plasma-based distribution with NextKDE preinstalled
and preselected, not a replacement for Plasma's compositor or session manager.

## What the package installs

| Path | Contents |
| :-- | :-- |
| `/usr/bin/{kos-settings,kos-apps,kos-app-update-agent,kos-flatpak-worker}` | Settings and application helpers |
| `/usr/libexec/{kos-platform,kos-data-service}` | Resident platform and data services |
| `/usr/share/kos-desktop/shell/` | Quickshell QML tree (dereferenced from the checkout) |
| `/usr/share/shared/{qml,Icons}` | Shared QML modules and the bundled icon font |
| `/usr/share/kos/settings/` | Settings QML and assets |
| `/usr/lib/qt6/qml/Kos/SurfaceShape` | Native QML plugin used by the shell |
| `/usr/lib/qt6/plugins/kwin/effects/plugins/` | KWin effects |
| `/usr/lib/qt6/plugins/org.kde.kdecoration3/` | Window decoration |
| `/usr/share/wayland-sessions/nextkde.desktop` | "NextKDE (Wayland)" session entry |
| `/usr/lib/systemd/user/kos-{shell,platform,data}.service` | User units |
| `/usr/lib/systemd/user/graphical-session.target.wants/` | Static enablement for every user |
| `/usr/bin/kos-shell-init` | Per-user QML tree sync on login |

The package does **not** install a display manager. Any Wayland-capable DM that
reads `wayland-sessions` (SDDM is the Plasma default) can select the session.

## Build

Follow the repository rule: build and run acceptance only in a dedicated VM or
CI, never on a maintainer workstation.

```sh
cd packaging/arch
# Defaults to the main branch:
makepkg -s

# Pin a release tag:
NEXTKDE_SOURCE="git+https://github.com/NextKde/NextKde.git#tag=v0.1.0" \
    makepkg -s

# Build a committed local checkout (commit first; git clones HEAD):
NEXTKDE_SOURCE="git+file://$PWD/../..#branch=feat/desktop-groups" \
    makepkg -s --holdver
```

`sha256sums=('SKIP')` is intentional for the source scaffold. A release package
must pin a tag or commit and carry a real checksum.

Spatial/depth wallpaper is disabled in this package (`-DKOS_BUILD_SPATIAL=OFF`)
to keep the dependency set to packages carried by Arch. Rebuilding with
`-DKOS_BUILD_SPATIAL=ON` additionally needs `opencv`, `onnxruntime-cpu` and
`qt6-quick3d`, and installs `kos-ai-worker` plus `Kos.Spatial3D`.

## Install and log in

```sh
sudo pacman -U nextkde-*.pkg.tar.zst
```

Then log out and choose **NextKDE (Wayland)** in the display manager. The
session entry runs Plasma's normal Wayland session; systemd starts
`kos-platform`, `kos-data` and `kos-shell` through the static
`graphical-session.target.wants` links.

`kos-shell-init` runs as `ExecStartPre` and copies the installed shell tree to
`~/.config/quickshell/kos`. It replaces that directory when the packaged
`VERSION` changes. Preferences and history live under
`$XDG_STATE_HOME/quickshell/kos` and are not touched.

Check the session with:

```sh
systemctl --user status kos-platform kos-data kos-shell
journalctl --user -u kos-shell.service -f
```

## Known gaps before this becomes a spin

- **No ISO or installer yet.** The next step is an `archiso` profile with
  Calamares, a Plasma package list, SDDM branding and a first-boot preset.
- **Plasma chrome is not hidden by the package.** A spin must preseed a Plasma
  configuration without the default panel/desktop, or ship a Look-and-Feel
  package, so the Plasma panel and the NextKDE bar do not both appear.
- **KWin effects are installed, not enabled.** Enable the NextKDE effects in
  Settings, or preseed `kwinrc` in the spin's `/etc/skel`.
- **Self-update UI still targets a Git source.** A packaged install should hide
  or disable source updates; a packaged-mode flag is still to be added.
- **KWin/Qt ABI.** The effects are native plugins. Every KWin or Qt upgrade
  requires rebuilding the package; the KWin 6.6/6.7/6.8 SDK CI jobs cover the
  build, but a rolling distro must rebuild on upgrades.
- **No acceptance yet.** This scaffold has not been built or installed. Run the
  VM checklist below before calling it supported.

## VM acceptance checklist

1. Build the package in a clean Arch VM.
2. Install into the VM and confirm `pacman -Ql nextkde` contains every path in
   the table above.
3. Log out, select NextKDE (Wayland), log in.
4. Confirm `graphical-session.target` pulled in all three user units, and
   `~/.config/quickshell/kos/shell.qml` exists.
5. Verify Dock, launcher, bar, notifications, Settings and desktop widgets.
6. Verify the KWin effects and decoration can be selected and survive a
   logout/login.
7. Upgrade the package and confirm the QML tree refreshes while
   `$XDG_STATE_HOME/quickshell/kos` keeps user state.
8. Remove the package, log back into Plasma, and confirm the session recovers.
