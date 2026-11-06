# 技术方案文档 · 影刀RPA工具包

> 版本：v0.1 ｜ 日期：2026-11-06 ｜ 状态：待确认
> 原则：只锁定技术栈与架构大方向，细节在实现中校准——过早写满细节，会把未验证的猜测包装成约束。

## 1. 技术栈

| 层面 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.10（Miniconda `python_3_10`） | 与本机既有环境一致；`X \| None` 等语法可用，不引入 3.12 专属特性 |
| 运行时依赖 | **无第三方依赖**（`urllib` / `argparse` / `logging` / `json`） | 技能要能被直接拷进 `~/.workbuddy/skills` 运行，不假设目标机装过 pip 包 |
| 包管理 | `pyproject.toml`（setuptools）+ `requirements*.txt` 说明 | 既可 `python scripts/yd.py` 直接跑，也可 `pip install -e .` 后得到 `yd` 命令 |
| 测试 | pytest（仅开发依赖） | 覆盖配置优先级、错误映射、HTTP 重试与 CLI JSON 契约，全部离线可跑 |
| 日志 | 标准库 `logging`，输出 stderr | stdout 必须留给单条 JSON；日志不能污染机器可读输出 |

## 2. 架构方向

分四层，依赖方向单向向下，入口层不直接碰 `urllib`：

1. **入口层**：`scripts/yd.py`（薄壳）→ `yingdao_rpa/cli.py`（解析参数、装配依赖、兜底异常）→ `yingdao_rpa/commands/*`（一个子命令一个模块，`register()` + `run()`）。
2. **领域封装层**：`client.py` 负责 token 生命周期（仅内存）、统一响应判定、401 刷新、429 退避；**不设 token 持久化模块**，跨命令通过参数/环境变量传递。
3. **基础设施层**：`transport.py` 只做 HTTP 往返与网络异常归一化；不判断业务成功与否。
4. **横切层**：`config.py`（四层配置合并与校验）、`errors.py`（异常体系 ↔ 退出码）、`logging_setup.py`（分级日志与脱敏）、`output.py`（stdout JSON 契约）。

新增一个接口的固定动作：在 `commands/` 建模块 → 写 `register()` 注册参数 → 写 `run()` 调 `client.request()` → 在 `commands/__init__.py` 挂上 → 补一条 tests。**不允许在命令里直接拼 URL 或发 `urllib` 请求。**

## 3. 备选方案与取舍记录

| 候选方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 标准库 `urllib` + `argparse` | 零依赖、拷贝即用、技能分发最稳 | 手写重试/超时/编码，代码量略多 | **采用** |
| `requests` / `httpx` | API 友好、连接池、超时语义清晰 | 目标机需装包；技能冷启动易失败 | 备选（若后续要连接池/并发再引入） |
| `click` / `typer` | 子命令与帮助更省代码 | 引入依赖；异常输出需额外接管才能保证 JSON 契约 | 不采用 |
| 直接上 FastAPI 常驻服务 | 可被外部系统远程调用 | 需端口、鉴权、并发与运维，超出本版范围 | 推迟（CLI 稳定后再加适配层） |
| 代码放 `src/` 布局 | 工程规范、避免误导入 | 技能目录被整体拷贝时需额外配 `PYTHONPATH` | 不采用，包放 `scripts/` 下随技能走 |

## 4. 已知风险

- **接口漂移**：影刀开放 API 字段可能随版本变化（如 `params` 长度从 3000 提到 8000）。对策：字段集中在 `client.py`/命令层，响应原样透传 `data`，不在中间层做过度裁剪。
- **token 不落盘与传递**：token 只在进程内存，跨命令需显式传递；调用方传入的 token 失效时不静默替换。对策：`auth token` 输出完整 token（禁止 `--save`），其它命令用 `--access-token` / `YD_ACCESS_TOKEN` 接收；401 时对"凭据换取"的 token 刷新一次，对"外部传入"的 token 直接报错并提示重新获取。
- **POST 重试的副作用**：`job/start` 非幂等，网络超时后重发可能重复启动。对策：仅对 429 退避重试；用户可传 `--idempotent-uuid` 获得服务端幂等保护。
- **Windows 编码**：中文参数与控制台 GBK 冲突。对策：入口 `reconfigure(encoding="utf-8")`，文件读写显式 `encoding="utf-8"`。
- **凭据泄漏**：日志、异常、`config show` 都可能带出 secret。对策：`Config.__repr__` 与 `config show` 统一脱敏；client 只记录 path 与 requestId。
- **长参数**：超过约 8000 字符会被服务端拒绝。对策：本地预估 JSON 长度并拦截，提示拆批或 `type=file`。

## 5. 运行与测试方式

- 运行命令：`python scripts/yd.py --help`（或 `yd --help`）
- 测试命令：`python -m pytest -q`
- Python 路径：`D:/Program Files/miniconda3/envs/python_3_10/python.exe`
- 验证工具（AI 自测所需）：pytest + CLI 冒烟（`--version`、`config show`、`auth token --dry-run`、`job start --dry-run`、无凭据 `auth check` 的退出码）
- 不依赖真实网络：client/transport 测试使用假传输对象；真实鉴权、取 token 与启动由人工验收。

> 填写后请同步更新 `AGENTS.md` 的"项目信息"一节。
