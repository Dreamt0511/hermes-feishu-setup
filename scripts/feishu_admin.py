#!/usr/bin/env python3
"""Inspect a Hermes Feishu bot or create an authorized private group.

Python 3.10+, standard library only. Credentials stay in memory. Group creation
defaults to a local preview and requires --execute plus a stable request UUID.
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SetupError(Exception):
    pass


def read_settings(home):
    path = home / ".env"
    if not path.is_file() or not (home / "config.yaml").is_file():
        raise SetupError("--home 必须指向本次 profile 的 Hermes 配置目录。")
    settings = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key.startswith("FEISHU_"):
            continue
        if value.startswith('"'):
            try:
                decoded, end = json.JSONDecoder().raw_decode(value)
            except ValueError as exc:
                raise SetupError("飞书环境变量的双引号格式无效。") from exc
            remainder = value[end:]
            value = decoded
            if not isinstance(value, str) or (remainder.strip() and not remainder.lstrip().startswith("#")):
                raise SetupError("飞书环境变量应为单行字符串。")
        elif value.startswith("'"):
            end = value.find("'", 1)
            if end < 0:
                raise SetupError("飞书环境变量的单引号未闭合。")
            remainder = value[end + 1:].strip()
            if remainder and not remainder.startswith("#"):
                raise SetupError("飞书环境变量存在多余字符。")
            value = value[1:end]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        if "${" in value:
            raise SetupError("辅助脚本不展开 .env 变量引用；请使用 Hermes 或安全工具解析。")
        settings[key] = value
    for key in ("FEISHU_APP_ID", "FEISHU_APP_SECRET"):
        if not settings.get(key):
            raise SetupError("缺少飞书应用凭证，请先完成 Hermes 飞书向导。")
    domain = settings.get("FEISHU_DOMAIN", "feishu")
    if domain not in ("feishu", "lark"):
        raise SetupError("仅支持官方 feishu/lark 域名，不向自定义地址发送凭证。")
    return settings


class Feishu:
    def __init__(self, settings):
        self.settings = settings
        self.base = "https://open.feishu.cn" if settings.get("FEISHU_DOMAIN", "feishu") == "feishu" else "https://open.larksuite.com"
        self.token = None

    def safe(self, value):
        text = str(value)
        for secret in (self.settings["FEISHU_APP_SECRET"], self.token):
            if secret:
                text = text.replace(secret, "<redacted>")
        return re.sub(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", "<redacted>", text)

    def request(self, path, payload=None):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(self.base + path, data=data, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise SetupError(f"飞书 HTTP {exc.code}；请按请求 ID 和官方权限说明诊断。") from None
        except (URLError, TimeoutError, OSError):
            raise SetupError("网络请求未取得明确结果；创建群时请保留相同 UUID 并先核对现有群。") from None
        except ValueError:
            raise SetupError("飞书返回非 JSON 内容，未输出原始响应。") from None
        if not isinstance(result, dict) or result.get("code") != 0:
            if isinstance(result, dict):
                message = self.safe(result.get("msg", "未知错误"))[:400]
                raise SetupError(f"飞书 API code={result.get('code')}: {message}")
            raise SetupError("飞书响应格式无效。")
        return result

    def authenticate(self):
        result = self.request("/open-apis/auth/v3/tenant_access_token/internal", {
            "app_id": self.settings["FEISHU_APP_ID"],
            "app_secret": self.settings["FEISHU_APP_SECRET"],
        })
        token = result.get("tenant_access_token")
        if not isinstance(token, str) or not token:
            raise SetupError("认证响应缺少访问 token。")
        self.token = token

    def inspect(self):
        bot = self.request("/open-apis/bot/v3/info").get("bot", {})
        groups, seen, page = [], set(), ""
        while True:
            query = {"page_size": 100}
            if page:
                query["page_token"] = page
            data = self.request("/open-apis/im/v1/chats?" + urlencode(query)).get("data", {})
            groups.extend({key: item.get(key) for key in ("chat_id", "name", "owner_id")} for item in data.get("items", []))
            if not data.get("has_more"):
                break
            page = data.get("page_token")
            if not isinstance(page, str) or not page or page in seen:
                raise SetupError("群列表分页异常，未将不完整结果报告为完整。")
            seen.add(page)
        return {
            "app_id": self.settings["FEISHU_APP_ID"],
            "bot_name": bot.get("app_name") or bot.get("bot_name"),
            "bot_open_id": bot.get("open_id"),
            "groups": groups,
        }


def save_record(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        os.chmod(temporary, 0o600)
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def create_group(client, home, args):
    request_id = str(uuid.UUID(args.request_id))
    if not re.fullmatch(r"ou_[A-Za-z0-9]+", args.owner_id):
        raise SetupError("owner-id 必须是当前应用下的真实 open_id，不能使用文档占位符。")
    if not args.name.strip() or len(args.name) > 60:
        raise SetupError("群名需为 1–60 个字符。")
    payload = {"name": args.name, "owner_id": args.owner_id, "user_id_list": [args.owner_id], "chat_type": "private", "chat_mode": "group"}
    path = "/open-apis/im/v1/chats?" + urlencode({"user_id_type": "open_id", "uuid": request_id})
    if not args.execute:
        return {"dry_run": True, "method": "POST", "path": path, "body": payload, "app_id": client.settings["FEISHU_APP_ID"]}

    record_path = home / "state" / "feishu-setup" / ("create-" + request_id + ".json")
    if record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("app_id") != client.settings["FEISHU_APP_ID"] or record.get("body") != payload:
            raise SetupError("该 UUID 已用于不同应用或参数；先核对原请求，不覆盖记录。")
        if not record.get("chat_id") and time.time() - record["created_at"] >= 10 * 3600:
            raise SetupError("未知结果的请求已超过服务端 10 小时去重窗口；先 inspect 人工核对，不自动再建群。")
    else:
        record = {"request_id": request_id, "created_at": time.time(), "app_id": client.settings["FEISHU_APP_ID"], "body": payload}
        save_record(record_path, record)

    client.authenticate()
    chat_id = record.get("chat_id")
    if chat_id:
        if not re.fullmatch(r"oc_[A-Za-z0-9]+", chat_id):
            raise SetupError("本机建群记录的 chat_id 无效。")
        data = client.request("/open-apis/im/v1/chats/" + chat_id + "?user_id_type=open_id").get("data", {})
    else:
        data = client.request(path, payload).get("data", {})
        chat_id = data.get("chat_id")
        if not isinstance(chat_id, str) or not re.fullmatch(r"oc_[A-Za-z0-9]+", chat_id):
            raise SetupError("建群响应缺少有效 chat_id，保留同一 UUID 先核对结果。")
        record["chat_id"] = chat_id
        save_record(record_path, record)
    return {"chat_id": chat_id, "name": data.get("name"), "owner_id": data.get("owner_id"), "request_id": request_id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, help="实际 Hermes profile home，不自动猜测或读取其他账号")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("new-request-id", help="生成建群去重 UUID；不访问配置或网络")
    commands.add_parser("inspect", help="只读查询当前机器人的基本信息与已加入群")
    create = commands.add_parser("create-group", help="预览或幂等创建已获授权的私有群")
    create.add_argument("--name", required=True)
    create.add_argument("--owner-id", required=True)
    create.add_argument("--request-id", required=True)
    create.add_argument("--execute", action="store_true", help="使用已授权的参数执行；省略则无网络、无写入")
    args = parser.parse_args()
    if args.command == "new-request-id":
        print(uuid.uuid4())
        return 0
    if args.home is None:
        parser.error("inspect 和 create-group 需要显式 --home")
    try:
        home = args.home.expanduser().resolve()
        client = Feishu(read_settings(home))
        if args.command == "inspect":
            client.authenticate()
            result = client.inspect()
        else:
            result = create_group(client, home, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (SetupError, ValueError, OSError) as exc:
        print("操作未完成：" + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
