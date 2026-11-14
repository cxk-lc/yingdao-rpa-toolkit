# 人工验收清单 · v0.1.2（增量）

> 基线：`v0.1.1` 已签署，记录见 `docs/acceptance-checklist-v0.1.1.md`。
> 范围：机器人调度规则、`job start` 默认自动选机器人、dry-run 预览修复、配置隔离修复。
> 验收依据：用户 2026-11-14 发布 `v0.1.2` 的指令 + AI 自测与真实接口只读抽样证据。

## 1. 冒烟测试

- [x] `python scripts/yd.py --version` 输出 `yingdao-rpa-toolkit 0.1.2`
- [x] `python -m pytest -q` 全绿（当前 AI 自测：221 passed）
- [x] `job start --help` 能看到 `--auto-robot` / `--queue-if-busy`
- [x] `config init --dry-run` 只显示目标路径，不创建文件
- [x] text 模式对 dry-run 输出预览，不出现「鉴权成功」等误导文案

## 2. 机器人调度规则

- [x] 指定 `--account-name` 且空闲：直接使用，不额外改派
- [x] 指定机器人非空闲：退出码 6，`data.kind=dispatch_decision`，含 `idleCandidates` 与 `queueOption`
- [x] 指定机器人非空闲 + `--queue-if-busy`：允许排队启动
- [x] 未指定账号/分组：默认自动选择空闲机器人
- [x] 多个空闲：优先该应用历史成功次数最多；并列/无历史随机
- [x] 无空闲：返回 `no_idle_robot` 与在线候选；无在线机器人返回 `no_available_robot`
- [x] `--auto-robot` 可显式覆盖配置默认机器人
- [x] 显式 `--account-name` 优先于配置默认分组
- [x] `--dry-run` 自动模式返回两段式预览，不发请求

## 3. 回归与修复

- [x] 配置向上查找不会把 `~/.yingdao/config.json` 误判为项目配置
- [x] dry-run 预览 headers 恒存在，meta 补齐 `api_code/api_success/request_id`
- [x] `robot info --uuid` 的 `requested` 与名称模式同形
- [x] 既有 `account list` / `app list` / `app runs` / `robot tasks` / `job query` 未回归

## 4. 交付物检查

- [x] `pyproject.toml`、`__init__.py`、`SKILL.md`、`USAGE.md` 版本均为 `0.1.2`
- [x] `references/robot-scheduling.md` 已随 SKILL 资源索引提供
- [x] 发布包使用 `tools/package_skill.py` 白名单构建
- [x] `git status` 干净；`.env` 与 `.yingdao/` 未入库

## 5. 验收结论

- 结论：通过
- 遗留问题：无
- 验收人 / 日期：用户（发布指令确认）/ 2026-11-14

## 6. 发布（可选）

- 是否发布：立即发布
- 版本号：v0.1.2
- 说明：GitHub Release + `yingdao-rpa-toolkit-v0.1.2.zip`；基于 `v0.1.2` tag 白名单构建。
