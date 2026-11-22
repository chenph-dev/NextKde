#!/usr/bin/env bash
# Build a NextKDE ISO from the pinned CachyOS-Live-ISO profile.
#
# Prerequisites: run on Arch/CachyOS (or an Arch container) with base-devel,
# archiso, squashfs-tools, grub, git and python. Never build on a maintainer
# workstation; use a dedicated VM or CI.
#
# The NextKDE package must be reachable by pacman during the build and by the
# installed system afterwards. Provide NEXTKDE_REPO_URL as a pacman Server base
# without the architecture suffix, for example:
#
#   NEXTKDE_REPO_URL=https://<user>.github.io/<repo>
#
# The local repository produced here is printed at the end; upload its
# x86_64/ directory to that URL before building, or point the URL at another
# static host. A file:// URL is accepted for experiments but mkarchiso may not
# see it during the package transaction; see README.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
work=${WORK_DIR:-"$root/.build/cachyos-nextkde"}
src_root="$work/src"
repo_dir="$work/repo"
iso_repo=${CACHYOS_ISO_REPO:-https://github.com/CachyOS/CachyOS-Live-ISO.git}
iso_ref=${CACHYOS_ISO_REF:-912e0cc16a426ca6818f3919258ed1b523237734}
cal_repo=${CACHYOS_CALAMARES_REPO:-https://github.com/CachyOS/cachyos-calamares.git}
cal_ref=${CACHYOS_CALAMARES_REF:-255a96ed16dbb73ceb535ddf2e18b5f07f0b2cc7}
repo_url=${NEXTKDE_REPO_URL:-}
siglevel=${NEXTKDE_SIGLEVEL:-"Optional TrustAll"}
package_path=${NEXTKDE_PKG:-}

die() { printf 'build-iso: %s\n' "$*" >&2; exit 1; }

[[ $(id -u) -ne 0 ]] || die "run as a normal user; buildiso.sh invokes sudo itself"
[[ -n "$repo_url" ]] || die "set NEXTKDE_REPO_URL to the pacman repository base URL (without /x86_64)"

for cmd in git python3 makepkg repo-add sudo mkarchiso mksquashfs; do
    command -v "$cmd" >/dev/null 2>&1 || die "missing command: $cmd"
done

mkdir -p "$src_root" "$repo_dir/x86_64"

if [[ -z "$package_path" ]]; then
    printf 'build-iso: building nextkde package\n'
    mkdir -p "$work/makepkg"
    (
        cd "$root/packaging/arch"
        PKGDEST="$work/makepkg" \
        SRCDEST="$work/makepkg/sources" \
        BUILDDIR="$work/makepkg/build" \
            makepkg -s --noconfirm
    )
    package_path=$(find "$work/makepkg" -maxdepth 1 -name 'nextkde-*.pkg.tar.zst' \
        -printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-)
    [[ -n "$package_path" ]] || die "makepkg produced no nextkde package"
fi

if [[ -n "${NEXTKDE_GPG_KEY:-}" ]]; then
    gpg --batch --yes --detach-sign --local-user "$NEXTKDE_GPG_KEY" "$package_path"
fi

cp "$package_path" "$repo_dir/x86_64/"
[[ -f "$package_path.sig" ]] && cp "$package_path.sig" "$repo_dir/x86_64/"
package_name=$(basename "$package_path")
(
    cd "$repo_dir/x86_64"
    if [[ -n "${NEXTKDE_GPG_KEY:-}" ]]; then
        repo-add --sign --key "$NEXTKDE_GPG_KEY" \
            "$repo_dir/x86_64/nextkde.db.tar.gz" "$package_name"
    else
        repo-add "$repo_dir/x86_64/nextkde.db.tar.gz" "$package_name"
    fi
)
printf 'build-iso: local repo: %s\n' "$repo_dir/x86_64"

clone_at() {
    local url=$1 directory=$2 ref=$3
    if [[ ! -d "$directory/.git" ]]; then
        git clone "$url" "$directory"
    fi
    git -C "$directory" fetch --all --tags --prune
    git -C "$directory" reset --hard
    git -C "$directory" clean -fdx
    git -C "$directory" checkout --detach "$ref"
}

iso_dir="$src_root/CachyOS-Live-ISO"
cal_dir="$src_root/cachyos-calamares"
clone_at "$iso_repo" "$iso_dir" "$iso_ref"
clone_at "$cal_repo" "$cal_dir" "$cal_ref"

python3 "$root/packaging/cachyos/apply-overlay.py" \
    --iso "$iso_dir" \
    --calamares "$cal_dir" \
    --overlay "$root/packaging/cachyos/overlay" \
    --repo-url "$repo_url" \
    --siglevel "$siglevel"

if [[ "$repo_url" == file://* ]]; then
    repo_path=${repo_url#file://}
    install -d "$iso_dir/archiso/airootfs$repo_path"
    cp -r "$repo_dir/x86_64/." "$iso_dir/archiso/airootfs$repo_path/"
    printf 'build-iso: warning: file:// repo copied into airootfs; mkarchiso may not\n'
    printf '            resolve it during the package transaction. Prefer an HTTP\n'
    printf '            repository for the first build.\n'
fi

printf 'build-iso: starting mkarchiso under sudo (this takes a while)\n'
(
    cd "$iso_dir"
    sudo ./buildiso.sh -p nextkde -v -w
)

printf '\nbuild-iso: ISO output:\n'
find "$iso_dir/out" -maxdepth 2 -name '*.iso' -printf '  %p\n'
printf 'build-iso: local pacman repo remains at %s\n' "$repo_dir/x86_64"
