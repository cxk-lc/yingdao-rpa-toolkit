---
name: yingdao-rpa-toolkit
displayName: 影刀RPA工具包
description: 通过影刀开放 API 触发 RPA 应用运行并查询结果，覆盖凭据配置、授权获取 token、启动应用（支持参数、优先级、幂等 uuid、干跑预览）、按 jobUuid 查询状态与轮询到终态。当用户要「用影刀/ShadowBot 跑一个应用」「触发影刀 RPA」「看这次运行结果/输出参数」「验证影刀 API 凭据是否有效」时使用。走云端开放 API，不是本地客户端操作。
agent_created: true
metadata:
  version: "0.1.1"
---

# 影刀 RPA 工具包

## 概述

把影刀开放 API 封装成一条可执行链路：**配置 → 鉴权 → 启动应用 → 查询结果**。
所有命令共用 `scripts/yd.py`，stdout 固定输出单条 JSON，便于代理稳定解析；日志与提示只写 stderr。

## 何时使用

- 用户要求用影刀/ShadowBot 执行某个应用，并给出了应用与机器人（或机器人分组）。
- 需要验证 `accessKeyId / accessKeySecret` 是否可用。
- 需要先取一个 accessToken，再把它直接传给后续命令或其它工具（token 不落盘）。
- 需要查询某台机器人的在线/空闲状态、IP 与备注（`robot info`）。
- 需要查 RPA 企业子账号列表，按关键词、手机号、账号类型或时间范围筛选（`account list`）。
- 需要找应用 `appId`、查应用列表（`app list`）或应用运行历史（`app runs`）。
- 需要查机器人任务队列/历史 job，按机器人、应用、状态、触发时间筛选（`robot tasks`）。
- 启动应用时需要按空闲状态、历史成功次数自动选机器人，或处理指定机器人忙碌的决策（`job start --auto-robot`）。
- 需要预览请求的 method / URL / query / body / headers（`--dry-run`，查询类命令均支持），先核对再提交。
- 已经拿到 `jobUuid`，需要查状态、输出参数、失败原因或截图地址。
- 需要轮询直到任务进入终态（`--wait`）。

不要在以下情况使用：

- 操作用户本机的影刀客户端（登录、触发器、Studio 编辑）→ 使用本地客户端类技能。
- 需要查询机器人全量列表、调度计划列表，或重试/停止运行、查运行日志、上传文件、写工作队列 → **本版未实现**，不要假装能调用。
- 只想了解影刀 API 文档、不执行操作 → 源码仓库内可读《影刀RPA开放API接口文档.md》；该文件不随发布包分发，安装态请改用 `references/` 中已沉淀的接口说明。
- 结果需要排版成固定汇报表格 → 交给 `rpa-result-formatter`。

## 前置约定

下文 `{SKILL_DIR}` 指本技能目录，即本 `SKILL.md` 所在目录（下例是本机安装位置，换机请替换为实际路径）。

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
| 查某台机器人是否在线/空闲 | `references/robot-info.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" robot info --name <名称>` |
| 查 RPA 企业账号列表 | `references/account-list.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" account list [--keyword ...]` |
| 查应用列表 / 找 appId | `references/app-list.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" app list [--app-name ...]` |
| 查应用运行历史 | `references/app-list.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" app runs (--app-id ... \| 时间范围)` |
| 查机器人任务队列 / 历史 job | `references/robot-tasks.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks [--status ...]` |
| 启动前选机器人 / 处理忙碌 | `references/robot-scheduling.md` | `"$PY" "$SKILL_DIR/scripts/yd.py" job start --app-id ... --auto-robot` |
| 触发一次应用运行 | 本文件「标准工作流」 | `"$PY" "$SKILL_DIR/scripts/yd.py" job start ...` |
| 查某次运行的状态/输出/失败原因 | 本文件「标准工作流」 | `"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid ...` |
| 字段含义、退出码、JSON 结构 | `references/output-contract.md` | — |

## 标准工作流

```bash
# 1. 首次使用：生成配置模板（项目级；无 .git 时生成到用户级）
#    只想先看落点：加 --dry-run，仅显示目标路径与是否存在，不创建文件
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

# 3. 可选：确认目标机器人在线且空闲
"$PY" "$SKILL_DIR/scripts/yd.py" robot info --name ceshi1
# 名称缺 @ 时：先查企业账号取 loginAccount；--suffix 可跳过查询；配置 enterpriseSuffix 仅作回退

# 3.1 可选：不知道 appId 时先查应用；也可查应用运行历史
"$PY" "$SKILL_DIR/scripts/yd.py" app list --app-name <应用名>
"$PY" "$SKILL_DIR/scripts/yd.py" app runs --app-id <appId> --begin-date <YYYY-MM-DD>

# 4. 先干跑核对请求体（不发送请求）
"$PY" "$SKILL_DIR/scripts/yd.py" job start \
  --app-id <appId> --account-name <机器人名称> \
  --param 月份=2026-10 --param 页数=10:int --dry-run

# 5. 确认后真实提交，拿 jobUuid
"$PY" "$SKILL_DIR/scripts/yd.py" job start \
  --app-id <appId> --account-name <机器人名称> \
  --param 月份=2026-10

# 6. 查结果：默认单次查询；加 --wait 轮询到终态
"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid <jobUuid>
"$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid <jobUuid> --wait --interval 30 --max-wait 1800
```

