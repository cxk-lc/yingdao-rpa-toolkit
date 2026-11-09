# 机器人任务队列与历史记录

> 命令中的 `$PY` / `$SKILL_DIR` 见 `SKILL.md`「前置约定」；不要 `cd` 到技能目录执行。

对应接口文档 **4.1 查询机器人任务队列**：`POST /oapi/dispatch/v2/job/list`。

该接口返回待执行队列与历史 job，可按机器人、应用、任务、状态与触发时间筛选，使用游标翻页。

## 1. 命令

```bash
# 最近一页（默认 20 条）
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks

# 按应用、机器人、状态筛选
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks --app-id <appId> --status error,finish
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks --robot-client-uuid <robotClientUuid> --status running

# 按触发时间筛选
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks \
  --trigger-begin "2026-11-01 00:00:00" --trigger-end "2026-11-09 00:00:00"

# 自动往下翻页
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks --all --size 100

# 从游标往回翻
"$PY" "$SKILL_DIR/scripts/yd.py" robot tasks --direction pre --cursor-id 284065875470133295
```

## 2. 参数

| 参数 | 接口字段 | 说明 |
|---|---|---|
| `--app-id` / `--robot-uuid` | `robotUuid` | **应用 uuid**，不是机器人 uuid |
| `--robot-client-uuid` | `robotClientUuid` | 机器人 uuid |
| `--schedule-uuid` | `scheduleUuid` | 计划任务 uuid |
| `--status` | `statusList` | 运行状态，可重复或逗号分隔 |
| `--trigger-begin` / `--trigger-end` | `triggerTimeBegin/End` | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS` |
| `--cursor-id` | `cursorId` | 第一页不传；从某一页继续时传上一页的 `nextId`/`preId` |
| `--direction next\|pre` | `cursorDirection` | 默认 `next`；`pre` 必须同时给 `--cursor-id` |
| `--size` | `size` | 默认 20，最大 100 |
| `--all` / `--max-pages` | — | 沿当前方向自动翻页，默认最多 50 页 |
| `--query-api` | `queryApi` | 查询控制台 API 执行记录列表 |

状态枚举：`created` 已创建、`waiting` 等待调度、`running` 运行中、`finish` 完成、`stopping` 停止中、`stopped` 已停止、`error` 异常、`skipped` 已跳过、`cancel` 已取消。工具会把 `statusName` 补进每条记录。

## 3. 游标翻页

响应 `data` 是对象，不是数组：

```json
{
  "hasData": true,
  "nextId": 284065875470133276,
  "preId": 284065875470133295,
  "cursorDirection": "next",
  "dataList": []
}
```

- 第一页不传 `cursorId`，方向默认 `next`。
- `--all` 时：`next` 方向用 `nextId`，`pre` 方向用 `preId`，直到 `hasData=false`。
- 工具按 `id` 去重；游标不前进时停止并返回 warning，避免死循环。
- 达到 `--max-pages` 仍未结束时返回 warning，不静默截断。

## 4. 返回结构

```json
{
  "kind": "robot_task_list",
  "items": [],
  "count": 20,
  "cursor": {"hasData": true, "nextId": 284065875470133276, "preId": 284065875470133295, "cursorDirection": "next"},
  "filters": {"robotUuid": "...", "statusList": ["error"]},
  "requested": {"all": false, "cursorId": null, "direction": "next", "size": 20}
}
```

每条记录包含 `jobUuid`、`taskName`、`status/statusName`、`triggerTime`、`startTime`、`endTime`、`robotName`、`robotClientName`、`remark` 等。

## 5. 注意事项

- `robotUuid` 是**应用 uuid**，与 `job start --app-id` 一致；不要拿机器人 uuid 填这里。
- 机器人 uuid 可通过 `robot info` 的返回或机器人列表接口获取；本工具暂未提供机器人全量列表。
- 历史记录可能很多，优先用时间范围与状态筛选，再配合 `--size 100`。
