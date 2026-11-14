# 发布记录 · 影刀RPA工具包

> 用途：为每个对外发布的版本留存可追溯记录（阶段五「发布子流程（可选）」的产出物）。
> 归档位置：`docs/release-record.md`；每个版本追加一节。

## v0.1.2 · 2026-11-14

### 1. 版本号

- 版本号：v0.1.2
- 发布方式：立即发布（GitHub 远端）
- 远端仓库：`git@github.com:cxk-lc/yingdao-rpa-toolkit.git`（public）
- GitHub Release：https://github.com/cxk-lc/yingdao-rpa-toolkit/releases/tag/v0.1.2
- Release 资产：`yingdao-rpa-toolkit-v0.1.2.zip`（76,943 字节）
- 资产 SHA256：`c7a2ad1870ea4f76161f8b35d6832c4b803b0f52c0fe8ea89f2d5f5a269645b4`
- 验收代码 commit：`9692881`（调度规则与默认自动选择）
- tag 指向 commit：`c162a70`（v0.1.2 发布提交；本记录为发布后补记，仅追加资产信息）
- 是否已推送远端：是（`main` 与 `v0.1.2`）

### 2. 变更摘要

- 新增机器人调度规则：指定机器人优先；忙碌时返回 `dispatch_decision`（排队/空闲候选），不自动排队或改派。
- `job start` 未指定账号/分组时默认自动选择空闲机器人；多个空闲按该应用历史成功次数最多，否则随机。
- 新增 `--auto-robot`（显式强制自动）与 `--queue-if-busy`（确认排队）。
- 修复 dry-run 预览：`config init --dry-run` 不写盘；text 模式优先渲染预览；headers/meta 契约补齐；`robot info --uuid` 的 `requested` 形状统一。
- 修复配置向上查找把 `~/.yingdao/config.json` 误判为项目配置的问题。
- 文档补充调度规则、安装态路径与输出契约；测试增至 221 项。

### 3. 验证证据

- 测试：`python -m pytest -q` → **221 passed**（2026-11-14）。
- 人工验收：`docs/acceptance-checklist-v0.1.2.md` 结论「通过」，验收人「用户（发布指令确认）」，日期 2026-11-14。
- 真实接口只读抽样：
  - 机器人列表 16 台，其中空闲 1 台。
  - 指定忙碌机器人返回 `specified_robot_busy`，空闲候选 1 台。
  - 自动模式选择唯一空闲机器人，`reason=auto_only_idle`。
  - 未实际调用 `job start`，避免产生真实运行。
- 远端校验：`git ls-remote origin` 可见 `refs/heads/main` 与 `refs/tags/v0.1.2`。
- Release 资产校验：从 GitHub Release 重新下载 `yingdao-rpa-toolkit-v0.1.2.zip`，SHA256 与本地白名单构建一致；压缩包内无 `tests/`、`docs/`、`AGENTS.md`、`README.md`、`USAGE.md`、`pyproject.toml` 与厂商接口文档。
- 护栏检查：`check_project` 8/8。

### 4. 已知问题

- 自动化测试全部离线；真实 `job start` / `job query` 的失败终态未纳入 AI 自测，依赖人工验收覆盖。
- 远端仓库当前为 **public**；如需私有，需在 GitHub 仓库设置中调整可见性。
- `job start --account-name` 仍按传入值使用，不参与机器人名称的 `loginAccount` 自动补全。
- 调度历史成功次数最多统计最近 5 页 × 100 条；查询失败时降级为随机空闲并返回 warning。
- Skill 发布包仅含运行文件，`README/USAGE/docs/tests` 等仓库文档不在包内。

### 5. 回滚指令

```bash
# 回退到上一个稳定版本
git checkout v0.1.1

# 撤销 v0.1.2 远端 tag（仅在需要撤回发布时）
git push origin :refs/tags/v0.1.2

# 撤销本地 tag
git tag -d v0.1.2
```

## v0.1.1 · 2026-11-09

### 1. 版本号

- 版本号：v0.1.1
- 发布方式：立即发布（GitHub 远端）
- 远端仓库：`git@github.com:cxk-lc/yingdao-rpa-toolkit.git`（public）
- GitHub Release：https://github.com/cxk-lc/yingdao-rpa-toolkit/releases/tag/v0.1.1
- Release 资产：`yingdao-rpa-toolkit-v0.1.1.zip`（66,067 字节）
- 资产 SHA256：`0904fbd80d85b18179a581b01cdc317211b85636aed28ca9cfe19918c4938191`
- Skill 包内容：`SKILL.md`、`scripts/`、`references/`、`config.example.json`、`.env.example`、`requirements.txt`、`LICENSE`；不含仓库级 `README/USAGE/docs/tests/AGENTS` 与厂商接口文档。
- 验收代码 commit：`cacc9c1`（新增应用/任务查询与文档）
- tag 指向 commit：`e0d9f29`（v0.1.1 发布提交；本记录为发布后补记，仅追加资产信息）
- 是否已推送远端：是（`main` 与 `v0.1.1`）

