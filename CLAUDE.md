# rag-document-assistant

基于 PDF 知识库的 RAG 聊天机器人 demo（LangChain + OpenAI + Chroma + FastAPI + Streamlit + Docker），作为 Upwork 投标作品。

## 必读
- `docs/ROADMAP.md`：需求对照、全局约定（技术栈、目录结构、配置项、chunk 元数据结构、`/chat` 接口约定）、每个阶段的详细说明
- `docs/status.json`：每个阶段的状态、任务、验收标准、审查清单、工作日志，**是唯一的进度来源**
- `docs/progress/P*.md`：每个阶段 worker 和 reviewer 的详细记录

## 工作流
- 按 P0→P9 顺序推进，每个阶段一个分支 `feat/p{N}-{name}`
- `phase-worker` 负责实现，`phase-reviewer` 负责独立审查并合并；用 `/run-phase` 调度
- 状态流转：pending → in_progress → in_review → (changes_requested → in_progress → in_review)* → done；审查 3 轮仍未通过 → blocked

## 规则
- **所有提交进仓库的内容必须是英文**：代码注释、docstring、日志、报错信息、UI 文案、commit message、README、评测报告。只有本地流程文件（`docs/status.json`、`docs/progress/`）可以写中文
- 调度 subagent 时，每个 worker 和 reviewer 都是全新的独立实例：不用 fork、不续用旧 agent，只通过 status.json、progress 和 git 传递信息
- git 提交只署用户本人：不加 `Co-Authored-By: Claude` 或任何 AI 署名行，PR 描述里也不加 "Generated with Claude Code"
- 不提交 `.env` 或任何密钥；不 push 到远端，除非用户明确要求
- 单元测试里不真实调用 OpenAI；真实调用的测试标记 `@pytest.mark.integration`
- 修改 status.json 后必须保证它仍是合法 JSON（`python -m json.tool docs/status.json > /dev/null`）
