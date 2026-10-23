---
name: hermes-feishu-setup
description: "从零安装或恢复 Hermes Agent，登录 ChatGPT/Codex 订阅并接入指定飞书账号和群；覆盖原生 Windows、WSL2、macOS/Linux、机器人复用、后台常驻、记忆技能验收和不回复排障。"
---

# Hermes 安装与飞书群接入

把目标电脑配置为可持续运行的 Hermes 飞书机器人，并分别核验模型调用、飞书发信、用户入站消息和上下文延续。已有安装或机器人时从缺失步骤继续。

## 开始前

1. 确认目标电脑、操作系统和执行环境；当前 Agent 所在电脑不一定是待安装电脑。没有目标机执行通道时，提供分步命令并让用户回传脱敏结果，不宣称已经远程完成。
2. 确认模型来源、飞书账号/租户、复用还是创建机器人、已有群还是新建群，以及谁能使用。已明确的事项不重复询问。账号登录和扫码由用户本人操作。
3. 先检查安装、实际配置路径、profile、网关状态和现有业务。已有其他账号或生产配置时先备份；需要并存时使用独立 profile，后续每条命令保持同一 profile。
4. 给出本次具体范围。已有授权覆盖的安装、登录、配置和测试继续执行；新建群、发测试消息、扩大可用成员或修改系统启动方式应落在用户已授权范围内。

本技能本身不包含凭证。不要输出或上传 `.env`、`auth.json`、token、App Secret、完整日志和真实会话；排障只提取必要字段。脚本、源码、依赖与状态保存在目标机本地磁盘。

## 1. 选择安装路径

先读 [references/platforms.md](references/platforms.md)，只执行适合目标机的一条路径。

- **原生 Windows**：截至 2026-10-24，官方支持 Windows 10/11 的原生 CLI 和消息网关，普通飞书接入优先采用原生安装，无需先装 WSL。
- **WSL2**：适合用户已有 Linux 开发环境、确实需要 POSIX 工具或明确选择 WSL。只用 WSL2，区分 Windows 和 Linux 两侧的路径、凭证与服务。
- **macOS/Linux**：使用官方安装方式。已有安装先诊断，不覆盖数据目录重装。

每次实际执行前打开当前官方安装文档并核对 `--help`；这里的命令是已核验的操作基线，不是永久不变的接口。

## 2. 登录模型并先验证一轮

读 [references/auth-and-learning.md](references/auth-and-learning.md)。默认遵循用户选择的 ChatGPT/Codex 订阅；不自行改成 Nous、OpenRouter 或 API 计费。

```text
hermes --version
hermes config path
hermes config env-path
hermes gateway status
hermes auth add --help
hermes model --help
```

需要独立订阅登录时，先确认该键受当前版本支持，再执行：

```text
hermes config set auth.adopt_external_logins false
hermes auth add openai-codex --type oauth --label hermes-chatgpt
```

设备码不可用时让用户在 ChatGPT 安全设置启用设备代码登录，或使用当前版本支持的 `--browser`。及时把本次新 URL 和验证码展示给用户，等待其完成；旧码过期则重新发起。

**`codex login --device-auth` 只完成 Codex CLI 登录，不能替代 Hermes 自己的登录。** 不要求先安装 Codex CLI；仅在用户需要该 CLI 或正在诊断它时使用该命令。

登录后通过 `hermes model` 的实际模型目录选择可用模型；显式设置 `model.provider=openai-codex`，检查旧 provider 的 `model.base_url` 和旧模型名是否残留。不把固定模型 ID 写成长期保证。调用模型时省略最大输出 token 参数。

```text
hermes auth status openai-codex
hermes usage --provider openai-codex --json
hermes chat --oneshot --quiet --toolsets terminal --reasoning low -q "请只回复：Hermes 模型连接成功。不要调用工具。"
```

按当前版本 `--help` 调整测试命令。`--toolsets none` 不是有效的禁用工具写法。读取额度成功只证明凭证可用，仍需一次实际模型回复。

## 3. 接入指定飞书账号及机器人

读 [references/feishu.md](references/feishu.md)。先检查所选 Hermes home 中是否已存在飞书凭证，再通过机器人基本信息验证它；不要输出密钥。

