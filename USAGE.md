# 影刀RPA工具包 · 使用说明

> 适用版本：`yingdao-rpa-toolkit 0.1.1`｜11 条叶子命令｜走云端开放 API，不操作本机影刀客户端  
> 命令速查见 README「命令清单」；本文讲**怎么用**：先讲怎么用一句话驱动它，再讲命令行逐条怎么敲。

---

## 0. 先分清三个标识

绝大多数失败，都是把这三个东西搞混了。

| 概念                  | 是什么                           | 从哪来                          | 用在哪                        |
| ------------------- | ----------------------------- | ---------------------------- | -------------------------- |
| **应用 appId**        | 你在影刀 Studio 里做好的流程，发版后才有 uuid | `app list`，或控制台「应用管理」复制        | `job start` / `app runs` / `robot tasks` |
| **机器人 accountName** | 真正执行流程的那台机器账号，形如 `机器人7号@abc`  | 控制台「机器人管理」，或 `robot info` 回显 | `job start --account-name` |
| **运行 jobUuid**      | 一次具体执行的编号                     | `job start` 返回               | `job query` / `robot tasks` |

一句话链路：**找应用（app list）→ 确认机器人（robot info）→ 启动拿 jobUuid（job start）→ 查结果（job query / robot tasks）**。

> `app list` 可以按名称/所有者筛选应用并拿到 `appId`；机器人仍只有 `robot info` 单台查询，没有全量列表。

---

## 1. 命令清单

| 命令             | 作用                       | 会不会改数据       |
| -------------- | ------------------------ | ------------ |
| `config init`  | 生成配置模板                   | 写本地文件        |
| `config show`  | 查看生效配置（密钥脱敏）             | 只读           |
| `auth check`   | 用 AK/SK 换 token，验证凭据     | 只读           |
| `auth token`   | 输出完整 accessToken，供其它命令传入 | 只读           |
| `robot info`   | 查单台机器人的状态、IP、备注          | 只读           |
| `robot tasks`  | 查机器人任务队列与历史 job           | 只读           |
| `account list` | 分页查 RPA 企业账号             | 只读           |
| `app list`     | 分页查应用列表，可用于找 `appId`       | 只读           |
| `app runs`     | 查应用运行历史                   | 只读           |
| `job start`    | 派发一次真实运行                 | **写：会真的跑流程** |
| `job query`    | 查某次运行的状态与输出参数            | 只读           |

没有的能力（本版边界）：机器人全量列表、调度计划列表、重试、停止、运行日志、文件上传、工作队列、回调。需要这些时不要期待有隐藏参数。

---

## 2. 准备：配置与凭据

### 2.1 四层优先级

```
命令行参数  >  环境变量 YD_*  >  项目级 .yingdao/config.json（向上查找 8 级）  >  用户级 ~/.yingdao/config.json
```

前面的层里只要该字段非空，就不再往下取。`config show` 的 `data.source` 会告诉你凭据最终来自哪一层（`cli` / `env` / `project` / `user` / `explicit`）。

### 2.2 生成与查看配置

```bash
python scripts/yd.py config init          # 有 .git 时写项目级，否则写用户级
python scripts/yd.py config init --scope user --force   # 明确覆盖用户级
python scripts/yd.py config show          # 看生效值（密钥脱敏）
```

`config init` 遇到已存在的文件默认**拒绝覆盖**（退出码 2），要覆盖得显式加 `--force`。

模板字段：

```json
{
  "baseUrl": "https://api.yingdao.com",
  "accessKeyId": "<在此填写 accessKeyId>",
  "accessKeySecret": "<在此填写 accessKeySecret>",
  "timeoutSeconds": 30,
  "pollIntervalSeconds": 30,
  "maxPollSeconds": 1800,
  "defaultAccountName": "",
  "defaultRobotClientGroupUuid": "",
  "enterpriseSuffix": ""
}
```

