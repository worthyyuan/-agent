# 代码审核平台（Code Review Agent）

输入一段代码变更（git diff / PR），多个专业 Agent 并行审查（逻辑、安全、性能、风格），汇总成结构化审查报告。

## 技术栈

Python · LangGraph · FastAPI · Pydantic · PostgreSQL · Langfuse · Redis · Docker

## 目录结构

    app/                主包（所有代码）
    ├── main.py         FastAPI 入口
    ├── ingest.py       Ingest 层：解析 git diff
    ├── models.py       Pydantic schema
    └── agents/         各 Agent（Week 2 起扩展多专家）
        └── reviewer.py 单 Agent 审查（Day 4）
    sample_code.py      测试用待审代码
    tests/              测试
    .env                密钥（不进 git）

## 运行方式

```powershell
# 先 cd 到项目根目录，然后：

# 单 Agent 审查（Day 4）
python -m app.agents.reviewer

# FastAPI 服务
uvicorn app.main:app --reload

# Ingest 层自测
python -m app.ingest
```

## 路线图

- [x] Day 0：FastAPI Hello World + Pydantic 热身
- [x] Day 1：项目初始化（pyproject / README / 目录）
- [x] Day 2：Ingest 层 —— 解析 git diff
- [x] Day 3：核心 schema（Finding / ReviewResult / 枚举）
- [x] Day 4：单 Agent 跑通（LLM 结构化输出）
- [ ] Day 5：FastAPI 骨架 POST /review
- Week 2-4：LangGraph 编排 · 并行 · 路由 · 容错
- Week 5-8：可观测性（Langfuse）
- Week 9-12：性能（缓存 · 路由 · 并发）
- Week 13-16：安全与部署
