# NextKDE Arch spin roadmap

[简体中文](PLAN.zh-CN.md)

Status: phase 0 is in this branch. It provides a system package and a Wayland
session entry, but no ISO, installer or distribution infrastructure.

## Scope

The first target is an Arch-based ISO/VM image that:

- boots into a KDE Plasma 6 Wayland session,
- presents the NextKDE shell as the visible desktop (no Plasma panel on top),
- installs to disk with Calamares,
- updates through pacman, not the in-app Git source updater.

A full independent NextKDE distribution (own repositories, mirrors, security
response, hardware programme, support organisation) is a separate decision.
This roadmap stops at a reference spin that can be published and tested.

NextKDE remains a shell on top of Plasma/KWin. The spin must not claim to
replace the compositor, session manager or Plasma services.

## Phase 0 - Package and session (this branch)

Deliverables:

- `packaging/arch/PKGBUILD`
- `packaging/arch/nextkde.desktop`
- `kos-{shell,platform,data}.service` and `kos-shell-init`
- bilingual packaging and acceptance notes

Exit criteria:

- the package builds in a clean Arch VM;
- `pacman -U` installs every documented path;
- the display manager offers **NextKDE (Wayland)** and the session starts;
- all three user units become active and the QML tree is synced;
- removing the package and logging back into Plasma recovers the session.

## Phase 1 - Reproducible package repository and CI

Deliverables:

- a local pacman repository produced with `repo-add`, plus a signing key and a
  `nextkde-keyring` package;
- an Arch CI job that builds the package in `archlinux:base-devel`, runs
  `namcap`, publishes the artifact and keeps the previous version for rollback;
- pinned source tags/commits and real `sha256sums` (the scaffold currently uses
  `SKIP`);
- a packaged-mode flag that hides or disables the in-app Git updater and source
  channel UI;
- a documented package upgrade/rollback and key-rotation procedure.

Exit criteria:

- CI builds the same package twice from a pinned source and compares the
  installed file list;
- a VM upgrade from the previous version refreshes QML without losing
  `$XDG_STATE_HOME/quickshell/kos`;
- the packaged install never offers a Git source update.

## Phase 2 - Reference archiso profile and Calamares

Deliverables:

- `packaging/arch/archiso/` with `profiledef.sh`, `packages.x86_64`,
  `pacman.conf` (including the NextKDE repository) and `airootfs`;
- a build script that builds the package, creates the local repository and runs
  `mkarchiso`;
- live and installed defaults:
  - SDDM default session **NextKDE (Wayland)**;
  - KWin effects and the NextKDE decoration enabled in `/etc/skel/.config/kwinrc`;
  - Plasma panel/desktop disabled, or replaced by a Look-and-Feel package that
    ships no panel;
  - locale, keyboard, timezone and NetworkManager defaults for the live image;
- Calamares configuration: unpackfs, pacman, users, locale, keyboard, timezone,
  bootloader (systemd-boot or GRUB), network and branding;
- removal of live-only packages during installation;
- a QEMU/VM job that boots the ISO, checks the first login, installs to a
  virtio disk, reboots and logs in again.

Exit criteria:

- the ISO builds in CI from the pinned package repository;
- the live session shows NextKDE without a second panel;
- Calamares completes an encrypted install;
- the installed system boots, offers the NextKDE session and starts the three
  user units;
- an offline install (no network) still completes.

## Phase 3 - Hardware and UX acceptance

Cover at least:

- Intel, AMD and NVIDIA GPUs; software fallback;
- HiDPI and mixed-DPI multi-monitor;
- suspend/resume, audio, Bluetooth, printing and input methods;
- accessibility, keyboard-only flows and screen readers;
- Secure Boot, disk encryption and Btrfs/snapper rollback;
- package upgrades across a KWin/Qt minor upgrade;
- long-running session stability and crash recovery.

Publish the tested matrix and keep unverified combinations explicitly labelled.

## Phase 4 - Distribution operations (only if going beyond a spin)

- mirrors/CDN, signing-key rotation and revocation;
- CVE intake, fixed-release cadence and security advisories;
- SBOM, provenance and reproducible builds;
- support channels, governance, funding and trademark/legal review;
- compatibility policy for KWin, Qt, Quickshell and Plasma.

## Decisions still open

- Plasma overlay (current) versus a custom session wrapper;
- how to remove Plasma chrome: preseeded configuration, a Look-and-Feel package,
  or both;
- package naming and branding (`nextkde` package, `kos-*` internals, KDE
  trademark policy);
- spatial/depth wallpaper and AI worker on or off by default;
- update model: pacman only, with the in-app updater disabled;
- base: plain Arch versus CachyOS; kernel and firmware choices.

## Immediate tasks

1. Add the packaged-mode guard to the update controller.
2. Add the Arch package CI workflow.
3. Add the `archiso` profile and build script.
4. Add the Calamares configuration and branding.
5. Add SDDM, `kwinrc` and Plasma preseed files.
6. Add the VM acceptance script and record its evidence.

## Risks

- KWin/Qt ABI: every upgrade requires rebuilt native plugins; a rolling base
  makes this continuous maintenance.
- Quickshell version availability across Arch repositories and upgrades.
- Plasma chrome and NextKDE chrome competing for the same screen edges.
- Self-update and pacman disagreeing about ownership of the installed tree.
- Trademark and licensing review for a public image using the KDE stack.
- Long-term maintenance capacity, not the initial ISO build, is the dominant
  cost.

## Definition of done for the first public ISO

- a reproducible package build in CI;
- an ISO built in CI that boots in QEMU and installs to a VM;
- first login defaults to NextKDE (Wayland) with no duplicate Plasma chrome;
- upgrade, rollback and uninstall paths are documented and tested;
- known issues and the hardware compatibility matrix are published.
