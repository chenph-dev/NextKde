# CachyOS NextKDE spin

[English](README.md)

这个目录基于开源的 CachyOS live-ISO 配置构建 NextKDE ISO。它是脚手架：
流程和固定版本都写清楚了，但还没有在 VM 中实际构建或验收。

NextKDE 是 KDE Plasma 6 Wayland 之上的 Shell。因此这个 spin 是“基于 CachyOS
的镜像 + Plasma/KWin 底层 + NextKDE 可见桌面”，不是替换合成器或会话管理器。

## 流程

```
packaging/arch（nextkde 包）
        │
        ├── makepkg
        ▼
  nextkde pacman 仓库  ──►  NEXTKDE_REPO_URL（GitHub Pages / 静态托管）
        │
        ▼
CachyOS-Live-ISO（固定 commit）
        │  apply-overlay.py
        │    ├── archiso/packages_nextkde.x86_64
        │    ├── archiso/pacman.conf  (+ [nextkde])
        │    ├── Live 会话 = nextkde.desktop
        │    ├── Calamares 配置（netinstall + shellprocess）
        │    └── /etc/skel/.config/kwinrc
        ▼
   buildiso.sh -p nextkde
        ▼
   out/nextkde/*.iso
```

固定的上游版本：

- `CachyOS/CachyOS-Live-ISO` `912e0cc16a426ca6818f3919258ed1b523237734`
- `CachyOS/cachyos-calamares` `255a96ed16dbb73ceb535ddf2e18b5f07f0b2cc7`
  （分支 `cachyos`）

两者都是 GPL-3.0；分发修改后的构建配置时，也要按 GPL-3.0 提供对应源码。

## 前置条件

- Arch 或 CachyOS 的 VM/CI，安装 `base-devel`、`archiso`、`squashfs-tools`、
  `grub`、`git`、`python`。
- 一个构建时和安装后都能访问的 pacman 仓库。第一次可以用 GitHub Pages：

  ```ini
  [nextkde]
  SigLevel = Required DatabaseOptional
  Server = https://<user>.github.io/<repo>/$arch
  ```

  设置 `NEXTKDE_REPO_URL=https://<user>.github.io/<repo>`（不要带 `/$arch`，
  overlay 会自己加）。

- 正式镜像应签名仓库并提供 `nextkde-keyring` 包。脚手架默认对未签名仓库使用
  `Optional TrustAll`；正式构建可覆盖：

  ```sh
  NEXTKDE_SIGLEVEL="Required DatabaseOptional" NEXTKDE_GPG_KEY=<key> ./build-iso.sh
  ```

## 构建

```sh
cd packaging/cachyos
NEXTKDE_REPO_URL=https://<user>.github.io/<repo> ./build-iso.sh
```

脚本会：

1. 从 `packaging/arch` 构建 `nextkde`（或用 `NEXTKDE_PKG=<file>` 指定现成包）；
2. 在 `work/repo/x86_64` 用 `repo-add` 建立本地仓库；
3. 克隆并重置两个固定版本的上游仓库；
4. 运行 `apply-overlay.py`，修改 ISO profile、Live 会话和 Calamares 配置；
5. 通过 `sudo` 调用 CachyOS 的 `buildiso.sh -p nextkde`；
6. 输出 ISO 路径。

本地仓库留在 `work/repo/x86_64`；构建前应把它上传到 `NEXTKDE_REPO_URL`，或者让
构建访问一个已经发布的仓库。

可用覆盖项：

```sh
WORK_DIR=/var/tmp/nextkde-iso
NEXTKDE_PKG=/path/to/nextkde-*.pkg.tar.zst
CACHYOS_ISO_REF=<commit>
CACHYOS_CALAMARES_REF=<commit>
```

## Overlay 改了什么

- 在 `util-iso.sh` 增加 `nextkde` profile，包列表复制 CachyOS 桌面列表并追加
  `quickshell`、`nextkde`。
- 在构建、Live 和安装后的 pacman 配置里加入 `[nextkde]` 仓库。
- 把 Live 的 Plasma Login Manager 会话设为 `nextkde.desktop`。
- 把固定版本的 CachyOS Calamares 配置铺进 ISO，并：
  - 选中 `KDE-Desktop` 组；
  - 向该组加入 `quickshell`、`nextkde`；
  - 增加一个 `shellprocess`，为安装后的系统写入 NextKDE 默认会话；
  - 把 `/etc/skel/.config/kwinrc` 复制到目标系统。
- 增加 `/etc/skel/.config/kwinrc`，启用 NextKDE 的 KWin 效果和装饰。
- 修改 NextKDE 的 ISO 名称、标签、发布者和应用描述。

## 安装流程

1. 以 UEFI 或 BIOS 启动 ISO。
2. Live 会话直接进入 NextKDE。
3. 启动 Calamares，选择 Plasma 桌面组（KDE 组已默认选中并包含 NextKDE）。
4. 安装到磁盘。
5. 重启：安装后的系统提供 NextKDE 会话；shell 的用户单元通过包的
   `graphical-session.target.wants` 链接启动。
6. 通过 pacman 从 NextKDE 仓库更新。

## 已知缺口

- **尚未构建或验收。** 必须在 VM 中跑下面的清单。
- **品牌图片仍是 CachyOS。** 只替换了 branding 文本，Logo、壁纸和截图还没换。
- **没有隐藏 Plasma 面板/桌面。** 发布前需要预置不带面板的 Plasma 布局，或提供
  Look-and-Feel 包，否则会和 NextKDE 顶栏重复。
- **默认会话取决于显示管理器。** overlay 同时写 `plasmalogin.conf.d` 和
  `sddm.conf.d`；需要确认安装后的镜像实际用哪一个，并验证登录器会预选 NextKDE。
  SDDM 在 `[Autologin]` 没有 `User` 时可能忽略 `Session`。
- **离线安装未解决。** CachyOS 的 Calamares 使用 `pacstrap` + 包仓库，安装时需要
  `[nextkde]` 仓库。脚本接受 `file://` 但会警告 `mkarchiso` 可能在包事务中看不到
  它；首次构建建议用 HTTP 仓库。
- **还没有 keyring 包。** 正式发布需要签名仓库、`nextkde-keyring` 和
  `SigLevel = Required`；脚手架默认 trust-all 方便本地测试。
- **KWin/Qt ABI。** CachyOS/Arch 更新 KWin 或 Qt 后必须重建 `nextkde`。
- **未提交 AUR/官方仓库。** 当前是独立的源码 PKGBUILD；是否进入 CachyOS/Arch
  官方仓库需要单独决定。
- **商标。** 可以事实性地说“基于 CachyOS”，但不能使用其 Logo 或暗示官方版本。

## VM 验收清单

1. 在干净的 CachyOS VM 中构建包和 ISO。
2. 用 QEMU 分别以 UEFI 和 BIOS 启动。
3. 确认 Live 会话是 NextKDE，三个用户单元都处于 active。
4. 用 Calamares 安装到 virtio 磁盘，开启加密。
5. 重启，确认安装后的系统提供/启动 NextKDE。
6. 确认 QML 已同步到 `~/.config/quickshell/kos`。
7. 确认新用户拿到 `/etc/skel/.config/kwinrc` 中的 KWin 效果和装饰。
8. 对 NextKDE 仓库执行 `pacman -Syu`。
9. 卸载包并重新登录 Plasma，确认会话恢复。
10. 记录上游 commit、包版本、ISO 校验和以及未覆盖项。

更完整的阶段计划见 [PLAN.md](../arch/PLAN.md)。
