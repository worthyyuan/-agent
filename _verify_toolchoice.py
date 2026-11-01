import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(r"C:\Users\jiawe\代码审核agent\.env")
api_key = os.getenv("DEEPSEEK_API_KEY")


def make_llm(no_thinking=False):
    kwargs = dict(
        model="deepseek-v4-flash",
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    if no_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return ChatOpenAI(**kwargs)


# 本地 mock CWE 库（Phase 2 数据源的最小原型，跑通后再换真实库/团队规范）
VULN_DB = {
    "sql": "CWE-89 SQL 注入：拼接用户输入到 SQL，攻击者可篡改查询。修复：参数化查询 / ORM。",
    "密钥": "CWE-798 硬编码凭证：密钥写死在代码里。修复：环境变量 / 密钥管理服务。",
    "pickle": "CWE-502 不安全反序列化：untrusted 数据反序列化导致 RCE。修复：白名单 / 避免 pickle。",
}


@tool
def search_vuln(keyword: str) -> str:
    """根据关键词检索 CWE 漏洞库，返回漏洞 ID、描述和修复建议。"""
    for k, v in VULN_DB.items():
        if k in keyword:
            return v
    return f"未找到与「{keyword}」相关的 CWE 条目"


class LocalFinding(BaseModel):
    severity: str
    file: str | None = None
    line: int | None = None
    message: str
    suggestion: str
    agent_type: str


class LocalFindings(BaseModel):
    findings: list[LocalFinding]


async def test_tool_loop():
    """完整 function calling 循环：绑工具 → 拿 tool_calls → 执行 → 喂回 → 出结论"""
    llm = make_llm(no_thinking=True)
    llm_tools = llm.bind_tools([search_vuln])
    msgs = [HumanMessage("代码里有 user_input 直接拼进 SQL 查询，帮我查一下这是什么漏洞")]
    ai_resp = await llm_tools.ainvoke(msgs)
    print("=== [1] 第一轮：模型发起的 tool_calls ===")
    print("tool_calls:", ai_resp.tool_calls)
    msgs.append(ai_resp)
    for tc in ai_resp.tool_calls:
        result = search_vuln.invoke(tc["args"])
        print("工具执行结果:", result)
        msgs.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    final = await llm.ainvoke(msgs)
    print("=== [2] 第二轮：喂回工具结果后模型的最终回答 ===")
    print(final.content)


async def test_json_mode():
    llm = make_llm(no_thinking=True)
    prompt = (
        "你是一名代码审核专家，只输出 JSON，结构严格如下："
        '{"findings":[{"severity":"high","file":"a.py","line":1,'
        '"message":"x","suggestion":"y","agent_type":"security"}]}。'
        "代码：x = eval(user_input)"
    )
    resp = await llm.with_structured_output(LocalFindings, method="json_mode").ainvoke(prompt)
    print("=== [3] json_mode 回归 ===")
    print(resp.model_dump())


async def main():
    try:
        await test_tool_loop()
    except Exception as e:
        print("tool loop FAILED:", type(e).__name__, str(e)[:600])
    print()
    try:
        await test_json_mode()
    except Exception as e:
        print("json_mode FAILED:", type(e).__name__, str(e)[:500])


asyncio.run(main())