- `baseUrl` 只填域名：带 `/oapi` 路径、或填成控制台域名都会被本地校验拦下（退出码 2）。
- `defaultAccountName` / `defaultRobotClientGroupUuid`：`job start` 没传 `--account-name` / `--robot-group-uuid` 时**会**用它们兜底，两者同时有值会报互斥错误。
- `enterpriseSuffix`：企业版账号后缀（如 `@csqy1`），给 `robot info` 补全名称用，写 `csqy1` 会自动补 `@`。

### 2.3 环境变量

| 变量                                                        | 对应配置项                       |
| --------------------------------------------------------- | --------------------------- |
| `YD_ACCESS_KEY_ID` / `YD_ACCESS_KEY_SECRET`               | 凭据（CI 里最常用）                 |
| `YD_ACCESS_TOKEN`                                         | 直接传 accessToken，优先级高于 AK/SK |
| `YD_BASE_URL`                                             | `baseUrl`                   |
| `YD_TIMEOUT`                                              | `timeoutSeconds`            |
| `YD_POLL_INTERVAL`                                        | `pollIntervalSeconds`（≥5）   |
| `YD_MAX_POLL_SECONDS`                                     | `maxPollSeconds`（≥30）       |
| `YD_DEFAULT_ACCOUNT_NAME` / `YD_DEFAULT_ROBOT_GROUP_UUID` | 默认机器人 / 分组                  |
| `YD_ENTERPRISE_SUFFIX`                                    | 企业账号后缀                      |

### 2.4 验证

```bash
python scripts/yd.py auth check
```

成功后 `data` 里有 `token_masked`、`expires_in`、`expires_at`、`source`（`fetched` / `cached`）、`config_source`。  
`auth check` 只输出**脱敏** token；要完整 token 用 `auth token`。

---

## 3. 方式一：自然语言调用

不用背命令：你说要做什么，我负责翻成第 4 节那些命令并执行，再把结果讲清楚。

### 3.1 它是怎么被触发的

1. **自动触发**：话里同时出现「影刀 / ShadowBot / RPA」和明确动作（跑、触发、查结果、看机器人、看账号），且属于云端开放 API 的范畴。
2. **手动指定**：输入框里 `@` 选 `yingdao-rpa-toolkit`（或直接引用 `SKILL.md`），强制本次按这个技能走。

触发后的动作序列和你在命令行做的一样：读配置 → 验凭据 → 确认机器人 → 干跑 → 真跑 → 查结果 → 汇报。

### 3.2 一句话模板

> 用影刀在【机器人名】上跑【appId】，参数【名称=值】，（跑完把输出参数汇总给我 / 失败告诉我原因）

| 口语要素 | 落到哪个参数                           |
| ---- | -------------------------------- |
| 应用   | `--app-id`（必须给 uuid，本版查不了应用列表）   |
| 机器人  | `--account-name`（企业版带 `@企业后缀`）   |
| 参数   | `--param 名称=值[:类型]`，多参数就重复写      |
| 等待   | 加不加 `--wait`                     |
| 产出   | `job query` 的 `data.job.outputs` |

### 3.3 说法 → 动作对照

| 你这么说                               | 我会执行                                                |
| ---------------------------------- | --------------------------------------------------- |
| 「影刀凭据还有效吗」                         | `auth check`，回有效期和配置来源                              |
| 「现在用的是哪份影刀配置」                      | `config show`，回 `source` 与 `config_path`            |
| 「机器人7号在线吗 / 忙不忙」                   | `robot info --name 机器人7号`（缺 `@` 自动补全）               |
| 「查一下企业里叫张三的 RPA 账号」                | `account list --keyword 张三`                         |
| 「找一下发票下载这个应用」                      | `app list --app-name 发票下载`，回 appId 与版本              |
| 「这个应用最近跑过吗 / 运行历史」                | `app runs --app-id <appId> --begin-date ... --end-date ...` |
| 「机器人7号最近跑了哪些任务 / 有没有失败」            | `robot tasks --robot-client-uuid <uuid> --status error,finish` |
| 「用影刀在机器人7号上跑 6b071a6e…，月份 2026-10」 | 干跑 → 确认 → `job start` → 回 jobUuid                   |
| 「刚才那个任务跑完没，输出是什么」                  | `job query --job-uuid <uuid>`，回状态/耗时/inputs/outputs |
| 「等它跑完再告诉我」                         | `job query --wait`，终态后汇报                            |
| 「这个任务失败了，为什么」                      | 读 `remark` 与 `screenshotUrl`，翻译成人话                  |

