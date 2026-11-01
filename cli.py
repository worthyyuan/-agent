import argparse
import asyncio
import sys


from app.graph import compiled_graph
from app.ingest import parse_diff, reconstruct_file
from app.models import dedup_findings
from app.vector import search_similar_code
from app.service import review_input



async def main():
    # 解析命令行参数
    parser=argparse.ArgumentParser(description="代码审核CLI:审 git diff 文件")
    # 添加命令行参数,日安家文件路径不需要再写死
    parser.add_argument("file",help="diff文件路径，如sample.diff")
    #获取到文件路径
    args=parser.parse_args()

    
    # 调用异步函数，获取审核结果，负责启动事件循环并同步等待它跑完
    findings,_=await review_input(args.file)
    # 打印审核结果
    sys.stdout.reconfigure(encoding="utf-8",errors="replace")
    severity_order= {"critical": 0, "high": 1,
        "medium": 2, "low": 3, "info": 4}
    # 按严重程度排序
    findings.sort(key=lambda f:severity_order.get(f.severity.value,9))
    print(f"共 {len(findings)} 条问题")
    for f in findings:
        print(f"[{f.agent_type.value}]{f.severity.value.upper()}  {f.file}:{f.line}")
        print(f"  问题：{f.message}")
        print(f"  建议：{f.suggestion}")
        print()

if __name__=="__main__":
    asyncio.run(main())