# Hermes 从零安装与飞书群接入 Skill

给 AI Agent 使用的中文操作技能：从检查目标电脑开始，完成 Hermes 安装、ChatGPT/Codex 订阅登录、飞书机器人接入、建群/复用群、访问控制、后台常驻与收发验收，并处理突然不回复的故障。

**Hermes 已支持原生 Windows 10/11，接飞书无需先装 WSL。** 本技能默认使用原生 Windows 路径，同时提供 WSL2、macOS 和 Linux 的条件分支。平台与接口核验日期为 2026-10-24；执行时仍需核对[当前官方文档](https://hermes-agent.nousresearch.com/docs/user-guide/windows-native)及目标机版本。

## 直接交给你的 Agent

把本仓库链接发给能操作目标电脑的 Agent，并说：

> 请读取这个仓库的 SKILL.md，根据我的操作系统安装或复用 Hermes，登录我指定的 ChatGPT 订阅，接入我指定的飞书账号和群。先核对已有机器人，保留现有配置，最后验证群内真实收发。不响应时按排障参考诊断。

如果 Agent 支持本地 skills，把整个仓库复制/克隆到它的技能目录中，文件夹名保持 `hermes-feishu-setup`，再在新会话中调用：

```text
$hermes-feishu-setup 帮我从零配置 Hermes 和飞书群。
```

Codex 可使用其 skill installer 从本仓库安装；其他 Agent 按其技能目录规范安装。只把技能下载到本机不会自动授权账号、创建机器人或执行安装，用户仍需在官方页面完成登录/扫码。

## 内容

- [SKILL.md](SKILL.md)：主流程、执行边界与验收标准。
- [平台安装](references/platforms.md)：原生 Windows、WSL2、macOS/Linux 与常驻差异。
- [认证与学习能力](references/auth-and-learning.md)：订阅独立登录、记忆、技能和后台复盘。
- [飞书接入](references/feishu.md)：指定账号扫码、复用机器人、建群、权限与测试。
- [不回复排障](references/troubleshooting.md)：状态/日志定位、网关重启及平台恢复路径。
- [辅助脚本](scripts/feishu_admin.py)：标准库实现的机器人查询与幂等建群；默认只预览建群请求。

## 准备与限制

- Agent 需要目标电脑的执行通道；无法连接时只能指导用户执行，不能假称已配置。
- 用户持有并选择自己的订阅账号、飞书账号和应用权限。
- 基础接入不要求安装 lark-cli 或 Codex CLI。
- 登录与扫码由账号持有人完成；其他服务、可选工具和外部记忆服务可能需要独立凭证。
- 机器人运行在哪台电脑，就受那台电脑的运行、联网和休眠状态影响。

仓库使用通用步骤和占位符，不附带可复用的账号、密钥、登录码、群 ID 或私人配置。不要将实际 `.env`、`auth.json`、日志、二维码、会话或备份提交到仓库。

## 辅助脚本示例

需要 Python 3.10+；路径必须替换为当前目标 profile 的真实 home。Windows 有 `py` 时可使用 `py -3` 替代 `python3`。

```text
python3 scripts/feishu_admin.py --help
python3 scripts/feishu_admin.py new-request-id
python3 scripts/feishu_admin.py --home "实际HermesHome" inspect
```

建群必须已有用户授权。先按飞书参考预览，使用相同 UUID 加 `--execute` 执行；结果未知时先核对，不更换 UUID 反复创建。

## 维护

优先依据 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs)、[OpenAI 认证文档](https://learn.chatgpt.com/docs/auth)和 [Microsoft WSL 文档](https://learn.microsoft.com/en-us/windows/wsl/)更新。不要把一次机器上的错误固化成所有电脑都要执行的重装、提权或关闭安全设置步骤。

验证范围：技能结构、相对链接、脚本本地预览与模拟 API 行为；实际接入流程在 macOS 验证过。Windows/WSL 步骤依据当前官方文档，未在本仓库发布时进行真实 Windows 安装验收。

MIT License。与 Hermes/Nous Research、OpenAI、飞书及 Microsoft 无官方隶属关系。
