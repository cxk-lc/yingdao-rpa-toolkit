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

## 2. 企业版账号后缀规则

影刀企业版的机器人账号形如 `ceshi1@csqy1`，`@` 及其后面是企业标识。工具按以下顺序处理 `--name`：

| 用户输入 | 配置 `enterpriseSuffix` | 实际请求的 `accountName` |
|---|---|---|
| `ceshi1@csqy1` | 任意 | `ceshi1@csqy1`（原样使用） |
| `ceshi1` | `@csqy1` | `ceshi1@csqy1` |
| `ceshi1` | `csqy1` | `ceshi1@csqy1`（自动补 `@`） |
| `ceshi1` | 空 | **本地拦截**，退出码 2，提示补充后缀 |

临时覆盖配置：

```bash
python scripts/yd.py robot info --name ceshi1 --suffix @csqy1
```

- `--suffix` 只能与 `--name` 一起用。
- 名称里已有 `@` 时一律原样使用，不会被配置覆盖；`ceshi1@` 这种缺企业标识的写法会被本地拦截。

配置方式（三选一）：

`.yingdao/config.json`：

```json
{"enterpriseSuffix": "@csqy1"}
```

环境变量：

```bash
export YD_ENTERPRISE_SUFFIX=@csqy1
```

单次命令覆盖：

```bash
python scripts/yd.py robot info --name ceshi1 --suffix @csqy1
```

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

`data.requested` 记录本次请求的补全情况：

```json
{
  "inputName": "ceshi1",
  "accountName": "ceshi1@csqy1",
  "suffixApplied": true
}
```

## 4. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `机器人名称缺少企业账号后缀`（退出码 2） | 名称无 `@`，配置也没有 `enterpriseSuffix` | 传完整名称、设置配置，或加 `--suffix` |
| `参数错误， 未查询到机器人`（退出码 1） | 名称/后缀不匹配，或机器人已被移出 | 对照控制台「机器人管理」；确认企业后缀；也可用 `--uuid` |
| 查询成功但 `status=offline` | 机器人离线或未进入调度模式 | 到机器人所在机器检查客户端与调度模式 |
| 用 uuid 查不到 | 切换调度模式后 uuid 会变化 | 改用 `--name` 查询 |

排障时把 `meta.request_id` 提供给影刀；不要贴 `accessKeySecret` 或完整 token。
