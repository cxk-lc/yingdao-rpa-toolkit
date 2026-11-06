# 影刀RPA工具包

把影刀开放 API 封装成 **WorkBuddy 技能 + 命令行工具**：用一条命令触发 RPA 应用运行，并拿回可解析的结果。

- 运行时**零第三方依赖**（Python 3.10 标准库 `urllib` / `argparse` / `logging`）。
- stdout 永远是一条 JSON；日志与提示只走 stderr。
- 固定退出码语义，便于 AI 与脚本判断下一步。
- 以 `SKILL.md` 作为技能入口，可直接拷进 `~/.workbuddy/skills/`。

## 目录结构

```
影刀RPA工具包/
├── SKILL.md                 # 技能入口：何时用、怎么调、硬规则
├── AGENTS.md                # AI 编程代理的项目值班手册
├── README.md
├── USAGE.md                 # 使用说明：命令行逐条详解 + 自然语言调用
├── pyproject.toml           # 包元数据；pip install -e . 后可用 yd 命令
├── requirements.txt         # 运行时依赖（空）
├── requirements-dev.txt     # pytest
├── config.example.json      # 配置样例
├── .env.example             # 环境变量样例
├── docs/
│   ├── product-design.md    # 做什么 / 不做什么
│   ├── tech-design.md       # 技术栈、架构、风险
│   └── acceptance-checklist.md
├── scripts/
│   ├── yd.py                # 唯一 CLI 入口（薄壳）
│   └── yingdao_rpa/         # 核心包
│       ├── cli.py           # 解析参数、装配依赖、异常兜底
│       ├── commands/        # 每个子命令一个模块
│       ├── client.py        # 影刀 API 封装（token/重试/错误分类）
│       ├── accounts.py      # 企业版账号后缀补全
│       ├── transport.py     # HTTP 传输层
│       ├── config.py        # 四层配置合并与校验
│       ├── errors.py        # 异常体系 ↔ 退出码
│       ├── logging_setup.py # stderr 日志
│       └── output.py        # stdout JSON 契约
├── references/
│   ├── auth.md              # 配置与鉴权排查
│   ├── account-list.md      # RPA 企业账号列表与筛选
│   ├── robot-info.md        # 机器人状态与账号后缀
│   └── output-contract.md   # JSON 结构与退出码
└── tests/                   # 离线 pytest 用例
```

## 快速开始

```bash
# 本机 Python 3.10
PY="D:/Program Files/miniconda3/envs/python_3_10/python.exe"

# 1. 生成配置模板（项目级；无 .git 时写到 ~/.yingdao/config.json）
"$PY" scripts/yd.py config init

# 2. 填入 accessKeyId / accessKeySecret 后查看生效配置（密钥脱敏）
"$PY" scripts/yd.py config show

# 3. 验证凭据
"$PY" scripts/yd.py auth check

# 4. 获取 token（不落盘），把 data.access_token 传给下一条命令
"$PY" scripts/yd.py auth token

# 5. 干跑：只输出请求预览，不发送
"$PY" scripts/yd.py job start --app-id <appId> --account-name <机器人名> \
  --param 月份=2026-10 --dry-run

# 5.1 查询机器人状态（名称缺 @ 时先查企业账号补全 loginAccount）
"$PY" scripts/yd.py robot info --name ceshi1

# 5.2 查询 RPA 企业账号列表（可按关键词、类型、时间筛选）
"$PY" scripts/yd.py account list --keyword 张三 --account-type basic

# 6. 真实启动并拿 jobUuid（也可不传 token，让命令自行用凭据换取）
"$PY" scripts/yd.py job start --app-id <appId> --account-name <机器人名> \
  --param 月份=2026-10

# 7. 查询结果；--wait 轮询到终态
"$PY" scripts/yd.py job query --job-uuid <jobUuid> --wait
```

不带 `scripts/yd.py` 前缀时，也可以 `pip install -e .` 后直接使用 `yd` 命令。

## 使用说明

上面是「最短可用路径」。完整的参数表、边界条件、常见坑，以及**用一句话让 AI 帮你跑**（自然语言调用）的写法，见 [`USAGE.md`](USAGE.md)：

- 第一次上手：看 USAGE 的「2. 准备：配置与凭据」+「4.4 完整链路」。
- 不想背命令：看「3. 方式一：自然语言调用」，里面有效说法/无效说法对照。
- 踩坑了：看「6. 常见坑」和「7. 排障三步」。

