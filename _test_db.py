from app.db import save_review, list_reviews, list_findings
from app.models import ReviewResult, Finding, Severity, AgentType

result = ReviewResult(
    diff_summary="测试总结",
    findings=[
        Finding(severity=Severity.critical, file="app.py", line=10, message="SQL 注入", suggestion="参数化", agent_type=AgentType.security),
        Finding(severity=Severity.high, file="app.py", line=5, message="硬编码密钥", suggestion="环境变量", agent_type=AgentType.security),
    ],
    status="success",
)

rid = save_review(result)
print("saved review id =", rid)

print("--- list_reviews ---")
for r in list_reviews():
    print("review", r.id, r.status, r.created_at)
    for f in r.findings:
        print("  finding:", f.severity, f.message)
