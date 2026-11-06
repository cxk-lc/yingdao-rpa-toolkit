# 发布记录 · 影刀RPA工具包

> 用途：为每个对外发布的版本留存可追溯记录（阶段五「发布子流程（可选）」的产出物）。
> 归档位置：`docs/release-record.md`；每个版本追加一节。

## v0.1.0 · 2026-11-06

### 1. 版本号

- 版本号：v0.1.0
- 发布方式：立即发布（本地 annotated tag；当前无远端，未推送）
- 验收代码 commit：`37b066d42abe40b4414b28753632ab34fc6f761b`
- tag 指向 commit：`v0.1.0` 指向本发布记录所在 commit；其代码树与验收代码 commit 一致，差异仅为 `docs/acceptance-checklist.md` 与 `docs/release-record.md`
- 是否已推送远端：否（未配置远端，保留「仅本地」标注）

### 2. 变更摘要

- 初始化 Skill + Python CLI 工具包：配置管理、鉴权、统一 JSON 输出、固定退出码、日志与错误体系。
- 鉴权：`auth check` / `auth token`；token 仅内存、不落盘，支持 `--access-token` / `YD_ACCESS_TOKEN` 跨命令传递。
- 企业账号：`account list`，支持关键词、手机号、账号类型、时间范围筛选与 `--all` 分页聚合。
- 机器人：`robot info`，名称缺 `@` 时先查企业账号取 `loginAccount`，再回退 `--suffix` / `enterpriseSuffix`。
- 应用运行：`job start`（dry-run、参数、优先级、幂等 uuid）与 `job query`（`--wait` 轮询终态）。
- 测试：146 项离线用例。

### 3. 验证证据

- 测试：`python -m pytest -q` → **146 passed**（2026-11-06）。
- 人工验收：`docs/acceptance-checklist.md` 结论「通过」，验收人「用户（对话确认）」，日期 2026-11-06。
- 真实接口抽样：
  - `auth token` 获取 token 成功，无缓存文件生成。
  - `account list --all --size 10` 拉取 3 页并聚合 27 条，`fetchedPages=3`。
  - `robot info` 用真实机器人名称前缀验证：请求链路为 `account list → client/query`，`resolvedBy=account`，状态 `running`。

### 4. 已知问题

- 自动化测试全部离线；真实 `job start` / `job query` 的失败终态未纳入 AI 自测，依赖人工验收覆盖。
- 当前未配置 git 远端，`v0.1.0` tag 未推送。
- `job start --account-name` 仍按传入值使用，不参与机器人名称的 `loginAccount` 自动补全。

### 5. 回滚指令

```bash
# 首个正式 tag 之前无更早稳定 tag；回退到验收代码基线
git checkout 37b066d

# 如需撤销本地 tag
git tag -d v0.1.0
```