### 3.4 有效 vs 无效说法

| 说法                                   | 结果                             |
| ------------------------------------ | ------------------------------ |
| 「用影刀在机器人7号上跑 6b071a6e…，参数月份=2026-10」 | ✅ 要素齐全，直接干活                    |
| 「影刀跑一下 6b071a6e…」                    | ⚠️ 缺机器人，会先问或查配置默认值             |
| 「用影刀跑一下发票下载」                         | ✅ 会先用 `app list --app-name` 找 appId；多个匹配时让你确认 |
| 「机器人7号上跑一下」                          | ❌ 缺 appId，无法执行                 |
| 「用影刀处理一下数据」                          | ❌ 没触发：没有对象、没有动作                |
| 「影刀 API 的 job/start 字段有哪些」           | ℹ️ 会答文档，不执行                    |
| 「帮我装影刀客户端」                           | ❌ 不归这个技能管（本地客户端操作走另一类技能）       |
| 「每天 9 点自动跑一次」                        | ℹ️ 单次执行归这个技能，定时要建自动化任务         |

### 3.5 为什么它有时会先反问、先干跑

1. **不编造标识**：appId、机器人名、jobUuid 只能来自你的输入或查询结果，猜错就是跑到别的机器、别的流程上。
2. **真跑前确认**：本轮没说清「应用 + 机器人 + 参数」时，先复述计划；说清了就直接执行。
3. **首次先干跑**：`--dry-run` 把请求体摊开给你看，确认后再发。
4. **机器人名要完整**：`机器人7号` 和 `机器人7号@abc` 是两回事，少了后缀要么查不到，要么补错。

### 3.6 定时跑：交给自动化

技能只负责"这一次"。要"每天早上 8 点跑一次"，用定时任务来编排，到点调用这套命令（或这个技能）。  
在对话里说「以后每天都跑」，也应该落成定时任务，而不是让某条命令一直挂着。

### 3.7 它明确不做的事

- 查机器人全量列表 / 调度计划列表（本版未封装）
- 重试运行、停止运行
- 查运行日志、下载运行产物（运行历史可用 `app runs` / `robot tasks`）
- 上传文件、写工作队列、注册回调
- 操作本机影刀客户端（登录、触发器、Studio 编辑）
- RPA 账号的增删改、重置密码

遇到这类需求，工具会直接说明边界，而不是假装能调。

---

## 4. 方式二：命令行调用

### 4.1 骨架

```bash
PY="D:/Program Files/miniconda3/envs/python_3_10/python.exe"
YD() { "$PY" scripts/yd.py "$@"; }   # 在仓库根目录执行
```

PowerShell：

```powershell
$env:PY = "D:\Program Files\miniconda3\envs\python_3_10\python.exe"
function YD { & $env:PY scripts/yd.py @args }
YD auth check
```

> 位置有讲究：项目级配置靠「从当前目录向上找 `.yingdao/config.json`」，所以要在**你自己的项目目录**里执行，别 `cd` 到别处。  
> `pip install -e .` 之后可以省掉前缀，直接用 `yd` 命令。

### 4.2 十一条命令速查

