"""测试客户端：python client.py [文件名]，默认审 sample.diff"""
import json
import sys
import urllib.error
import urllib.request

# 审核接口地址：默认走 /review-diff（审 git diff 文本）
# URL = "http://127.0.0.1:8000/graph"
URL = "http://127.0.0.1:8000/review-diff"
# 严重程度排序权重：数字越小越严重，用于对结果按严重度排序
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}#严重程度


# def review(code_file: str) -> dict:
#     code = open(code_file, encoding="utf-8").read()
#     payload = json.dumps({"code": code, "file_name": code_file}).encode("utf-8")
#     req = urllib.request.Request(
#         URL, data=payload, headers={"Content-Type": "application/json"}
#     )#构造一个HTTP请求指令，声明请求体是JSON格式
#     #发送请求并处理响应
#     try:
#         with urllib.request.urlopen(req) as resp:
#             return json.loads(resp.read().decode("utf-8"))
#     except urllib.error.HTTPError as e:
#         print(f"服务器返回 {e.code}，去 uvicorn 窗口看红色报错")
#         sys.exit(1)

def review_diff(diff_file: str) -> dict:
    # 读取本地的 git diff 文件内容
    diff_text=open(diff_file,encoding="utf-8").read()
    # 构造 JSON 请求体：字段名 diff_text 对应服务端 DiffRequest 模型
    payload=json.dumps({"diff_text":diff_text}).encode("utf-8")
    # 构造 HTTP 请求，声明请求体是 JSON 格式
    req=urllib.request.Request(
        URL,data=payload,headers={"Content-Type":"application/json"}
    )
    # 发送请求并解析响应
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 服务端报错（如 500）时给出提示，让用户去 uvicorn 窗口看堆栈
        print(f"服务器返回 {e.code}，去 uvicorn 窗口看红色报错")
        sys.exit(1)

if __name__ == "__main__":
    # 第一个命令行参数是 diff 文件名，不传则默认 sample.diff
    file_name = sys.argv[1] if len(sys.argv) > 1 else "sample.diff"
    result = review_diff(file_name)
    findings = result["findings"]
    # 按严重程度从小到大排序（critical 排最前）
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 9))

    print("=" * 60)
    print("【审查总结】")
    print(result.get("diff_summary", ""))
    print("=" * 60)
    print(f"共 {len(findings)} 条问题")
    print("=" * 60)
    # 逐条打印发现：维度、严重程度、位置、问题描述、修复建议
    for f in findings:
        print(f"[{f['agent_type']}] {f['severity'].upper()}  {f['file']}:{f['line']}")
        print(f"  问题：{f['message']}")
        print(f"  建议：{f['suggestion']}")
        print()
