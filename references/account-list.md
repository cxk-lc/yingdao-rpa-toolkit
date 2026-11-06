# RPA 企业账号列表

对应接口文档 **2.2 查询RPA企业账号列表**：`GET /oapi/rpa/user/v1/list`。

## 1. 命令

```bash
python scripts/yd.py account list
python scripts/yd.py account list --keyword 张三 --page 1 --size 20
python scripts/yd.py account list --account-type basic --account-type senior
python scripts/yd.py account list --all --size 100
```

`account list` 只读，不会创建或修改账号。

## 2. 参数

| 参数 | 对应接口字段 | 说明 |
|---|---|---|
| `--keyword` | `accountKeyword` | 账号关键词 |
| `--phone` | `phone` | 完整手机号 |
| `--account-type` | `accountTypes` | `basic` / `senior`，可重复或逗号分隔 |
| `--latest-login-begin` | `latestLoginTimeBegin` | 最近登录时间起点 |
| `--latest-login-end` | `latestLoginTimeEnd` | 最近登录时间终点 |
| `--expired-begin` | `expiredTimeBegin` | 过期时间起点 |
| `--expired-end` | `expiredTimeEnd` | 过期时间终点 |
| `--page` | `page` | 页码，默认 1 |
| `--size` | `size` | 每页条数，默认 20，最大 100 |
| `--all` | — | 自动翻页拉取全部结果 |
| `--max-pages` | — | `--all` 时最多拉取页数，默认 50 |

时间参数支持三种写法，内部统一转成**秒级时间戳**：

```bash
--latest-login-begin 1710000000
--latest-login-begin 2026-01-01
--latest-login-begin "2026-01-01 12:30:00"
```

不带时区的日期按本机时区解释；起点不能晚于终点。

## 3. 分页行为

- 不加 `--all`：只查一页，`data.page` 返回 `total/size/page/pages`。
- 加 `--all`：从 `--page`（默认 1）开始，按 `--size` 连续翻页，直到最后一页。
- 达到 `--max-pages` 仍未结束：停止并返回 `warnings`，不会静默截断。
- 接口未返回 `page.pages` 时，用“本页条数 < size”判断是否最后一页。

## 4. 返回结构

```json
{
  "kind": "account_list",
  "count": 27,
  "items": [
    {
      "userUuid": "...",
      "loginAccount": "xxx@corp",
      "name": "张三",
      "phone": "133****5678",
      "role": "e_user",
      "roleName": "员工",
      "accountType": "basic",
      "accountTypeName": "基础账号",
      "latestLoginTime": "2026-01-01 10:00:00",
      "expiredTime": "2027-01-01 23:59:59"
    }
  ],
  "page": {"total": 27, "size": 20, "page": 1, "pages": 2},
  "filters": {"accountKeyword": "张三"},
  "requested": {"all": true, "page": 1, "size": 20, "maxPages": 50, "fetchedPages": 2}
}
```

- `count` 是本次实际拉取条数；`page.total` 是服务端总数。
- `filters` 回显本次生效的筛选条件，便于复现。
- `--dry-run` 只输出 `request.query`，不发送请求。

## 5. 注意事项

- `size` 最大 100；需要全量时优先 `--all --size 100`，减少请求次数。
- `accountTypes` 在 URL 中以重复参数传递（`accountTypes=basic&accountTypes=senior`）。
- 返回结果含手机号等个人信息，属于敏感数据：不要写入公开文档、日志或无关的共享位置。
- 账号类型：`basic` 基础账号、`senior` 高级账号。