```bash
YD config init [--scope project|user] [--force]
YD config show

YD auth check
YD auth token

YD robot info (--name <名称> | --uuid <uuid>) [--suffix @企业标识]
YD robot tasks [--app-id <appId>] [--robot-client-uuid <uuid>] \
  [--status error,finish] [--trigger-begin ...] [--all] [--size 20]

YD account list [--keyword 关键词] [--phone 手机号] \
  [--account-type basic|senior]... [--page 1] [--size 20] [--all] [--max-pages 50]

YD app list [--app-id <appId>] [--app-name 名称] [--owner 账号] [--all]
YD app runs (--app-id <appId> | --begin-date <日期> --end-date <日期>) \
  [--min-id 0] [--size 30] [--all]

YD job start --app-id <appId> (--account-name <机器人名> | --robot-group-uuid <uuid>) \
  [--param 名称=值[:类型]]... [--params-file 参数.json] [--dry-run]

YD job query --job-uuid <uuid> [--wait]
```

### 4.3 分命令详解

#### config init / config show

| 参数                      | 说明                          |
| ----------------------- | --------------------------- |
| `--scope project\|user` | 模板位置；不传时有 `.git` 就项目级，否则用户级 |
| `--force`               | 覆盖已存在的配置文件                  |

`config show` 输出全部生效值（`access_key_secret` 恒为 `***`，`access_key_id` 只露首尾），排查"到底读的哪份配置"时先看这个。

#### auth check

无参数。成功退出码 0，凭据有问题退出码 3。`--dry-run` 可以只看换取 token 的请求（不发送）。

#### auth token

输出**完整** accessToken，给下一条命令用。

- 禁止 `--save`（会写文件），本地直接拦下，退出码 2。
- `--format text` 只输出 token 原文，方便 shell 管道。
- token 只在当前进程内存里，**不落盘、不写日志**，跨命令必须自己传。

```bash
# 做法 A：显式传参（Agent 读 JSON 里的 data.access_token）
YD auth token
YD job query --job-uuid <uuid> --access-token <token>

# 做法 B：shell 管道（text 模式只输出 token）
TOKEN=$(YD auth token --format text)
YD job query --job-uuid <uuid> --access-token "$TOKEN"
# 或 YD_ACCESS_TOKEN="$TOKEN" YD job query --job-uuid <uuid>
```

传入的 token 优先于 AK/SK，命令不会再换新 token；token 失效时返回退出码 3 并提示重新 `auth token`，不会静默替换。

#### robot info

```bash
YD robot info --name "机器人7号@abc"
YD robot info --name 机器人7号 --suffix @abc     # 跳过企业账号查询
YD robot info --uuid <robotClientUuid>           # uuid 会随调度模式切换变化，少用
```

名称解析顺序（`--name` 不带 `@` 时）：

1. 先用 `account list` 按关键词查企业账号，取匹配的 `loginAccount`；
2. 匹配到多条 → 报错并列出候选，让你改用完整 `loginAccount`；
3. 一条都没匹配到 → 回退配置里的 `enterpriseSuffix`；
4. 既没匹配也没配后缀 → 本地拦截，要求补全名称。

输出 `data.robot` 含 `status`、`statusName`、`online`、`idle`、`clientIp`、`description`、`remark` 等，`data.requested.resolvedBy` 告诉你名称是怎么补全的（`input` / `account` / `suffix`）。

状态含义：

| 状态          | 含义              | 能否直接派发                |
| ----------- | --------------- | --------------------- |
| `idle`      | 空闲              | 能，不排队                 |
| `connected` | 已连接（长链刚建立，瞬态）   | 不建议作为判断依据             |
| `allocated` | 已分配未运行          | 会排队                   |
| `running`   | 运行中             | 会排队                   |
| `offline`   | 离线（断网 / 退出调度模式） | 派发接口可能照样成功，但任务只会排队到超时 |

#### account list