- **已有机器人**：复用正确的 App ID/App Secret，核验所属租户、机器人名称、群权限和长连接。
- **新机器人**：运行 `hermes gateway setup`，按菜单文本选择 Feishu / Lark，再选择扫码创建。菜单序号随版本改变，不能固定输入某个序号。
- 需要新飞书账号时，让用户先在手机切换到该账号再扫码；不要改动本机原有飞书客户端或其他 CLI 的登录。
- 显示实际创建链接；工具支持时同时展示 PNG 二维码。不要仅生成图片而不展示，也不要将授权链接发送到第三方二维码服务。
- 保存授权会话/进程句柄，用户回复后读取结果。拿到机器人信息和凭证即复用继续，不重复发起创建。
- 选择 **WebSocket 长连接**，通常不需要公网域名、开放入站端口或 webhook。

依赖缺失时先确认安装类型和命令支持，再通过 Hermes 自己的包管理安装 `feishu` extra；不对托管环境运行裸 `pip install`。

## 4. 配置群与访问范围

先核对机器人已加入的群，使用用户指定群；用户授权新建时创建私有群，把**扫码账号在当前应用下的 open_id**加为成员并设为群主。不同 App 的 open_id 不可混用。

可用 [scripts/feishu_admin.py](scripts/feishu_admin.py) 读取机器人/群信息或幂等创建群。它只用 Python 标准库；不依赖本机 lark-cli 登录。使用方法与备选原生 API 路径见 [references/feishu.md](references/feishu.md)。

默认按本次方案限制成员及群范围。首次个人测试可设为只允许扫码账号、仅指定群、必须 @机器人；用户明确要求多人使用时按其名单或群策略配置。

检查并合并配置，不整段覆盖已有 `platforms`：

```yaml
platforms:
  feishu:
    extra:
      default_group_policy: disabled
      group_rules:
        oc_TARGET_CHAT:
          policy: allowlist
          allowlist:
            - ou_ALLOWED_USER
          require_mention: true
```

以上 ID 是占位符。同步核对 `.env` 中 `FEISHU_ALLOWED_USERS`、`FEISHU_GROUP_POLICY` 与 `FEISHU_ALLOW_ALL_USERS`，避免全局门禁和群规则冲突。以实际读取配置为准，不以向导一行提示为准。

## 5. 启动、学习能力与验收

所有写入完成后，再安装/启动或重启网关，并等待健康状态；**不要并行运行重启和模型验证**。

```text
hermes gateway install
hermes gateway start
hermes gateway status
```

网关已经运行、需要应用新配置时用 `hermes gateway restart`，不要重复安装。Windows、WSL2 与 macOS 的常驻差异见平台参考。

检查下列实际结果，不为接入飞书盲目打开所有可选工具，也不擅自关闭已有审批：

```text
hermes tools list --platform feishu
hermes memory status
hermes config get memory
hermes config get skills
hermes config get auxiliary.background_review
hermes curator status
hermes config get group_sessions_per_user
```

长期记忆、技能创建、后台复盘与 Curator 是不同机制，说明见认证与学习参考。能力开启不等于已经写入了记忆或产生了技能。

依次验收：

1. 网关在所选 profile 下运行，Feishu 状态为 connected。
2. 所选 provider 实际模型调用成功，记录模型名与认证方式，隐藏账号信息。
3. 在已授权范围内向目标群发一条测试消息，核对成功结果/消息 ID。
4. 用户用指定飞书账号在群内真正 @机器人，收到模型回复；机器人给自己发消息不能替代入站验收。
5. 同一用户连续两轮验证上下文，例如先说“本轮测试代号是蓝松”，下一轮问代号。换话题可用 `/new`。
6. 用户需要验证长期学习时，使用其同意的无敏感测试偏好，核对真实记忆写入，再开新会话验证；不凭“我记住了”这句回复判断成功。

交付说明包含群链接、机器人名称、模型来源、使用范围、常驻方式、已完成与待用户完成的验收。说明服务在哪台电脑，休眠/关机/断网会影响可用性。已加入群的飞书链接可用 `https://applink.feishu.cn/client/chat/open?openChatId=群ID`，不要误用 `chatId=`。

## 不回复或断连

直接转到 [references/troubleshooting.md](references/troubleshooting.md)。先定位“没收到消息 / 收到但被门禁拦截 / 模型失败 / 回信失败 / 网关停机”哪一层，再做最小恢复。无需重走整个安装或建机器人流程。

## 官方依据与版本变化

核验基线：2026-10-24，Hermes Agent v0.22.5；其他版本以实际命令和当前官方文档为准。

- [Hermes 安装](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
- [平台支持](https://hermes-agent.nousresearch.com/docs/getting-started/platform-support)
- [原生 Windows](https://hermes-agent.nousresearch.com/docs/user-guide/windows-native)
- [飞书接入](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu)
- [Codex 认证](https://learn.chatgpt.com/docs/auth)
