import uuid

from fastapi import FastAPI
from app.db import save_review,list_reviews,list_findings
from app.agents.reviewer import review_code
from app.models import ReviewResult, ReviewRequest, dedup_findings, DiffRequest, Finding, Severity, AgentType
from app.graph import compiled_graph
from app.ingest import parse_diff,reconstruct_file
from app.service import review_input
from app.vector import search_similar_code, write_review


app = FastAPI()

# @app.post("/review")
# def review(req:ReviewRequest)->ReviewResult:
#     findings=review_code(req.code)
#     return ReviewResult(
#         diff_summary="",
#         findings=findings,
#         status="success"
#     )

@app.post("/review-diff")
async def review_diff(req:DiffRequest)->ReviewResult:
    # 把 git diff 文本解析成一个个文件差异（每个 FileDiff 含文件名 + 若干 hunk）
    findings, code_map = await review_input(req.diff_text)
    
    
    # 打包统一响应：diff_summary 这里留空（/review-diff 不做整体总结），findings 去重
    result=ReviewResult(
        diff_summary="",
        findings=findings,
        status="success",
    )
    # 持久化：先存关系库拿 review_id，再把代码与发现写入向量库供后续检索复用
    review_id=save_review(result)
    write_review(result,review_id, code_map)
    return result
            





@app.post("/graph")#graph接口：直接审一段完整代码（非 diff），请求体按 ReviewRequest 模型自动解析校验
async def view(req:ReviewRequest)->ReviewResult:
    # 检索历史相似代码及其问题，作为审查参考上下文
    context = search_similar_code(req.code)
    # 把代码和上下文送入 LangGraph 图，返回 findings（各维度发现）和 summary（主审总结）
    results = await compiled_graph.ainvoke({"code":req.code, "context": context},config={"configurable":{"thread_id":uuid.uuid4().hex}})
    findings = results["findings"]
    summary = results["summary"]
  
    # 构造 code_map：文件名（没传则用 "unknown" 兜底）-> 代码，供写向量库用
    code_map={}
    code_map[req.file_name or "unknown"]=req.code
    # 如果请求带了文件名，就把每条 finding 的 file 字段补上
    for f in findings:
        f.file = req.file_name or "unknown"
    # 对发现做去重（同文件同行同维度只保留最严重的一条）
    de_dup_findings=dedup_findings(findings)
   
    # 打包成统一响应格式返回给客户端；这里 diff_summary 用图里的总结
    result= ReviewResult(
        diff_summary=summary,
        findings=de_dup_findings,
        status="success",
       
    )
    # 持久化：存关系库 + 写向量库
    review_id=save_review(result)
    write_review(result,review_id, code_map)
    return result

@app.get("/reviews")
def get_reviews()->list[ReviewResult]:
    # 查询历史所有审核记录（含关联的 findings），再转回 API 的 Pydantic 模型返回
    results=[]
    for r in list_reviews():
        results.append(ReviewResult(
            diff_summary=r.diff_summary,
            status=r.status,
            # 数据库里存的是字符串，这里把 severity / agent_type 还原成对应的枚举
            findings=[Finding(
                severity=Severity(f.severity),
                file=f.file,
                line=f.line,
                message=f.message,
                suggestion=f.suggestion,
                agent_type=AgentType(f.agent_type),
            ) for f in r.findings]
        ))
    return results
