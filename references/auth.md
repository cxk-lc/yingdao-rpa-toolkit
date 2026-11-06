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

## 3. token 生命周期

- 用 `accessKeyId` / `accessKeySecret` 调 `/oapi/token/v2/token/create` 换取 `accessToken`。
- token 最长有效期 2 小时；官方要求按响应 `expiresIn` 缓存，本工具预留 30 秒安全边界。
- 缓存文件默认位于：
  - Windows：`%LOCALAPPDATA%\yingdao-rpa-toolkit\token-cache.json`
  - 其他：`~/.cache/yingdao-rpa-toolkit/token-cache.json`
- 缓存按 `baseUrl + accessKeyId` 哈希隔离；可用 `--no-cache` 完全禁用。
- 业务接口返回 401 时，会自动强制刷新一次 token 并重试原请求。

## 4. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `缺少 accessKeyId / accessKeySecret`（退出码 2） | 四层配置都没有凭据 | 执行 `config init` 并填写，或设置环境变量 |
| `HTTP 401` / `接口未授权`（退出码 3） | 密钥错误、被禁用、环境不对 | 核对密钥与 `baseUrl`；专有云不要用公有云域名 |
| `baseUrl 只填域名`（退出码 2） | 把 `/oapi` 带进了域名 | 改为 `https://api.yingdao.com` |
| 配置存在但读到旧值 | 项目级文件覆盖了用户级 | `config show` 看 `source` 与 `config_path` |
| token 总是重新获取 | 缓存目录不可写或用了 `--no-cache` | 检查目录权限；或接受每次获取 |
| 中文参数乱码 | 终端编码不是 UTF-8 | 入口已统一 `reconfigure`；仍异常时先写 `--params-file` |

## 5. 安全边界

- 工具不会把 `accessKeySecret` 写回任何文件，也不会在 `config show` / 日志 / 异常中输出完整值。
- `auth check` 只输出 `token_masked`（形如 `520d****c88e`）。
- 排查问题时可以贴 `request_id`、命令与退出码，不要贴密钥或完整 token。
