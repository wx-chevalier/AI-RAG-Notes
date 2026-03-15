import os
from modelscope.hub.snapshot_download import snapshot_download

# BAAI/bge-reranker-v2-m3 在 ModelScope 上的 ID 通常是一样的，或者叫 "Xorbits/bge-reranker-v2-m3"
# 经查，ModelScope 上 BAAI 官方发布的 ID 为: 'AI-ModelScope/bge-reranker-v2-m3' 
# 或者我们可以直接搜 'bge-reranker-v2-m3'
# 实际上 BAAI 在 ModelScope 的组织通常是 'baichuan-inc' 或者直接就是 'Xorbits' 维护。
# 最稳妥的通用 ID 是: 'Xorbits/bge-reranker-v2-m3' (这是社区经常用的)
# 但最好的方式是搜索。

# 让我们尝试直接用官方映射的 ID，通常 HuggingFace 的 ID 在 ModelScope 上对应的是：
MODEL_ID = "AI-ModelScope/bge-reranker-v2-m3" # 这是一个常见的镜像 ID
# 备选: "Xorbits/bge-reranker-v2-m3"

print(f"Downloading {MODEL_ID} from ModelScope (Alibaba Cloud)...")

try:
    # cache_dir 指定下载到当前目录下的 model_cache 文件夹，方便管理
    local_dir = snapshot_download(MODEL_ID, cache_dir='./model_cache')
    print(f"\nDownload success! Model path: {local_dir}")
    
    # 将此路径打印出来，稍后填入 rag_engine.py
    print(f"PLEASE UPDATE rag_engine.py WITH THIS PATH: {local_dir}")
    
except Exception as e:
    print(f"Error: {e}")
    # Fallback try
    print("Trying fallback ID: 'Xorbits/bge-reranker-v2-m3'")
    try:
         local_dir = snapshot_download('Xorbits/bge-reranker-v2-m3', cache_dir='./model_cache')
         print(f"\nDownload success! Model path: {local_dir}")
         print(f"PLEASE UPDATE rag_engine.py WITH THIS PATH: {local_dir}")
    except Exception as e2:
        print(f"Fallback failed too: {e2}")
