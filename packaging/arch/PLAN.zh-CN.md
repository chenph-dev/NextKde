# NextKDE Arch spin 路线图

[English](PLAN.md)

状态：本分支完成阶段 0，提供系统包和 Wayland 会话入口；还没有 ISO、安装器或
发行版基础设施。

## 范围

第一个目标是基于 Arch 的 ISO/VM 镜像：

- 启动进入 KDE Plasma 6 Wayland 会话；
- 以 NextKDE Shell 作为可见桌面，不叠加 Plasma 面板；
- 使用 Calamares 安装到磁盘；
- 通过 pacman 更新，而不是内置的 Git 源码更新器。

完整独立的 NextKDE 发行版（自有仓库、镜像站、安全响应、硬件计划、支持组织）
是另一个决策。本路线图止步于可发布、可测试的参考 spin。

NextKDE 仍然是 Plasma/KWin 之上的 Shell。spin 不应宣称替换合成器、会话管理器
或 Plasma 服务。

## 阶段 0 - 包与会话（本分支）

交付：

- `packaging/arch/PKGBUILD`
- `packaging/arch/nextkde.desktop`
- `kos-{shell,platform,data}.service` 与 `kos-shell-init`
- 双语打包与验收说明

退出条件：

- 在干净的 Arch VM 中构建成功；
- `pacman -U` 安装出文档列出的全部路径；
- 显示管理器提供 **NextKDE (Wayland)** 且会话可启动；
- 三个用户单元全部激活，QML 树已同步；
- 卸载后重新登录 Plasma，会话恢复。

## 阶段 1 - 可复现的包仓库与 CI

交付：

- 用 `repo-add` 生成本地 pacman 仓库，配套签名密钥和 `nextkde-keyring` 包；
- Arch CI：在 `archlinux:base-devel` 中构建、运行 `namcap`、发布产物并保留上一版
  用于回滚；
- 固定源码 tag/commit 和真实 `sha256sums`（脚手架目前是 `SKIP`）；
- packaged-mode 开关，隐藏或禁用内置 Git 更新器和源码通道 UI；
- 文档化的升级/回滚与密钥轮换流程。

退出条件：

- CI 从固定源构建两次，安装文件列表一致；
- VM 中从上一版升级，QML 刷新且 `$XDG_STATE_HOME/quickshell/kos` 用户状态保留；
- 打包安装不再提供 Git 源码更新。

## 阶段 2 - 参考 archiso 与 Calamares

交付：

- `packaging/arch/archiso/`：`profiledef.sh`、`packages.x86_64`、包含 NextKDE 仓库
  的 `pacman.conf`、`airootfs`；
- 构建脚本：构建包、创建本地仓库并运行 `mkarchiso`；
- Live 与安装后的默认值：
  - SDDM 默认会话 **NextKDE (Wayland)**；
  - `/etc/skel/.config/kwinrc` 中启用 KWin 效果与 NextKDE 装饰；
  - 关闭 Plasma 面板/桌面，或提供不带面板的 Look-and-Feel 包；
  - Live 镜像的 locale、键盘、时区和 NetworkManager 默认值；
- Calamares：unpackfs、pacman、users、locale、keyboard、timezone、bootloader
  （systemd-boot 或 GRUB）、network 和品牌配置；
- 安装时移除 live-only 包；
- QEMU/VM 任务：启动 ISO、检查首次登录、安装到 virtio 磁盘、重启并再次登录。

退出条件：

- CI 从固定包仓库构建出 ISO；
- Live 会话只显示 NextKDE，没有第二套面板；
- Calamares 完成加密安装；
- 安装后的系统可启动，提供 NextKDE 会话并拉起三个用户单元；
- 离线安装（无网络）也能完成。

## 阶段 3 - 硬件与体验验收

至少覆盖：

- Intel、AMD、NVIDIA GPU 与软件回退；
- HiDPI 与混合 DPI 多显示器；
- 挂起/恢复、音频、蓝牙、打印和输入法；
- 无障碍、纯键盘流程和屏幕阅读器；
- Secure Boot、磁盘加密、Btrfs/snapper 回滚；
- 跨 KWin/Qt 小版本升级的包升级；
- 长时间会话稳定性与崩溃恢复。

发布已测试矩阵，明确标注未验证的组合。

## 阶段 4 - 发行版运营（仅在超越 spin 时）

- 镜像/CDN、签名密钥轮换与吊销；
- CVE 接收、修复发布节奏与安全公告；
- SBOM、来源证明与可复现构建；
- 支持渠道、治理、资金与商标/法务审查；
- KWin、Qt、Quickshell 和 Plasma 的兼容策略。

## 仍待决定

- Plasma 叠加（当前）还是自定义会话包装器；
- 如何移除 Plasma 界面：预置配置、Look-and-Feel 包，或两者并用；
- 包命名与品牌（`nextkde` 包名、`kos-*` 内部命名、KDE 商标政策）；
- 空间/景深壁纸与 AI worker 默认开关；
- 更新模型：只用 pacman，禁用内置更新器；
- 基础选择：纯 Arch 还是 CachyOS；内核与固件策略。

## 立即任务

1. 给更新控制器增加 packaged-mode 保护。
2. 增加 Arch 包 CI 工作流。
3. 增加 `archiso` profile 与构建脚本。
4. 增加 Calamares 配置与品牌。
5. 增加 SDDM、`kwinrc` 和 Plasma 预置文件。
6. 增加 VM 验收脚本并记录证据。

## 风险

- KWin/Qt ABI：每次升级都要重建原生插件，滚动基础意味着持续维护。
- Quickshell 在 Arch 仓库和升级中的版本可用性。
- Plasma 界面与 NextKDE 界面争夺同一屏幕边缘。
- 内置自更新与 pacman 对已安装树的归属冲突。
- 公开镜像使用 KDE 技术栈的商标与许可证审查。
- 初始 ISO 构建不是主要成本，长期维护能力才是。

## 首个公开 ISO 的完成标准

- CI 中可复现地构建包；
- CI 中构建的 ISO 能在 QEMU 启动并安装到 VM；
- 首次登录默认 NextKDE (Wayland)，没有重复的 Plasma 界面；
- 升级、回滚和卸载路径有文档且经过测试；
- 已知问题与硬件兼容矩阵已发布。
