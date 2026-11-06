---
name: yingdao-rpa-toolkit
displayName: 影刀RPA工具包
description: 通过影刀开放 API 触发 RPA 应用运行并查询结果，覆盖凭据配置、授权获取 token、启动应用（支持参数、优先级、幂等 uuid、干跑预览）、按 jobUuid 查询状态与轮询到终态。当用户要「用影刀/ShadowBot 跑一个应用」「触发影刀 RPA」「看这次运行结果/输出参数」「验证影刀 API 凭据是否有效」时使用。走云端开放 API，不是本地客户端操作。
agent_created: true
metadata:
  version: "0.1.0"
---

# 影刀 RPA 工具包

## 概述

把影刀开放 API 封装成一条可执行链路：**配置 → 鉴权 → 启动应用 → 查询结果**。
所有命令共用 `scripts/yd.py`，stdout 固定输出单条 JSON，便于代理稳定解析；日志与提示只写 stderr。

## 何时使用

- 用户要求用影刀/ShadowBot 执行某个应用，并给出了应用与机器人（或机器人分组）。
- 需要验证 `accessKeyId / accessKeySecret` 是否可用。
- 需要先取一个 accessToken，再把它直接传给后续命令或其它工具（token 不落盘）。
- 需要预览一次启动请求的 method / URL / body（`--dry-run`），先核对再提交。
- 已经拿到 `jobUuid`，需要查状态、输出参数、失败原因或截图地址。
- 需要轮询直到任务进入终态（`--wait`）。

不要在以下情况使用：

- 操作用户本机的影刀客户端（登录、触发器、Studio 编辑）→ 使用本地客户端类技能。
- 需要查询机器人列表、应用列表、调度任务，或重试/停止运行、查运行日志、上传文件、写工作队列 → **本版未实现**，不要假装能调用。
- 只想了解影刀 API 文档、不执行操作 → 直接读项目根目录的《影刀RPA开放API接口文档.md》。
- 结果需要排版成固定汇报表格 → 交给 `rpa-result-formatter`。

## 前置约定

下文 `{SKILL_DIR}` 指本技能目录（安装后默认 `C:/Users/admin/.workbuddy/skills/yingdao-rpa-toolkit`）。

```bash
SKILL_DIR="C:/Users/admin/.workbuddy/skills/yingdao-rpa-toolkit"
PY="D:/Program Files/miniconda3/envs/python_3_10/python.exe"
[ -x "$PY" ] || PY=python
# 不要 cd 到技能目录：保持当前工作目录，才能发现当前项目的 .yingdao/config.json
```

核心零第三方依赖（标准库 `urllib`），Python 3.10+ 均可运行；上面的 3.10 路径只是本机约定。

## 意图路由

| 用户意图 | 先读 | 执行 |
|---|---|---|
| 首次配置、凭据缺失、换环境 | `references/auth.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" config init` |
| 看当前生效配置（密钥脱敏） | `references/auth.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" config show` |
| 验证凭据、token 是否有效 | `references/auth.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" auth check` |
| 获取 token 并传给后续命令 | `references/auth.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" auth token`，再把 `data.access_token` 传给 `--access-token` |
| 触发一次应用运行 | 本文件「标准工作流」 | `"$PY" "$SKILL_DIR/scripts/yd.py" job start ...` |
| 查某次运行的状态/输出/失败原因 | 本文件「标准工作流」 | `"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid ...` |
| 字段含义、退出码、JSON 结构 | `references/output-contract.md` | — |

## 标准工作流

```bash
# 1. 首次使用：生成配置模板（项目级；无 .git 时生成到用户级）
"$PY" "$SKILL_DIR/scripts/yd.py" config init
# 编辑 .yingdao/config.json 填入 accessKeyId / accessKeySecret

# 2. 验证凭据
"$PY" "$SKILL_DIR/scripts/yd.py" auth check

# 2.1 可选：先取 token，再显式传给后续命令（token 不落盘）
"$PY" "$SKILL_DIR/scripts/yd.py" auth token
# 读取 data.access_token 后：
#   job start ... --access-token <token>
# 或用 shell 管道：
#   TOKEN=$("$PY" ... auth token --format text)
#   YD_ACCESS_TOKEN="$TOKEN" "$PY" ... job query --job-uuid <uuid>

# 3. 先干跑核对请求体（不发送请求）
"$PY" "$SKILL_DIR/scripts/yd.py" job start \
  --app-id <appId> --account-name <机器人名称> \
  --param 月份=2026-10 --param 页数=10:int --dry-run

# 4. 确认后真实提交，拿 jobUuid
"$PY" "$SKILL_DIR/scripts/yd.py" job start \
  --app-id <appId> --account-name <机器人名称> \
  --param 月份=2026-10

# 5. 查结果：默认单次查询；加 --wait 轮询到终态
"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid <jobUuid>
"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid <jobUuid> --wait --interval 30 --max-wait 1800
```

长流程建议分两步：先 `job start` 拿 `jobUuid`，再由用户决定何时 `job query --wait`，避免单条命令长时间阻塞。

