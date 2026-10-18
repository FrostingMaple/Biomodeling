# 合作贡献指南

## 适用范围

本项目是团队合作项目，所有成员都应通过规范的 GitHub 协作流程提交改动。本文以默认分支 `main` 为例；如果仓库的主分支名为 `master`，请按实际情况替换。

> [!IMPORTANT]
> 上传、提交或合并代码时，必须使用本人的 GitHub 账号，以项目合作贡献者身份进行。禁止冒用他人身份、借用他人的 GitHub 凭据，或绕过团队审查直接修改主分支。

## 核心原则

1. **保护主分支**：不得直接向 `main` / `master` 推送，所有改动通过 Pull Request（PR）申请合并。
2. **保护他人成果**：不得未经沟通覆盖、回退、删除他人的提交或文件。
3. **小步提交**：一个分支只解决一个明确问题，避免把无关改动混在同一次提交中。
4. **先审查再合并**：PR 应说明改动范围、测试结果和潜在影响，并按项目设置完成审查与自动检查。
5. **出现冲突先沟通**：解决冲突时确认双方改动意图，不能为了“消除冲突”而简单丢弃他人的代码。
6. **测试文献只保留在本地**：`data/` 中的论文和测试材料不得提交；该目录仅保留 `README.md`。

## 1. 配置本人身份

首次克隆仓库后，在仓库目录内配置与本人 GitHub 账号关联的姓名和邮箱：

```powershell
git config --local user.name "<你的 GitHub 显示名>"
git config --local user.email "<与 GitHub 账号关联的邮箱>"
```

检查配置：

```powershell
git config user.name
git config user.email
```

不要把自己的令牌、密码或 SSH 私钥提交到仓库，也不要使用其他成员的身份或凭据进行操作。

## 2. 创建独立分支

先同步主分支，再从最新主分支创建工作分支：

```powershell
git clone https://github.com/<owner>/<repo>.git
cd <repo>
git switch main
git pull --ff-only origin main
git switch -c <type>/<github-username>/<short-topic>
```

推荐的分支类型：

| 类型 | 用途 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat/alice/pdf-parser` |
| `fix` | 缺陷修复 | `fix/bob/solver-boundary` |
| `docs` | 文档改动 | `docs/chen/contributing-guide` |
| `refactor` | 不改变行为的重构 | `refactor/dana/model-ir` |
| `test` | 测试补充 | `test/erin/ode-regression` |

分支名应使用简短的英文或拼音，避免空格和含糊名称。

## 3. 开发与验证

提交前至少完成以下检查：

```powershell
git status
git diff
git diff --check
```

运行项目测试；如果本次改动涉及数值引擎、CLI 或模型 IR，还应运行对应的演示或集成流程：

```powershell
.\bootstrap.ps1 -CheckOnly
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\run.ps1 --demo
```

命令是否适用以本次改动范围和团队要求为准。不要在测试失败或存在未处理冲突时提交 PR。

## 4. 提交改动

只暂存与本次任务相关的文件，并检查暂存内容：

```powershell
git add <本次改动的文件>
git diff --cached
git commit -m "<type>: <简要说明>"
```

提交信息应能说明改了什么以及为什么改，例如：

```text
feat: add two-column PDF text extraction
fix: validate missing PDE boundary conditions
docs: document collaborative GitHub workflow
```

不要提交 API Key、`.env`、虚拟环境、缓存、`data/` 中的测试文献、个人临时文件或未经确认的大型二进制文件。

## 5. 推送分支并申请合并

将工作分支推送到本人可访问的远程仓库：

```powershell
git push -u origin <type>/<github-username>/<short-topic>
```

随后在 GitHub 上创建 Pull Request，目标分支为 `main` / `master`。PR 描述至少包含：

- 本次改动解决的问题和范围；
- 主要修改的文件或模块；
- 已执行的测试及结果；
- 可能影响其他成员工作的风险；
- 关联 Issue（如有）；
- 需要 Reviewer 重点关注的内容。

创建 PR 后，请求至少一名团队成员审查，并等待必要的自动检查通过。不要在没有审查或检查未通过时自行绕过保护规则合并。

## 6. 审查与合并

作为 Reviewer，应重点检查：

- 改动是否与 PR 描述一致；
- 是否破坏了已有接口、数据格式或测试；
- 是否误改、覆盖或删除了他人的工作；
- 是否引入敏感信息、无关文件或不可维护的实现。

合并方式（Merge commit、Squash merge 或 Rebase merge）以仓库设置为准。合并前确认分支已同步最新主分支、冲突已解决、测试已通过。合并后如需删除工作分支，应确认对应 PR 已合并且分支不再需要。

## 7. 处理冲突与保护共享历史

同步主分支并处理冲突：

```powershell
git fetch origin
git merge origin/main
git status
```

逐个检查冲突文件，保留双方有意的改动；解决后执行：

```powershell
git add <已解决冲突的文件>
git commit
git push
```

处理冲突时禁止：

- 直接使用 `git reset --hard`、`git checkout -- .` 等命令清理共享工作区；
- 对 `main` / `master` 或他人正在使用的分支执行强制推送；
- 未经沟通回退、覆盖或删除他人的提交；
- 只保留自己的版本，或把无法理解的冲突直接标记为已解决。

如果必须调整已被他人审查的分支历史，应先与相关成员沟通，并遵循仓库的保护规则。默认优先使用普通提交和合并，不要改写共享历史。

## 8. 大型改动与跨模块协作

以下改动建议先创建 Issue 或在团队沟通渠道中说明方案，再开始编码：

- 修改 Model IR、数据库或配置格式；
- 调整公共接口、CLI 参数或依赖版本；
- 重构多个模块；
- 修改其他成员正在开发的文件；
- 引入较大体积的数据、模型或二进制资源。

先说明范围和计划，可以减少重复劳动与合并冲突。发现他人的工作可能受影响时，应在 PR 中明确标注并邀请相关人员审查。

## 9. 合并前检查清单

- [ ] 已从最新主分支创建并同步工作分支；
- [ ] 使用本人 GitHub 身份提交；
- [ ] 只包含本次任务相关改动；
- [ ] 未提交密钥、虚拟环境、缓存或临时文件；
- [ ] 已运行相关测试并记录结果；
- [ ] PR 描述完整，关联 Issue（如有）；
- [ ] 已完成团队审查，自动检查通过；
- [ ] 冲突已与相关成员确认并正确解决；
- [ ] 未覆盖、回退或删除他人的有效工作。

如有疑问，先与项目负责人或相关模块维护者沟通，不要通过强制推送或直接修改主分支解决。
