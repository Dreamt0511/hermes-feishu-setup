# 订阅登录与学习能力

## 登录与账号边界

- 使用用户指定的 ChatGPT 账号和工作区；不把 API key 计费当成订阅额度。
- Hermes 使用自己的认证存储。Codex CLI 的成功登录不代表 Hermes 已登录，反之亦然；安装 Hermes 也不要求先装 Codex CLI。
- 与 Codex CLI/桌面端并用时，优先给 Hermes 独立 OAuth 登录；在版本支持时设置 `auth.adopt_external_logins=false`，避免后台自动借用其他客户端的凭证。
- 不把别人的 `auth.json` 拷到目标机，不通过聊天接收 refresh token。账号持有人自行登录/扫码。

首先检查本机已有状态，避免无意义地重复登录：

```text
hermes auth status openai-codex
hermes auth list openai-codex
hermes config get model
```

没有有效 Hermes 凭证时运行 `hermes auth add openai-codex --type oauth --label hermes-chatgpt`。需要在聊天里清楚展示设备码而不自动开浏览器时，确认支持后加 `--no-browser`。浏览器 PKCE 备选为 `--browser`，由 Hermes 自己处理 callback；不要让两个登录程序同时占用同一个回调端口。

设备码流程提示需要启用时，让用户打开 [ChatGPT 安全设置](https://chatgpt.com/#settings/Security)，在自己的账号/工作区允许设备代码登录。启用后重新发起 **Hermes** 登录，给新验证码；不额外绕一轮 `codex login`。企业工作区受管理员策略限制时，如实说明并使用已允许的路径。

发起后立即显示工具实际返回的 URL、验证码和有效期，保留进程句柄。用户回复完成后由 Agent 继续检查该进程结果，再检查 Hermes 登录状态。过期、拒绝和额度不足分别处理，不反复登录消耗用户时间。

## 模型与计费验收

通过 `hermes model` 实时选择该账号可用的模型，再读回 `model`。切到 `openai-codex` 后检查旧 OpenRouter/Claude 的模型名、base URL 和自定义覆盖是否仍在；删除明确过时的那一项，保留其他配置。

额度查询、模型列表、模型推理是三种不同证据。完整验收至少包含实际推理成功。不要给请求添加 `max_tokens`、`max_output_tokens`、`max_completion_tokens`、`maxOutputTokens` 或同义的输出上限。

如果用户自己还需要 Codex CLI，可独立执行其 `codex login --device-auth`。报告时分别说明两个程序的登录结果，不能让用户以为一个验证码自动登录全部客户端。

## 记忆、技能、复盘：检查实际开启状态

| 机制 | 核验入口 | 正确解释 |
|---|---|---|
| 内置长期记忆/用户档案 | `hermes memory status`、`hermes config get memory` | 偏好、项目事实等由 memory 工具实际保存，跨会话使用 |
| 会话搜索 | `hermes tools list --platform feishu` 中 session_search | 检索该 profile 的历史会话，区别于飞书完整群历史 |
| 技能沉淀 | 同一工具列表中的 skills、`hermes config get skills` | 用 skill_manage 记录可复用流程；不会每句聊天都生成 skill |
| 对话后的后台复盘 | `hermes config get auxiliary.background_review` | 可在会话后提出/写入有价值的记忆与技能，取决于开关及审批 |
| 技能库维护 Curator | `hermes curator status` | 独立的低频维护；开启不代表启用 LLM 自动合并 |
| 外部用户画像服务 | `hermes memory status` | Honcho 等需另外配置；不为基础接入自动注册或购买 |

新安装常见默认是内置记忆和用户档案启用、技能创建提示启用、后台复盘启用，Curator 的 LLM consolidation 关闭。每次以实际配置为准，不为“完整配置”把所有选项强行打开。保留用户原有写入审批选择。

记忆和技能按 Hermes profile 组织。若要为测试账号与原有个人助手隔离资料，应使用不同 profile；仅仅换一个飞书账号并不会自动创建隔离的记忆库。

记忆只有真正写入才会持久化。允许使用用户同意的无敏感偏好进行验证，检查对应 home 的 `memories` 文件是否新增内容，再 `/new` 开新会话询问；不要把用户敏感偏好作为公开测试材料，也不要自行清空其记忆。

会话中的历史上下文和跨会话记忆分别管理。自然任务边界可使用 `/new`，让新的记忆快照生效；后台重启通常不等于新会话。

## 依据

- [OpenAI Codex 认证](https://learn.chatgpt.com/docs/auth)
- [Hermes 模型 providers](https://hermes-agent.nousresearch.com/docs/integrations/providers)
- [Hermes 借用 CLI 登录](https://hermes-agent.nousresearch.com/docs/user-guide/security#borrowed-cli-logins)
- [长期记忆](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
- [技能机制](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Curator](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator)
