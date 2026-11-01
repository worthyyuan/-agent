from app.agents.base import review_with_json_mode


def review_code(code: str):
    prompt = f"""你是一名资深代码审核专家，请审查下面的代码，找出其中的问题，覆盖四类：
- logic：逻辑错误、边界条件、潜在 bug
- security：SQL 注入、硬编码密钥、不安全反序列化等
- performance：N+1 查询、重复计算等
- style：命名、可读性

必须以 JSON 格式输出，结构严格如下（不要输出其他任何内容）：
{{"findings": [{{"severity": "critical|high|medium|low|info", "file": "文件名", "line": 行号或 null, "message": "问题描述", "suggestion": "修复建议", "agent_type": "logic|security|performance|style"}}]}}

代码：
{code}
"""
    return review_with_json_mode(prompt)


def review_file(file_name: str):
    with open(file_name, encoding="utf-8") as f:
        code = f.read()
    return review_code(code)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")#把输出标准强制转换为UTF-8
    for finding in review_file("sample_code.py"):
        print(finding.model_dump())#遍历返回的每一个Findings，并转换为字典后输出
