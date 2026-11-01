import operator
from typing import TypedDict,Annotated

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,START,END
from app.agents.base import synthesize
from app.models import Finding
from app.agents.experts import review_logic,review_security,review_performance,review_style
import re
class ReviewState(TypedDict):
    summary:str
    code:str
    context:str
    findings:Annotated[list[Finding],operator.add]
    #langgraph会自动合并多个节点的输出，使用operator.add运算符将多个节点的输出合并为一个列表。
def route(state:ReviewState):#指路函数
    code_lower = state["code"].lower()
    experts=["logic_agent","style_agent"]
    sec_words  = ["sql", "eval", "token", "secret", "password", "pickle", "execute"]   # 纯单词，会误伤
    sec_substr = ["subprocess", "os.system", "request.form"]                             # 带符号/够长，子串安全
    perf_words = ["for", "while"]
    perf_substr = [".all()", "range(", "+="]

    if any(re.search(rf"\b{w}\b", code_lower) for w in sec_words) or any(s in code_lower for s in sec_substr):
        experts.append("security_agent")
    if any(re.search(rf"\b{w}\b", code_lower) for w in perf_words) or any(s in code_lower for s in perf_substr):
        experts.append("performance_agent")
    return experts


async def logic_agent(state:ReviewState):
    return {"findings":await review_logic(state["code"],state.get("context",
  ""))}
    #节点函数返回的字典里面只放想更新的字段

async def security_agent(state:ReviewState):
    return {"findings":await review_security(state["code"],state.get("context",
  ""))}

async def performance_agent(state:ReviewState):
    return {"findings":await review_performance(state["code"],state.get("context",
  ""))}

async def style_agent(state:ReviewState):
    return {"findings":await review_style(state["code"],state.get("context",
  ""))}
async def synthesize_node(state:ReviewState):
    return {"summary":await synthesize(state["findings"])}
graph=StateGraph(ReviewState)
graph.add_node("logic_agent",logic_agent)
graph.add_node("security_agent",security_agent)
graph.add_node("performance_agent",performance_agent)
graph.add_node("style_agent",style_agent)
graph.add_node("synthesize",synthesize_node)


graph.add_conditional_edges(START,route)
parallel_node={"logic_agent":logic_agent,"security_agent":security_agent,
               "performance_agent":performance_agent,"style_agent":style_agent}
for i in parallel_node:
   
    graph.add_edge(i, "synthesize")
graph.add_edge("synthesize", END)


checkpointer=MemorySaver()
compiled_graph=graph.compile(checkpointer=checkpointer)
if __name__=="__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with open("sample_code.py", encoding="utf-8") as f:
        code = f.read()
    result = compiled_graph.invoke({"code": code})
    for finding in result["findings"]:
        print(finding.model_dump())

    