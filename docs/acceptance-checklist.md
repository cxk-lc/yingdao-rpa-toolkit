# 人工验收清单 · 影刀RPA工具包

> 原则：AI 自测通过 ≠ 无 Bug；验收单只能由人签。
> 本清单对应 v0.1「基础框架 + 机器人状态 + 触发/查询闭环」。

## 1. 冒烟测试（能不能跑）

- [ ] `python scripts/yd.py --version` 输出 `yingdao-rpa-toolkit 0.1.0`，退出码 0
- [ ] `python scripts/yd.py --help` 能看到 `account / auth / config / job / robot` 五个命令
- [ ] `python -m pytest -q` 全绿（当前 AI 自测：135 passed）
- [ ] `python scripts/yd.py config show` 输出合法 JSON，`ok=true`

## 2. 主流程走查（好不好用）

- [ ] `config init` 能生成 `.yingdao/config.json`；填入真实密钥后 `config show` 能看到 `source` 与 `config_path`
- [ ] `auth check` 能成功换到 token，显示 `expires_in` 与脱敏 token，`source=fetched`
- [ ] `auth token` 输出完整 token，`data.persisted=false`，且磁盘上没有新增 token 缓存文件
- [ ] `auth token --save token.json` 退出码 2，且文件未生成
- [ ] `auth check --dry-run` 默认掩码：`accessKeySecret=***`、`accessKeyId` 只露首尾各 4 位；加 `--show-secrets` 才输出原文
- [ ] `TOKEN=$(... auth token --format text)` 得到纯 token 原文；用 `--access-token "$TOKEN"` 调用 `job query` 时不再请求 token 接口
- [ ] `job start --app-id ... --account-name ... --param 月份=2026-10 --dry-run` 的预览 body 与预期一致，且未发出真实请求
- [ ] `robot info --name <前缀>` 能按 `enterpriseSuffix` 补全为 `<前缀>@<企业标识>`，`data.requested.suffixApplied=true`
- [ ] 传入完整名称 `ceshi1@xxx` 时原样使用，不被配置覆盖；`--suffix` 可临时覆盖配置
- [ ] `robot info` 能显示 `status`、`statusName`、`online`、`idle`、IP 与备注
- [ ] `account list` 能按关键词/手机号/账号类型/时间范围筛选，`data.page.total` 与 `data.count` 符合预期
- [ ] `account list --all --size 10` 能自动翻页并聚合全部账号；`requested.fetchedPages` 与总页数一致
- [ ] 去掉 `--dry-run` 后能拿到 `jobUuid`，控制台能看到对应运行记录
- [ ] `job query --job-uuid ... --wait` 能轮询到终态；成功任务退出码 0
- [ ] `--format text` 的人读输出对 `config show / auth check / robot info / account list / job query` 都可读

## 3. 边界与异常（稳不稳）

- [ ] 未配置凭据时 `auth check` 退出码 2，stdout 仍是合法 JSON，并给出配置指引
- [ ] 配置里仍是 `<在此填写 ...>` 占位符时，报错明确指出是占位符（退出码 2）
- [ ] `job start` 同时给 `--account-name` 与 `--robot-group-uuid`，退出码 2
- [ ] `job start` 两者都不给，退出码 2（本地拦截，不发请求）
- [ ] `--param` 缺少 `=` 或参数名重复，退出码 2
- [ ] 参数总长超过 8000 字符，退出码 2 并提示拆批 / `type=file`
- [ ] `robot info --name ceshi1` 且配置无 `enterpriseSuffix`、也没传 `--suffix`，退出码 2 并提示补充后缀
- [ ] `robot info --name ceshi1@` 或 `--suffix` 与 `--uuid` 同时使用，退出码 2
- [ ] 用不匹配的名称/后缀查询，返回“未查询到机器人”，hint 指向 `enterpriseSuffix` / `--suffix` / `--uuid`
- [ ] `account list --size 0` 或 `--size 101`、`--page 0` 退出码 2
- [ ] `account list --account-type vip` 退出码 2；`--account-type basic,senior` 正常
- [ ] 时间起点晚于终点退出码 2；`2026-01-01` 能转成秒级时间戳
- [ ] `account list --all --max-pages 1` 只拉一页且返回 warning，不静默截断
- [ ] 明显错误的 `accessKeySecret` 返回退出码 3，且输出里没有完整密钥
- [ ] 传入一个过期/错误的 `--access-token`，退出码 3 且提示重新执行 `auth token`
- [ ] 断网或错误域名时退出码 4，提示可重试
- [ ] `job query` 查一个失败任务，退出码 5 且 `data.job` 带 `remark`
- [ ] `--wait` 超过 `--max-wait` 仍未终态，退出码 4 且带最后状态

## 4. 交付物检查

- [ ] 所有改动均有对应 Git commit（docs / 骨架 / 测试与技能文档）
- [ ] 测试全部通过（含 Agent 提交的命令与结果证据）
- [ ] `AGENTS.md` 的「项目信息」与实际命令一致
- [ ] `SKILL.md` 只声明已实现能力，未实现项写在「当前版本边界」
- [ ] `git status` 干净；`.yingdao/`、`.env` 未被提交

## 5. 验收结论

- 结论：通过 / 有条件通过 / 不通过
- 遗留问题：
- 验收人 / 日期：

## 6. 发布（可选）

> 验收签署完成后询问一次；选「跳过」直接结束，不产生任何发布产物，不影响闭环。
> 细则见技能包 stable-delivery-workflow 的「发布子流程（可选）」：S0–S5 与可选约束。

- 是否发布：立即发布 / 仅本地留痕（打 tag 不推送）/ 跳过
- 版本号（若发布）：
- 说明：（跳过原因，或需随版本说明的已知问题；可留空）