```bash
YD account list --keyword 张三 --account-type basic
YD account list --account-type basic,senior --all --size 100
YD account list --latest-login-begin "2026-01-01" --latest-login-end "2026-11-06 23:59:59"
```

| 参数                                               | 说明                                                    |
| ------------------------------------------------ | ----------------------------------------------------- |
| `--keyword` / `--phone`                          | 账号关键词 / 完整手机号                                         |
| `--account-type`                                 | `basic` / `senior`，可重复或逗号分隔                           |
| `--latest-login-begin/end`、`--expired-begin/end` | 秒级时间戳，也可写 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`，工具自动转换 |
| `--page` / `--size`                              | `size` 上限 100                                         |
| `--all` / `--max-pages`                          | 自动翻页，默认最多 50 页                                        |

返回含手机号等个人信息，只在你需要的范围内使用，别粘到公开文档或日志里。

#### app list

```bash
YD app list --app-name 订单
YD app list --owner zhangsan@corp --all --size 100
```

| 参数 | 说明 |
|---|---|
| `--app-id` / `--app-name` | 应用 ID 精确匹配 / 名称模糊匹配 |
| `--owner` | 所有者账号，精确匹配 |
| `--page` / `--size` | 默认 1 / 30，`size` 上限 100 |
| `--all` / `--max-pages` | 自动翻页，默认最多 50 页 |

返回 `appId`、`appName`、`version`、`supportParam`、所有者、创建/更新时间。找 `job start` 需要的 `appId` 时优先用它。

#### app runs

```bash
YD app runs --app-id <appId>
YD app runs --begin-date 2026-11-02 --end-date 2026-11-09 --all --size 100
```

| 参数 | 说明 |
|---|---|
| `--app-id` | 应用 ID；与时间筛选**至少给一个** |
| `--begin-date` / `--end-date` | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`；未给 appId 时必须同时提供 |
| `--min-id` | 游标起始 id，默认 0 |
| `--size` | 默认 30，上限 100 |
| `--all` / `--max-pages` | 按 `minId` 自动翻页 |

接口限制**时间跨度最多 7 天**，超过本地拦截（退出码 2）。`--all` 取上一页最大 `id` 作为下一轮 `minId`，并按 id 去重。

#### robot tasks

```bash
YD robot tasks --status error,finish --all
YD robot tasks --app-id <appId> --trigger-begin 2026-11-01 --trigger-end 2026-11-09
YD robot tasks --direction pre --cursor-id 284065875470133295
```

| 参数 | 说明 |
|---|---|
| `--app-id`（别名 `--robot-uuid`） | **应用 uuid**，接口字段 `robotUuid` |
| `--robot-client-uuid` / `--schedule-uuid` | 机器人 uuid / 计划 uuid |
| `--status` | 运行状态，可重复或逗号分隔 |
| `--trigger-begin/end` | 触发时间范围 |
| `--cursor-id` / `--direction` | 游标 id / `next`或`pre`；`pre` 必须带 cursor |
| `--size` | 默认 20，上限 100 |
| `--all` / `--max-pages` | 沿当前方向自动翻页 |
| `--query-api` | 查询控制台 API 执行记录 |

返回 `data.cursor`（`hasData/nextId/preId`）与 `data.items`；每条记录补了 `statusName`。

#### job start

```bash
# 先干跑，不发请求
YD job start --app-id 6b071a6e-2e70-4610-9953-83375dc60836 \
  --account-name "机器人7号@abc" \
  --param 月份=2026-10 --param 页数=10:int --dry-run
```

干跑输出 `data.request.body`，就是真正会发出去的内容（示例里的 appId / 机器人名来自实测，换成你自己的）：

```json
{
  "robotUuid": "6b071a6e-2e70-4610-9953-83375dc60836",
  "accountName": "机器人7号@abc",
  "params": [
    {"name": "月份", "value": "2026-10", "type": "str"},
    {"name": "页数", "value": "10", "type": "int"}
  ]
}
```

