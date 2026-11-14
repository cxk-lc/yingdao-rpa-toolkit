# 机器人调度选择规则

`job start` 在提交运行前会先做机器人选择/预检，规则如下：

1. **用户指定机器人优先**：`--account-name`（或配置 `defaultAccountName`）指定的机器人优先。
2. **指定机器人非空闲**：不自动改派、不自动排队，返回退出码 6 的决策请求，列出：
   - 排队等待选项；
   - 当前空闲机器人候选列表（按该应用历史成功次数降序）。
3. **未指定机器人**：`--auto-robot` 优先选择空闲机器人；多个空闲时优先该应用历史成功次数最多的，否则随机选一个。

## 1. 命令

```bash
# 自动选择空闲机器人
python scripts/yd.py job start --app-id <appId> --auto-robot

# 指定机器人；若忙碌则返回决策请求
python scripts/yd.py job start --app-id <appId> --account-name busy@corp

# 已与用户确认排队，允许在忙碌机器人上排队
python scripts/yd.py job start --app-id <appId> --account-name busy@corp --queue-if-busy
```

| 参数 | 说明 |
|---|---|
| `--auto-robot` | 未指定机器人时自动选择；不能与 `--account-name` / `--robot-group-uuid` 同用 |
| `--queue-if-busy` | 仅与 `--account-name` 同用；明确接受在非空闲机器人上排队 |
| `--account-name` | 指定机器人；省略时可用配置默认值或 `--auto-robot` |
| `--robot-group-uuid` | 走分组调度，不应用本规则 |

## 2. 指定机器人忙碌：决策请求

```json
{
  "ok": false,
  "command": "job start",
  "error": {
    "type": "PreconditionError",
    "message": "指定的机器人当前不是空闲状态",
    "hint": "请询问用户选择「排队等待」或「改派」，详见 data.idleCandidates。"
  },
  "data": {
    "kind": "dispatch_decision",
    "reason": "specified_robot_busy",
    "appId": "...",
    "requestedRobot": {"accountName": "busy@corp", "status": "running", "statusName": "运行中"},
    "idleCandidates": [
      {"accountName": "idle1@corp", "status": "idle", "statusName": "空闲", "successCount": 12},
      {"accountName": "idle2@corp", "status": "idle", "statusName": "空闲", "successCount": 3}
    ],
    "queueOption": {"accountName": "busy@corp", "flag": "--queue-if-busy"},
    "instructions": "请询问用户：1) 排队等待... 2) 改派..."
  }
}
```

调用方（Agent）应把 `idleCandidates` 展示给用户，二选一：

- **排队等待**：重跑原命令并加 `--queue-if-busy`。
- **改派**：重跑并把 `--account-name` 换成候选中的 `accountName`。

工具不会在未确认的情况下自动排队或改派。

## 3. 未指定机器人：自动选择

`--auto-robot` 的流程：

1. 调 4.4 `client/list?status=idle` 取空闲机器人。
2. 若多个，调 4.1 `job/list`（`robotUuid=appId`、`statusList=["finish"]`）统计近期成功次数。
3. 成功次数最多的优先；并列或全部为 0 时随机选一个空闲机器人。
4. 只有一个空闲时直接使用。

输出 `data.dispatch`：

```json
{
  "accountName": "idle1@corp",
  "robotClientUuid": "...",
  "status": "idle",
  "statusName": "空闲",
  "reason": "auto_most_success",
  "successCount": 12,
  "idleCandidates": 3,
  "warnings": []
}
```

`reason` 取值：

- `specified_idle`：指定机器人空闲。
- `specified_queue`：指定机器人非空闲，用户明确要求排队。
- `auto_only_idle`：只有一个空闲机器人。
- `auto_most_success`：多个空闲，按历史成功次数选择。
- `auto_random`：没有成功历史或并列，随机选择。

## 4. 没有空闲机器人

- 若存在在线但忙碌的机器人，返回 `reason="no_idle_robot"` 的决策请求，`onlineCandidates` 列出可排队的机器人。
- 若只有离线机器人，返回 `reason="no_available_robot"`。

调用方应询问用户是否选择一台在线机器人排队，确认后重跑：

```bash
python scripts/yd.py job start --app-id <appId> \
  --account-name <选中的在线机器人> --queue-if-busy
```

## 5. 边界

- 历史成功次数最多统计最近 5 页 × 100 条；查询失败时降级为随机空闲，并在 `dispatch.warnings` 中说明。
- `--dry-run` 不查询机器人状态：指定机器人时只预览启动请求；`--auto-robot` 时预览「查空闲机器人 + 用 `<selected-account>` 启动」两段请求。
- 指定机器人离线且用户明确 `--queue-if-busy` 时允许排队，但会返回 warning：可能排队到超时。
- 机器人 uuid 可通过 4.4 列表获取；本工具暂未提供独立的 `robot list` 命令。
