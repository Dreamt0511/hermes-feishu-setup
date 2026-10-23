# 飞书机器人、建群与权限

## 识别正确的账号与应用

以 `hermes config path` 和 `env-path` 确认所选 home；凭证只检查“存在/缺失”，不整份打印。不同 profile 的 `.env` 不自动共享。

已有 App ID/App Secret 时，先查询机器人名称和已加入群。可以使用本技能的辅助脚本，不读取或改动机器上 lark-cli、飞书客户端已有登录：

```text
python3 scripts/feishu_admin.py --home "实际HermesHome" inspect
```

Windows 有 `py` 启动器时将前缀换为 `py -3`。在技能根目录执行，或对脚本使用绝对路径。`--home` 必须是本次选中 profile 的真实目录，不能照抄当前电脑路径。

## 新建与复用

`hermes gateway setup` → 按菜单文本选择 Feishu / Lark。

- 新建：选扫码创建，用户用**目标账号**在手机确认。创建成功后继续同一向导；记录机器人名称、非敏感标识，不再要求扫第二次创建码。
- 复用：选手动输入现有 App ID 和 App Secret；密钥使用隐藏输入或安全本机文件，不贴在聊天或命令行参数中。
- 长连接：选择 websocket。客户端向飞书建立出站连接，不额外开公网回调。
- 凭证写入后读回基本信息。向导可能使用启动时的旧快照，收尾一行“没有配置平台”不能推翻 API 验证与实际配置；用新进程核对。

若没有自动创建流程，走官方开发者后台：创建企业自建应用、启用机器人、配置接收消息与发送消息等当前必要权限；事件订阅 `im.message.receive_v1`，长连接模式。若要使用审批卡片，另配置 `card.action.trigger` 回调。权限和事件通常需发布应用版本后生效，管理员审批由用户组织处理。

权限以当前官方文档/错误所需 scope 为准，不默认申请通讯录、云盘或所有消息的最大权限。

## 访问策略

个人测试的建议值（具体范围以用户方案为准）：

```dotenv
FEISHU_CONNECTION_MODE=websocket
FEISHU_ALLOW_ALL_USERS=false
FEISHU_ALLOWED_USERS=ou_ALLOWED_USER
FEISHU_GROUP_POLICY=allowlist
FEISHU_REQUIRE_MENTION=true
```

由向导或安全文件编辑工具合并写入；不能用此片段覆盖整份 `.env`。允许的 open_id 必须来自**当前机器人 App**对应的用户，不能照搬其他飞书应用/CLI 返回的 ID。

向导的“只允许名单用户私聊”和“群内被 @时回复”并非同一项策略。收尾核对全局门禁和 `platforms.feishu.extra.group_rules` 两层，防止向导默认 `open` 让任何群成员都能调用模型。

若希望共享全群上下文，先说明当前 `group_sessions_per_user=true` 会分用户保存对话，再按用户明确选择调整。当前飞书适配器会拦截未 @的消息，不会自动把所有闲聊写入模型上下文；引用回复能带入原消息。关闭 `require_mention` 会改变触发行为，不能宣传为“静默读取全群、仅 @才回复”。

## 接入已有群

确认准确群名/ID，用户用目标飞书账号将机器人添加到群，或在已具备权限及授权时用机器人/应用 API 加入。不要用另一个账号看到的同名群代替。

只读查询群，核对机器人、群主和允许用户。保留已有成员，不把“接入机器人”扩大成修改群成员/群设置。

## 用户授权新建群

辅助脚本用新机器人自身的凭证调用官方 OpenAPI，不需要目标用户的密码，也不借用本机旧账号。新群是私有普通群，用户为群主，创建用机器人自动入群。

1. 指定正确 home、当前 App 下的用户 open_id 与群名。
2. 用 `python3 scripts/feishu_admin.py new-request-id` 生成请求 UUID。
3. 预览下面命令，保留同一个 UUID：

```text
python3 scripts/feishu_admin.py --home "实际HermesHome" create-group --name "Hermes 测试群" --owner-id ou_ALLOWED_USER --request-id UUID
```

4. 范围已获用户授权后，在**原命令末尾**追加 `--execute`。不重复索取已给出的授权。
5. 脚本在该 home 的 `state/feishu-setup/` 记录请求及结果。超时/结果未知时使用相同请求 UUID，先 inspect 核对；不要换 UUID 反复创建。

如果用现有连接器或自行调用 API，契约为：

```text
POST /open-apis/auth/v3/tenant_access_token/internal
POST /open-apis/im/v1/chats?user_id_type=open_id&uuid=稳定请求UUID
```

创建群正文包含 `name`、`owner_id`、`user_id_list: [owner_id]`、`chat_type: private`、`chat_mode: group`。token 仅保留在进程内，密钥不写进请求记录。出现缺 scope、目标用户不可见或跨租户错误时，报告实际错误并处理对应限制；不换用无关账号绕过。

## 测试与交付

先看 `hermes send --help`。用户已授权向这个群发连接测试时使用：

```text
hermes send --to feishu:oc_TARGET_CHAT --json "连接测试：请使用约定账号在本群 @机器人 发送你好。"
```

只报告真实结果；机器人发信成功不等于用户入站成功。用户用其账号 @机器人后，核对同群同用户的入站、模型处理和回信证据。

如果 Agent 无法控制目标手机/账号，交接这一个必要动作并保留已完成配置。用户回复完成后继续验证，不重新创建机器人或群。

## 依据

- [Hermes 飞书接入](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu)
- [飞书创建群 API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/chat/create)
- [飞书开发者平台](https://open.feishu.cn/)