长流程建议分两步：先 `job start` 拿 `jobUuid`，再由用户决定何时 `job query --wait`，避免单条命令长时间阻塞。

## 关键参数

- `--app-id`（别名 `--robot-uuid`）：**应用 uuid（appId）**，不是机器人 uuid。
- `--account-name` / `--robot-group-uuid` / `--auto-robot`：三者只能选一个；都为空时用配置默认值，仍为空则本地拦截。
- `--param NAME=VALUE[:TYPE]`：可重复；`TYPE` 取 `str/int/float/bool/file`，默认 `str`。
- `--params-file`：参数 JSON（对象，或 `{name,value,type}` 数组），适合参数很多的场景。
- `--idempotent-uuid`：不超过 36 位；网络超时重发时避免重复启动。
- `--priority` / `--wait-timeout-seconds` / `--run-timeout` / `--execute-scope`：透传接口同名字段。
- `--access-token`：直接使用已有 token（优先于凭据）；也可用 `YD_ACCESS_TOKEN` 传入。token 只在内存，不写文件。
- `robot info --name`：机器人账号名；不带 `@企业标识` 时，先查企业账号取 `loginAccount`，查不到再回退 `--suffix` / 配置 `enterpriseSuffix`；都没有则本地拦截。
- `robot info --uuid`：机器人 uuid；切换调度模式后会变化，通常优先用 `--name`。该模式返回 `requested.resolvedBy=uuid`，`inputName/accountName` 为 `null`。
- `account list`：`--keyword` / `--phone` / `--account-type basic|senior` / 时间范围；`--size` 最大 100，`--all` 自动翻页（默认最多 50 页）。
- `app list`：`--app-id` / `--app-name`（模糊）/ `--owner`；`--size` 最大 100，`--all` 按页码翻页。
- `app runs`：`--app-id` 与时间范围至少给一个；只给时间时必须同时给起止；时间跨度最多 7 天；`--all` 按 `minId` 游标翻页。
- `robot tasks`：`--app-id`（接口字段 robotUuid）/ `--robot-client-uuid` / `--status` / 触发时间；`--all` 沿 `next`/`pre` 游标翻页。
- `job start`：未指定 `--account-name` / `--robot-group-uuid` 时默认自动选空闲机器人；`--auto-robot` 可显式强制自动（覆盖配置默认机器人）。
- `job start` 自动模式：多个空闲按该应用历史成功次数最多，否则随机；`--queue-if-busy` 仅与 `--account-name` 同用。
- `--dry-run`（全局）：只构造并输出预览，**不发请求、不写盘**；`config init --dry-run` 只显示目标路径与 `exists`，不会创建文件。
- `--show-secrets`（全局）：仅在 `--dry-run` 预览中生效，放开密钥原文；默认掩码，非预览场景传了也不改变行为。

## 硬规则（必须遵守）

1. **不得编造标识**：`appId`、`robotClientName`、`jobUuid` 必须来自用户明确提供或上游查询结果，不要猜测。
2. **机器人名称要完整**：企业版账号形如 `ceshi1@csqy1`。用户只给前缀时，先显式 `--suffix`；否则用 `account list` 找对应 `loginAccount`，再回退配置 `enterpriseSuffix`；都没有就停下来让用户补充，**不要猜企业后缀**。
3. **真实启动前先确认**：用户尚未在本轮明确给出「应用 + 机器人 + 参数」时，先复述计划并确认；首次执行先 `--dry-run`。
4. **忙碌不自动改派**：指定机器人非空闲时，`job start` 返回退出码 6 的 `dispatch_decision`，必须把 `idleCandidates` 给用户选择「排队」或「改派」；不得自行排队或换机器人。
5. **两个成功要分开看**：接口是否成功看 `success`；任务是否成功看终态 `finish`。终态非 `finish` 时命令退出码为 5。
6. **token 默认不外泄**：`auth check` 只输出脱敏 token。唯一例外是 `auth token`——它的用途就是交付完整 token，必须**直接传给下一条命令**（`--access-token` / `YD_ACCESS_TOKEN`），不得写入文件、日志或回复正文，也不得使用 `--save`。`--dry-run` 预览同样默认掩码（`secret`/`token` 类字段为 `***`，`accessKeyId` 为 `abcd****wxyz`）；只有用户明确要求核对原文时才加 `--show-secrets`。
7. **不跨技能越界**：本地客户端操作走本地客户端类技能；结果排版走 `rpa-result-formatter`。
8. **未实现的能力不要假装有**：本版没有机器人全量列表、调度计划列表、重试/停止、运行日志接口，遇到这类需求直接说明并给出替代路径。
9. **账号列表含个人信息**：`account list` 返回手机号等敏感数据，只在必要范围内展示，不要写入公开文档、日志或无关的共享位置。