没传的可选字段不会出现在 body 里（由接口取默认值），所以 preview 是"你实际要发的"，不是"接口最终生效的"。

确认后去掉 `--dry-run`：

```bash
YD job start --app-id <appId> --account-name "机器人7号@abc" --param 月份=2026-10
```

| 参数                                      | 说明                                                                    |
| --------------------------------------- | --------------------------------------------------------------------- |
| `--app-id`（别名 `--robot-uuid`）           | **应用 uuid**，不是机器人 uuid。必填                                             |
| `--account-name` / `--robot-group-uuid` | 二选一；都没传时用配置里的默认值，仍为空则本地拦截                                             |
| `--param NAME=VALUE[:TYPE]`             | 可重复；`TYPE` 取 `str/int/float/bool/file`，默认 `str`。注意分隔符是**冒号**          |
| `--params-file <json>`                  | 参数文件：对象（`{"月份":"2026-10"}`）或 `[{name,value,type}]` 数组；可与 `--param` 叠加 |
| `--idempotent-uuid`                     | ≤36 位；网络超时重发时防重复启动。不传就不发该字段                                           |
| `--priority`                            | `high` / `middle` / `low`                                             |
| `--wait-timeout-seconds`                | 排队等待超时，60~950400 秒                                                    |
| `--run-timeout`                         | 运行超时，60~950400 秒（需客户端 5.10+）                                          |
| `--execute-scope`                       | 分组执行范围 `any` / `all`                                                  |
| `--wait`                                | 提交后直接轮询到终态                                                            |
| `--interval` / `--max-wait`             | 轮询间隔（≥5 秒）/ 总上限；默认取配置 `pollIntervalSeconds` / `maxPollSeconds`        |

参数约束：参数名**不能重复**；序列化后总长超过 **8000 字符**直接报错。长文本请拆批，或转成文件 URL 用 `file` 类型。

`file` 类型的值必须是 `http(s)://` 可访问 URL，传本地路径会被接口拒绝。

#### job query

```bash
YD job query --job-uuid <uuid> --format text
YD job query --job-uuid <uuid> --wait --interval 30 --max-wait 1800
```

| 参数                          | 说明                   |
| --------------------------- | -------------------- |
| `--job-uuid`                | 启动接口返回的 jobUuid，必填   |
| `--wait`                    | 轮询到终态；间隔下限 5 秒       |
| `--interval` / `--max-wait` | 默认取配置（30 秒 / 1800 秒） |

状态机：

| 状态                                             | 含义                 | 是否终态 |
| ---------------------------------------------- | ------------------ | ---- |
| `created` / `waiting` / `running` / `stopping` | 排队 / 运行中 / 停止中     | 否    |
| `finish`                                       | 成功                 | 是    |
| `error` / `stopped` / `skipped` / `cancel`     | 异常 / 已停止 / 跳过 / 取消 | 是    |

**两个成功要分开看**：`ok=true` 只代表接口调用成功；任务成没成看 `status == finish`。  
终态非 `finish` 时命令退出码为 **5**，`error.data.job` 里仍会带完整的任务详情（含 `remark`、`screenshotUrl`），方便你直接看失败原因。

### 4.4 完整链路

```bash
PY="D:/Program Files/miniconda3/envs/python_3_10/python.exe"
YD() { "$PY" scripts/yd.py "$@"; }

# 1. 配置与凭据
YD config show
YD auth check

# 2. 找应用 appId（也可按 --owner 精确筛选）
YD app list --app-name "订单" --format text

# 3. 确认机器人（名称缺 @ 时先补全）
YD robot info --name "机器人7号@abc" --format text

# 4. 干跑核对参数
YD job start --app-id <appId> --account-name "机器人7号@abc" \
  --param 月份=2026-10 --dry-run

# 5. 真跑，拿 jobUuid
YD job start --app-id <appId> --account-name "机器人7号@abc" \
  --param 月份=2026-10

# 6. 查结果（长流程建议分两次查，别让一条命令挂太久）
YD job query --job-uuid <jobUuid> --wait --interval 30 --max-wait 1800

# 7. 事后查历史
YD app runs --app-id <appId> --begin-date 2026-11-02 --end-date 2026-11-09
YD robot tasks --app-id <appId> --status error,finish
```


