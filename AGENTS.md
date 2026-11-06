# AGENTS.md

> 本文件是 AI 编程代理的项目值班手册。进入本项目开启新会话时，先读取本文件并遵守以下规则。
> 保持精简：高频规则放在这里，细节按需引用其他文档。

## 交付规则（必须遵守）

1. **每完成一个可验证的功能或修复后必须创建 Git commit**，保留可追踪的版本快照，便于随时回退。
2. **每次改动后必须编写或更新相关测试**，并在交付前确保所有测试与验收全部通过。
3. **所有 Git commit 信息统一使用简体中文**（初始化时确认，如需变更请同步修改本文件）。
4. **不提交密钥与敏感数据**：不要提交 `.env`、密钥、客户数据；配置示例写入 `.env.example`。

## 项目信息

- 项目名称：影刀RPA工具包（Skill + Python CLI，零第三方运行时依赖）
- 技术栈：Python 3.10 / 标准库 `urllib` + `argparse` + `logging` / pytest（仅开发）
- 运行命令：`python scripts/yd.py --help`
- 测试命令：`python -m pytest -q`
- 本机解释器：`D:/Program Files/miniconda3/envs/python_3_10/python.exe`
- 目录说明：
  - `docs/`：产品设计（product-design.md）与技术方案（tech-design.md）、验收清单
  - `scripts/yd.py`：唯一 CLI 入口（薄壳）
  - `scripts/yingdao_rpa/`：核心包
    - `cli.py` 参数解析与装配；`commands/` 每子命令一个模块
    - `client.py` 影刀 API 封装（token/重试/错误分类）；`transport.py` HTTP 传输
    - `config.py` 配置管理；`errors.py` 异常与退出码；`logging.py` 日志；`output.py` JSON 契约
  - `tests/`：pytest 离线用例
  - `references/`：技能子文档；根目录 `SKILL.md` 为技能入口

## 本项目专属规则

- 新增接口只允许在 `scripts/yingdao_rpa/commands/` 加模块并走 `client.request()`；禁止在命令里直接拼 URL 或调用 `urllib`。
- stdout 永远只能有一条 JSON；任何日志、提示、进度都写 stderr。
- 不得在代码、测试、文档、日志中出现真实 `accessKeySecret` / 完整 token；示例统一用占位符。
- **accessToken 不落盘**：不得新增任何 token 文件缓存；跨命令只能通过 `--access-token` / `YD_ACCESS_TOKEN` 传递，`auth token` 禁止 `--save`。
- 修改 API 字段后，同步更新 `SKILL.md` 的"关键事实"与 `references/` 对应文档。

## 边界约定

- 不擅自扩大需求范围；"暂时不做"的功能清单见 `docs/product-design.md`。
- 遇到规格不明确的情况：先提问或停下，不要猜测后直接实现。
- 涉及密钥、客户数据或隐私信息时先询问，不要写入代码、日志或提交。
- 重大架构调整前，先给出方案并等待确认。