## 配置优先级

```
命令行参数  >  环境变量 YD_*  >  项目级 .yingdao/config.json（向上查找）  >  用户级 ~/.yingdao/config.json
```

- 凭据也可用 `YD_ACCESS_KEY_ID` / `YD_ACCESS_KEY_SECRET` 注入，适合 CI 或临时会话。
- 企业版机器人账号后缀用 `enterpriseSuffix`（如 `@csqy1`）；`robot info --name` 缺少 `@` 时先查企业账号取 `loginAccount`，无匹配再回退该配置。
- `.env`、`.yingdao/` 已在 `.gitignore` 中，不会被提交。
- 私有化部署只改 `baseUrl` 为专属域名，不要带 `/oapi` 路径。

## 命令清单（v0.1）

| 命令                                                                                  | 作用                              |
| ----------------------------------------------------------------------------------- | ------------------------------- |
| `config init [--scope project\|user] [--force]`                                     | 生成配置模板                          |
| `config show`                                                                       | 查看生效配置（脱敏）                      |
| `auth check`                                                                        | 验证凭据，输出脱敏 token 与有效期            |
| `auth token`                                                                        | 获取完整 accessToken，供其它命令直接传入；不写文件 |
| `robot info (--name <名称> \| --uuid <uuid>) [--suffix @企业标识]`                        | 查询单台机器人状态；名称缺 `@` 时先查企业账号补全     |
| `account list [--keyword ...] [--phone ...] [--account-type basic\|senior] [--all]` | 分页查询 RPA 企业账号，支持时间范围筛选          |
| `job start --app-id ... (--account-name \| --robot-group-uuid) ...`                 | 启动一次应用运行                        |
| `job query --job-uuid ... [--wait]`                                                 | 查询运行状态与输出参数                     |

|                                  |                                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------ |
| 全局参数：`--dry-run`、\`--format json | text`、`--save <file>`、`--access-token <token>`、`--debug`、`--log-file <file>`、`--timeout\`。 |

## Token 不落盘与跨命令传递

`auth token` 只把 token 放在当前进程内存并输出，**不会写任何缓存文件**。其它命令通过两种方式直接接收：

```bash
# 方式一：显式传入（Agent 读取 JSON 的 data.access_token 后传参）
"$PY" scripts/yd.py auth token
"$PY" scripts/yd.py job query --job-uuid <uuid> --access-token <上一步的 token>

# 方式二：环境变量 / shell 管道（text 模式只输出 token 原文）
TOKEN=$("$PY" scripts/yd.py auth token --format text)
YD_ACCESS_TOKEN="$TOKEN" "$PY" scripts/yd.py job query --job-uuid <uuid>
```

- 传入的 token 优先于凭据，命令不会再换取新 token。
- 传入的 token 失效时返回退出码 3，并提示重新执行 `auth token`，不会静默替换。
- `auth token` 禁止 `--save`，避免误落盘。

## 输出与退出码

成功与失败都输出同一条 JSON 结构；退出码 0/1/2/3/4/5/6 分别对应成功、业务错误、参数/配置、鉴权、网络/超时、任务失败、前置条件。详见 [`references/output-contract.md`](references/output-contract.md)。

## 测试

```bash
"$PY" -m pytest -q
```

测试全部离线：使用假传输层，不触网、不需要真实凭据。真实鉴权与启动属于人工验收项。

## 作为技能安装

- 目标目录名需与 SKILL.md 的 name 一致
- 直接克隆仓库代码或者从release下载skill压缩包到本地并解压缩，然后将代码文件夹整个放到智能体工作台的技能目录中
- 不知道工作台的skill目录可以直接问智能体，或者直接让智能体帮你安装

### 安装提示词

- 请根据 https://skillhub.cn/install/skillhub.md，安装 @indiv-cxk/yingdao-rpa-toolkit。
- 请从 https://github.com/cxk-lc/yingdao-rpa-toolkit，安装 cxk-lc/yingdao-rpa-toolkit。

> 该目录名已存在一份旧版实现；本版验收通过前建议先备份旧目录，再替换。

## 当前边界

已实现：配置管理、`auth check` / `auth token`、`robot info`、`account list`、`job start` / `job query` 的触发与查询闭环。机器人/应用/任务**列表**、重试/停止、运行日志、文件上传、工作队列、回调、常驻 HTTP 服务均**未实现**，按 `docs/product-design.md` 的推迟清单逐项迭代。