### 4.5 全局开关（所有叶子命令通用）

| 开关                                   | 作用                              |
| ------------------------------------ | ------------------------------- |
| `--format json\|text`                | `json`（默认，机器读）/ `text`（人读）      |
| `--dry-run`                          | 只输出预览：不发请求、不写盘（`config init` 仅显示目标路径） |
| `--show-secrets`                     | 预览里输出密钥原文（默认掩码，只在核对密钥时用）        |
| `--save <path>`                      | 把完整 JSON 另存到文件（`auth token` 禁用） |
| `--access-token <token>`             | 直接用传入的 token，优先于 AK/SK          |
| `--config <path>`                    | 指定配置文件                          |
| `--base-url <url>` / `--timeout <秒>` | 覆盖 API 域名 / 单次 HTTP 超时          |
| `--log-file <path>`                  | 把 DEBUG 日志追加写入文件                |
| `--debug`                            | stderr 打调试日志                    |
| `--quiet`                            | 不输出 warnings                    |

### 4.6 输出契约与退出码

stdout 永远是一条 JSON，脚本里 `json.loads` 直接用：

```json
{"schema_version":1,"ok":true,"command":"job query","data":{},"warnings":[],"meta":{}}
```

失败时 `ok=false`，带 `error={type,code,message,hint,request_id}`；人读提示写 stderr，stdout 仍是合法 JSON。

| 退出码 | 含义                     | 脚本里怎么处理                           |
| --- | ---------------------- | --------------------------------- |
| 0   | 成功（job 类要求终态 `finish`） | 继续                                |
| 1   | 接口/业务错误（含机器人查不到）       | 读 `error.message` + `request_id`  |
| 2   | 参数或配置错误（未发请求）          | 改参数/配置重试                          |
| 3   | 鉴权失败                   | 跑 `auth check`，核对 AK/SK 与 baseUrl |
| 4   | 网络错误或轮询超时              | 用同一命令再查一次                         |
| 5   | 任务终态非 `finish`         | 读 `error.data.job.remark`         |
| 6   | 前置条件不满足（本版暂无命令使用）      | 预留                                |

```bash
YD job query --job-uuid "$UUID"
case $? in
  0) echo "任务成功" ;;
  3) echo "凭据有问题" ;;
  5) echo "任务失败，看 remark" ;;
  *) echo "其它错误" ;;
esac
```

---

## 5. 两种方式怎么选

| 场景                  | 建议                       |
| ------------------- | ------------------------ |
| 第一次跑、要核对参数          | 命令行 `--dry-run`，看得最清楚    |
| 接进 CI / 定时脚本 / 别的程序 | 命令行 + 判退出码（0/3/5 分支）     |
| 临时跑一次、不想记参数         | 自然语言，说清 appId + 机器人 + 参数 |
| 要边跑边解读结果            | 自然语言，把 outputs 讲成人话      |
| 批量/循环跑多个应用          | 命令行写脚本；自然语言不适合跑几十次       |
| 排查鉴权、机器人状态          | 两边都行，命令行更快               |

---

## 6. 常见坑

