import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app.vector import search_similar_code
from app.ingest import parse_diff, reconstruct_file

with open("sample2.diff", encoding="utf-8") as f:
    files = parse_diff(f.read())

for fd in files:
    code = reconstruct_file(fd)
    print("=" * 50)
    print("查询文件:", fd.file)
    print("=" * 50)
    result = search_similar_code(code)
    if result:
        print(result[:800])
    else:
        print("(没命中任何历史)")
    print()
