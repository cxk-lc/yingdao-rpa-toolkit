# 人工验收清单 · v0.1.1（增量）

> 基线：`v0.1.0` 已签署，记录见 `docs/acceptance-checklist.md`。
> 范围：`app list`、`app runs`、`robot tasks`、README 接口清单与官方文档链接、版本号 `0.1.1`。
> 验收依据：用户 2026-11-09 发布 `v0.1.1` 的指令 + AI 自测与真实接口抽样证据。

## 1. 冒烟测试

- [x] `python scripts/yd.py --version` 输出 `yingdao-rpa-toolkit 0.1.1`，退出码 0
- [x] `python scripts/yd.py --help` 能看到 `app` 与 `robot tasks`
- [x] `python -m pytest -q` 全绿（当前 AI 自测：187 passed）
- [x] `config show`、`auth check` 等既有命令未回归

## 2. 新增功能

- [x] `app list` 可按 appId/名称/所有者筛选；`--all` 能按页码翻页
- [x] `app runs` 支持 appId、时间范围、`minId` 游标；`--all` 能去重聚合
- [x] `robot tasks` 支持应用/机器人/计划/状态/触发时间筛选；`--all` 能沿游标翻页
- [x] 三个命令的 `--format text` 可读，`--dry-run` 不发送请求

## 3. 边界与异常

- [x] `app runs` 未给 appId 且未给时间范围时退出码 2
- [x] `app runs` 只给时间时未同时给起止，退出码 2
- [x] `app runs` 时间跨度超过 7 天，退出码 2
- [x] `app list` / `app runs` / `robot tasks` 的 `size` 超过 100，退出码 2
- [x] `robot tasks --direction pre` 未给 `--cursor-id`，退出码 2
- [x] `robot tasks --status` 未知状态，退出码 2
- [x] 达到 `--max-pages` 时返回 `warnings`，不静默截断

## 4. 交付物检查

- [x] README 已列出 8 组直接支持的接口工具及对应文档章节
- [x] README 已说明未封装接口可临时调用，并附接口文档链接
- [x] 接口文档顶部已加入官方文档链接
- [x] `pyproject.toml`、`__init__.py`、`SKILL.md`、`USAGE.md` 版本均为 `0.1.1`
- [x] `git status` 干净；`.env` 与 `.yingdao/` 未入库

## 5. 验收结论

- 结论：通过
- 遗留问题：无
- 验收人 / 日期：用户（发布指令确认）/ 2026-11-09

## 6. 发布（可选）

- 是否发布：立即发布
- 版本号（若发布）：v0.1.1
- 说明：GitHub Release + `yingdao-rpa-toolkit-v0.1.1.zip`；基于 `v0.1.1` tag 构建，按 `.gitignore` 排除忽略文件。