| #  | 现象                    | 原因                                 | 处理                                          |
| -- | --------------------- | ---------------------------------- | ------------------------------------------- |
| 1  | 任务一直停在 `waiting`      | 没传机器人，或名称不完整（缺 `@企业`）              | `robot info` 核对；补全名称或配 `defaultAccountName` |
| 2  | 派发返回成功但一直不跑           | 机器人 `offline`                      | `robot info` 看状态，换一台                        |
| 3  | 400 参数校验失败            | 参数名与应用主流程不一致                       | 控制台核对入参名；`--dry-run` 看 body                 |
| 4  | 参数被拒                  | 序列化后超 8000 字符，或参数名重复               | 拆批；长文本改 `file` 类型 URL                       |
| 5  | `file` 类型报错           | 传了本地路径                             | 先上传，传 `http(s)://` URL                      |
| 6  | 401 / 退出码 3           | baseUrl 带 `/oapi` 或写成控制台域名；AK/SK 错 | `config show` + `auth check`，必要时 `--debug`  |
| 7  | `config init` 报"已存在"  | 默认不覆盖                              | 备份后删除，或加 `--force`                          |
| 8  | `auth token` 报错       | 加了 `--save`                        | 去掉；token 只能通过参数或环境变量传递                      |
| 9  | `robot info` 说匹配到多个账号 | 名称不唯一                              | 用完整 `loginAccount`（含 `@企业`）                 |
| 10 | 退出码 5 但没有报错信息         | 任务终态非 `finish` 属正常失败               | 看 `error.data.job.remark` 与 `screenshotUrl` |
| 11 | 429 限流                | 请求太密                               | 降 `--size`、减少 `--all`；轮询间隔保持 30 秒           |

---

## 7. 排障三步

```bash
# 1. 配置读的对不对、凭据通不通
YD config show
YD auth check --format text

# 2. 机器人状态（名称解析结果也会回显）
YD robot info --name 机器人7号 --format text

# 3. 请求体对不对（不发请求）
YD job start --app-id <appId> --account-name <机器人名> --dry-run --show-secrets
```

还不行就看 `request_id`，联系影刀支持时报这个最有用。

---

## 8. 本机实测快照（2026-11-06 / 2026-11-09）

用本仓库 CLI 跑只读命令的结果：

| 命令                            | 实测                                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `config show`                 | `source=project`，路径 `D:\Documents\WorkBuddy\影刀RPA工具包\.yingdao\config.json`，`pollIntervalSeconds=30`、`maxPollSeconds=1800` |
| `auth check`                  | 成功，`expires_in≈6600s`，`source=fetched`                                                                                    |
| `robot info --name 机器人7号@abc` | `idle`（空闲），`ip=172.17.28.133`，`resolvedBy=input`                                                                          |
| `account list --size 1`       | 成功，`page.total=27`（企业共 27 个 RPA 账号）                                                                                       |
| `app list --size 1`           | 成功，`page.total=1012`（2026-11-09）                                                                                              |
| `app runs`（7 天范围，`--size 1`） | 成功，返回 1 条，`nextMinId` 正常推进（2026-11-09）                                                                                        |
| `robot tasks --size 1`        | 成功，`cursor.hasData=true`，状态 `finish`（2026-11-09）                                                                           |

结论：配置、鉴权、机器人、账号、应用、任务历史查询链路都通。  
提醒：同环境里多数机器人处于 `offline`，派发前先 `robot info` 确认，别对着离线机器发。

---

## 9. 文件位置

| 内容    | 路径                                                                          |
| ----- | --------------------------------------------------------------------------- |
| 命令入口  | `scripts/yd.py`                                                             |
| 核心包   | `scripts/yingdao_rpa/`                                                      |
| 技能入口  | `SKILL.md`                                                                  |
| 项目级配置 | `<项目>/.yingdao/config.json`                                                 |
| 用户级配置 | `~/.yingdao/config.json`                                                    |
| 配置样例  | `config.example.json`、`.env.example`                                        |
| 分项文档  | `references/auth.md`、`account-list.md`、`app-list.md`、`robot-info.md`、`robot-tasks.md`、`output-contract.md` |
| 设计文档  | `docs/product-design.md`、`docs/tech-design.md`                              |