### 2. 变更摘要

- 新增 `app list`（3.2）：按 appId/名称/所有者筛选应用，支持页码翻页。
- 新增 `app runs`（3.3）：按应用或时间查运行记录，`minId` 游标分页；本地限制 7 天跨度。
- 新增 `robot tasks`（4.1）：按应用/机器人/计划/状态/触发时间查任务队列与历史 job，`next/pre` 游标翻页。
- README 增加「已直接支持的接口工具」表与「其他接口的临时调用」说明。
- 接口文档顶部补充官方文档链接 https://www.yingdao.com/yddoc/rpa/zh-CN/971279704374095872 。
- 版本号统一升级为 `0.1.1`；测试增至 187 项。

### 3. 验证证据

- 测试：`python -m pytest -q` → **187 passed**（2026-11-09）。
- 人工验收：`docs/acceptance-checklist-v0.1.1.md` 结论「通过」，验收人「用户（发布指令确认）」，日期 2026-11-09。
- 真实接口抽样：
  - `app list --size 1`：成功，`page.total=1012`。
  - `app runs` 7 天范围、`size=2`、`max-pages=3`：3 页、6 条唯一记录，游标正常推进。
  - `robot tasks` `size=2`、`max-pages=3`：3 页、6 条，状态中文映射正常。
- 远端校验：`git ls-remote origin` 可见 `refs/heads/main` 与 `refs/tags/v0.1.1`。
- Release 资产校验：从 GitHub Release 重新下载 `yingdao-rpa-toolkit-v0.1.1.zip`，SHA256 与本地白名单构建一致；压缩包内无 `tests/`、`docs/`、`AGENTS.md`、`README.md`、`USAGE.md`、`pyproject.toml` 与厂商接口文档。

### 4. 已知问题

- 自动化测试全部离线；真实 `job start` / `job query` 的失败终态未纳入 AI 自测，依赖人工验收覆盖。
- 远端仓库当前为 **public**；如需私有，需在 GitHub 仓库设置中调整可见性。
- `job start --account-name` 仍按传入值使用，不参与机器人名称的 `loginAccount` 自动补全。
- `app runs` 单次时间跨度受接口限制为 7 天，超出时由 CLI 本地拦截。

### 5. 回滚指令

```bash
# 回退到上一个稳定版本
git checkout v0.1.0

# 撤销 v0.1.1 远端 tag（仅在需要撤回发布时）
git push origin :refs/tags/v0.1.1

# 撤销本地 tag
git tag -d v0.1.1
```

## v0.1.0 · 2026-11-06

### 1. 版本号

- 版本号：v0.1.0
- 发布方式：立即发布（GitHub 远端）
- 远端仓库：`git@github.com:cxk-lc/yingdao-rpa-toolkit.git`（public）
- GitHub Release：https://github.com/cxk-lc/yingdao-rpa-toolkit/releases/tag/v0.1.0
- Release 资产：`yingdao-rpa-toolkit-v0.1.0.zip`（112,840 字节）
- 资产 SHA256：`86d493f280255a6c0ca4e5088eb0b229f5efc67a888f0c6d88c021933ecd7eea`
- 验收代码 commit：`37b066d42abe40b4414b28753632ab34fc6f761b`
- tag 指向 commit：`v0.1.0` 指向本发布记录所在 commit；首次推送前由 `d2a1f2a` 重建，代码树相对验收 commit 仅新增 `LICENSE`、验收签署与发布记录
- 是否已推送远端：是（`main` 与 `v0.1.0`）

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
- 远端校验：`git ls-remote origin` 可见 `refs/heads/main` 与 `refs/tags/v0.1.0`。
- Release 资产校验：从 GitHub Release 重新下载 `yingdao-rpa-toolkit-v0.1.0.zip`，SHA256 与本地构建一致。
- 真实接口抽样：
  - `auth token` 获取 token 成功，无缓存文件生成。
  - `account list --all --size 10` 拉取 3 页并聚合 27 条，`fetchedPages=3`。
  - `robot info` 用真实机器人名称前缀验证：请求链路为 `account list → client/query`，`resolvedBy=account`，状态 `running`。

### 4. 已知问题

- 自动化测试全部离线；真实 `job start` / `job query` 的失败终态未纳入 AI 自测，依赖人工验收覆盖。
- 远端仓库当前为 **public**；如需私有，需在 GitHub 仓库设置中调整可见性。
- `job start --account-name` 仍按传入值使用，不参与机器人名称的 `loginAccount` 自动补全。

### 5. 回滚指令

```bash
# 回退到验收代码基线
git checkout 37b066d

# 撤销远端 tag（仅在需要撤回发布时）
git push origin :refs/tags/v0.1.0

# 撤销本地 tag
git tag -d v0.1.0
```
