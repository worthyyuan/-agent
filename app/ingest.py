"""Day 2：Ingest 层 —— 把 git diff 文本解析成 list[FileDiff]"""
import os
SKIP_EXTS={".md",".txt",".rst",".pdf",".doc",".docx"}
SKIP_DIRS={"__pycache__", "node_modules", "venv", "env", "dist", "build"}
from app.models import FileDiff, DiffHunk
def parse_diff(diff_text: str) -> list[FileDiff]:
    """解析代码差异文本，返回文件差异列表"""
    files = []
    current_file = None
    current_hunk = None

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" ")
            file_name = parts[2].replace("a/", "")
            current_file = FileDiff(file=file_name, hunks=[])
            files.append(current_file)
            current_hunk = None  # 换文件了，清空上一个文件的 hunk，否则 ---/+++ 头会串进上一个文件

        elif line.startswith("@@"):
            parts = line.split(" ")
            old = parts[1][1:].split(",")
            new = parts[2][1:].split(",")
            current_hunk = DiffHunk(
                old_start=int(old[0]),
                old_lines=int(old[1]) if len(old) > 1 else 1,
                new_start=int(new[0]),
                new_lines=int(new[1]) if len(new) > 1 else 1,
                content=[],
            )
            current_file.hunks.append(current_hunk)

        elif line.startswith(("+", "-", " ")) and current_hunk is not None: #存一行内容，挂到当前的hunk
            current_hunk.content.append(line)

    return files
def reconstruct_file(file_diff:FileDiff)->str:
    """根据文件差异，重构文件内容"""
    lines=[]
    for hunk in file_diff.hunks:
        real_line=hunk.new_start
        for raw in hunk.content:
            if raw.startswith("-"):
                continue
            elif raw.startswith("+")or raw.startswith(" "):
                lines.append(f"{real_line}|{raw[1:]}")
                real_line+=1

    return "\n".join(lines)
def annotated_code(file_path:str):
    with open(file_path, encoding="utf-8") as f:
        lines=f.readlines()
        code=[]
        for i,ln in enumerate(lines):
            ln=ln.rstrip("\r\n")
            code.append(f"{i+1}|{ln}")
        return  "\n".join(code)

def normalize_input(src:str)->list[tuple[str,str]]:
    if os.path.exists(src):
        if os.path.isdir(src): #文件夹
            list_files=[]
            for root,dirs, file in os.walk(src):
                dirs[:]=[d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
                for name in file:
                    if os.path.splitext(name)[1].lower() in SKIP_EXTS:
                        continue
                    file_path=os.path.join(root,name)
                    try :
                       code=annotated_code(file_path)
                       list_files.append((file_path,code))
                            
                    except (UnicodeDecodeError, OSError):
                        continue
                
            return list_files
        else: #文件
            with open(src,encoding="utf-8")as f:
                content=f.read()
            if  content.lstrip().startswith("diff --git"):
                file_diff = parse_diff(content)
                return  [(fd.file,reconstruct_file(fd)) for fd in file_diff]
            else:
                return [(src,annotated_code(src))]
        
    if src.lstrip().startswith("diff --git"):
        file_diff= parse_diff(src)
        return  [(fd.file,reconstruct_file(fd)) for fd in file_diff]
    return [("unknown",src)]

if __name__ == "__main__":
    # with open("sample.diff", encoding="utf-8") as f:
    #     diff_text = f.read()
    # files = parse_diff(diff_text)
    # print("文件数:", len(files))
    # for fd in files:
    #     print(f"\n===== {fd.file} =====\n" + reconstruct_file(fd))
    #     print(f"\n文件 {fd.file}: {len(fd.hunks)} 个 hunk")
    #     for h in fd.hunks:
    #         print(f"  hunk: old {h.old_start},{h.old_lines} -> new {h.new_start},{h.new_lines}")
    #         for ln in h.content:
    #             print("   ", repr(ln))
    print(normalize_input("./app")) 




