# 影刀 RPA 开放 API 接口文档

> 依据影刀官方开放 API 文档与官方 OpenAPI 规范（v1.0.0）整理，覆盖 **10 个功能模块、31 个接口**。
> 整理日期：2026-11-05　|　Base URL：`https://api.yingdao.com`（私有化部署请替换为专有云域名）
> 官方文档：[影刀 RPA 开放 API 文档](https://www.yingdao.com/yddoc/rpa/zh-CN/971279704374095872)
> 本文件为项目内整理版；如与官方文档不一致，以官方文档为准。

---

## 目录

1. [接口总览](#overview)
2. [通用调用规范](#conventions)
3. [典型调用链路](#flows)
4. **接口明细**
   4.1 **鉴权**（1 个）
      - [授权获取token](#api-oapi-token-v2-token-create)
   4.2 **RPA企业账号**（5 个）
      - [创建RPA企业账号](#api-oapi-rpa-user-v1-create)
      - [查询RPA企业账号列表](#api-oapi-rpa-user-v1-list)
      - [修改RPA企业账号](#api-oapi-rpa-user-v1-modify)
      - [删除RPA企业账号](#api-oapi-rpa-user-v1-delete)
      - [重置账号密码](#api-oapi-useracl-v1-rest-pwd)
   4.3 **应用相关**（4 个）
      - [查询应用主流程参数结构](#api-oapi-robot-v2-queryrobotparam)
      - [查询应用列表](#api-oapi-app-open-query-list)
      - [查询应用运行记录](#api-oapi-app-open-query-use-record-list)
      - [转移应用所有者](#api-oapi-app-open-translate-owner)
   4.4 **机器人相关**（4 个）
      - [查询机器人任务队列](#api-oapi-dispatch-v2-job-list)
      - [查询机器人信息](#api-oapi-dispatch-v2-client-query)
      - [查询机器人分组列表](#api-oapi-dispatch-v2-client-group-list)
      - [查询机器人列表](#api-oapi-dispatch-v2-client-list)
   4.5 **JOB运行**（4 个）
      - [停止应用运行](#api-oapi-dispatch-v2-job-stop)
      - [启动应用](#api-oapi-dispatch-v2-job-start)
      - [查询应用运行结果](#api-oapi-dispatch-v2-job-query)
      - [重试应用运行](#api-oapi-dispatch-v2-job-retry)
   4.6 **任务运行**（3 个）
      - [查询任务运行结果](#api-oapi-dispatch-v2-task-query)
      - [停止任务运行](#api-oapi-dispatch-v2-task-stop)
      - [启动任务](#api-oapi-dispatch-v2-task-start)
   4.7 **任务**（5 个）
      - [查询任务&机器人应用运行详情](#api-oapi-dispatch-v2-task-process-detail)
      - [最新任务执行记录](#api-oapi-dispatch-v2-task-newest-list)
      - [单个任务执行记录列表](#api-oapi-dispatch-v2-task-list)
      - [查询任务详情](#api-oapi-dispatch-v2-schedule-detail)
      - [查询任务列表](#api-oapi-dispatch-v2-schedule-list)
   4.8 **运行日志**（3 个）
      - [查询应用运行日志](#api-oapi-dispatch-v2-job-log-search)
      - [通知查询应用运行日志](#api-oapi-dispatch-v2-job-log-notify)
      - [轮询应用运行日志](#api-oapi-dispatch-v2-job-log-query)
   4.9 **文件**（1 个）
      - [文件上传](#api-oapi-dispatch-v2-file-upload)
   4.10 **工作队列**（1 个）
      - [新增队列项](#api-oapi-tool-queue-v1-queues-queueuuid-enqueue)
5. [枚举值参考](#enum-ref)
6. [状态码参考](#status-code)

---

<a id="overview"></a>

## 接口总览

| # | 模块 | 接口名称 | 方法 | 路径 |
|---|---|---|---|---|
| 1 | 鉴权 | [授权获取token](#api-oapi-token-v2-token-create) | `GET` | `/oapi/token/v2/token/create` |
| 2 | RPA企业账号 | [创建RPA企业账号](#api-oapi-rpa-user-v1-create) | `POST` | `/oapi/rpa/user/v1/create` |
| 3 | RPA企业账号 | [查询RPA企业账号列表](#api-oapi-rpa-user-v1-list) | `GET` | `/oapi/rpa/user/v1/list` |
| 4 | RPA企业账号 | [修改RPA企业账号](#api-oapi-rpa-user-v1-modify) | `POST` | `/oapi/rpa/user/v1/modify` |
| 5 | RPA企业账号 | [删除RPA企业账号](#api-oapi-rpa-user-v1-delete) | `POST` | `/oapi/rpa/user/v1/delete` |
| 6 | RPA企业账号 | [重置账号密码](#api-oapi-useracl-v1-rest-pwd) | `POST` | `/oapi/useracl/v1/rest/pwd` |
| 7 | 应用相关 | [查询应用主流程参数结构](#api-oapi-robot-v2-queryrobotparam) | `GET` | `/oapi/robot/v2/queryRobotParam` |
| 8 | 应用相关 | [查询应用列表](#api-oapi-app-open-query-list) | `POST` | `/oapi/app/open/query/list` |
| 9 | 应用相关 | [查询应用运行记录](#api-oapi-app-open-query-use-record-list) | `POST` | `/oapi/app/open/query/use/record/list` |
| 10 | 应用相关 | [转移应用所有者](#api-oapi-app-open-translate-owner) | `POST` | `/oapi/app/open/translate/owner` |
| 11 | 机器人相关 | [查询机器人任务队列](#api-oapi-dispatch-v2-job-list) | `POST` | `/oapi/dispatch/v2/job/list` |
| 12 | 机器人相关 | [查询机器人信息](#api-oapi-dispatch-v2-client-query) | `POST` | `/oapi/dispatch/v2/client/query` |
| 13 | 机器人相关 | [查询机器人分组列表](#api-oapi-dispatch-v2-client-group-list) | `POST` | `/oapi/dispatch/v2/client/group/list` |
| 14 | 机器人相关 | [查询机器人列表](#api-oapi-dispatch-v2-client-list) | `POST` | `/oapi/dispatch/v2/client/list` |
| 15 | JOB运行 | [停止应用运行](#api-oapi-dispatch-v2-job-stop) | `POST` | `/oapi/dispatch/v2/job/stop` |
| 16 | JOB运行 | [启动应用](#api-oapi-dispatch-v2-job-start) | `POST` | `/oapi/dispatch/v2/job/start` |
| 17 | JOB运行 | [查询应用运行结果](#api-oapi-dispatch-v2-job-query) | `POST` | `/oapi/dispatch/v2/job/query` |
| 18 | JOB运行 | [重试应用运行](#api-oapi-dispatch-v2-job-retry) | `POST` | `/oapi/dispatch/v2/job/retry` |
| 19 | 任务运行 | [查询任务运行结果](#api-oapi-dispatch-v2-task-query) | `POST` | `/oapi/dispatch/v2/task/query` |
| 20 | 任务运行 | [停止任务运行](#api-oapi-dispatch-v2-task-stop) | `POST` | `/oapi/dispatch/v2/task/stop` |
| 21 | 任务运行 | [启动任务](#api-oapi-dispatch-v2-task-start) | `POST` | `/oapi/dispatch/v2/task/start` |
| 22 | 任务 | [查询任务&机器人应用运行详情](#api-oapi-dispatch-v2-task-process-detail) | `POST` | `/oapi/dispatch/v2/task/process/detail` |
| 23 | 任务 | [最新任务执行记录](#api-oapi-dispatch-v2-task-newest-list) | `POST` | `/oapi/dispatch/v2/task/newest/list` |
| 24 | 任务 | [单个任务执行记录列表](#api-oapi-dispatch-v2-task-list) | `POST` | `/oapi/dispatch/v2/task/list` |
| 25 | 任务 | [查询任务详情](#api-oapi-dispatch-v2-schedule-detail) | `POST` | `/oapi/dispatch/v2/schedule/detail` |
| 26 | 任务 | [查询任务列表](#api-oapi-dispatch-v2-schedule-list) | `POST` | `/oapi/dispatch/v2/schedule/list` |
| 27 | 运行日志 | [查询应用运行日志](#api-oapi-dispatch-v2-job-log-search) | `POST` | `/oapi/dispatch/v2/job/log/search` |
| 28 | 运行日志 | [通知查询应用运行日志](#api-oapi-dispatch-v2-job-log-notify) | `POST` | `/oapi/dispatch/v2/job/log/notify` |
| 29 | 运行日志 | [轮询应用运行日志](#api-oapi-dispatch-v2-job-log-query) | `POST` | `/oapi/dispatch/v2/job/log/query` |
| 30 | 文件 | [文件上传](#api-oapi-dispatch-v2-file-upload) | `POST` | `/oapi/dispatch/v2/file/upload` |
| 31 | 工作队列 | [新增队列项](#api-oapi-tool-queue-v1-queues-queueuuid-enqueue) | `POST` | `/oapi/tool/queue/v1/queues/{queueUuid}/enqueue` |

---

<a id="conventions"></a>

## 通用调用规范

### 认证方式

所有业务接口均需在请求头携带 accessToken：

```http
Authorization: Bearer {accessToken}
```

获取流程：企业管理员在影刀控制台「高级设置 → API 配置」创建 `accessKeyId` 与 `accessKeySecret`，
再调用 [授权获取token](#api-oapi-token-v2-token-create) 换取。token 最长有效期 2 小时，
请按响应中的 `expiresIn`（秒）缓存，不要自定固定缓存时长。

### 统一响应结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 状态码，200 表示成功（个别列表接口返回 0 也表示成功） |
| `success` | boolean | 是否调用成功，**判断成功应以此字段为准** |
| `msg` | string | 状态码描述 |
| `data` | object / array | 业务数据 |
| `requestId` | string | 请求 ID，排查问题时提供给影刀 |

### 调用限制

| 项目 | 限制 |
|---|---|
| 入参总长度 | 建议不超过 8000 字符（专有云 6.0.0 之前为 3000）；超限改用文件上传 + `type=file` |
| 幂等 | `idempotentUuid` 长度不超过 36 位，相同值只成功创建一次 |
| 排队等待 | `waitTimeoutSeconds` 最小 60，最大 950400，默认 600 |
| 运行超时 | `runTimeout` 最小 60，最大 950400，需客户端 5.10 及以上 |
| 结果轮询 | 官方建议 30 秒一次，终态即停止 |

### 字段与排版约定

| 约定 | 含义 |
|---|---|
| `∟` 或 `\|─` 前缀 | 表示嵌套在上一级对象内的子字段，前缀数量即嵌套层级 |
| 必填列 | 「是」表示不可缺省，否则报参数校验错误 |
| 「已废弃」标记 | 官方已声明不建议使用，保留仅为兼容存量系统 |

---

<a id="flows"></a>

## 典型调用链路

### 链路一：触发应用并取回执行结果

| 步骤 | 接口 | 关键动作 |
|---|---|---|
| 1 | [授权获取token](#api-oapi-token-v2-token-create) | 换取 accessToken，按 `expiresIn` 缓存 |
| 2 | [查询应用列表](#api-oapi-app-open-query-list) | 取 `appId`，即启动接口的 `robotUuid` |
| 3 | [查询机器人列表](#api-oapi-dispatch-v2-client-list) | 筛选 `status=idle` 的机器人，取 `robotClientName` |
| 4 | [启动应用](#api-oapi-dispatch-v2-job-start) | 传 `robotUuid` + `accountName` + `params`，得 `jobUuid` |
| 5 | [查询应用运行结果](#api-oapi-dispatch-v2-job-query) | 每 30 秒轮询，`status` 进入终态即停止 |

> 应用运行终态为 `finish`（成功）、`stopped`、`error`、`skipped`、`cancel`。

### 链路二：机器人状态巡检与告警

| 步骤 | 接口 | 关键动作 |
|---|---|---|
| 1 | [授权获取token](#api-oapi-token-v2-token-create) | 同上 |
| 2 | [查询机器人列表](#api-oapi-dispatch-v2-client-list) | 分页拉取全部机器人，读取 `status` 与 `clientIp` |
| 3 | 业务侧判断 | 对 `offline` 超过阈值的机器人推送告警 |

### 链路三：高并发任务排队

| 步骤 | 接口 | 关键动作 |
|---|---|---|
| 1 | [新增队列项](#api-oapi-tool-queue-v1-queues-queueuuid-enqueue) | 把待处理数据写入工作队列 |
| 2 | 机器人侧流程 | 循环消费队列，逐条处理 |

> 相比直接调用启动接口，工作队列自带排队与重试语义，更适合大批量、可容忍延迟的场景。

---

## 接口明细

### 1. 鉴权

所有接口的前置依赖。用控制台创建的 accessKeyId / accessKeySecret 换取 accessToken。

<a id="api-oapi-token-v2-token-create"></a>

#### 1.1 授权获取token

`GET` `/oapi/token/v2/token/create`

**功能说明**：用 accessKeyId 与 accessKeySecret 换取 accessToken。后续所有接口需把该 token 放入 `Authorization: Bearer {accessToken}` 请求头。token 最长有效期 2 小时，未过期时重复请求返回同一 token。

**前置条件**：使用企业管理员账号登录影刀控制台，在api配置界面新增accessKeyId和accessKeySecret，取后请妥善保管，管理员可以给每个需要对接影刀的系统自创建一对密钥。

**注意**

- accessToken的最大有效期是 2 小时。当accessToken未过期时，请求会返回老的accessToken，当accessToken已过期时，，accessToken是一个临时token，请求会返回新的token，调用方可以不用缓存，如果需要缓存，可以根据请求token时返回的 expiresIn 字段进行缓存，该字段此次获取token的有效期，单位是秒(不要自定义缓存时间， 可能会导致我方token和调用方缓存的有效期不一致)。任务运行完成就会失效。

**请求参数**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| accessKeyId | query | string | 是 | 示例：`EBCgDuVc1m5kPfjt@platform` |
| accessKeySecret | query | string | 是 | 示例：`CkDqYb4e1NRr7HM2GhEpKzaZFtw63Sjn` |

**返回参数**

| 名称 | 类型 | 必填 |
|---|---|---|
| code | int | 是 |
| success | boolean | 是 |
| msg | string | 是 |
| data | object | 是 |
| ∟ accessToken | string | 是 |
| ∟ expiresIn | int | 是 |

**调用示例**

```bash
curl "https://api.yingdao.com/oapi/token/v2/token/create?accessKeyId=<accessKeyId>&accessKeySecret=<accessKeySecret>"
```

响应示例：

```json
{
    "data": {
        "accessToken": "520da9c9-694d-4b40-9332-0c179243c88e",
        "expiresIn": 7199
    },
    "code": 200,
    "success": true,
    "requestId": "601cf6274032e2cc335c97d2"
}
```

### 2. RPA企业账号

管理企业下的 RPA 子账号，包括创建、查询、修改、删除与重置密码。

<a id="api-oapi-rpa-user-v1-create"></a>

#### 2.1 创建RPA企业账号

`POST` `/oapi/rpa/user/v1/create`

**功能说明**：在企业下创建一个 RPA 子账号，创建后可用于登录影刀客户端。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| name | string | 员工姓名, 必填 |
| account | string | 账号, 必填 |
| phone | string | 手机号, 必填 |
| email | string | 邮箱, 可选 |
| accountType | string | 账号类型: basic 基础账号, senior 高级账号, 必填 |
| userRole | string | 用户角色: e_admin 管理员, e_user 员工, 必填 |
| password | string | 密码, 必填 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | object | 结果数据 |
| \|─userUuid | string |   |
| \|─name | string |   |
| \|─account | string |   |
| code | integer | 返回结果编码 |
| success | boolean | true 表示成功，false 表示失败 |
| requestId | string |   |
| msg | string | 结果信息 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/rpa/user/v1/create" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<name>",
    "account": "<account>",
    "phone": "<phone>",
    "email": "<email>",
    "accountType": "<accountType>",
    "userRole": "<userRole>",
    "password": "<password>"
  }'
```

<a id="api-oapi-rpa-user-v1-list"></a>

#### 2.2 查询RPA企业账号列表

`GET` `/oapi/rpa/user/v1/list`

**功能说明**：分页查询企业下的 RPA 子账号列表。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| phone | String | 否 | 完整的手机号 |
| accountKeyword | String | 否 | 账号关键词 |
| latestLoginTimeBegin | Long | 否 | 最后登录时间左边界，秒级时间戳 |
| latestLoginTimeEnd | Long | 否 | 最近登录时间右边界，秒级时间戳 |
| expiredTimeBegin | Long | 否 | 过期时间左边界，秒级时间戳 |
| expiredTimeEnd | Long | 否 | 过期时间右边界，秒级时间戳 |
| accountTypes | List<String> | 否 | 账号类型列表，基础账号-basic，高级账号-senior |
| page | int | 否 | 页码 |
| size | int | 否 | 一页默认20条，最大支持100 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | array | 结果数据 |
| \|─ | object |   |
| \|─userUuid | string | 用户uuid |
| \|─loginAccount | string | 登录账户 |
| \|─name | string | 账户名称 |
| \|─phone | string | 手机号 |
| \|─role | string | 角色 |
| \|─roleName | string | 角色名称 |
| \|─accountType | string | 帐户类型 |
| \|─accountTypeName | string | 帐户类型名称 |
| \|─latestLoginTime | string | 最近登录时间 |
| \|─expiredTime | string | 过期时间 |
| page | object | 分页数据 |
| \|─total | integer | 总条数 |
| \|─size | integer | 每页条数 |
| \|─page | integer | 当前页 |
| \|─pages | integer | 总页数 |
| \|─offset | integer | 偏移量 |
| \|─sortColumn | string | 用于排序的 column 的名称 |
| \|─order | string | 排序方式 desc/asc |
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求id，方便排查使用 |
| serverIp | string | 处理服务的Ip |
| serverInstName | string | 处理服务实例名称 |
| msg | string | 状态码描述 |

**调用示例**

```bash
curl "https://api.yingdao.com/oapi/rpa/user/v1/list?<query>" \
  -H "Authorization: Bearer <accessToken>"
```

响应示例：

```json
{
    "data": [
        {
            "userUuid": "xxxuuid",
            "loginAccount": "xxxacc@abbr",
            "name": "xxxname",
            "phone": "13312345678",
            "role": "e_user",
            "roleName": "员工",
            "accountType": "basic",
            "accountTypeName": "基础账号",
            "latestLoginTime": "2024-02-28 15:21:51",
            "expiredTime": "2025-01-19 23:59:59"
        }
    ],
    "page": {
        "total": 1,
        "size": 20,
        "page": 1,
        "pages": 1,
        "offset": 0,
        "order": "desc"
    },
    "code": 200,
    "success": true,
    "requestId": "44265d53-842b-4a7f-9174-6bd900ebaa91"
}
```

<a id="api-oapi-rpa-user-v1-modify"></a>

#### 2.3 修改RPA企业账号

`POST` `/oapi/rpa/user/v1/modify`

**功能说明**：修改指定 RPA 子账号的信息。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| account | string | 账号, （确定需要修改的账号）, 必传 |
| name | string | 员工姓名, 传空(或者空串或者不传)表示不修改 |
| phone | string | 手机号, 传空(或者空串或者不传)表示不修改 |
| email | string | 邮箱, 传空(或者不传或者传空串)表示不修改 |
| userRole | string | 用户角色: e_admin 管理员, e_user 员工, 传空(或者空串或者不传)表示不修改 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | object | 结果数据 |
| \|─userUuid | string |   |
| code | integer | 返回结果编码 |
| success | boolean | true 表示成功，false 表示失败 |
| requestId | string |   |
| msg | string | 结果信息 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/rpa/user/v1/modify" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "<account>",
    "name": "<name>",
    "phone": "<phone>",
    "email": "<email>",
    "userRole": "<userRole>"
  }'
```

<a id="api-oapi-rpa-user-v1-delete"></a>

#### 2.4 删除RPA企业账号

`POST` `/oapi/rpa/user/v1/delete`

**功能说明**：删除指定的 RPA 子账号。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| account | string | 登录账号, （确定需要修改的账号）, 必传 |
| receiveAccount | string | 接收的登录账号（删除account账号时，将其开发的应用转移给receiveAccount账号）, 必传 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| code | integer | 返回结果编码 |
| success | boolean | true 表示成功，false 表示失败 |
| requestId | string |   |
| msg | string | 结果信息 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/rpa/user/v1/delete" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "<account>",
    "receiveAccount": "<receiveAccount>"
  }'
```

<a id="api-oapi-useracl-v1-rest-pwd"></a>

#### 2.5 重置账号密码

`POST` `/oapi/useracl/v1/rest/pwd`

**功能说明**：重置指定账号的登录密码。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| loginAccount | string | 账号, （确定需要修改的账号）, 必传 |
| oldPwd | string | 老密码，修改时需要和现有密码进行比对 |
| pwd | string | 新密码，不能为空 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | object | 结果数据 |
| code | integer | 返回结果编码 200为成功，其他错误结果都为500 |
| success | boolean | true 表示成功，false 表示失败 |
| requestId | string |   |
| msg | string | 结果信息 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/useracl/v1/rest/pwd" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "loginAccount": "<loginAccount>",
    "oldPwd": "<oldPwd>",
    "pwd": "<pwd>"
  }'
```

### 3. 应用相关

查询已发版应用清单、主流程参数结构、运行记录，以及转移应用所有者。

<a id="api-oapi-robot-v2-queryrobotparam"></a>

#### 3.1 查询应用主流程参数结构　`已废弃`

`GET` `/oapi/robot/v2/queryRobotParam`

**功能说明**：查询已发版应用的主流程入参与出参结构，用于在调用前确认参数名称与类型。**官方已标记废弃**，建议改用「查询应用版本详情」接口。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口只能查询已经发版过的应用

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | accessToken变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| robotUuid | string | 否 |   |
| accurateRobotName | string | 否 | 该参数是精确匹配应用名称，不支持模糊查询 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | array | 是 | 响应数据 |
| ∟ inputParams | array | 否 | 入参 |
| ∟ name | string | 是 | 参数名称 |
| ∟ direction | string | 是 | 入参出参 |
| ∟ type | string | 是 | 参数类型，str,float,file等五种类型 |
| ∟ value | string | 是 | 参数值 |
| ∟ description | string | 是 | 参数描述 |
| ∟ kind | string | 是 | kind是客户端的一个定义，目前不需要。字符串他对应的类型是Text |
| ∟ outputParams | array |   | 出参同上 |
| ∟ 同上 |   |   |   |

**调用示例**

```bash
curl "https://api.yingdao.com/oapi/robot/v2/queryRobotParam?<query>" \
  -H "Authorization: Bearer <accessToken>"
```

响应示例：

```json
{
    "data": {
        "inputParams": [
            {
                "name": "input_str_variable",
                "direction": "In",
                "type": "str",
                "value": "",
                "description": "",
                "kind": "Text"
            },
            {
                "name": "input_float_variable",
                "direction": "In",
                "type": "float",
                "value": "0.0",
                "description": "",
                "kind": "Expression"
            },
            {
                "name": "input_bool_variable",
                "direction": "In",
                "type": "bool",
                "value": "False",
                "description": "",
                "kind": "Expression"
            },
            {
                "name": "input_file_variable",
                "direction": "In",
                "type": "file",
                "value": "",
                "description": "",
                "kind": "Text"
            }
        ],
        "outputParams": [
            {
                "name": "input_int_variable",
                "direction": "Out",
                "type": "int",
                "value": "0",
                "description": "",
                "kind": "Expression"
            }
        ]
    },
    "code": 200,
    "success": true,
    "requestId": "7484425d-2525-4b58-aacf-50f205a603fd"
}
```

<a id="api-oapi-app-open-query-list"></a>

#### 3.2 查询应用列表

`POST` `/oapi/app/open/query/list`

**功能说明**：分页查询企业下的应用列表，可获取应用 UUID、版本与是否支持参数。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| appId | String | 否 | 应用ID |
| size | String | 否 | 一页大小，默认30，最大100 |
| page | String | 否 | 页码 默认1 |
| ownerUserSearchKey | String | 否 | 用户搜索关键字，仅支持账号精确匹配 |
| appName | String | 否 | 应用名称模糊匹配 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | object | 结果数据 |
| \|─ ownerName | string | 应用所有者名称 |
| \|─ ownerAccount | string | 应用所有者账号 |
| \|─ ownerId | string | 所有者id |
| \|─ appId | string | appid |
| \|─ appName | string | 应用名称 |
| \|─ appTypeName | string | 应用类型名称 |
| \|─ appType | string | 应用类型枚举,app:应用,activity:指令 |
| \|─ createTime | string | 创建时间 |
| \|─ updateTime | string | 修改时间 |
| \|─ version | string | 版本，值内容：未发版、版本 |
| \|─ supportParam | boolean | 是否支持应用参数 |
| \|─ icon | string | icon图下载地址 |
| page | object | 分页信息 |
| \|─ total | integer | 总条数 |
| \|─ size | integer | 一页大小 |
| \|─ page | integer | 当前页 |
| \|─ pages | integer | 总页数 |
| \|─ offset | integer | 偏移量 |
| \|─ sortColumn | string¦ | 用于排序的 column 的名称 |
| \|─ order | string¦ | 排序方式 desc/asc，默认降序排列 |
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求id，方便排查使用 |
| serverIp | string | 处理服务的Ip |
| serverInstName | string | 处理服务实例名称 |
| msg | string | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/app/open/query/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "appId": "<appId>",
    "size": "<size>",
    "page": "<page>",
    "ownerUserSearchKey": "<ownerUserSearchKey>",
    "appName": "<appName>"
  }'
```

响应示例：

```json
{
  "data": [
    {
      "ownerName": "测试",
      "ownerAccount": "ceshi2@csqy1",
      "ownerId": "c8d9647f-1435-4b5f-bd64-b5d4613e5283",
      "appId": "107f0f23-3584-4b1b-8665-443605722f95",
      "appName": "kkkkk",
      "appTypeName": "应用",
      "appType": "app",
      "createTime": "2024-05-08 13:49:13",
      "updateTime": "2024-05-08 13:50:24",
      "version": "1",
      "supportParam": false,
      "icon": ""
    }
  ],
  "page": {
    "total": 1,
    "size": 30,
    "page": 1,
    "pages": 30,
    "offset": 0,
    "order": "desc"
  },
  "code": 200,
  "success": true,
  "requestId": "2f296259-d953-4939-9701-bc28ac43e002"
}
```

<a id="api-oapi-app-open-query-use-record-list"></a>

#### 3.3 查询应用运行记录

`POST` `/oapi/app/open/query/use/record/list`

**功能说明**：查询应用的被调用记录。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| appId | String | 否 | 应用ID,与时间筛选必传其中之一 |
| size | String | 否 | 一页大小，默认30，最大100 |
| minId | int | 是 | 游标分页字段，每次传上一页最大id作为起始id，不传则minId默认0 |
| beginDate | String | 否 | 开始时间,与应用筛选必传其中之一 |
| endDate | String | 否 | 结束时间,与应用筛选必传其中之一 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求ID |
| msg | string | 状态码描述 |
| data | [object] | 结果数据 |
| \|─id | number | 主键id 分页时需要带上当前页的最后一条数据的id |
| \|─ runRecordId | string | 运行记录对外主键 |
| \|─ appId | string | 应用id |
| \|─ userName | string | 账号 |
| \|─ startTime | string | 运行开始时间 |
| \|─ endTime | string | 运行结束时间 |
| \|─ updateTime | string | 同步时间 |
| \|─ runStatusName | string | 运行状态 |
| \|─ runStatus | string | 运行状态 |
| \|─ runningTime | integer | 运行时间长（秒） |
| \|─ heartTime | string | 心跳时间 |
| \|─ appName | string | 应用名 |
| \|─ startMode | string | 触发启动方式 |
| \|─ startModeName | string | 触发启动方式 名称 |
| \|─ remark | string | 错误信息 |
| page | [PageDTO | 分页信息 |
| \|─ total | integer | 总条数 |
| \|─ size | integer | 一页大小 |
| \|─ page | integer | 当前页 |
| \|─ pages | integer | 总页数 |
| \|─ offset | integer | 偏移量 |
| \|─ sortColumn | string¦ | 用于排序的 column 的名称 |
| \|─ order | string¦ | 排序方式 desc/asc，默认降序排列 |
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求id，方便排查使用 |
| serverIp | string | 处理服务的Ip |
| serverInstName | string | 处理服务实例名称 |
| msg | string | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/app/open/query/use/record/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "appId": "<appId>",
    "size": "<size>",
    "minId": "<minId>",
    "beginDate": "<beginDate>",
    "endDate": "<endDate>"
  }'
```

响应示例：

```json
{
  "data": [
    {
      "runRecordId": "360164898894159873",
      "appId": "29deebe9-95fc-4bdd-a6ba-df362d7215e0",
      "userName": "ceshi3@csqy1",
      "startTime": "2024-05-07 20:46:43",
      "endTime": "2024-05-07 20:46:44",
      "updateTime": "24-5-7 下午8:46",
      "runStatus": "finish",
      "runningTime": 1,
      "heartTime": "2024-05-07 20:46:44",
      "appName": "kkkkkk",
      "startMode": "manual",
      "startModeName": "手工执行"
    }
  ],
  "code": 200,
  "success": true,
  "requestId": "8c7a95ea-4ee6-4f01-8bcb-0925658ac283"
}
```

<a id="api-oapi-app-open-translate-owner"></a>

#### 3.4 转移应用所有者

`POST` `/oapi/app/open/translate/owner`

**功能说明**：把应用的所有者转移给企业内另一个账号。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| appId | String | 是 | 应用ID |
| receiveUserAccount | String | 是 | 接收人账号，需要精确匹配 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求ID |
| msg | string | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/app/open/translate/owner" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "appId": "<appId>",
    "receiveUserAccount": "<receiveUserAccount>"
  }'
```

响应示例：

```json
{
  "code": 200,
  "success": true,
  "requestId": "102778b7-3751-4d82-b919-e9d03f347f87"
}
```

### 4. 机器人相关

管理调度模式下的机器人（ShadowBot 客户端）：状态、分组、执行记录。

<a id="api-oapi-dispatch-v2-job-list"></a>

#### 4.1 查询机器人任务队列

`POST` `/oapi/dispatch/v2/job/list`

**功能说明**：查询机器人的执行记录（待执行队列与历史 job），支持按机器人、应用、任务、状态与触发时间筛选。采用游标翻页。

**注意**

- 查询调度运行记录列表

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| robotClientUuid | string | 否 | 机器人uuid，通过机器人列表接口获取 |
| scheduleUuid | string | 否 | 计划uuid，通过任务列表接口获取 |
| statusList | array | 否 | 参考 应用运行状态枚举值说明 |
| robotUuid | string | 否 | 应用uuid，通过应用列表接口获取 |
| triggerTimeBegin | string | 否 | 触发时间-起, 字符串, 格式是 “yyyy-MM-dd HH:mm:ss”, 如, 2025-11-10 10:00:00 |
| triggerTimeEnd | string | 否 | 触发时间-止, 字符串, 格式是 “yyyy-MM-dd HH:mm:ss”, 如, 2025-11-10 10:00:00 |
| cursorId | long | 否 | 游标id, 当第一页时，默认空 |
| cursorDirection | string | 是 | pre表示往上翻，next表示往下翻，默认为next |
| size | int | 是 | 最小是1，最大是100，默认20 |
| queryApi | boolean | 否 | 默认false，该参数填写true，能实现控制台api执行记录列表 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| data | object | 是 |   |
| ∟code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| ∟success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| ∟msg | string | 是 | 状态码描述 |
| ∟hasData | boolean | 是 | 用于判断继续翻页时是否有数据，可用作翻页按钮置灰操作比如当往下翻页到20页时，第21页没有数据，则在20页时hasData为false，表示不能继续往下翻页，只能往上翻页 |
| ∟nextId | long | 是 | 往下翻页时，可作为 cursorId 使用，表示从这个id开始往下翻页 |
| ∟preId | long | 是 | 往上翻页时，可作为 cursorId 使用，表示从这个id开始往上翻页 |
| ∟cursorDirection | string | 是 | 当前的翻页方向 next表示当前往下翻页 pre表示当前往上翻页 |
| ∟dataList | array | 是 | 响应数据 |
| ∟ id | long | 是 | 游标id |
| ∟ jobUuid | string | 是 | 应用运行uuid |
| ∟ taskName | string | 是 | 任务名称 |
| ∟ status | string | 是 | 应用运行状态 |
| ∟ triggerTime | date | 是 | 触发时间，任务被触发的时间 |
| ∟ startTime | date | 否 | 应用开始运行时间，当应用开始调度之后，值不为空 |
| ∟ endTime | date | 否 | 应用结束运行时间，当应用结束运行时，值不为空 |
| ∟ robotUuid | string | 是 | 应用uuid |
| ∟ robotName | string | 是 | 应用名称 |
| ∟ remark | string | 否 | 应用运行异常备注 |
| ∟ robotClientUuid | string | 否 | 机器人uuid |
| ∟ robotClientName | string | 否 | 机器人名称 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "robotClientUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0",
    "cursorDirection": "next", // 默认往下翻页
    "size": 20
  }'
```

响应示例：

```json
{
    "data": {
        "hasData": true,
        "nextId": 284065875470133276,
        "preId": 284065875470133295,
        "cursorDirection": "next",
        "dataList": [
            {
                "id": 284065875470133295,
                "jobUuid": "a54f25ef-9373-499a-afbb-79699f2c39e5",
                "status": "error",
                "taskName": "测试任务3",
                "robotUuid": "db5c419d-0ae7-4104-a313-45dc27ce3e49",
                "robotName": "应用A",
                "triggerTime": "2023-10-24 09:03:00",
                "robotClientUuid": "b21e8ffc-028c-40ae-a074-45a19f07cbda"
            },
            {
                "id": 284065875470133276,
                "jobUuid": "20db77a9-4126-412a-930c-0cc02c7b2d0c",
                "status": "error",
                "taskName": "测试3",
                "robotUuid": "799a2b1d-30ae-40ac-b011-f8a2beea5373",
                "robotName": "迁移测试",
                "triggerTime": "2023-10-24 09:00:00",
                "robotClientUuid": "b21e8ffc-028c-40ae-a074-45a19f07cbda"
            }
        ]
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-client-query"></a>

#### 4.2 查询机器人信息

`POST` `/oapi/dispatch/v2/client/query`

**功能说明**：按机器人账号名或机器人 UUID 查询单台机器人的详情与状态。

**前置条件**：需要到控制台-机器人管理，复制机器人账号或者机器人uuid，机器人uuid目前需要F12抓包从client/list接口获取uuid

**注意**

- 该接口是可以获取机器人信息，支持机器人名称或者机器人uuid查询，只需要填其中一个，两个都填的情况，请确认名称和uuid对的上，建议用机器人名称查询，因为机器人移出后，重新切换调度模式，机器人uuid会生成新的。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| accountName | string | 否 | accountName和robotClientUuid互斥，二选一即可，推荐使用机器人账号 |
| robotClientUuid | string | 否 | accountName和robotClientGroupUuid互斥，二选一即可，机器人uuid目前需要F12抓包从client/list接口获取uuid |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ robotClientUuid | string | 是 | 机器人uuid |
| ∟ robotClientName | string | 是 | 机器人名称，同accountName |
| ∟ status | string | 是 | 机器人状态，参考机器人状态枚举值说明 |
| ∟ description | string | 否 | 机器人备注描述 |
| ∟ remark | string | 否 | 运行备注 |
| ∟ clientIp | string | 是 | 客户端ip |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/client/query" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "accountName": "boyi@csqy"
  }'
```

响应示例：

```json
{
    "data": {
        "robotClientUuid": "0d6a835a-2e08-414a-af73-1e43f9d9c8ff",
        "robotClientName": "ceshi1@csqy1",
        "status": "idle",
        "description": "ceshi1",
        "clientIp": "172.16.28.156", 
      	"remark": "运行成功"
        
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-client-group-list"></a>

#### 4.3 查询机器人分组列表

`POST` `/oapi/dispatch/v2/client/group/list`

**功能说明**：查询企业下的机器人分组列表。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口查询该租户下机器人分组列表

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| key | string | 否 | 关键字模糊搜索，支持右边模糊搜索，类似 like "xx%" |
| page | Integer | 否 | 默认1，从第一页开始 |
| size | Integer | 否 | 默认20,每页20 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | array | 是 | 响应数据 |
| ∟ robotClientGroupUuid | string | 是 | 机器人分组uuid |
| ∟ robotClientGroupName | string | 是 | 机器人分组名称 |
| page | objects | 是 | 分页信息 |
| ∟ total | int | 是 | 分页总数 |
| ∟ size | int | 是 | 每页数量 |
| ∟ page | int | 是 | 第几页 |
| ∟ pages | int | 是 | 分成多少页 |
| ∟ offset | int | 是 | 分页偏移量 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/client/group/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json"
```

响应示例：

```json
{
    "data": [
        {
            "uuid": "a3d67252-6795-4a69-99ef-bce60e67xxxd",
            "name": "double11",
        }
    ],
    "page": {
        "total": 5,
        "size": 20,
        "page": 1,
        "pages": 1,
        "offset": 0,
        "order": "desc"
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-client-list"></a>

#### 4.4 查询机器人列表

`POST` `/oapi/dispatch/v2/client/list`

**功能说明**：分页查询企业下全部机器人及其状态、IP 与主机名，可用于构建机器人管理面板或筛选空闲机器人派发任务。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口是可以指定参数筛选查询本企业下的所有机器人，返回字段包括状态，名称，以及机器人所在终端的信息，可用作构建机器人管理模块，也可用于筛选空闲的机器人派发任务

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| status | string | 否 | 机器人状态，参考机器人状态枚举值说明 |
| key | string | 否 | 关键字模糊搜索，目前只对机器人名称有作用，等同于robotClientName |
| robotClientGroupUuid | string | 否 | 机器人分组uuid |
| page | Integer | 是 | 第几页 |
| size | Integer | 是 | 每页多少条 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | array | 是 | 响应数据 |
| ∟ robotClientUuid | string | 是 | 机器人uuid |
| ∟ robotClientName | string | 是 | 机器人名称，同accountName |
| ∟ status | string | 是 | 机器人状态，参考机器人状态枚举值说明 |
| ∟ description | string | 否 | 机器人备注描述 |
|   | object | 否 | 客户端终端信息 |
| ∟ windowsAccount | string | 否 | 客户端系统账号 |
| ∟ clientIp | string | 否 | 客户端系统ip |
| ∟ machineName | string | 否 | 客户端系统host名称 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/client/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "page":1,
    "size": 10
  }'
```

响应示例：

```json
{
  "data": [{
    "robotClientUuid": "xxx",
    "robotClientName": "admin@ydsc",
    "status": "idle",
    "description": "rpa001",
    "windowsUserName": "by",
    "clientIp": "127.0.0.1",
    "machineName": "RPA-PC"
  }],
  "page": {
    "total": 100,
    "size": 10,
    "page": 1,
    "pages": 10
  },
  "code": 0,
  "success": true,
  "msg": "success"
}
```

### 5. JOB运行

以「应用」为粒度触发运行，直接指定机器人或机器人分组，适用于简单调度场景。

<a id="api-oapi-dispatch-v2-job-stop"></a>

#### 5.1 停止应用运行

`POST` `/oapi/dispatch/v2/job/stop`

**功能说明**：按 jobUuid 停止单次应用运行。

**前置条件**：需要先调用启动应用应用接口，获取jobUuid

**注意**

- 应用运行状态处于终态，调用该接口无效果

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的accessToken |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| jobUuid | string | 是 | 无 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/stop" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0"
  }'
```

响应示例：

```json
{
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-job-start"></a>

#### 5.2 启动应用

`POST` `/oapi/dispatch/v2/job/start`

**功能说明**：指定机器人（或机器人分组）与目标应用，启动一次应用运行，返回 jobUuid。适用于简单调度场景；有多机器人、多应用编排需求时应改用任务运行接口。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中；新创建的用户账号，必须先进过一次调度模式

**注意**

- 该接口是指定机器人/机器人分组以及单个应用去运行，适用于简单调度场景，如若涉及到复杂的多个机器人执行多个应用等，建议使用调度任务接口能力，另外获取应用运行信息可通过在控制台-api执行配置回调接口和查询应用运行详情接口获取
- 影刀针对输入参数会有大小限制，一般建议所有输入参数加起来不超过8000，如遇到输入参数超过阈值，可有两种方案解决
- 方案一: 可以进行输入参数切割，如电商场景，1000个订单号传进来一次性调用，可以切割成100个订单号进行一次调用，将一次请求转换成10次
- 方案二: 可以把长文本转换成文件类型传递

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的accessToken |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| accountName | string | 否 | accountName和robotClientGroupUuid互斥，二选一即可，accountName可在控制台-机器人管理列表复制名称 |
| robotClientGroupUuid | string | 否 | accountName和robotClientGroupUuid互斥，二选一即可，robotClientGroupUuid可在控制台-机器人分组列表复制UUID |
| robotUuid | string | 是 | 登录控制台-应用管理-查看应用详情复制uuid |
| idempotentUuid | string | 否 | 为避免因为网络请求超时，导致重复启动任务，可指定本次请求的幂等uuid，影刀会判断当有多次相同幂等uuid请求时，只会成功过创建一次, 建议使用uuid，另外长度不可超过36位 |
| waitTimeout | string | 否 | 等待超时，可指定job排队时长 等待超时说明 |
| waitTimeoutSeconds | number | 否 | 等待超时时间，单位秒，最小设置60(1分钟)，最大设置950400(11天), 默认600(10分钟) |
| runTimeout | number | 否 | 可用于指定应用运行多长时间后自动停止， 常用来避免应用运行时间不可控或者卡死，影响排队任务运行，最小设置60 最大设置950400，单位秒，需要配合客户端5.10以及之上版本使用 |
| priority | string | 否 | 可通过该参数指定job在等待排队的优先级，参考等待排队优先级说明，默认是middle |
| executeScope | string | 否 | any:机器人分组中随机一个机器人执行 all:机器人分组中全部机器人都执行 |
| params | object | 否 | 共支持五种应用参数，最大支持params长度10000，应用运行参数说明，专有云6.0.0之前版本支持3000，之后版本支持8000 |
| ∟ name | string | 否 | 参数名称 |
| ∟ value | string | 否 | 参数值 |
| ∟ type | string | 否 | 参数类型，参考应用运行参数枚举值说明 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ jobUuid | string | 是 | 应用运行uuid，用于后续停止运行，查询运行状态入参 |
| ∟ idempotentFlag | boolean | 是 | 是否幂等创建标识，为true时表示重复请求，配合入参idempotentUuid使用 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/start" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "accountName": "admin@fckj",
    "robotUuid": "73d9a119-7ec7-4226-b679-506afefae667",
    "idempotentUuid":"69ba7c82-4087-42ca-b1ce-bd117bfea097",
    "waitTimeout":"10m",
    "executeScope":"any",
    "priority": "middle",
    "params":[
      {
        "name":"获取页数",
        "value":"10",
        "type":"str"
      }
    ]
  }'
```

响应示例：

```json
{
    "data": {
        "jobUuid": "fc38f4f1-8444-475e-83f8-3292eeb1606b",
        "idempotentFlag": true
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-job-query"></a>

#### 5.3 查询应用运行结果

`POST` `/oapi/dispatch/v2/job/query`

**功能说明**：按 jobUuid 查询单次应用运行的状态、耗时、截图与输入输出参数。官方建议 30 秒轮询一次，状态进入终态即停止。

**前置条件**：需要先调用启动应用接口，获取jobUuid

**注意**

- 该接口是可以轮询获取job执行状态，一般可以配合回调接口使用，当回调接口收到job相关信息或者轮询到job状态是终态时，需要停止轮询，job运行状态参考应用运行状态枚举值说明，影刀建议的轮询频率是30s一次，

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| jobUuid | string | 是 | 通过启动job接口获 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ jobUuid | string | 是 | 应用运行uuid |
| ∟ status | string | 是 | 应用运行状态 |
| ∟ statusName | string | 是 | 应用运行状态描述 |
| ∟ remark | string | 否 | 备注信息，当运行异常，值不为空 |
| ∟ robotClientUuid | string | 否 | 机器人uuid，当应用已被调度之后，值不为空 |
| ∟ robotClientName | string | 否 | 机器人名称，当应用已被调度之后，值不为空 |
| ∟ startTime | string | 否 | 应用开始运行时间，当应用开始调度之后，值不为空 |
| ∟ endTime | string | 否 | 应用结束运行时间，当应用结束调度之后，值不为空 |
| ∟ robotUuid | string | 是 | 应用uuid |
| ∟ robotName | string | 是 | 应用名称 |
| ∟ screenshotUrl | string | 否 | job的截屏url |
| ∟ robotParams | object | 否 | 应用运行参数 |
| ∟ inputs | array | 否 | 输入参数 |
| ∟ item | object | 否 |   |
| ∟ name | string | 否 | 参数名称 |
| ∟ value | string | 否 | 参数值 |
| ∟ type | string | 否 | 参数类型，参考应用运行参数枚举值说明 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/query" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0"
  }'
```

响应示例：

```json
{
    "data": {
        "jobUuid": "42c2e0ce-499b-47aa-8642-3a1125b4759a",
        "status": "waiting",
        "statusName": "等待调度",
        "remark": "应用启动",
        "robotClientUuid": "00a7a1de-af0b-47ad-a3a8-a8fc2b009762",
        "robotClientName": "ceshi1@csqy1",
        "startTime":"2021-02-03 11:11:11", 
        "endTime": "2021-03-03 12:12:12",
        "robotUuid": "00a7a1de-af0b-47ad-a3a8-a8fc2b009761",
        "robotName": "打印日志应用",
        "screenshotUrl": "https://winrobot-pub-a-dev.oss-cn-hangzhou.aliyuncs.com/image/xxx.jpg",
        "robotParams": {
            "inputs": [ 
                {
                    "name": "姓",
                    "value": "王",
                    "type": "str" 
                },
                {
                    "name": "名",
                    "value": "5",
                    "type": "str"  
                },
                {
                    "name": "上传文件",
                    "value": "https://winrobot-pub-a-dev.oss-cn-hangzhou.aliyuncs.com/document/temp/request.txt",
                    "type": "file"  
                }
            ],
          "outputs":[ 
            {
                    "name": "姓",
                    "value": "王",
                    "type": "str"  
            }
          ]
        }
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-job-retry"></a>

#### 5.4 重试应用运行

`POST` `/oapi/dispatch/v2/job/retry`

**功能说明**：对失败的应用运行记录发起重试。

**前置条件**：需要先调用启动job接口，获取jobUuid

**注意**

- 应用运行状态非异常或已停止状态，重试无效果

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| jobUuid | string | 是 | 无 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/retry" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUuid": "<jobUuid>"
  }'
```

响应示例：

```json
{
    "code": 200,
    "success": true
}
```

### 6. 任务运行

以「调度任务」为粒度触发运行，由调度中心按任务配置分配机器人。

<a id="api-oapi-dispatch-v2-task-query"></a>

#### 6.1 查询任务运行结果

`POST` `/oapi/dispatch/v2/task/query`

**功能说明**：按 taskUuid 查询一次调度任务的运行状态与输出参数。

**前置条件**：需要先调用启动任务接口，获取taskUuid

**注意**

- 该接口是可以轮询任务运行结果，可获取任务下多个应用的运行结果数据，当任务运行结果处于终态时，需要停止轮询，任务运行状态参考 任务运行状态枚举说明

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的accessToken |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| taskUuid | string | 是 | 由启动任务接口返 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ taskUuid | string | 是 | 任务运行uuid |
| ∟ taskName | string | 是 | 任务名称 |
| ∟ status | string | 是 | 任务运行状态，该字段可以判断任务是否终态，终态时需要停止轮询该接口，参考：任务运行状态枚举说明 |
| ∟ statusName | string | 是 | 任务运行状态描述 |
| ∟ startTime | string | 否 | 任务运行开始时间，当任务被调度时不为空 |
| ∟ endTime | string | 否 | 任务运行结束时间，当任务结束运行时不为空 |
| ∟ jobDataList | array | 是 | 任务所关联的应用运行信息，多个应用有多条 |
| ∟ jobUuid | string | 是 | 应用运行uuid |
| ∟ status | string | 是 | 应用运行状态 |
| ∟ statusName | string | 是 | 应用运行状态描述 |
| ∟ remark | string | 否 | 备注信息，当运行异常，值不为空 |
| ∟ robotClientUuid | string | 否 | 机器人uuid，当应用已被调度之后，值不为空 |
| ∟ robotClientName | string | 否 | 机器人名称，当应用已被调度之后，值不为空 |
| ∟ startTime | string | 否 | 应用开始运行时间，当应用开始调度之后，值不为空 |
| ∟ endTime | string | 否 | 应用结束运行时间，当应用结束调度之后，值不为空 |
| ∟ robotUuid | string | 是 | 应用uuid |
| ∟ robotName | string | 是 | 应用名称 |
| ∟ screenshotUrl | string | 否 | job的截屏url |
| ∟ robotParams | object | 否 | 应用运行参数 |
| ∟ inputs | array | 否 | 输入参数 |
| ∟ name | string | 否 | 参数名称 |
| ∟ value | string | 否 | 参数值 |
| ∟ type | string | 否 | 参数类型，参考：任务运行状态枚举说明 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/query" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "taskUuid":"4d8aae66-cec5-4043-85cc-70f4e0430111"
  }'
```

响应示例：

```json
{
    "data": {
        "taskUuid": "4d8aae66-cec5-4043-85cc-70f4e0430d4e",
        "taskName": "测试-api任务", 
        "status": "running",  
        "statusName": "运行中",
        "startTime": "2022-01-22 15:10:28",
        "endTime": "2022-01-22 15:10:46",
        "jobDataList": [
            {
                "jobUuid": "b934597c-f06d-4c52-9624-e62e7f7b9489",
                "status": "finish", 
                "statusName": "完成", 
                "remark": "", 
                "robotParams":  {
            				"name":"获取页数", 
            				"value":"10",
            				"type":"str" 
       					 }, 
                "robotClientUuid": "cfcc5904-2e82-4295-911c-0ce65c9099f2", 
                "robotClientName": "ceshi1@csqy1",
                "robotUuid": "3f3c9861-9300-4400-9c1f-f4e7f8bb4d08", 
                "robotName": "wait-10", 
                "startTime": "2022-01-22 15:10:28", 
                "endTime": "2022-01-22 15:10:46",
                "screenshotUrl": "https://winrobot-pub-a-dev.oss-cn-hangzhou.aliyuncs.com/image/xxx.jpg"
            },
            {
                "jobUuid": "97421b0b-2f64-4adf-94b9-0bdfc73face6",
                "status": "created",
                "statusName": "已创建",
                "remark": "",
                "robotParams":  {
            				"name":"获取页数", 
            				"value":"10",
            				"type":"str" 
       					 }, 
                "robotClientUuid": "cfcc5904-2e82-4295-911c-0ce65c9099f2",
                "robotClientName": "ceshi1@csqy1",
                "robotUuid": "e8be5a0a-ec3a-4f3a-b4a2-b9319fe6fd0a",
                "robotName": "等待-10s",
               "startTime": "2022-01-22 15:10:28", 
                "endTime": "2022-01-22 15:10:46",
                "screenshotUrl": "https://winrobot-pub-a-dev.oss-cn-hangzhou.aliyuncs.com/image/xxx.jpg"
            }
        ]
    },
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-task-stop"></a>

#### 6.2 停止任务运行

`POST` `/oapi/dispatch/v2/task/stop`

**功能说明**：按 taskUuid 停止正在运行或排队中的调度任务。

**前置条件**：需要先调用启动任务接口，获取taskUuid

**注意**

- 任务运行状态处于终态，调用该接口无效果

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| taskUuid | string | 是 | 无 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考： 状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/stop" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "taskUuid": "<taskUuid>"
  }'
```

响应示例：

```json
{
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-task-start"></a>

#### 6.3 启动任务

`POST` `/oapi/dispatch/v2/task/start`

**功能说明**：按 scheduleUuid 启动一个已配置好的调度任务，由调度中心分配机器人执行。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口需要在控制台新建任务，编排好应用和机器人，适用于更复杂的调度场景，该接口也支持从外部传入应用运行参数，如果有多个应用，需要填写多个应用的运行参数，服务内部逻辑会根据robotUuid取出传入的应用运行参数，透传到客户端
- 影刀针对输入参数会有大小限制，一般建议所有输入参数加起来不超过8000，如遇到输入参数超过阈值，可有两种方案解决
- 方案一: 可以进行输入参数切割，如电商场景，1000个订单号传进来一次性调用，可以切割成100个订单号进行一次调用，将一次请求转换成10次
- 方案二: 可以把长文本转换成文件类型传递

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | accessToken变量需要替换成鉴权接口返回的accessToken |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| scheduleUuid | string | 是 | 启动任务uuid，可在控制台-任务管理-右键获取 |
| idempotentUuid | string | 否 | 本次请求幂等uuid，建议使用uuid，避免网络重试多次触发任务执行, 影刀检测到两次请求的幂等id一样，会执行一次，并且第二次会返回上一次的taskUuid |
| scheduleRelaParams | array | 否 | 任务可能配置多个应用运行参数，是一个数组结构，需要指定robotUuid和对应的应用参数，如果没有指定，会取默认的应用运行参数 |
| ∟ robotUuid | string | 否 | 带运行参数的应用uuid |
| ∟ runTimeout | number | 否 | 可用于指定应用运行多长时间后自动停止， 常用来避免应用运行时间不可控或者卡死，影响排队任务运行，最小设置60 最大设置950400，单位秒，需要配合客户端5.10以及之上版本使用 |
| ∟ params | array | 否 | 关联该应用的应用运行参数,最大不能超过8000长度 |
| ∟ name | string | 否 | 参数名称 |
| ∟ value | string | 否 | 参数值 如果是文件类型可以使用文件上传接口文件上传接口先上传文件，将响应的fileKey作为参数值传递 |
| ∟ type | string | 否 | 参数类型，参考：应用运行参数枚举值说明 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ taskUuid | string | 是 | 任务运行uuid |
| ∟ jobUuidList | array | 是 | 任务下每条应用的运行记录uuid集合 |
| ∟ idempotentFlag | boolean | 是 | 是否幂等创建标识，为true时表示重复创建，配合入参idempotentUuid使用 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/start" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '// api调用任务
  {
    "scheduleUuid": "79985266-f37a-4bb1-b456-b928914d3437",
    "idempotentUuid":"adss82cb-3333-111-1112-asdsad",
    "scheduleRelaParams": [
      {
        "robotUuid": "8ccc82cb-3945-4c7e-bb02-ab4ba4b183fd",
        "runTimeout":456,
        "params": [
          {
            "name": "str1",
            "value": "测试1",
            "type": "str"
          }
        ]
      }
    ]
  }'
```

响应示例：

```json
{
    "data": {
        "taskUuid": "fc38fbsa-8333-1111-83f8-3292aaaaaa",
        "jobUuidList": ["fd57564f-11f5-4035-a20f-b2838fcc0b05", "d64b1246-f0ef-436e-a948-01c325614e16"],
        "idempotentFlag": false
    },
    "code": 200,
    "success": true
}
```

### 7. 任务

查询调度任务的配置与执行记录。

<a id="api-oapi-dispatch-v2-task-process-detail"></a>

#### 7.1 查询任务&机器人应用运行详情

`POST` `/oapi/dispatch/v2/task/process/detail`

**功能说明**：查询一次任务运行下，各机器人执行应用的明细（jobList）。

**前置条件**：1.调用该接口前请获取taskUuid以及robotClientUuid，作为参数，可通过查询单个任务详情接口以及最新执行记录接口获取taskUuid和robotClientUuid

**注意**

- 该接口可以获取该条任务运行记录下该客户端所有应用运行记录，等同于中控平台执行记录-点击具体某个客户端查看应用运行详情

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| taskUuid | string | 是 | 通过启动任务接口获取 |
| robotClientUuid | string | 是 | 机器人uuid |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ jobList | array | 是 | 应用运行记录 |
| ∟ jobUuid | string | 是 | 应用运行记录uuid |
| ∟ taskUuid | string | 是 | 任务运行记录uuid |
| ∟ status | string | 是 | 应用运行状态，参考应用运行状态枚举值说明 |
| ∟ createTime | string | 是 | 创建时间，一般等同触发时间 |
| ∟ updateTime | string | 是 | 更新时间 |
| ∟ dispatchCount | number | 是 | 调度次数 |
| ∟ startTime | string | 否 | 开始运行时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ endTime | string | 否 | 结束运行时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ existsParam | boolean | 是 | 是否存在输入/输出参数 |
| ∟ priority | string | 是 | 优先级 参考优先级枚举值说明 |
| ∟ remark | string | 是 | 应用运行备注，当应用运行报错后，该字段可视为错误备注 |
| ∟ robotClientUuid | string | 是 | 机器人uuid |
| ∟ robotName | string | 是 | 应用名称 |
| ∟ robotUuid | string | 是 | 应用uuid |
| ∟ screenshotUrl | string | 否 | 错误截屏url，当应用运行某一次运行异常后，值不为空 |
| ∟ sourceType | string | 是 | 执行来源类型，参考执行来源类型枚举值说明 |
| ∟ sourceUuid | string | 是 | 执行来源uuid，一般等同于scheduleUuid |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/process/detail" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "taskUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0",
    "robotClientUuid": "b2c85558-2ecb-421c-99db-fa2bd56de123"
  }'
```

<a id="api-oapi-dispatch-v2-task-newest-list"></a>

#### 7.2 最新任务执行记录

`POST` `/oapi/dispatch/v2/task/newest/list`

**功能说明**：查询最近的任务执行记录，用于快速巡检。

**注意**

- 该接口用户获取每条任务最新执行记录
- 该接口是可以指定参数筛选查询本企业下的所有机器人，返回字段包括状态，名称，以及机器人所在终端的信息，可用作构建机器人管理模块，也可用于筛选空闲的机器人派发任务

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| statusList | array | 否 | 参考任务运行状态说明 |
|   | string | 否 |   |
| startTime | string | 否 | 开始时间，以触发时间进行查询 |
| endTime | string | 否 | 结束时间，以触发时间进行查询 |
| page | number | 否 | 分页参数，第几页 默认1 |
| size | number | 否 | 分页参数一页多少条，默认20 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ cursorDirection | string | 是 | 游标方向，next表明下一页，pre表示上一页 |
| ∟ hasData | boolean | 是 | 是否还有下一页数据 |
| ∟ nextId | number | 是 | 下一页id |
| ∟ preId | number | 是 | 上一页id |
| ∟ dataList | array | 是 | 任务所关联的应用运行信息，多个应用有多条 |
| ∟ createTime | string | 是 | 创建时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ updateTime | string | 是 | 更新时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ executeScope | string | 是 | 机器人执行策略 参考机器人执行策略枚举说明 |
| ∟ clientScope | string |   |   |
| ∟ taskName | string | 是 | 任务运行名称，等同于taskName |
| ∟ id | numer | 是 | 任务运行id |
| ∟ sourceUuid | string | 是 | 来源uuid，一般是scheduleUuid |
| ∟ sourceType | string | 是 | 来源类型，参考执行来源枚举说明 |
| ∟ status | string | 是 | 任务运行状态，该字段可以判断任务是否终态，终态时需要停止轮询该接口，参考任务运行状态枚举说明 |
| ∟ taskUuid | string | 是 | 任务运行uuid 等同于sceneInstUuid |
| ∟ userUuid | string | 是 | 触发用户uuid |
| ∟ userName | string | 否 | 触发用户名称 |
| ∟ runTimes | number | 是 | 任务运行次数 |
| ∟ taskClients | array | 是 | 等同sceneInstClients |
| ∟ clientIp | string | 否 | 机器人客户端ip |
| ∟ robotClientStatus | string | 是 | 机器人状态 参考机器人状态枚举说明 |
| ∟ currentRobotUuid | string | 否 | 当前运行引用uuid |
| ∟ currentRobotName | string | 否 | 当前运行应用名称 |
| ∟ description | string | 否 | 机器人备注名称 |
| ∟ robotClientName | string | 否 | 机器人名称 |
| ∟ robotClientUuid | string | 否 | 机器人uuid |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/newest/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "startTime":"2022-05-15 17:50:00",
    "endTime":"2022-05-16 17:50:00",
    "statusList":["finish","running"],
    "page":1,
    "size": 20
  }'
```

响应示例：

```json

```

<a id="api-oapi-dispatch-v2-task-list"></a>

#### 7.3 单个任务执行记录列表

`POST` `/oapi/dispatch/v2/task/list`

**功能说明**：查询单个任务的执行记录列表，支持游标翻页。

**前置条件**：1.通过任务列表接口获取scheduleUuid作为sourceUuid传入

**注意**

- 该接口获取单个任务执行记录，可用作点击具体某个任务时，展示任务下所有的执行记录(以瀑布流展示)，不支持跳页

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |   |
|---|---|---|---|---|
| sourceUuid | string | 是 | 任务uuid |   |
| statusList | array | 否 | 参考任务运行状态说明 |   |
|   | string | 否 |   |   |
| startTime | string | 否 | 开始时间，以触发时间进行查询 |   |
| endTime | string | 否 | 结束时间，以触发时间进行查询 |   |
| cursorId | number | 否 | 第一页时不用传，点击下一页时需要传，该值取上一页最后一条记录id即可,点击上一页时，该值取上一次请求记录的第一条记录id即可 |   |
| cursorDirection | string | 是 | pre:点击上一页，next:点击下一页，第一页时默认next |   |
| size | number | 是 | number | 每页多少 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ cursorDirection | string | 是 | 游标方向，next表明下一页，pre表示上一页 |
| ∟ hasData | boolean | 是 | 是否还有下一页数据 |
| ∟ nextId | number | 是 | 下一页id |
| ∟ preId | number | 是 | 上一页id |
| ∟ dataList | array | 是 | 任务所关联的应用运行信息，多个应用有多条 |
| ∟ createTime | string | 是 | 创建时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ updateTime | string | 是 | 更新时间 格式yyyy-mm-dd hh:MM:dd |
| ∟ executeScope | string | 是 | 机器人执行策略 参考机器人执行策略枚举说明 |
| ∟ clientScope | string |   |   |
| ∟ taskName | string | 是 | 任务运行名称，等同于taskName |
| ∟ id | numer | 是 | 任务运行id |
| ∟ sourceUuid | string | 是 | 来源uuid，一般是scheduleUuid |
| ∟ sourceType | string | 是 | 来源类型，参考执行来源枚举说明 |
| ∟ status | string | 是 | 任务运行状态，该字段可以判断任务是否终态，终态时需要停止轮询该接口，参考任务运行状态枚举说明 |
| ∟ taskUuid | string | 是 | 任务运行uuid 等同于sceneInstUuid |
| ∟ userUuid | string | 是 | 触发用户uuid |
| ∟ userName | string | 否 | 触发用户名称 |
| ∟ runTimes | number | 是 | 任务运行次数 |
| ∟ taskClients | array | 是 | 等同sceneInstClients |
| ∟ clientIp | string | 否 | 机器人客户端ip |
| ∟ robotClientStatus | string | 是 | 机器人状态 参考机器人状态枚举说明 |
| ∟ currentRobotUuid | string | 否 | 当前运行引用uuid |
| ∟ currentRobotName | string | 否 | 当前运行应用名称 |
| ∟ description | string | 否 | 机器人备注名称 |
| ∟ robotClientName | string | 否 | 机器人名称 |
| ∟ robotClientUuid | string | 否 | 机器人uuid |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/task/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceUuid":"4d8aae66-cec5-4043-85cc-70f4e0430111",
    "startTime":"2022-05-15 17:50:00",
    "endTime":"2022-05-16 17:50:00",
    "statusList":["finish","running"],
    "cursorId":123,
    "cursorDirection": "next",
    "size":10
  }'
```

<a id="api-oapi-dispatch-v2-schedule-detail"></a>

#### 7.4 查询任务详情

`POST` `/oapi/dispatch/v2/schedule/detail`

**功能说明**：按 scheduleUuid 查询调度任务的配置详情，含关联应用、机器人与定时器。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口查询单个任务详情，适用于用户自己建设任务管理功能

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| scheduleUuid | string | 是 | 从任务列表接口中获取 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ scheduleUuid | string | 是 | 任务uuid |
| ∟ scheduleName | string | 是 | 任务名称 |
| ∟ scheduleType | string | 是 | 任务类型，参考任务类型枚举值说明 |
| ∟ createTime | string | 是 | 创建时间 yyyy-mm-dd hh:MM:ss |
| ∟ updateTime | string | 是 | 更新时间 yyyy-mm-dd hh:MM:ss |
| ∟ clientScope | string | 是 | 机器人选择范围 参考机器人选择范围 |
| ∟ executeScope | string | 是 | 机器人执行策略 机器人执行策略枚举说明 |
| ∟ creatorName | string | 是 | 创建人账号 |
| ∟ creatorUuid | string | 是 | 创建人uuid |
| ∟ modifierName | string | 是 | 修改人账号 |
| ∟ modifierUuid | string | 是 | 修改人uuid |
| ∟ enabled | boolean | 是 | 是否启用任务 |
| ∟ enabledWaitTimeout | boolean | 是 | 是否开启等待超时设置 |
| ∟ errorProcess | string | 是 | 错误执行策略 异常执行策略枚举说明 |
| ∟ newestTaskUuid | string | 否 | 最新一次任务运行uuid |
| ∟ runTimes | number | 是 | 运行时间 |
| ∟ priority | number | 是 | 运行次数 |
| ∟ robotClientList | array | 是 | 机器人相关 |
| ∟ uuid | string** ** | 是 | 机器人uuid |
| ∟ robotClientName | string | 否 | 机器人名称，机器人被删除时为空 |
| ∟ robotList | array | 是 | 应用相关 |
| ∟ enableRunTimeout | boolean | 是 | 是否开启应用运行超时设置 |
| ∟ icon | string | 否 | 图标 |
| ∟ robotName | string | 否 | 应用名称，如果应用被删除，为空 |
| ∟ robotUuid | string | 否 | 应用uuid，如果应用被删除，为空 |
| ∟ supportParam | boolean | 是 | 是否支持应用参数 |
| ∟ settings | array | 否 | 当 supportParam = true时， 应用主流程参数不为空 |
| ∟ inputs | array | 否 | 应用主流程输入参数 |
| ∟ description | string | 否 | 参数描述 |
| ∟ direction | string | 否 | 参数方向 Out为出参，In为入参 |
| ∟ name | string | 否 | 参数名称 |
| ∟ type | string | 否 | 参数类型，参考应用类型参数类型枚举值说明 |
| ∟ value | string | 否 | 参数值 |
| ∟ outputs | array | 否 | 应用主流程输出参数 |
| ∟ description | string | 否 | 参数描述 |
| ∟ direction | string | 否 | 参数方向 Out为出参，In为入参 |
| ∟ name | string | 否 | 参数名称 |
| ∟ type | string | 否 | 参数类型，参考应用类型参数类型枚举值说明 |
| ∟ value | string | 否 | 参数值 |
| ∟ userGrantList | array | 是 | 任务用户授权相关 |
| ∟ userUuid | string | 是 | 用户uuid |
| ∟ accountName | string | 是 | 用户账号名称 |
| ∟ waitTimeoutSettings | object | 是 | 超时设置 |
| ∟ waitTimeoutDay | number | 否 | 等待超时 以天为单位 |
| ∟ waitTimeoutHour | number | 否 | 等待超时 以小时为单位 |
| ∟ waitTimeoutMin | number | 否 | 等待超时 以分钟为单位 |
| ∟ cronInterface | object | 是 | 定时器 |
| ∟ cronExpress | string | 否 | cron表达式 |
| ∟ dayOfWeeks | number | 否 | 周天 |
| ∟ hour | number | 否 | 小时 |
| ∟ minimumIntervalSeconds | number | 否 | 最小秒 |
| ∟ minute | numner | 否 | 分钟 |
| ∟ month | numner | 否 | 月 |
| ∟ nextTime | string | 否 | 下一次触发时间 yyyy-mm-dd hh:MM:ss |
| ∟ time | string | 否 | 时分秒 |
| ∟ type | string | 否 | 定时器类型 参考定时器类型枚举说明 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/schedule/detail" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduleUuid":"xxx"
  }'
```

<a id="api-oapi-dispatch-v2-schedule-list"></a>

#### 7.5 查询任务列表

`POST` `/oapi/dispatch/v2/schedule/list`

**功能说明**：分页查询调度任务列表，支持按名称、启用状态与任务类型筛选。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口查询租户下所有任务列表，适用场景用于建立自己的任务管理功能

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| key | string | 否 | 目前作用在任务名称模糊搜索 |
| enabled | boolean | 否 | 是否启用任务 |
| scheduleType | string | 否 | 参考任务类型枚举值说明 |
| page | number | 否 | 默认值1，从第一页开始 |
| size | number | 否 | 默认值20，一页20条，该值最高上限500 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟ scheduleUuid | string | 是 | 任务uuid |
| ∟ scheduleName | string | 是 | 任务名称 |
| ∟ scheduleType | string | 是 | 任务类型，参考任务类型枚举值说明 |
| ∟ createTime | string | 是 | 创建时间 yyyy-mm-dd hh:MM:ss |
| ∟ updateTime | string | 是 | 更新时间 yyyy-mm-dd hh:MM:ss |
| ∟ cronInterface | object | 是 | 定时器 |
| ∟ cronExpress | string | 否 | cron表达式 |
| ∟ dayOfWeeks | number | 否 | 周天 |
| ∟ hour | number | 否 | 小时 |
| ∟ minimumIntervalSeconds | number | 否 | 最小秒 |
| ∟ minute | numner | 否 | 分钟 |
| ∟ month | numner | 否 | 月 |
| ∟ nextTime | string | 否 | 下一次触发时间 yyyy-mm-dd hh:MM:ss |
| ∟ time | string | 否 | 时分秒 |
| ∟ type | string | 否 | 定时器类型 参考定时器类型枚举说明 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/schedule/list" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "key":"测试",
    "enabled":true,
    "type":"period",
    "page":1,
    "size":10,
    "orderBy":"createTime"
  }'
```

响应示例：

```json

```

### 8. 运行日志

查询单次应用运行的日志，支持轮询与主动通知两种模式。

<a id="api-oapi-dispatch-v2-job-log-search"></a>

#### 8.1 查询应用运行日志

`POST` `/oapi/dispatch/v2/job/log/search`

**功能说明**：按条件检索应用运行日志。

**前置条件**：需要先调用启动应用接口，或者通过其他的方式获取jobUuid

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| jobUuid | string | 是 | 通过启动应用接口获取 |
| page | int | 否 | 默认第一页 |
| size | int | 否 | 默认20条 |
| queryFilter |   |   |   |
| ∟ beginTime | string | 否 | 开始时间 |
| ∟ endTime | string | 否 | 结束时间 |
| ∟ searchKey | string | 否 | 查询关键字 |
| ∟ sort | object | 否 |   |
| ∟ sortKey | string | 否 | 默认time，目前仅支持time |
| ∟ sortOrder | string | 否 | asc 升序 desc 降序 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，500表示失败 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 |   |
| ∟requestId |   |   |   |
| ∟ page |   |   |   |
| ∟ total | int | 是 | 总的数量 |
| ∟ page | int | 是 | 第几页 |
| ∟ size | int | 是 | 一页多少条 |
| ∟ logs | object | 否 | 无日志时为空 |
| ∟ time | string | 是 | 时间 参考 03/20/2024 15:35:23 |
| ∟ level | string | 是 | 日志等级 |
| ∟ text | string | 是 | 日志文本，不超过1K，超长会截取 |
| ∟ logId | long | 是 | 日志id |

**错误码**

| 错误码 | 说明 | 排查建议 |
|---|---|---|
| 200 | 正常 | 调用正常 |
| 500 | 服务端错误 | 服务端错误需要联系技术支持 |
| 80204001 | 日志查询失败 | 表示无法查询日志(原因有机器人未连接，机器人已被删除) |
| 80204004 | 日志查询超时 | 表示 日志查询超时 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/log/search" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0",
    "page": 1,
    "size": 20,
    "queryFilter":{
      "beginTime":"2024-03-20 11:11:11",
      "endTime":"2024-03-20 11:11:12",
      "searchKey":"淘宝",
      "sort": {
        "sortKey": "time",
        "sortOrder": "desc"
      }
    }
  }'
```

响应示例：

```json
{
    "requestId":"xxxxx",
    "page": {
            "total": 18,
            "size": 10,
            "page": 1
        },
    "logs": [
            {
                "level": "信息",
                "logId": 1,
                "text": "开始执行...",
                "time": "03/20/2024 15:35:23"
            }
        ],    
      
}
```

<a id="api-oapi-dispatch-v2-job-log-notify"></a>

#### 8.2 通知查询应用运行日志

`POST` `/oapi/dispatch/v2/job/log/notify`

**功能说明**：注册日志通知，由服务端在日志产生后推送，适合长时间运行的流程。

**前置条件**：需要先调用启动应用接口，或者通过其他的方式获取jobUuid

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| jobUuid | string | 是 | 通过启动应用接口获取 |
| page | int | 否 | 默认第一页 |
| size | int | 否 | 默认20条 |
| queryFilter |   |   |   |
| ∟ beginTime | string | 否 | 开始时间 |
| ∟ endTime | string | 否 | 结束时间 |
| ∟ searchKey | string | 否 | 查询关键字 |
| ∟ sort | object | 否 |   |
| ∟ sortKey | string | 否 | 默认time，目前仅支持time |
| ∟ sortOrder | string | 否 | asc 升序 desc 降序 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，500表示查询失败，80204001表示(无法查询日志) |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | string | 是 | 本次请求的requestId |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/log/notify" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUuid": "45c882ed-e44f-4818-afc0-05172e7ffbe0",
    "page": 1,
    "size": 20,
    "queryFilter":{
      "beginTime":"2024-03-20 11:11:11",
      "endTime":"2024-03-20 11:11:12",
      "searchKey":"淘宝",
      "sort": {
        "sortKey": "time",
        "sortOrder": "desc"
      }
    }
  }'
```

响应示例：

```json
{
    "data": "5qwedqeasdc0zssadasdasdqwq",
    "code": 200,
    "success": true
}
```

<a id="api-oapi-dispatch-v2-job-log-query"></a>

#### 8.3 轮询应用运行日志

`POST` `/oapi/dispatch/v2/job/log/query`

**功能说明**：轮询获取应用运行日志。

**前置条件**：需要先调用通知查询应用运行日志接口，获取requestld code定义: 1.200：表示已经获取到日志 2.500: 表示错误，不用轮询 3.80204002：表明日志上传处理中，则需要继续轮询 ps: 特殊情况，如果 通知查询应用运行日志 获取requestId后，超过60s再调用轮询应用运行日志接口，则日志会失效(云端日志保存60s)，则会提示该状态码

**注意**

- 该接口可以使用requestId，轮询此次的日志，建议每隔100ms轮询一次，轮询超过100次

**请求头**

|   |   |   |
|---|---|---|
| 基本 |   | 说明 |
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |
| Content-Type | application/json |   |

**请求参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| requestId | string | 是 | 通过启动应用接口获 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，500表示失败 , 80204002 表明处理中，需要继续轮询，建议轮询10s，如果还没有日志，则中断 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 本次请求的requestId |
| ∟ requestId |   |   |   |
| ∟ page |   |   |   |
| ∟ total | int | 是 | 总的数量 |
| ∟ page | int | 是 | 第几页 |
| ∟ size | int | 是 | 一页多少条 |
| ∟ logs | object | 否 | 无日志时为空 |
| ∟ time | string | 是 | 时间 参考 03/20/2024 15:35:23 |
| ∟ level | string | 是 | 日志等级 |
| ∟ text | string | 是 | 日志文本，不超过1K，超长会截取 |
| ∟ logId | long | 是 | 日志id |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/job/log/query" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d 'https://api.yingdao.com/oapi/dispatch/v2/job/log/query?requestId=xxx'
```

响应示例：

```json

```

### 9. 文件

上传文件到影刀文件服务器，用于突破输入参数长度限制。

<a id="api-oapi-dispatch-v2-file-upload"></a>

#### 9.1 文件上传

`POST` `/oapi/dispatch/v2/file/upload`

**功能说明**：上传文件到影刀文件服务器，返回文件标识，供 `type=file` 类型的应用入参使用。用于突破入参总长 8000 字符的限制。

**前置条件**：需要使用鉴权接口获取accessToken后，填写到对应的hearder中

**注意**

- 该接口用于调度api 启动任务或者启动应用场景，当流程中有文件类型输入参数时，先调用该接口完成文件上传，该接口会返回一个文件key，将文件key作为输入参数传递即可，影刀调度程序会根据文件key构建成机器人可识别下载的文件url。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken} 变量需要替换成鉴权接口返回的access Token |
| Content-Type | multipart/form-data |   |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | file | 是 | 目标文件的二进制文件流，具体用法请参照上面的示例代码 |

**返回参数**

| 名称 | 类型 | 必填 | 描述 |
|---|---|---|---|
| code | int | 是 | 状态码 200表示成功，非200表示失败 参考：状态码说明 |
| success | boolean | 是 | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| msg | string | 是 | 状态码描述 |
| data | object | 是 | 响应数据 |
| ∟fileKey | string | 是 | 文件fileKey， 用于启动应用和启动任务 文件类型输入参数 |

**错误码**

| 错误码 | 说明 | 排查建议 |
|---|---|---|
| 200 | 正常 | 调用正常 |
| 500 | 服务端错误 | 服务端错误需要联系技术支持 |
| 80204003 | 文件上传失败 | 根据文案中的提示进行处理，一般是上述限制条件被触发导致的失败 |
| 80200010 | 单词文件上传过大 | 文件大小超出限制，阈值:3145728 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/dispatch/v2/file/upload" \
  -H "Authorization: Bearer <accessToken>" \
  -F "file=@/path/to/your_file.xlsx"
```

响应示例：

```json
{
    "data": {
        "fileKey": "aedbdaad-0c9c-4c05-9082-be42f0ba03a2"
    },
    "code": 200,
    "success": true
}
```

### 10. 工作队列

向工作队列写入队列项，由机器人循环消费，适用于高并发排队场景。

<a id="api-oapi-tool-queue-v1-queues-queueuuid-enqueue"></a>

#### 10.1 新增队列项

`POST` `/oapi/tool/queue/v1/queues/{queueUuid}/enqueue`

**功能说明**：向指定工作队列写入一条队列项，供机器人循环消费，适用于高并发排队与重试场景。

**前置条件**：使用鉴权接口获取accessToken。

**请求头**

| 基本 | 参数值 | 说明 |
|---|---|---|
| Authorization | Bearer {accessToken} | {accessToken}变量需要替换成鉴权接口返回的access Token |

**请求参数**

| 名称 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | String | 是 | 队列任务项名称，长度应在1~100之间 |
| priority | Integer | 是 | 优先级，枚举值 【0，100，200】 0-高，100-中，200-低 |
| expireTime | Long | 否 | 过期时间，值为时间戳，单位：秒 |
| effectiveTime | Long | 否 | 生效时间，值为时间戳，单位：秒 |
| bizInfo | String | 是 | 业务信息，长度应在1~1000之间 |
| description | String | 否 | 描述，长度应在0~2000之间 |
| source | String | 是 | 来源，使用 OpenAPI 即可 |

**返回参数**

| 名称 | 类型 | 说明 |
|---|---|---|
| data | object | 结果数据 |
| \|─uuid | string | 队列项uuid |
| \|─name | string | 名称 |
| \|─status | string | 状态 |
| \|─priority | Integer | 优先级 |
| \|─expireTime | Long | 到期时间，值为时间戳，单位：秒 |
| \|─bizInfo | string | 业务信息 |
| \|─description | string | 描述 |
| \|─createTime | Long | 创建时间，值为时间戳，单位：秒 |
| \|─updateTime | Long | 更新时间，值为时间戳，单位：秒 |
| code | integer | 返回结果编码 200表示成功，其他表示失败 |
| success | boolean | 调用是否成功，可以根据该字段判断接口调用是否成功 |
| requestId | string | 请求id，方便排查使用 |
| serverIp | string | 处理服务的Ip |
| serverInstName | string | 处理服务实例名称 |
| msg | string | 状态码描述 |

**调用示例**

```bash
curl -X POST "https://api.yingdao.com/oapi/tool/queue/v1/queues/<queueUuid>/enqueue" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<name>",
    "priority": 1,
    "expireTime": 1,
    "bizInfo": "<bizInfo>",
    "description": "<description>",
    "source": "<source>"
  }'
```

响应示例：

```json
{
	"data": {
		"uuid": "q683587567319805952_R683587960149929985",
		"name": "1",
		"status": "queued",
		"priority": 100,
		"expireTime": 1714993713,
		"bizInfo": "1",
		"description": "1",
		"createTime": 1714983758,
		"updateTime": 1714983758
	},
	"page": null,
	"code": 200,
	"success": true,
	"requestId": null,
	"serverIp": null,
	"serverInstName": null,
	"msg": null
}
```

---

<a id="enum-ref"></a>

## 枚举值参考

### 任务运行状态枚举说明(sceneInstStatus)

| 状态码 | 状态码描述 | 是否终态 |
|---|---|---|
| waiting | 等待调度 | 否 |
| running | 任务运行中 | 否 |
| finish | 任务运行结束 | 是 |
| stopping | 任务正在停止 | 否 |
| stopped | 已结束 | 是 |
| error | 异常 | 是 |

### 应用运行状态枚举值说明(sceneInstJobStatus)

| 状态码 | 状态码描述 | 是否终态 |
|---|---|---|
| created | 已创建 | 否 |
| waiting | 等待调度 | 否 |
| running | 运行中 | 否 |
| finish | 完成 | 是 |
| stopping | 停止中 | 否 |
| stopped | 已停止 | 是 |
| error | 异常 | 是 |
| skipped | 已跳过 | 是 |
| cancel | 已取消 | 是 |

### 等待超时时间枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| 10m | 10分钟 |
| 20m | 20分钟 |
| 30m | 30分钟 |
| 1h | 1小时 |
| 2h | 2小时 |

### 应用运行参数类型说明

| 状态码 | 状态码描述 |
|---|---|
| str | 字符串 |
| int | 整型 |
| float | 浮点 |
| bool | 布尔 |
| file | 文件 |

### 应用运行优先级枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| high | 高 |
| middle | 中 |
| low | 低 |

### 机器人状态枚举值说明

| 状态码 | 状态码描述 | 描述 |
|---|---|---|
| connected | 已连接 | 长链建立起来时的状态，该状态持续时间非常短 |
| idle | 空闲 | 该状态下，可以直接调度应用，不需要排队 |
| allocated | 已分配 | 表示机器人已被分配应用，但是机器人还未运行应用，该状态下继续分配应用，会进行排队，该状态持续时间较短 |
| running | 运行中 | 表示机器人正在运行应用，该状态下继续分配应用会进行排队 |
| offline | 离线 | 断网或者退出调度模式，退出客户端，机器人所处的状态，该状态下继续分配应用会进行排队 |

### 回调数据类型枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| job | 应用运行数据回调 |
| task | 任务运行数据回调 |

### 执行范围枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| any | 任意一台 |
| all | 全部执行 |

### 定时器类型枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| timer | 定时模式，固定时间 |
| minute | 分钟 |
| hour | 小时 |
| day | 天 |
| week | 周 |
| month | 月 |
| cron | cron周期模式 |
| manual | 手动 |

### 机器人选择范围枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| assign | 指定具体需要运行应用的机器人 |
| group | 通过指定机器人分组的方式来指定机器人范围 |

### 机器人执行策略枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| any | 随机空闲机器人 |
| all | 全部机器人执行 |

### 异常执行策略枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| terminate | 停止执行 |
| continue | 继续执行 |
| retry | 重试 |
| retry_continue | 重试-继续执行 |

### 执行来源枚举值说明

| 状态码 | 状态码描述 |
|---|---|
| period | 计划触发 |
| timer | 定时触发 |
| manual | 手动触发 |
| api | api触发 |

---

<a id="status-code"></a>

## 状态码参考

| 错误码 | 说明 | 排查建议 |
|---|---|---|
| 200 | 正常 | 调用正常 |
| 401 | 接口未授权 | 1.排查accessKeyId和accessSecret配置项是否正确 2.排查请求地址是否填写正常， 公有云需要填写:https://console.yingdao.com/dispatch/monitoring/index 专有云填写对应专有云部署对应的地址 |
| 400 | 接口参数校验错误 | 1.未配置accessKeyId, 请用企业管理员登录后台并进行配置 2.未配置accessKeySecret, 请用企业管理员登录后台并进行配置3.accessKeyId错误，请用企业管理员登录后台并进行核对 4.accessKeySecret错误，请用企业管理员登录后台并进行核对!!! |
| 429 | 触发接口限流 | 请求频率过高触发接口限流，稍后重试。详情参考https://www.yingdao.com/yddoc/rpa/zh-CN/912893828744491008 |
| 500 | 服务内部错误 | 请联系技术支持进行排查 |

---

> **数据来源**：影刀官方开放 API 文档（`https://www.yingdao.com/yddoc`）与官方 OpenAPI 定义文件（v1.0.0）。
> 本文档共收录 10 个功能模块、31 个接口，请求与返回字段均取自官方文档原文，功能说明为归纳性描述。
> 影刀接口迭代较快，正式接入前建议比对官方文档最新内容；私有化部署请将 Base URL 替换为专有云域名。