import uuid

from app.models import dedup_findings
from app.ingest import normalize_input
from app.vector import search_similar_code
from app.graph import compiled_graph



async def review_input(src:str):
    files=normalize_input(src)
    all_findings=[]
    code_map={}
    for file_name,code in files:
        code_map[file_name]=code
        context=search_similar_code(code)
        out = await compiled_graph.ainvoke(
            {"code": code, "context": context},
            config={"configurable": {"thread_id": uuid.uuid4().hex}},
        )
        for f in out["findings"]:
            f.file=file_name
        all_findings.extend(out["findings"])
    return dedup_findings(all_findings),code_map