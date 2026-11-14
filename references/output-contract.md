# 输出契约与退出码

> 命令中的 `$PY` / `$SKILL_DIR` 见 `SKILL.md`「前置约定」；不要 `cd` 到技能目录执行。

所有命令的 stdout **只有一条 JSON**。日志、进度、人读提示一律写 stderr，避免污染机器解析。

## 1. 成功结构

```json
{
  "schema_version": 1,
  "ok": true,
  "command": "job start",
  "started_at": "2026-11-06T09:00:00+08:00",
  "finished_at": "2026-11-06T09:00:01+08:00",
  "elapsed_ms": 1024,
  "data": {},
  "warnings": [],
  "meta": {
    "base_url": "https://api.yingdao.com",
    "api_code": 200,
    "api_success": true,
    "request_id": "601cf6274032e2cc335c97d2",
    "dry_run": false
  }
}
```

`meta` 的五个键恒定存在。未发出请求时（`--dry-run`，以及 `config init/show` 这类本地命令）`api_code` / `api_success` / `request_id` 显式为 `null`，`dry_run` 为 `true` 或 `false`，调用方不必做"键是否存在"的判断。

## 2. 失败结构

```json
{
  "schema_version": 1,
  "ok": false,
  "command": "job query",
  "started_at": "...",
  "finished_at": "...",
  "elapsed_ms": 120,
  "error": {
    "type": "JobFailedError",
    "code": null,
    "message": "应用运行结束，状态：error（异常）",
    "hint": "查看 remark 与 screenshotUrl 定位失败原因；确认可重试后再发起重试。",
    "request_id": null
  },
  "data": {"kind": "job", "jobUuid": "...", "job": {"status": "error"}},
  "warnings": []
}
```

失败时仍可能带 `data`（例如失败任务的最终状态、调度决策候选），方便调用方展示细节。

## 3. 各命令的 data 形态

| 命令 | `data` |
|---|---|
| `config init` | `{path, scope, config_file}`；加 `--dry-run` 时改为下方预览形态，且不写盘 |
| `config show` | 脱敏后的配置字段 |
| `auth check` | `{base_url, expires_in, expires_at, source, token_masked, config_source}` |
| `auth token` | `{access_token, token_type, expires_in, expires_at, source, persisted:false, base_url}` |
| `robot info` | `{kind:"robot", requested:{inputName,accountName,resolvedBy,suffixApplied,lookup?,fallback?}, robot:{...原始字段, statusName, online, idle}}`；`--uuid` 模式下 `resolvedBy="uuid"`、`inputName/accountName` 为 `null`，另带 `robotClientUuid` |
| `robot tasks` | `{kind:"robot_task_list", items:[...statusName], count, cursor:{hasData,nextId,preId,cursorDirection}, filters, requested}` |
| `app list` | `{kind:"app_list", items:[...], count, page:{total,size,page,pages}, filters, requested}` |
| `app runs` | `{kind:"app_run_list", items:[...statusName], count, page, nextMinId, filters, requested}` |
| `account list` | `{kind:"account_list", items:[...], count, page:{total,size,page,pages}, filters, requested}` |
| `job start` | `{kind:"job_start", jobUuid, idempotentFlag, request_id, dispatch?}`；`dispatch` 含 `accountName/statusName/reason/successCount/idleCandidates/warnings`；加 `--wait` 时多一个 `job` |
| `job query` | `{kind:"job", jobUuid, job}` |
| 任意 `--dry-run` | `{kind:"request_preview", request:{method,url,query,body,headers}}`：`headers` 恒存在（`Accept`，有 body 时加 `Content-Type`，需 token 时加 `Authorization: Bearer <accessToken>`）；`body` 无请求体时为 `null`；`query`/`body` 默认掩码。`robot info` 无 `@` 且无 `--suffix` 时返回两段式预览（`resolution:"account-lookup"` + `followup`）；`job start --auto-robot` 返回 `resolution:"auto-robot"` + 空闲机器人查询 `request` + `<selected-account>` 占位 `followup`；`config init` 为本地写盘预览（`method:"WRITE"`、`url` 为目标路径、`body.exists` 指示是否已存在），**不创建任何文件** |


## 4. 退出码

| 退出码 | 含义 | 典型 `error.type` |
|---|---|---|
| 0 | 成功（job 类要求终态 `finish`） | — |
| 1 | 接口或业务错误 | `ApiError` |
| 2 | 参数或配置错误（未发请求） | `ParamError` / `ConfigError` |
| 3 | 鉴权失败 | `AuthError` |
| 4 | 网络错误、超时、轮询超时 | `NetworkError` / `TimeoutError` |
| 5 | 任务终态为 `error/stopped/skipped/cancel` | `JobFailedError` |
| 6 | 前置条件不满足（如调度忙碌需用户决策） | `PreconditionError` |

## 5. 任务状态

终态：`finish`、`stopped`、`error`、`skipped`、`cancel`。
非终态：`created`、`waiting`、`running`、`stopping`。

- `job query` 查到非终态时退出码为 0，表示"查询成功，任务还在跑"。
- 查到终态但非 `finish` 时退出码为 5，并在 `data.job` 中返回完整状态。
- `--wait` 超时仍未见终态时退出码为 4，`data` 中带最后一次状态。

## 6. 解析建议

- 先看 `ok` 与退出码，再看 `error.type` 决定是改参数、改配置、重试还是放弃。
- 排障时把 `meta.request_id` 提供给影刀；不要打印 `accessKeySecret` 或完整 token。
- `warnings` 非空不代表失败，但应在回复中转述给用户。

## 7. 唯一例外：`auth token --format text`

`auth token` 的用途就是交付 token，因此 `--format text` 只输出 token 原文（不含 JSON 包装），便于：

```bash
TOKEN=$("$PY" "$SKILL_DIR/scripts/yd.py" auth token --format text)
YD_ACCESS_TOKEN="$TOKEN" "$PY" "$SKILL_DIR/scripts/yd.py" job query --job-uuid <uuid>
```

该命令禁止 `--save`；JSON 模式下的完整 token 位于 `data.access_token`，应直接传给下一条命令的 `--access-token`。

加 `--dry-run` 时 text 模式不再输出 token，而是输出预览文本（以 `[预览]` 开头），避免把"空输出"误当成空 token。

