import asyncio
import json
import logging

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from app.models import ReviewFindings, Finding
load_dotenv()
api_key=os.getenv("DEEPSEEK_API_KEY")
logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
)
llm_no_thinking=ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
    extra_body={"thinking":{"type":"disabled"}}
)
async  def review_with_json_mode(prompt:str) ->list[Finding]:
    for attempt in range(3):
        try:
            result=await llm.with_structured_output(ReviewFindings,method="json_mode").ainvoke(prompt)
            return result.findings
        except Exception as e:
            logger.warning("json_mode 结构化输出失败（第 %d 次尝试）", attempt + 1, exc_info=True)
            if attempt<2:
                await asyncio.sleep(2 ** attempt)
    return []
   
async def synthesize(findings: list[Finding]) -> str:
    data = [f.model_dump() for f in findings]
    prompt = (
        "你是一名代码审核主审，下面是 4 位专家对代码的审查结果（JSON），"
        "请提炼最关键的 2~3 个问题，并给出整体评价和优先修复建议：\n"
        + json.dumps(data, ensure_ascii=False)
    )
    result = await llm.ainvoke(prompt)
    return result.content