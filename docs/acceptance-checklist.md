# 人工验收清单 · 影刀RPA工具包

> 原则：AI 自测通过 ≠ 无 Bug；验收单只能由人签。
> 本清单对应 v0.1「基础框架 + 机器人状态 + 触发/查询闭环」。
> 验收记录：2026-11-06 由用户在对话中确认验收完成；以下条目按该确认勾选，AI 自测证据为 146 passed。

## 1. 冒烟测试（能不能跑）

- [x] `python scripts/yd.py --version` 输出 `yingdao-rpa-toolkit 0.1.0`，退出码 0
- [x] `python scripts/yd.py --help` 能看到 `account / auth / config / job / robot` 五个命令
- [x] `python -m pytest -q` 全绿（当前 AI 自测：146 passed）
- [x] `python scripts/yd.py config show` 输出合法 JSON，`ok=true`

## 2. 主流程走查（好不好用）

- [x] `config init` 能生成 `.yingdao/config.json`；填入真实密钥后 `config show` 能看到 `source` 与 `config_path`
- [x] `auth check` 能成功换到 token，显示 `expires_in` 与脱敏 token，`source=fetched`
- [x] `auth token` 输出完整 token，`data.persisted=false`，且磁盘上没有新增 token 缓存文件
- [x] `auth token --save token.json` 退出码 2，且文件未生成
- [x] `auth check --dry-run` 默认掩码：`accessKeySecret=***`、`accessKeyId` 只露首尾各 4 位；加 `--show-secrets` 才输出原文
- [x] `TOKEN=$(... auth token --format text)` 得到纯 token 原文；用 `--access-token "$TOKEN"` 调用 `job query` 时不再请求 token 接口
- [x] `job start --app-id ... --account-name ... --param 月份=2026-10 --dry-run` 的预览 body 与预期一致，且未发出真实请求
- [x] `robot info --name <前缀>` 会先请求 `account list`；命中时 `resolvedBy=account`，`accountName` 等于该账号的 `loginAccount`
- [x] 企业账号无匹配时回退 `enterpriseSuffix`，`requested.fallback=no-account-match`
- [x] 传入完整名称 `ceshi1@xxx` 时原样使用，不触发账号查询；`--suffix` 可跳过查询直接补全
- [x] `robot info --name <前缀> --dry-run` 在无 `@`、无 `--suffix` 时返回两段式预览（账号查询 + `<loginAccount>` 占位）
- [x] `robot info` 能显示 `status`、`statusName`、`online`、`idle`、IP 与备注
- [x] `account list` 能按关键词/手机号/账号类型/时间范围筛选，`data.page.total` 与 `data.count` 符合预期
- [x] `account list --all --size 10` 能自动翻页并聚合全部账号；`requested.fetchedPages` 与总页数一致
- [x] 去掉 `--dry-run` 后能拿到 `jobUuid`，控制台能看到对应运行记录
- [x] `job query --job-uuid ... --wait` 能轮询到终态；成功任务退出码 0
- [x] `--format text` 的人读输出对 `config show / auth check / robot info / account list / job query` 都可读

## 3. 边界与异常（稳不稳）

- [x] 未配置凭据时 `auth check` 退出码 2，stdout 仍是合法 JSON，并给出配置指引
- [x] 配置里仍是 `<在此填写 ...>` 占位符时，报错明确指出是占位符（退出码 2）
- [x] `job start` 同时给 `--account-name` 与 `--robot-group-uuid`，退出码 2
- [x] `job start` 两者都不给，退出码 2（本地拦截，不发请求）
- [x] `--param` 缺少 `=` 或参数名重复，退出码 2
- [x] 参数总长超过 8000 字符，退出码 2 并提示拆批 / `type=file`
- [x] `robot info --name no-such-robot-zzz`（企业账号无匹配且配置无 `enterpriseSuffix`）退出码 2，并提示补充名称/后缀
- [x] `robot info --name ceshi1@` 或 `--suffix` 与 `--uuid` 同时使用，退出码 2
- [x] 用不匹配的完整名称查询，返回“未查询到机器人”，hint 指向 `loginAccount` / `--uuid`
- [x] `account list --size 0` 或 `--size 101`、`--page 0` 退出码 2
- [x] `account list --account-type vip` 退出码 2；`--account-type basic,senior` 正常
- [x] 时间起点晚于终点退出码 2；`2026-01-01` 能转成秒级时间戳
- [x] `account list --all --max-pages 1` 只拉一页且返回 warning，不静默截断
- [x] 明显错误的 `accessKeySecret` 返回退出码 3，且输出里没有完整密钥
- [x] 传入一个过期/错误的 `--access-token`，退出码 3 且提示重新执行 `auth token`
- [x] 断网或错误域名时退出码 4，提示可重试
- [x] `job query` 查一个失败任务，退出码 5 且 `data.job` 带 `remark`
- [x] `--wait` 超过 `--max-wait` 仍未终态，退出码 4 且带最后状态

## 4. 交付物检查

- [x] 所有改动均有对应 Git commit（docs / 骨架 / 测试与技能文档）
- [x] 测试全部通过（含 Agent 提交的命令与结果证据）
- [x] `AGENTS.md` 的「项目信息」与实际命令一致
- [x] `SKILL.md` 只声明已实现能力，未实现项写在「当前版本边界」
- [x] `git status` 干净；`.yingdao/`、`.env` 未被提交

## 5. 验收结论

- 结论：通过
- 遗留问题：无
- 验收人 / 日期：用户（对话确认）/ 2026-11-06

## 6. 发布（可选）

> 验收签署完成后询问一次；选「跳过」直接结束，不产生任何发布产物，不影响闭环。
> 细则见技能包 stable-delivery-workflow 的「发布子流程（可选）」：S0–S5 与可选约束。

- 是否发布：立即发布
- 版本号（若发布）：v0.1.0
- 说明：已推送至 `git@github.com:cxk-lc/yingdao-rpa-toolkit.git`（public），包含 `main` 与 annotated tag `v0.1.0`；Release 资产 `yingdao-rpa-toolkit-v0.1.0.zip` 已上传。
