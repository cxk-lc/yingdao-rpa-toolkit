# 配置与鉴权

## 1. 在影刀控制台取密钥

1. 使用**企业管理员**账号登录影刀控制台。
2. 进入「高级设置 → API 配置」。
3. 新建一对 `accessKeyId` / `accessKeySecret`；建议一个对接系统一对密钥，便于审计与吊销。
4. 把密钥写入本地配置或环境变量，**不要**提交到 Git、不要写进聊天记录。

## 2. 配置来源与优先级

```
命令行参数  >  环境变量 YD_*  >  项目级 .yingdao/config.json（从当前目录向上查找）
            >  用户级 ~/.yingdao/config.json
```

| 字段 | 环境变量 | 说明 |
|---|---|---|
| `baseUrl` | `YD_BASE_URL` | 公有云 `https://api.yingdao.com`；专有云填专属域名，不要带 `/oapi` |
| `accessKeyId` | `YD_ACCESS_KEY_ID` | 控制台创建 |
| `accessKeySecret` | `YD_ACCESS_KEY_SECRET` | 控制台创建 |
| `timeoutSeconds` | `YD_TIMEOUT` | 单次 HTTP 超时，默认 30 |
| `pollIntervalSeconds` | `YD_POLL_INTERVAL` | 轮询间隔，默认 30，最小 5 |
| `maxPollSeconds` | `YD_MAX_POLL_SECONDS` | 单次 `--wait` 最长等待，默认 1800 |
| `defaultAccountName` | `YD_DEFAULT_ACCOUNT_NAME` | 默认机器人名称 |
| `defaultRobotClientGroupUuid` | `YD_DEFAULT_ROBOT_GROUP_UUID` | 默认机器人分组 uuid（与上一项互斥） |

生成模板：

```bash
python scripts/yd.py config init              # 有 .git 时写项目级，否则写用户级
python scripts/yd.py config init --scope user # 强制写用户级
```

查看当前生效配置（密钥脱敏）：

```bash
python scripts/yd.py config show
```

`config_path` 为空表示四层都没有配置文件，当前使用默认值。

## 3. token 的获取、传递与失效

### 3.1 两个命令的分工

| 命令 | 用途 | 输出 |
|---|---|---|
| `auth check` | 验证凭据是否可用；确认能换到 token | 脱敏 token、有效期、来源 |
| `auth token` | 取一个可用的完整 token，交给后续命令/工具 | `data.access_token`（完整） |

两者都调用 `GET /oapi/token/v2/token/create`，但**都不会把 token 写到磁盘**。

### 3.2 不落盘 + 直接传递

```bash
# 取 token（JSON）
python scripts/yd.py auth token

# 显式传给后续命令：把上一步 data.access_token 原样传入
python scripts/yd.py job query --job-uuid <uuid> --access-token <token>

# 或者：text 模式只输出 token 原文，配合 shell 变量 / 环境变量
TOKEN=$(python scripts/yd.py auth token --format text)
YD_ACCESS_TOKEN="$TOKEN" python scripts/yd.py job query --job-uuid <uuid>
```

- 传入的 token 优先于 `accessKeyId/accessKeySecret`，命令不会再换取新 token。
- `auth token` 禁止 `--save`；token 只存在于进程内存与调用方手中。
- 命令行参数可能出现在进程列表里；多用户机器上优先用 `YD_ACCESS_TOKEN`。

### 3.3 有效期与 401

- token 最长 2 小时；工具按响应 `expiresIn` 计算内存过期时间，预留 30 秒安全边界。
- 用凭据换取的 token 在业务接口返回 401 时，会自动重新获取一次并重试原请求。
- 调用方显式传入的 token 被视为权威：401 时直接返回退出码 3，并提示重新执行 `auth token`，**不会静默替换**成凭据换取的新 token。

## 4. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `缺少 accessKeyId / accessKeySecret`（退出码 2） | 四层配置都没有凭据 | 执行 `config init` 并填写，或设置环境变量 |
| `HTTP 401` / `接口未授权`（退出码 3） | 密钥错误、被禁用、环境不对，或传入的 token 已过期 | 核对密钥与 `baseUrl`；传入 token 时重新执行 `auth token` |
| `传入的 accessToken 已失效`（退出码 3） | `--access-token` / `YD_ACCESS_TOKEN` 过期 | 重新获取并传递新 token |
| `baseUrl 只填域名`（退出码 2） | 把 `/oapi` 带进了域名 | 改为 `https://api.yingdao.com` |
| 配置存在但读到旧值 | 项目级文件覆盖了用户级 | `config show` 看 `source` 与 `config_path` |
| `auth token` 报“不允许 --save” | 该命令禁止落盘 | 去掉 `--save`，用 `--access-token` 传递 |
| 中文参数乱码 | 终端编码不是 UTF-8 | 入口已统一 `reconfigure`；仍异常时先写 `--params-file` |

## 5. 安全边界

- 工具不会把 `accessKeySecret` 写回任何文件，也不会在 `config show` / 日志 / 异常中输出完整值。
- `auth check` 只输出 `token_masked`（形如 `520d****c88e`）。
- `auth token` 是唯一会输出完整 token 的命令，且明确禁止 `--save`；不要把它的输出粘进聊天、工单或日志。
- 排查问题时可以贴 `request_id`、命令与退出码，不要贴密钥或完整 token。

