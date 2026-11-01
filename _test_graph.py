import asyncio
import sys

from app.graph import compiled_graph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    with open("sample_code.py", encoding="utf-8") as f:
        code = f.read()
    result = await compiled_graph.ainvoke({"code": code})
    print("=== summary ===")
    print(result["summary"][:400])
    print()
    print("=== findings count:", len(result["findings"]), "===")
    for f in result["findings"]:
        print(f"[{f.agent_type.value}] {f.severity.value} line={f.line} | {f.message[:50]}")


asyncio.run(main())
