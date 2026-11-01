"""向量检索层：用 ChromaDB 存历史代码与审核发现，实现"相似代码 → 召回历史问题"。

整体思路：
1. 用嵌入模型（Embedding）把「代码」和「问题描述」都转成向量；
2. 审核完成后，把代码向量存进 code_col，把问题向量存进 findings_col；
3. 以后审新代码时，先把它转成向量，在 code_col 里找最相似的几段历史代码；
4. 拿到这些历史代码对应的 review_id，再去 findings_col 里把当年发现的问题捞出来，
   作为"历史经验"辅助本次审核。

这样做的价值：同一个项目里，相似的 bug 往往反复出现，向量检索能帮 LLM"想起"以前踩过的坑。
"""

import os                                    # 读取环境变量
import chromadb                              # 轻量级向量数据库（本地持久化）
from dotenv import load_dotenv               # 把 .env 文件里的变量加载进环境变量
from langchain_openai import OpenAIEmbeddings  # 嵌入模型客户端（OpenAI 兼容接口）

from app.models import ReviewResult          # 审核结果模型（含 findings 列表）

load_dotenv()  # 读取项目根目录的 .env，加载 SILICONFLOW_API_KEY 等密钥

# 创建 ChromaDB 客户端，数据持久化到本地 chroma_db 目录（重启不丢）
client = chromadb.PersistentClient(path="chroma_db")

# 从环境变量读取嵌入服务的密钥（这里用的是 SiliconFlow 提供的 bge-m3 模型）
embedding_api_key = os.getenv("SILICONFLOW_API_KEY")

# 初始化嵌入模型：bge-m3 是 BAAI 的多语言嵌入模型，适合中英文代码/文本
embeddings = OpenAIEmbeddings(
    model="BAAI/bge-m3",
    base_url="https://api.siliconflow.cn/v1",  # SiliconFlow 的 OpenAI 兼容端点
    api_key=embedding_api_key,
)

# 集合（collection）可以理解为"一张向量表"。
# get_or_create_collection：存在就复用，不存在就新建。

# 集合一：存「代码」向量 —— 用于按代码相似度检索
code_col = client.get_or_create_collection(
    name="review_code",
    metadata={"hnsw:space": "cosine"},  # 用余弦相似度衡量两个向量"像不像"
)

# 集合二：存「问题发现」向量 —— 用于按 review_id 捞出对应的历史问题
findings_col = client.get_or_create_collection(
    name="review_findings",
    metadata={"hnsw:space": "cosine"},
)


def write_review(result: ReviewResult, review_id: int, code_map: dict[str, str]):
    """把一次审核的「代码」和「发现的问题」都写进向量库。

    参数：
        result：本次审核结果（主要用它的 findings 列表）
        review_id：这次审核在数据库里的唯一 ID（来自 db.save_review 的返回值）
        code_map：{文件名: 文件内容} 的映射，一次审核可能涉及多个文件
    """
    # ---- 第一步：把每个文件的代码转成向量，存进 code_col ----
    for file_name, code in code_map.items():
        # embed_documents 接收一个字符串列表，返回对应的向量列表（这里只传一个文件）
        # 注意：返回的 emb 是"一个列表里套一个向量"，长度和输入一致
        emb = embeddings.embed_documents([code])
        code_col.add(
            ids=[f"{review_id}_{file_name}"],   # 唯一 ID：审核ID_文件名，方便反查
            documents=[code],                    # 原始文本（代码），检索时可返回原文
            embeddings=emb,                      # 对应的向量
            metadatas=[{                          # 附带元数据，用于过滤和回查
                "review_id": review_id,           # 属于哪次审核
                "file_name": file_name,           # 是哪个文件
            }],
        )

    # ---- 第二步：把问题发现（findings）转成向量，存进 findings_col ----
    if result.findings:  # 只有存在 findings 时才写入，避免空列表
        # 每条 finding 只取 message（问题描述）作为向量化的文本
        docs = [f.message for f in result.findings]

        # 每条 finding 对应一份元数据，供后续筛选/展示
        metas = [{
            "review_id": review_id,              # 属于哪次审核（关键：用来和 code 关联）
            "file_name": f.file or "unknown",    # 文件名，可能为 None，用 unknown 兜底
            "severity": f.severity.value,        # 严重程度（取枚举的字符串值，如 "high"）
            "agent_type": f.agent_type.value,    # 审核维度（logic/security/...）
        } for f in result.findings]

        # 把所有 message 批量转成向量
        emb = embeddings.embed_documents(docs)

        findings_col.add(
            # 唯一 ID：审核ID_序号（enumerate 给每条 finding 编号）
            ids=[f"{review_id}_{i}" for i, f in enumerate(result.findings)],
            documents=docs,       # 问题描述原文
            embeddings=emb,       # 向量
            metadatas=metas,      # 元数据
        )


def search_similar_code(code: str, k: int = 3):
    """根据一段代码，找回历史上最相似的代码，并返回它们当年发现的问题。

    参数：
        code：待检索的代码片段
        k：返回最相似的前 k 段代码（默认 3）

    流程：代码转向量 → 在 code_col 里找 top-k 相似 → 拿到 review_id → 在 findings_col 里捞问题
    """
    # 把待检索代码转成一个查询向量（embed_query 只处理单条文本）
    try:
        query_vec = embeddings.embed_query(code)
    except Exception:
        # embedding 服务挂了就降级：返回空上下文，不让辅助功能拖垮主审核流程
        return ""

    # 在代码集合里查询最相似的 k 段代码，并带上每条命中的余弦距离
    res = code_col.query(
        query_embeddings=[query_vec],   # 查询向量（套一层列表，因为接口支持批量查询）
        n_results=k,                     # 返回 top-k
        include=["metadatas", "distances"],  # 同时返回距离，用于过滤"不够像"的
    )

    # 距离越小越像（余弦距离：0=相同，2=相反）。只保留足够像的命中，其余丢弃
    SIMILARITY_THRESHOLD = 0.3  # 约等于余弦相似度 > 0.7，可按需调
    hits = [
        meta for meta, dist in zip(res["metadatas"][0], res["distances"][0])
        if dist < SIMILARITY_THRESHOLD
    ]

    # 每条命中同时带 review_id 和 file_name，用这对组合去精确捞 findings，
    # 避免只按 review_id 捞会把同一 review 里其他文件的发现混进来（file 级过滤）
    lines = []
    seen = set()
    for h in hits:
        key = (h["review_id"], h["file_name"])
        if key in seen:
            continue
        seen.add(key)
        found = findings_col.get(
            where={"$and": [
                {"review_id": h["review_id"]},
                {"file_name": h["file_name"]},
            ]},
            include=["documents", "metadatas"],   # 只取原文和元数据，不取向量
        )
        # zip 把 documents（问题描述）和 metadatas（元数据）一一配对
        for doc, meta in zip(found["documents"], found["metadatas"]):
            # 每行格式：[类型]严重程度 文件名: 问题描述
            lines.append(f"[{meta['agent_type']}]{meta['severity']} {meta['file_name']}: {doc}")
    return "\n".join(lines)


if __name__ == "__main__":
    # 直接运行本文件时：读 sample.diff，检索相似代码对应的历史问题并打印
    with open("sample.diff", encoding="UTF-8") as f:
        diff_text = f.read()
    print(search_similar_code(diff_text))
