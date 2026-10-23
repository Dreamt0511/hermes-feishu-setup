# 平台选择、安装与常驻

## 原生 Windows：普通飞书接入的默认路径

官方原生支持 Windows 10/11 的 CLI 和消息网关。Windows 11 22H2+ 还可选择官方 MSIX/App Installer；Windows 10 的脚本支持不等于 MSIX 也支持 Windows 10。先检查版本、架构与安装渠道：

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture
Get-Command hermes -All -ErrorAction SilentlyContinue
```

在普通 PowerShell 使用官方安装器，默认稳定版；不需要为了安装 Hermes 提权：

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

希望由 Agent 分阶段配置时，核对当前安装器参数后可跳过交互阶段：

```powershell
& ([scriptblock]::Create((irm https://hermes-agent.nousresearch.com/install.ps1))) -NonInteractive -Channel stable
```

安装器管理 Python、Git/Bash 和依赖，不先要求用户手动安装一套固定版本的 Python/Node。安装后打开新终端，以更新后的 User PATH 运行：

```powershell
hermes --version
hermes config path
hermes config env-path
hermes doctor
```

默认 home 为 `%LOCALAPPDATA%\hermes`，而不是 `C:\Users\某人\.hermes`；`HERMES_HOME`、profile 和桌面包可能改变路径，始终以命令返回值为准。检查 `Get-Command hermes -All`，避免旧安装遮住新安装。

Windows 的终端工具通过 Git Bash 工作，配置命令与宿主 PowerShell 的语法仍应区分。原生安装能运行消息网关，不因个别可选依赖缺失就默认改用 WSL。

### Windows 常驻

使用 `hermes gateway install` 注册当前用户登录后的启动任务，再 `start` 和 `status`。当前实现使用 Scheduled Tasks，受策略限制时可能使用 Startup 文件夹。以实际输出确认，不能把“注册成功”说成“重启前、未登录也始终在线”。

可只读查看任务是否存在：

```powershell
Get-ScheduledTask | Where-Object TaskName -Like '*Hermes*' | Select-Object TaskName, State
```

用户登出、机器休眠或关机会影响服务。开机后无需交互登录的系统服务是独立部署需求，不擅自配置为管理员服务或索取 Windows 登录密码。

## WSL2：按需使用

适合已有 WSL/Linux 工具链、需要 Linux 原生工具或用户明确选择的情形。当前原生 Windows 指南与旧 WSL 指南若对某个 UI 功能有冲突，应查当前功能文档及目标机验证，不沿用“Windows 必须装 WSL”的旧结论。

先在 Windows PowerShell 查询：

```powershell
wsl --status
wsl --list --verbose
```

确需安装时，在管理员 PowerShell 运行：

```powershell
wsl --install -d Ubuntu
```

按系统提示重启，让用户完成 Ubuntu 的 Linux 用户初始化。重启前先交接当前进度，不假设 Agent 会话能够跨重启自动恢复。安装未完成时暂停依赖它的步骤。

确认发行版 `VERSION` 为 `2`；仅在需要时转换：

```powershell
wsl --set-version Ubuntu 2
```

进入 Ubuntu 后再安装 Hermes：

```bash
uname -a
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Linux 的代码、运行环境和 home 放在 Linux 本地文件系统，例如 `~/.hermes`；不要将运行环境放入 `/mnt/c`、OneDrive 同步目录或网络共享盘。Windows 原生 home 和 WSL home 的凭证、会话及服务不自动共享，也不要让两套网关同时使用同一机器人。

### WSL 常驻

先在 Linux 中查看：

```bash
ps -p 1 -o comm=
```

已是 systemd 则不改系统配置。确需启用时，备份并**合并** `/etc/wsl.conf` 的 `[boot]` 下 `systemd=true`；保留现有其他配置。然后由用户在 Windows 执行 `wsl --shutdown`，重新进入发行版后检查。该命令会停止所有 WSL 实例中的工作，执行前确认没有其他在跑的任务。

之后使用 `hermes gateway install/start/status`。systemd 服务随发行版启动，不等于 Windows 开机后一定启动该发行版。需要 Windows 登录时启动发行版时另行配置并实际验证；不把 WSL 的启动生命周期当成全天候服务器。

## macOS / Linux

```bash
command -v hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

已有 Hermes 时跳过安装命令，先诊断。新安装后重新打开 shell 或加载安装器提示的 shell 配置；默认 POSIX home 为 `~/.hermes`，仍以 `hermes config path` 为准。

macOS 通常由当前用户 launchd agent 常驻；Linux 通常由用户 systemd 服务管理。使用 Hermes 自己的 gateway 命令，不凭猜测写 plist 或服务单元。不要用 `sudo hermes` 做普通用户安装或更换 home 的属主。

## 依赖与辅助脚本

先核对 `hermes pm install --help`、`hermes pm doctor`。源码安装缺飞书依赖时可使用：

```text
hermes pm install --extra feishu
```

受管桌面包按其渠道处理依赖与更新；不要对包内文件 `git pull`、裸 pip 安装或假设存在 `.venv/bin/python`。

本技能的辅助脚本需要可执行的 Python 3.10+，只使用标准库。可用目标机已有 Python（Windows 常见 `py -3`，POSIX 常见 `python3`）；先确认命令实际存在。没有独立 Python 时，优先用现成的飞书连接器/目标机执行工具，或请用户在新账号的飞书 UI 建群并添加机器人，不为跑辅助脚本强改 Hermes 的依赖环境。脚本属于可选自动化，主流程不依赖它。

## 依据

- [原生 Windows 官方指南](https://hermes-agent.nousresearch.com/docs/user-guide/windows-native)
- [Hermes WSL2 指南](https://hermes-agent.nousresearch.com/docs/user-guide/windows-wsl-quickstart)
- [Microsoft WSL 安装](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Microsoft WSL systemd](https://learn.microsoft.com/en-us/windows/wsl/systemd)
