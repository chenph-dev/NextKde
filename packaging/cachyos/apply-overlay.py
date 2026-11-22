#!/usr/bin/env python3
"""Apply the NextKDE overlay to a pinned CachyOS-Live-ISO checkout.

The CachyOS ISO build is an archiso profile with a small profile switch in
util-iso.sh. This script keeps the changes explicit and fails loudly when the
pinned upstream layout changes.

What it changes:

  * adds a `nextkde` profile to util-iso.sh and packages_nextkde.x86_64;
  * adds a [nextkde] pacman repository to the build and live configs;
  * starts the live environment in the NextKDE session;
  * layers the pinned Calamares config into airootfs and patches it:
      - selects the KDE desktop group;
      - adds quickshell and nextkde to that group;
      - adds a shellprocess that sets NextKDE as the installed session;
      - copies the KWin defaults from /etc/skel into the target;
  * copies the small overlay files (kwinrc, shellprocess config).

Usage is handled by build-iso.sh; run --help for the direct form.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"apply-overlay: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing upstream file: {path}")
    except OSError as error:
        fail(f"cannot read {path}: {error}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        fail(f"upstream layout changed: {label}; expected:\n{old}")
    if text.count(old) != 1:
        fail(f"upstream layout changed: {label}; {text.count(old)} matches")
    return text.replace(old, new, 1)


def insert_once_before(text: str, needle: str, insertion: str, label: str) -> str:
    if text.count(needle) != 1:
        fail(f"upstream layout changed: {label}; {text.count(needle)} matches for {needle!r}")
    return text.replace(needle, insertion + needle, 1)


def patch_util_iso(iso: Path) -> None:
    path = iso / "util-iso.sh"
    text = read(path)
    if '[ "$profile" == "nextkde" ]' in text:
        return
    marker = '    else\n        die "Unknown profile: [%s]" "${profile}"'
    insertion = (
        '    elif [ "$profile" == "nextkde" ]; then\n'
        '        cp ${src_dir}/archiso/packages_nextkde.x86_64 ${src_dir}/archiso/packages.x86_64\n'
        '        ln -sf /usr/lib/systemd/system/plasmalogin.service '
        '${src_dir}/archiso/airootfs/etc/systemd/system/display-manager.service\n'
    )
    write(path, replace_once(text, marker, insertion + marker, "util-iso.sh profile switch"))


def patch_packages_list(iso: Path) -> None:
    source = iso / "archiso" / "packages_desktop.x86_64"
    target = iso / "archiso" / "packages_nextkde.x86_64"
    lines = [line.strip() for line in read(source).splitlines() if line.strip()]
    for package in ("quickshell", "nextkde"):
        if package not in lines:
            lines.append(package)
    write(target, "\n".join(lines) + "\n")


def patch_pacman_conf(path: Path, repo_url: str, siglevel: str) -> None:
    text = read(path)
    if "[nextkde]" in text:
        return
    stanza = f"[nextkde]\nSigLevel = {siglevel}\nServer = {repo_url.rstrip('/')}/$arch\n\n"
    write(path, insert_once_before(text, "\n[core]\n", "\n" + stanza, str(path)))


def patch_profiledef(iso: Path) -> None:
    path = iso / "archiso" / "profiledef.sh"
    text = read(path)
    replacements = {
        r"^iso_name=.*$": 'iso_name="nextkde"',
        r"^iso_label=.*$": 'iso_label="NEXTKDE_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"',
        r"^iso_publisher=.*$": 'iso_publisher="NextKDE <https://github.com/NextKde>"',
        r"^iso_application=.*$": 'iso_application="NextKDE Live/Install"',
    }
    for pattern, replacement in replacements.items():
        text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
        if count != 1:
            fail(f"upstream layout changed: profiledef.sh {pattern}")
    write(path, text)


def patch_live_session(iso: Path) -> None:
    for relative in ("etc/plasmalogin.conf", "etc/plasmalogin.conf.d/autologin.conf"):
        path = iso / "archiso" / "airootfs" / relative
        if not path.exists():
            continue
        text = read(path)
        if "Session=nextkde.desktop" in text:
            continue
        write(path, replace_once(text, "Session=plasma.desktop",
                                 "Session=nextkde.desktop", relative))


def copy_calamares(calamares: Path, airootfs: Path) -> None:
    dest = airootfs / "etc" / "calamares"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    settings = calamares / "settings_online.conf"
    if not settings.exists():
        fail(f"missing Calamares settings: {settings}")
    shutil.copy2(settings, dest / "settings.conf")

    modules = dest / "modules"
    modules.mkdir()
    for config in sorted((calamares / "src" / "modules").glob("*/*.conf")):
        shutil.copy2(config, modules / config.name)
    netinstall = calamares / "src" / "modules" / "netinstall" / "netinstall.yaml"
    if not netinstall.exists():
        fail(f"missing netinstall.yaml: {netinstall}")
    shutil.copy2(netinstall, modules / "netinstall.yaml")

    for tree in ("scripts", "images"):
        source = calamares / "src" / tree
        if source.exists():
            shutil.copytree(source, dest / tree)

    branding_src = calamares / "src" / "branding" / "cachyos"
    branding_dst = dest / "branding" / "nextkde"
    if branding_src.exists():
        shutil.copytree(branding_src, branding_dst)
        for desc in branding_dst.rglob("*.desc"):
            text = read(desc)
            text = text.replace("CachyOS", "NextKDE").replace("cachyos", "nextkde")
            write(desc, text)
    else:
        print("apply-overlay: warning: no cachyos branding directory; keeping upstream branding",
              file=sys.stderr)


def patch_calamares_settings(airootfs: Path) -> None:
    path = airootfs / "etc" / "calamares" / "settings.conf"
    text = read(path)
    if "nextkde_session" in text:
        return
    instance = (
        "- id:       nextkde_session\n"
        "  module:   shellprocess\n"
        "  config:   shellprocess-nextkde.conf\n\n"
    )
    text = insert_once_before(text, "\nsequence:\n", "\n" + instance, "Calamares sequence")
    text = replace_once(text, "  - displaymanager\n",
                        "  - displaymanager\n  - shellprocess@nextkde_session\n",
                        "Calamares displaymanager step")
    text = replace_once(text, "\nbranding: cachyos\n", "\nbranding: nextkde\n",
                        "Calamares branding")
    write(path, text)


def patch_netinstall(airootfs: Path) -> None:
    path = airootfs / "etc" / "calamares" / "modules" / "netinstall.yaml"
    text = read(path)
    starts = list(re.finditer(r"(?m)^- name: ", text))
    block = None
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        if 'name: "KDE-Desktop"' in text[start.start():end]:
            block = (start.start(), end)
            break
    if block is None:
        fail("upstream layout changed: KDE-Desktop group missing from netinstall.yaml")
    head, body = text[:block[0]], text[block[0]:block[1]]
    tail = text[block[1]:]
    lines = body.splitlines(keepends=True)
    present = {line.strip() for line in lines if line.strip().startswith("- ")}
    if "selected: false" in body:
        body = body.replace("  selected: false\n", "  selected: true\n", 1)
    additions = []
    if "- quickshell" not in present:
        additions.append("    - quickshell\n")
    if "- nextkde" not in present:
        additions.append("    - nextkde\n")
    if additions:
        body = replace_once(body, "  packages:\n",
                            "  packages:\n" + "".join(additions),
                            "KDE-Desktop package list")
    write(path, head + body + tail)


def patch_pacstrap(airootfs: Path) -> None:
    path = airootfs / "etc" / "calamares" / "modules" / "pacstrap.conf"
    text = read(path)
    if "/etc/skel/.config/kwinrc" in text:
        return
    write(path, replace_once(text, "postInstallFiles:\n",
                             'postInstallFiles:\n  - "/etc/skel/.config/kwinrc"\n',
                             "pacstrap postInstallFiles"))


def copy_overlay(overlay: Path, iso: Path) -> None:
    airootfs = iso / "archiso" / "airootfs"
    for source in sorted(overlay.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(overlay)
        dest = airootfs / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path, help="CachyOS-Live-ISO checkout")
    parser.add_argument("--calamares", required=True, type=Path,
                        help="cachyos-calamares checkout")
    parser.add_argument("--overlay", required=True, type=Path,
                        help="overlay directory (contents copied into airootfs)")
    parser.add_argument("--repo-url", required=True,
                        help="pacman repository base URL, without the architecture suffix")
    parser.add_argument("--siglevel", default="Optional TrustAll",
                        help="pacman SigLevel for [nextkde] (production: Required DatabaseOptional)")
    args = parser.parse_args()

    patch_util_iso(args.iso)
    patch_packages_list(args.iso)
    patch_profiledef(args.iso)
    patch_live_session(args.iso)
    for relative in ("archiso/pacman.conf",
                     "archiso/airootfs/etc/pacman.conf",
                     "archiso/airootfs/etc/pacman-more.conf"):
        patch_pacman_conf(args.iso / relative, args.repo_url, args.siglevel)

    copy_calamares(args.calamares, args.iso / "archiso" / "airootfs")
    patch_calamares_settings(args.iso / "archiso" / "airootfs")
    patch_netinstall(args.iso / "archiso" / "airootfs")
    patch_pacstrap(args.iso / "archiso" / "airootfs")
    copy_overlay(args.overlay, args.iso)

    print("apply-overlay: CachyOS ISO profile patched for NextKDE")


if __name__ == "__main__":
    main()
