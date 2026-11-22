# CachyOS NextKDE spin

[简体中文](README.zh-CN.md)

This directory builds a NextKDE ISO from the open-source CachyOS live-ISO
profile. It is a scaffold: the pipeline is explicit and pinned, but it has not
been built or accepted in a VM yet.

NextKDE is a shell on top of KDE Plasma 6 Wayland. The spin is therefore a
CachyOS-based image with Plasma/KWin underneath and NextKDE as the visible
desktop, not a replacement compositor or session manager.

## Pipeline

```
packaging/arch (nextkde package)
        │
        ├── makepkg
        ▼
  nextkde-pacman repo  ──►  NEXTKDE_REPO_URL (GitHub Pages / static host)
        │
        ▼
CachyOS-Live-ISO (pinned commit)
        │  apply-overlay.py
        │    ├── archiso/packages_nextkde.x86_64
        │    ├── archiso/pacman.conf  (+ [nextkde])
        │    ├── live session = nextkde.desktop
        │    ├── Calamares config (netinstall + shellprocess)
        │    └── /etc/skel/.config/kwinrc
        ▼
   buildiso.sh -p nextkde
        ▼
   out/nextkde/*.iso
```

Pinned upstreams:

- `CachyOS/CachyOS-Live-ISO` `912e0cc16a426ca6818f3919258ed1b523237734`
- `CachyOS/cachyos-calamares` `255a96ed16dbb73ceb535ddf2e18b5f07f0b2cc7`
  (branch `cachyos`)

Both are GPL-3.0. Reusing them means publishing your modified build sources
under the same license.

## Prerequisites

- Arch or CachyOS VM/CI with `base-devel`, `archiso`, `squashfs-tools`, `grub`,
  `git`, `python`.
- A pacman repository reachable by both the build and the installed system.
  GitHub Pages is enough for a first spin:

  ```ini
  [nextkde]
  SigLevel = Required DatabaseOptional
  Server = https://<user>.github.io/<repo>/$arch
  ```

  Set `NEXTKDE_REPO_URL=https://<user>.github.io/<repo>` (no `/$arch`; the
  overlay appends it).

- For a production image, sign the repository and ship a `nextkde-keyring`
  package. The scaffold defaults to `Optional TrustAll` for unsigned local
  builds; override with:

  ```sh
  NEXTKDE_SIGLEVEL="Required DatabaseOptional" NEXTKDE_GPG_KEY=<key> ./build-iso.sh
  ```

## Build

```sh
cd packaging/cachyos
NEXTKDE_REPO_URL=https://<user>.github.io/<repo> ./build-iso.sh
```

The script:

1. builds `nextkde` from `packaging/arch` (or uses `NEXTKDE_PKG=<file>`),
2. creates `work/repo/x86_64` with `repo-add`,
3. clones and resets the two pinned upstream repositories,
4. runs `apply-overlay.py` to patch the ISO profile, live session and
   Calamares configuration,
5. runs CachyOS's `buildiso.sh -p nextkde` under `sudo`,
6. prints the ISO path.

The local repository stays at `work/repo/x86_64`; upload it to
`NEXTKDE_REPO_URL` before building (or immediately after, if the build can
reach a different already-published repository).

Useful overrides:

```sh
WORK_DIR=/var/tmp/nextkde-iso
NEXTKDE_PKG=/path/to/nextkde-*.pkg.tar.zst
CACHYOS_ISO_REF=<commit>
CACHYOS_CALAMARES_REF=<commit>
```

## What the overlay changes

- Adds a `nextkde` profile to `util-iso.sh`, with a package list copied from
  CachyOS's desktop list plus `quickshell` and `nextkde`.
- Adds `[nextkde]` to the build, live and installed pacman configurations.
- Sets the live Plasma Login Manager session to `nextkde.desktop`.
- Layers the pinned CachyOS Calamares config into the ISO and:
  - selects the `KDE-Desktop` group;
  - adds `quickshell` and `nextkde` to that group;
  - adds a `shellprocess` step that writes the installed system's default
    session for Plasma Login Manager and SDDM;
  - copies `/etc/skel/.config/kwinrc` into the target.
- Adds `/etc/skel/.config/kwinrc` with the NextKDE KWin effects enabled and the
  NextKDE decoration selected.
- Sets NextKDE ISO name, label, publisher and application strings.

## Install flow

1. Boot the ISO (UEFI or BIOS).
2. The live session starts NextKDE.
3. Start Calamares and pick the Plasma desktop group (the KDE group is already
   selected and contains NextKDE).
4. Install to disk.
5. Reboot: the installed system offers the NextKDE session; the shell's user
   units start through the packaged `graphical-session.target.wants` links.
6. Update through pacman from the NextKDE repository.

## Known gaps

- **Not built or accepted yet.** Run the checklist below in a VM.
- **Branding images are still CachyOS.** Text names in the copied branding file
  are replaced, but the logos, wallpapers and screenshots are not. Replace
  `src/branding/nextkde` assets before publishing.
- **Plasma chrome is not hidden.** The image still ships the Plasma panel and
  desktop. Preseed a Plasma layout without a panel, or ship a Look-and-Feel
  package, before calling this a NextKDE desktop.
- **Default session depends on the display manager.** The overlay writes both
  `plasmalogin.conf.d` and `sddm.conf.d`; verify which one the installed image
  actually uses and that the greeter preselects NextKDE. SDDM may ignore
  `[Autologin] Session` without a `User`.
- **Offline install is not solved.** CachyOS's Calamares uses `pacstrap` +
  packages, so the installer needs the `[nextkde]` repository. The script
  accepts a `file://` URL but warns that `mkarchiso` may not see it during the
  package transaction. Prefer an HTTP repository for the first build; a fully
  offline ISO needs the repository or its packages embedded in a path the live
  installer can read.
- **No keyring package yet.** Production needs a signed repo, a
  `nextkde-keyring` package and `SigLevel = Required`; the scaffold defaults to
  trust-all for local testing.
- **KWin/Qt ABI.** Rebuild `nextkde` whenever CachyOS/Arch updates KWin or Qt.
- **No AUR/package review.** The `nextkde` package is a source PKGBUILD outside
  the Arch/CachyOS repositories. Decide whether to stay independent or submit
  it upstream.
- **Trademark.** "Based on CachyOS" is a factual description; do not use
  CachyOS logos or imply an official CachyOS edition without permission.

## VM acceptance checklist

1. Build the package and the ISO in a clean CachyOS VM.
2. Boot the ISO in QEMU with UEFI and BIOS.
3. Confirm the live session is NextKDE and the three user units are active.
4. Run Calamares, install with encryption to a virtio disk.
5. Reboot; confirm the installed system offers/starts NextKDE.
6. Confirm the shell QML was synced to `~/.config/quickshell/kos`.
7. Confirm KWin effects and decoration from `/etc/skel/.config/kwinrc` are
   active for the new user.
8. Run `pacman -Syu` against the NextKDE repository.
9. Remove the package and log back into Plasma; confirm the session recovers.
10. Record the exact upstream commits, package versions, ISO checksum and
    skipped coverage.

See [PLAN.md](../arch/PLAN.md) for the broader phase plan and the remaining
distribution-operations work.
