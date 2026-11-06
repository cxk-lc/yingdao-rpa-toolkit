# 机器人信息与状态查询

对应接口文档 **4.2 查询机器人信息**：`POST /oapi/dispatch/v2/client/query`。

## 1. 命令

```bash
# 按名称查询（推荐）
python scripts/yd.py robot info --name ceshi1

# 按 uuid 查询（不推荐：切换调度模式后会生成新 uuid）
python scripts/yd.py robot info --uuid 0d6a835a-2e08-414a-af73-1e43f9d9c8ff
```

`--name` 与 `--uuid` 互斥，必须给其中一个。提前看请求体：

```bash
python scripts/yd.py robot info --name ceshi1 --dry-run
```

## 2. 名称解析顺序

影刀企业版的机器人账号形如 `ceshi1@csqy1`，`@` 及其后面是企业标识。`--name` 按以下顺序解析：

1. **已带 `@`**：原样使用，不再查询企业账号。
2. **显式传了 `--suffix`**：按指定后缀补全，跳过企业账号查询。
3. **只有前缀、没有 `--suffix`**：先调用 `account list`（2.2）按 `accountKeyword=<前缀>` 查找企业账号：
   - 优先匹配 `loginAccount` 的 `@` 前缀（忽略大小写）；
   - 没有再匹配账号的 `name` 字段；
   - 恰好一个匹配：用它的 `loginAccount` 查询机器人；
   - 多个匹配：退出码 2，列出候选 `loginAccount`，要求改用完整名称；
   - 没有匹配：回退到配置 `enterpriseSuffix`；
   - 企业账号接口报错：配置了后缀则回退后缀，否则原样抛出错误。
4. **仍然补不出后缀**：退出码 2，提示传完整名称、设置配置或加 `--suffix`。

| 用户输入 | 企业账号查询 | 配置 `enterpriseSuffix` | 实际请求的 `accountName` |
|---|---|---|---|
| `ceshi1@csqy1` | 跳过 | 任意 | `ceshi1@csqy1` |
| `ceshi1 --suffix @x` | 跳过 | 任意 | `ceshi1@x` |
| `ceshi1` | 找到 `ceshi1@corp` | 任意 | `ceshi1@corp`（来自 loginAccount） |
| `ceshi1` | 无匹配 | `@corp` | `ceshi1@corp` |
| `ceshi1` | 无匹配 | 空 | **本地拦截**，退出码 2 |

企业账号查询最多拉取 3 页 × 100 条，只提取 `loginAccount`，不会把账号列表的手机号等字段带进机器人结果。

配置方式（三选一）：

`.yingdao/config.json`：

```json
{"enterpriseSuffix": "@csqy1"}
```

环境变量：

```bash
export YD_ENTERPRISE_SUFFIX=@csqy1
```

单次命令覆盖（同时跳过企业账号查询）：

```bash
python scripts/yd.py robot info --name ceshi1 --suffix @csqy1
```

- `--suffix` 只能与 `--name` 一起用。
- 名称里已有 `@` 时一律原样使用，不会被配置覆盖；`ceshi1@` 这种缺企业标识的写法会被本地拦截。
- 无 `@` 且未传 `--suffix` 时，`--dry-run` 会先展示企业账号查询请求，再用 `<loginAccount>` 占位展示后续机器人查询；如果配置了后缀，还会给出 fallback。

## 3. 返回与状态

`data.robot` 保留接口原始字段，并补充：

| 字段 | 说明 |
|---|---|
| `robotClientName` | 机器人账号名（同 `accountName`） |
| `status` | 接口原始状态码 |
| `statusName` | 中文状态 |
| `online` | 是否在线（`connected/idle/allocated/running`） |
| `idle` | 是否空闲，可直接调度 |
| `clientIp` / `description` / `remark` | IP、备注、运行备注 |

| `status` | `statusName` | 在线 | 可立即调度 |
|---|---|---|---|
| `connected` | 已连接 | 是 | 否（持续时间极短） |
| `idle` | 空闲 | 是 | **是** |
| `allocated` | 已分配 | 是 | 否（会排队） |
| `running` | 运行中 | 是 | 否（会排队） |
| `offline` | 离线 | 否 | 否（会排队到超时） |

`data.requested` 记录本次名称解析情况：

```json
{
  "inputName": "ceshi1",
  "accountName": "ceshi1@csqy1",
  "resolvedBy": "account",
  "suffixApplied": false,
  "lookup": {"keyword": "ceshi1", "matched": 1}
}
```

- `resolvedBy`：`input`（原样使用）/ `suffix`（后缀补全）/ `account`（企业账号 loginAccount）。
- `fallback`：`no-account-match` 或 `account-query-failed`，表示走了配置后缀回退。

## 4. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `未找到匹配的企业账号，且没有可用的企业账号后缀`（退出码 2） | 账号列表无匹配，配置也没有 `enterpriseSuffix` | 传完整名称、设置配置，或加 `--suffix` |
| `机器人名称匹配到 N 个企业账号`（退出码 2） | 前缀对应多个账号（不同企业标识） | 按 hint 里的候选改用完整 `loginAccount` |
| `参数错误， 未查询到机器人`（退出码 1） | loginAccount 不是机器人账号，或机器人已被移出 | 确认该账号是否已接入调度；也可用 `--uuid` |
| 企业账号接口无权限，但配置了后缀 | 账号列表不可读 | 看 warning；工具已回退配置后缀，也可直接传完整名称 |
| 查询成功但 `status=offline` | 机器人离线或未进入调度模式 | 到机器人所在机器检查客户端与调度模式 |
| 用 uuid 查不到 | 切换调度模式后 uuid 会变化 | 改用 `--name` 查询 |

排障时把 `meta.request_id` 提供给影刀；不要贴 `accessKeySecret` 或完整 token。
