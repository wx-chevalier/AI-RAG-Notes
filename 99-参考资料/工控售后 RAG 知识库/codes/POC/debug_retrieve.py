import os
import chromadb
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# --- Configuration ---
POC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(POC_DIR)
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
CHROMA_PATH = os.path.join(PROJECT_ROOT, 'chroma_db')
COLLECTION_NAME = "industrial_kb"

# Load Env
load_dotenv(dotenv_path=ENV_PATH)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    # try fallback to 'api_key' if older env
    OPENROUTER_API_KEY = os.getenv("api_key")
EMBEDDING_MODEL = os.getenv("embeddings_model_name", "qwen/qwen3-embedding-8b")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def debug_retrieval_logic():
    print("🚀 Starting Retrieval Debug...")
    print(f"DB Path: {CHROMA_PATH}")
    print(f"Model: {EMBEDDING_MODEL}")
    
    # 1. Init Vector Store
    embedding_function = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False
    )
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
        persist_directory=CHROMA_PATH
    )
    
    query = "MQTT 驱动的各项参数含义是什么？特别是 KeepAlive"
    print(f"\n❓ Query: {query}")
    
    # 2. Step 1: Similarity Search
    print("\n🔍 Step 1: Vector Search (Top-5)")
    initial_docs = vector_store.similarity_search(query, k=5)
    
    unique_filenames = set()
    
    if not initial_docs:
        print("❌ No docs found in Step 1!")
        return

    for i, doc in enumerate(initial_docs):
        fname = doc.metadata.get('filename')
        cidx = doc.metadata.get('chunk_index')
        snippet = doc.page_content[:100].replace('\n', ' ')
        print(f"   [{i+1}] {fname} (Chunk {cidx}) | Content: {snippet}...")
        unique_filenames.add(fname)
        
    print(f"\n📋 Target Files for Expansion: {unique_filenames}")
    
    # 3. Step 2: Parent Retrieval (The "Inquisition")
    print("\n🧹 Step 2: Fetching ALL chunks for these files...")
    
    # Debugging the `get` call specifically
    # Does 'filename' field actually exist in metadata?
    # We check the first initial_doc's metadata keys
    print(f"   (Metadata Keys in DB: {list(initial_docs[0].metadata.keys())})")
    
    try:
        # NOTE: Chroma where clause needs exact match logic
        # We try fetching for the first filename explicitly to debug
        target_file = "MQTT配置.docx" # Hardcoded for focused debugging
        print(f"   -> FORCING fetch chunks for: '{target_file}'")
        
        expanded_results = vector_store.get(
            where={"filename": target_file},
            include=["documents", "metadatas"]
        )
        
        found_count = len(expanded_results['ids'])
        print(f"   -> Found {found_count} chunks for '{target_file}'")
        
        if found_count > 0:
            # Sort and Preview
            sorted_indices = sorted(range(found_count), key=lambda k: expanded_results['metadatas'][k].get('chunk_index', 0))
            
            print("\n📄 Full Content Preview (Chunks Joined):")
            full_text = ""
            for idx in sorted_indices:
                meta = expanded_results['metadatas'][idx]
                content = expanded_results['documents'][idx]
                print(f"   [Chunk {meta.get('chunk_index')}] Length: {len(content)}")
                full_text += content + "\n\n"
            
            print("-" * 40)
            # Find keywords in full text
            print(f"   Keyword 'KeepAlive' found? {'YES' if 'KeepAlive' in full_text else 'NO'}")
            print(f"   Keyword '心跳' found? {'YES' if '心跳' in full_text else 'NO'}")
            print("-" * 40)
            print("Preview of Content Chunk 1 (where the table might be):")
            # Try to find "Content Chunk 1" marker
            marker = "Content Chunk 1:"
            if marker in full_text:
                start = full_text.find(marker)
                print(full_text[start:start+500])
            else:
                print("(Content Chunk 1 marker not found, showing raw snippet)")
                print(full_text[:500])
                
        else:
            print("❌ 'get' returned 0 results. Metadata filtering failed!")

    except Exception as e:
        print(f"❌ Error during expanded Retrieval: {e}")

if __name__ == "__main__":
    debug_retrieval_logic()
