# 突然不回复：从事实到最小恢复

保留正确账号、机器人和群，不从零重装。执行命令前确认当前机器、执行环境、Hermes home、profile；排查错误 profile 会得到误导的正常结果。

## 先做三项检查

1. 用户是否在正确群中用允许账号真正 @了机器人，使用的是系统的 @提及而非手打名字？该消息是刚发出的还是旧消息？
2. `hermes gateway status` 是否运行，平台是否 connected / retrying / failed？主机是否休眠、断网、登出或刚刚重启？
3. 查看本次消息附近的日志，区分没有入站、权限拦截、模型错误或发送错误。先用 `hermes logs --help` 核对参数，再使用 `hermes logs`、`hermes logs errors` 或对应 home 的日志。

记录故障时间、所选 profile、平台状态、必要的错误类型和请求 ID。日志只摘取与本次故障有关的少量行，并去掉 token、App Secret、邮箱、真实聊天内容及无关文件路径；不要整份上传。

## 按故障层定位

| 观察到的现象 | 检查重点 | 恢复方向 |
|---|---|---|
| 主机离线/睡眠，进程不在 | 电源、网络、登录态、服务启动方式 | 恢复主机，再 start；不能用重装解决主机离线 |
| gateway 未运行 | profile、服务是否安装、最近退出日志 | 已安装用 start；未安装且需要常驻再 install/start |
| gateway 运行但 Feishu retrying | 代理、DNS、TLS、WebSocket、凭证、飞书状态 | 保留凭证，修网络；连接长期不恢复再 restart |
| 飞书没有本次消息入站 | 群成员、账号/租户、@、事件订阅、应用发布 | 修正确切配置，不重建机器人 |
| 有消息但被拒绝 | allowed_users、group_rules、default_group_policy、App 下的 open_id | 只修复约定账号/群范围，不用全局开放绕过 |
| 消息已进入，模型没回复 | 当前模型、provider、OAuth、额度、网络、卡住的工具 | 独立执行短模型测试，按具体错误处理 |
| 模型已有答案，群里没发出 | 发送权限、机器人是否被移除、资源/卡片错误 | 检查发送错误；不要反复重跑用户任务 |
| 同一问题发多次才收到 | 重启窗口、正在执行的长任务、排队、重复实例 | 查看 active work；避免同时启动多个网关 |

### 模型凭证、额度与网络

```text
hermes auth status openai-codex
hermes usage --provider openai-codex --json
hermes config get model
```

确认网关稳定后，运行技能入口中的短模型测试。

- 明确凭证失效/被撤销：使用 Hermes 自己的 `hermes auth add openai-codex` 重新授权，成功后再应用到网关；不删除整个 `.hermes`，不先退出其他程序的账号。
- 额度不足/429：查看实际额度和重置时间。重启或反复 OAuth 不能增加额度；不要自动换到 API 付费。
- 模型不支持/旧 Claude 或 OpenRouter 配置残留：用 `hermes model` 选当前账号可用模型，核对 provider 与 base URL。
- TLS/代理错误：检查目标进程实际环境。终端能联网不代表 Windows 登录任务、launchd 或 systemd 继承了相同代理；保留 TLS 校验，不用 `--insecure` 作为常规修复。

## 正确重启网关

在所选实例的终端执行，命令在各平台保持一致：

```text
hermes gateway status
hermes gateway restart
hermes gateway status
```

如果没有运行则 `hermes gateway start`。如果服务确实未安装且用户需要常驻，再 `hermes gateway install` 和 `start`。如果之前明确使用前台模式，在可保留的终端里重新 `hermes gateway run`；不要给同一机器人同时再开一个后台实例。

**先收集状态，再重启；重启完成后再测试。** 当前实现可能先排空运行中的任务，输出 draining 及等待上限。检查 active work 和退出进度，等待合理完成，不立刻 `kill -9` 或连续 restart。强制终止可能影响正在执行的业务；仅在确定无法恢复并且用户已授权中断时使用受支持的强制方式。

CLI/TUI 也可能连接同一个本地网关。刚开始模型测试就同时 restart，可能出现 WebSocket `1000/1013` 或连接关闭错误。先等健康，再补测一轮；这类现象不直接证明订阅失效。

### 原生 Windows

在同一 Windows 用户、同一 Hermes 安装的 PowerShell 中运行上述命令。可用 `Get-Command hermes -All` 排除旧安装遮挡，用 `Get-ScheduledTask` 检查 Hermes 任务状态。常驻通常是用户登录任务，不把登出后停机当成认证故障。

如果任务运行但子进程立刻退出，查看 Hermes 自己的日志与任务最近结果。不要关闭杀毒软件、全盘添加排除项，或手动删除整个任务计划程序目录。

### WSL2

Windows 中先检查 `wsl --list --verbose`，必要时启动正确发行版，再进入 Linux 执行 Hermes 命令。核对 systemd 与用户服务是否运行。不要在 PowerShell 重启原生 Hermes 后声称修复了 WSL 里的实例。

不要把 `wsl --shutdown` 当作常规重启按钮：它会终止所有发行版里的工作。需要它时先说明影响并检查其他任务。

### macOS / Linux

在原安装用户下执行 gateway 命令；macOS 检查 launchd，Linux 检查实际使用的 user/system systemd scope。普通用户服务不先加 sudo。服务环境缺新工具时按安装渠道更新服务定义，保留已有业务配置。

## 恢复后的闭环

1. 重新确认网关和 Feishu healthy/connected，而不只看命令退出 0。
2. 模型测试成功后，在原目标群让用户用原允许账号 @机器人发一条新消息。
3. 核对入站、模型回复和回信；确认没有重复网关或重复回复。
4. 说明故障原因、最小改动、验证结果和仍待用户操作的事项。正常恢复不需要新建机器人、新群或清空历史。

若同一失败重现，保留新的证据并换层诊断；不要无限重启、重新扫码、重复发消息或重复提交有副作用的用户任务。