## 输出契约与退出码

```json
{"schema_version":1,"ok":true,"command":"job query","data":{},"warnings":[],"meta":{}}
```

失败时 `ok=false`，`error={type,code,message,hint,request_id}`，stdout 仍是合法 JSON。
`meta` 恒含 `base_url` / `api_code` / `api_success` / `request_id` / `dry_run`；未发请求时中间三项为 `null`。
`auth token --format text` 是唯一例外：只输出 token 原文，便于 shell 管道消费；加 `--dry-run` 时改为输出预览文本，绝不输出 token。

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
- `job start` 未指定账号/分组时默认自动选机器人（走 4.4 空闲列表、4.1 近期成功次数）；指定机器人非空闲返回退出码 6 的 `dispatch_decision`，需用户选择排队或改派。
- `robot info` 的 `accountName` 必须是完整企业账号；`status` 为 `connected/idle/allocated/running/offline`，`online` 与 `idle` 是工具补充的派生字段。
- `robot info --name` 不带 `@` 时会先查企业账号（最多 3 页 × 100 条），匹配 `loginAccount` 的 @ 前缀或账号 `name`；多个匹配会要求改用完整 `loginAccount`。
- `accountName` 与 `robotClientGroupUuid` 互斥；两者都缺时任务不会执行，只会排队到超时。
- 机器人 `offline` 时派发仍可能返回成功，但任务会排队，直到 `waitTimeoutSeconds` 超时。
- 入参总长按 8000 字符本地拦截；超限请拆批，或把长文本转成 `type=file` 的 URL。
- 官方建议轮询 30 秒一次，终态即停止；本工具默认取配置 `pollIntervalSeconds`。
- `account list` 的 `size` 最大 100；时间筛选字段是秒级时间戳，CLI 可用 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS` 自动转换。
- `app list` 的 `size` 最大 100；`app runs` 的时间跨度最多 **7 天**，应用与时间筛选至少给一个，`--all` 用上一页最大 `id` 作为 `minId`。
- `robot tasks` 的 `robotUuid` 是 **应用 uuid**；`--all` 用 `nextId`/`preId` 游标，`hasData=false` 时停止。
- token 最长 2 小时，按响应 `expiresIn` 计算内存过期时间（预留 30 秒安全边界）；**不落盘**，跨命令用 `--access-token` 或 `YD_ACCESS_TOKEN` 传递。
- 传入的 token 失效时返回退出码 3，并提示重新执行 `auth token`，不会静默换成凭据换取的新 token。
- 遇到 429 会按 `Retry-After`（缺省指数退避）重试，最多 3 次。
- Windows 控制台编码已在入口统一为 UTF-8。

## 当前版本边界

已实现：`config init/show`、`auth check`、`auth token`、`robot info`、`robot tasks`、`account list`、`app list`、`app runs`、`job start`（含自动选机器人与忙碌决策）、`job query`。
未实现（后续迭代）：机器人全量列表、调度计划列表、`job retry/stop`、运行日志、文件上传、工作队列、回调、RPA 账号增删改/重置密码、HTTP 常驻服务。

## 资源索引

> Skill 发布包只包含 `SKILL.md`、`scripts/`、`references/`、配置样例与 `LICENSE`；`docs/`、`tests/`、`README.md`、`USAGE.md` 等仓库级文件不随包分发。表中标注「仅源码仓库」的条目在安装态不存在，不要当作可用资源引用。

| 资源 | 路径 | 何时使用 |
|---|---|---|
| 主命令 | `scripts/yd.py` | 所有操作的唯一入口 |
| 核心库 | `scripts/yingdao_rpa/` | 排障或二次开发时阅读 |
| 输出契约 | `references/output-contract.md` | 解析 JSON、确认退出码 |
| 配置与鉴权 | `references/auth.md` | 配置凭据、token 失效排查 |
| 机器人状态 | `references/robot-info.md` | 账号后缀规则、状态枚举、查不到机器人 |
| 机器人调度规则 | `references/robot-scheduling.md` | 指定优先、忙碌决策、空闲成功率选择 |
| 机器人任务队列 | `references/robot-tasks.md` | 游标翻页、状态筛选、任务字段 |
| 企业账号列表 | `references/account-list.md` | 筛选条件、时间戳、分页与字段说明 |
| 应用列表/运行记录 | `references/app-list.md` | 找 appId、应用筛选、7 天时间范围、minId 游标 |
| 配置样例 | `config.example.json` | 首次配置参考 |
| 接口原文（仅源码仓库） | `影刀RPA开放API接口文档.md` | 查完整接口定义；安装态不可用 |
| 项目文档（仅源码仓库） | `docs/product-design.md`、`docs/tech-design.md` | 了解范围与架构；安装态不可用 |
