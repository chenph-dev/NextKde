# Arch 打包

[English](README.md)

这个目录是 Arch 版 NextKDE spin 的第一步：把 NextKDE 打成系统包，并增加一个
独立的 Wayland 会话入口。它还没有构建 ISO，也没有接入安装器。从当前包到可发布
参考 ISO 的分阶段计划见 [PLAN.zh-CN.md](PLAN.zh-CN.md)。

NextKDE **不是**独立桌面环境，而是运行在 KDE Plasma 6 Wayland 会话之上的用户态
Shell，需要 KWin 6.6+、Quickshell 0.3.x、Plasma 会话服务以及本仓库构建的 KWin
插件。因此 Arch spin 的形态是“基于 Plasma 的发行版预装并默认选中 NextKDE”，
而不是替换 Plasma 的合成器或会话管理器。

## 包安装的内容

| 路径 | 内容 |
| :-- | :-- |
| `/usr/bin/{kos-settings,kos-apps,kos-app-update-agent,kos-flatpak-worker}` | 设置与应用辅助程序 |
| `/usr/libexec/{kos-platform,kos-data-service}` | 常驻平台与数据服务 |
| `/usr/share/kos-desktop/shell/` | Quickshell QML 树（从源码树解引用复制） |
| `/usr/share/shared/{qml,Icons}` | 共享 QML 模块与内置图标字体 |
| `/usr/share/kos/settings/` | 设置页 QML 与资源 |
| `/usr/lib/qt6/qml/Kos/SurfaceShape` | Shell 使用的原生 QML 插件 |
| `/usr/lib/qt6/plugins/kwin/effects/plugins/` | KWin 效果 |
| `/usr/lib/qt6/plugins/org.kde.kdecoration3/` | 窗口装饰 |
| `/usr/share/wayland-sessions/nextkde.desktop` | “NextKDE (Wayland)” 会话入口 |
| `/usr/lib/systemd/user/kos-{shell,platform,data}.service` | 用户单元 |
| `/usr/lib/systemd/user/graphical-session.target.wants/` | 对所有用户静态启用 |
| `/usr/bin/kos-shell-init` | 登录时同步每个用户的 QML 树 |

包本身不安装显示管理器。任何读取 `wayland-sessions` 的 Wayland 显示管理器
（Plasma 默认的 SDDM）都能选择该会话。

## 构建

遵守仓库规则：只在专用 VM 或 CI 中构建和验收，不要在维护者工作站上运行。

```sh
cd packaging/arch
# 默认跟踪 main：
makepkg -s

# 固定发布 tag：
NEXTKDE_SOURCE="git+https://github.com/NextKde/NextKde.git#tag=v0.1.0" \
    makepkg -s

# 构建已提交的本地 checkout（git 只克隆 HEAD，先提交）：
NEXTKDE_SOURCE="git+file://$PWD/../..#branch=feat/desktop-groups" \
    makepkg -s --holdver
```

`sha256sums=('SKIP')` 是脚手架阶段的临时值。正式发布包必须固定 tag 或 commit
并填写真实校验和。

这个包默认关闭空间/景深壁纸（`-DKOS_BUILD_SPATIAL=OFF`），只依赖 Arch 仓库
已有的包。改用 `-DKOS_BUILD_SPATIAL=ON` 需要额外的 `opencv`、`onnxruntime-cpu`
和 `qt6-quick3d`，并会安装 `kos-ai-worker` 与 `Kos.Spatial3D`。

## 安装与会话

```sh
sudo pacman -U nextkde-*.pkg.tar.zst
```

注销后，在显示管理器中选择 **NextKDE (Wayland)**。会话入口运行 Plasma 正常的
Wayland 会话；systemd 通过静态 `graphical-session.target.wants` 链接启动
`kos-platform`、`kos-data` 和 `kos-shell`。

`kos-shell-init` 作为 `ExecStartPre` 运行，把安装的 Shell 树复制到
`~/.config/quickshell/kos`。包内 `VERSION` 变化时会替换该目录；偏好与历史位于
`$XDG_STATE_HOME/quickshell/kos`，不会被清除。

检查会话：

```sh
systemctl --user status kos-platform kos-data kos-shell
journalctl --user -u kos-shell.service -f
```

## 成为 spin 之前仍缺

- **还没有 ISO 与安装器。** 下一步是 archiso profile + Calamares、Plasma 包列表、
  SDDM 品牌配置和首次启动预设。
- **包不会隐藏 Plasma 自带界面。** spin 需要预置不带默认面板/桌面的 Plasma 配置，
  或提供 Look-and-Feel 包，避免 Plasma 面板与 NextKDE 顶栏同时出现。
- **KWin 效果只安装、不启用。** 在设置中启用，或在 spin 的 `/etc/skel` 里预置
  `kwinrc`。
- **内置自更新仍指向 Git 源码。** 打包安装应隐藏或禁用源码更新；打包模式开关
  尚未实现。
- **KWin/Qt ABI。** 效果是原生插件，每次 KWin 或 Qt 升级都必须重建包；CI 覆盖
  6.6/6.7/6.8 SDK 构建，滚动发行版仍需跟随升级重建。
- **尚未验收。** 这个脚手架还没有实际构建或安装。正式宣称支持前请完成下面的
  VM 验收清单。

## VM 验收清单

1. 在干净的 Arch VM 中构建包。
2. 安装后确认 `pacman -Ql nextkde` 包含上表全部路径。
3. 注销，选择 NextKDE (Wayland)，重新登录。
4. 确认三个用户单元都被 `graphical-session.target` 拉起，且
   `~/.config/quickshell/kos/shell.qml` 存在。
5. 验证 Dock、启动器、顶栏、通知、设置和桌面组件。
6. 验证 KWin 效果与窗口装饰可选中，并在注销/登录后保持。
7. 升级包，确认 QML 树刷新，同时 `$XDG_STATE_HOME/quickshell/kos` 的用户状态保留。
8. 卸载包，重新登录 Plasma，确认会话恢复。