## 关键参数

- `--app-id`（别名 `--robot-uuid`）：**应用 uuid（appId）**，不是机器人 uuid。
- `--account-name` 或 `--robot-group-uuid`：必须且只能提供一个；都为空时任务会永久停在 `waiting`，工具已在本地拦截。
- `--param NAME=VALUE[:TYPE]`：可重复；`TYPE` 取 `str/int/float/bool/file`，默认 `str`。
- `--params-file`：参数 JSON（对象，或 `{name,value,type}` 数组），适合参数很多的场景。
- `--idempotent-uuid`：不超过 36 位；网络超时重发时避免重复启动。
- `--priority` / `--wait-timeout-seconds` / `--run-timeout` / `--execute-scope`：透传接口同名字段。
- `--access-token`：直接使用已有 token（优先于凭据）；也可用 `YD_ACCESS_TOKEN` 传入。token 只在内存，不写文件。

## 硬规则（必须遵守）

1. **不得编造标识**：`appId`、`robotClientName`、`jobUuid` 必须来自用户明确提供或上游查询结果，不要猜测。
2. **真实启动前先确认**：用户尚未在本轮明确给出「应用 + 机器人 + 参数」时，先复述计划并确认；首次执行先 `--dry-run`。
3. **两个成功要分开看**：接口是否成功看 `success`；任务是否成功看终态 `finish`。终态非 `finish` 时命令退出码为 5。
4. **token 默认不外泄**：`auth check` 只输出脱敏 token。唯一例外是 `auth token`——它的用途就是交付完整 token，必须**直接传给下一条命令**（`--access-token` / `YD_ACCESS_TOKEN`），不得写入文件、日志或回复正文，也不得使用 `--save`。`--dry-run` 预览同样默认掩码（`secret`/`token` 类字段为 `***`，`accessKeyId` 为 `abcd****wxyz`）；只有用户明确要求核对原文时才加 `--show-secrets`。
5. **不跨技能越界**：本地客户端操作走本地客户端类技能；结果排版走 `rpa-result-formatter`。
6. **未实现的能力不要假装有**：本版没有列表查询、重试、停止、日志接口，遇到这类需求直接说明并给出替代路径。

## 输出契约与退出码

```json
{"schema_version":1,"ok":true,"command":"job query","data":{},"warnings":[],"meta":{}}
```

失败时 `ok=false`，`error={type,code,message,hint,request_id}`，stdout 仍是合法 JSON。
`auth token --format text` 是唯一例外：只输出 token 原文，便于 shell 管道消费。

| 退出码 | 含义 |
|---|---|
| 0 | 成功（job 类要求终态 `finish`） |
| 1 | 接口或业务错误 |
| 2 | 参数或配置错误（未发请求） |
| 3 | 鉴权失败 |
| 4 | 网络错误、超时或轮询超时 |
| 5 | 任务终态为 `error/stopped/skipped/cancel` |
| 6 | 前置条件不满足（预留给重试/停止类命令） |

## 关键事实与易错点

- `job start` 的 `robotUuid` 是 **应用 uuid**（appId），不是机器人 uuid。
- `accountName` 与 `robotClientGroupUuid` 互斥；两者都缺时任务不会执行，只会排队到超时。
- 机器人 `offline` 时派发仍可能返回成功，但任务会排队，直到 `waitTimeoutSeconds` 超时。
- 入参总长按 8000 字符本地拦截；超限请拆批，或把长文本转成 `type=file` 的 URL。
- 官方建议轮询 30 秒一次，终态即停止；本工具默认取配置 `pollIntervalSeconds`。
- token 最长 2 小时，按响应 `expiresIn` 计算内存过期时间（预留 30 秒安全边界）；**不落盘**，跨命令用 `--access-token` 或 `YD_ACCESS_TOKEN` 传递。
- 传入的 token 失效时返回退出码 3，并提示重新执行 `auth token`，不会静默换成凭据换取的新 token。
- 遇到 429 会按 `Retry-After`（缺省指数退避）重试，最多 3 次。
- Windows 控制台编码已在入口统一为 UTF-8。

## 当前版本边界

已实现：`config init/show`、`auth check`、`auth token`、`job start`、`job query`。
未实现（后续迭代）：机器人/应用/任务列表、`job retry/stop`、运行日志、文件上传、工作队列、回调、RPA 账号管理、HTTP 常驻服务。

## 资源索引

| 资源 | 路径 | 何时使用 |
|---|---|---|
| 主命令 | `scripts/yd.py` | 所有操作的唯一入口 |
| 核心库 | `scripts/yingdao_rpa/` | 排障或二次开发时阅读 |
| 输出契约 | `references/output-contract.md` | 解析 JSON、确认退出码 |
| 配置与鉴权 | `references/auth.md` | 配置凭据、token 失效排查 |
| 配置样例 | `config.example.json` | 首次配置参考 |
| 项目文档 | `docs/product-design.md`、`docs/tech-design.md` | 了解范围与架构 |
