# 应用列表与运行记录

> 命令中的 `$PY` / `$SKILL_DIR` 见 `SKILL.md`「前置约定」；不要 `cd` 到技能目录执行。

对应接口文档：

- **3.2 查询应用列表**：`POST /oapi/app/open/query/list`
- **3.3 查询应用运行记录**：`POST /oapi/app/open/query/use/record/list`

两个命令都只读，不会启动或修改应用。

## 1. 应用列表 · `app list`

```bash
# 第一页，默认 30 条
"$PY" "$SKILL_DIR/scripts/yd.py" app list

# 按名称模糊查、按所有者账号精确查
"$PY" "$SKILL_DIR/scripts/yd.py" app list --app-name 订单 --owner zhangsan@corp

# 拉全量（默认最多 50 页）
"$PY" "$SKILL_DIR/scripts/yd.py" app list --all --size 100

# 先看请求
"$PY" "$SKILL_DIR/scripts/yd.py" app list --app-name 订单 --dry-run
```

| 参数 | 接口字段 | 说明 |
|---|---|---|
| `--app-id` | `appId` | 应用 ID，精确匹配 |
| `--app-name` | `appName` | 应用名称，模糊匹配 |
| `--owner` | `ownerUserSearchKey` | 所有者账号，精确匹配 |
| `--page` / `--size` | `page` / `size` | 默认 1 / 30，`size` 最大 100 |
| `--all` / `--max-pages` | — | 按页码翻页，默认最多 50 页 |

返回字段包含 `appId`、`appName`、`appTypeName`、`ownerName/ownerAccount`、`version`、`supportParam`、`createTime/updateTime`。`data.page` 返回总数与页数。

输出结构：

```json
{
  "kind": "app_list",
  "items": [],
  "count": 30,
  "page": {"total": 1012, "size": 30, "page": 1, "pages": 34},
  "filters": {"appName": "订单"},
  "requested": {"all": false, "page": 1, "size": 30}
}
```

## 2. 应用运行记录 · `app runs`

```bash
# 按应用查（第一页）
"$PY" "$SKILL_DIR/scripts/yd.py" app runs --app-id <appId>

# 按时间范围查（应用与时间至少给一个）
"$PY" "$SKILL_DIR/scripts/yd.py" app runs --begin-date "2026-11-02" --end-date "2026-11-09"

# 应用 + 时间 + 自动翻页
"$PY" "$SKILL_DIR/scripts/yd.py" app runs --app-id <appId> \
  --begin-date "2026-11-02 00:00:00" --end-date "2026-11-09 00:00:00" \
  --all --size 100

# 从某个游标继续
"$PY" "$SKILL_DIR/scripts/yd.py" app runs --app-id <appId> --min-id 479746186064532771
```

| 参数 | 接口字段 | 说明 |
|---|---|---|
| `--app-id` | `appId` | 应用 ID；与时间筛选至少提供一个 |
| `--begin-date` / `--end-date` | `beginDate` / `endDate` | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`；**未给 appId 时必须同时提供** |
| `--min-id` | `minId` | 游标起始 id，默认 0 |
| `--size` | `size` | 默认 30，最大 100 |
| `--all` / `--max-pages` | — | 按 `minId` 游标自动翻页 |

**时间跨度限制：接口最多允许 7 天**，超过会在本地被拦截（退出码 2）。查询更大范围请分段。未提供 `--app-id` 时，必须同时提供 `--begin-date` 与 `--end-date`。

游标规则：接口要求把上一页的最大 `id` 作为下一次的 `minId`。工具在 `--all` 时会自动取每页最大 `id`，并按 `id` 去重；同时参考 `page.page/pages`，避免重复拉取。

输出结构：

```json
{
  "kind": "app_run_list",
  "items": [],
  "count": 100,
  "page": {"total": 350, "size": 100, "page": 1, "pages": 4},
  "nextMinId": 479746186064532771,
  "filters": {"appId": "..."},
  "requested": {"all": false, "minId": 0, "size": 100}
}
```

运行状态沿用应用运行状态枚举：`created/waiting/running/finish/stopping/stopped/error/skipped/cancel`。接口不保证返回 `runStatusName`，工具会按枚举补充 `statusName`，文本模式优先使用中文名。

## 3. 注意事项

- 运行记录包含 `userName`、应用名等业务信息，按需展示。
- `app list` 可用来找 `appId`，再交给 `app runs` 或 `job start`。
- `--all` 达到 `--max-pages` 时返回 `warnings`，不会静默截断。
