import os
import json
import logging
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings

# Use OpenAI embeddings for OpenRouter
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_BASE_DIR = os.path.join(PROJECT_ROOT, 'Cleaned_Knowledge_Base')
METADATA_PATH = os.path.join(KB_BASE_DIR, 'metadata.json')
CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, 'chroma_db')
COLLECTION_NAME = "industrial_kb"  # 知识库名称

# API Configuration
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))
# Prefer SiliconFlow
API_KEY = os.getenv('siliconflow_api_key') or os.getenv('api_key')
# FORCE Qwen/Qwen3-Embedding-8B as requested by user
EMBEDDING_MODEL_NAME = "Qwen/Qwen3-Embedding-8B" 

# Determine Base URL
if os.getenv('siliconflow_api_key'):
    BASE_URL = "https://api.siliconflow.cn/v1"
else:
    BASE_URL = "https://openrouter.ai/api/v1" # Fallback (but Model Name might fail on OpenRouter if it's diff)

# Batch size for ingestion
BATCH_SIZE = 20
CHUNK_SIZE = 6000 
CHUNK_OVERLAP = 500

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_metadata():
    if not os.path.exists(METADATA_PATH):
        logger.error(f"Metadata file not found at {METADATA_PATH}")
        return []
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_markdown_content(relative_path):
    if os.path.exists(relative_path):
         try:
             with open(relative_path, 'r', encoding='utf-8') as f:
                 return f.read()
         except Exception as e:
             logger.warning(f"Failed to read file {relative_path}: {e}")
             return None
    else:
        logger.warning(f"File not found: {relative_path}")
        return None

def main():
    if not API_KEY:
        logger.error("API Key missing in .env")
        return

    logger.info(f"Starting ingestion into ChromaDB ({CHROMA_PERSIST_DIR}) using {BASE_URL}: {EMBEDDING_MODEL_NAME}")
    
    # 1. Initialize Chroma Client
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Reset collection for fresh start
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted existing collection '{COLLECTION_NAME}' for a fresh start.")
    except Exception:
        pass 

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 2. Initialize Embeddings
    logger.info("Initializing Embeddings...")
    embeddings_model = OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        openai_api_key=API_KEY,
        openai_api_base=BASE_URL,
        # check_embedding_ctx_length=False # Removed for clarity
    )
    
    # Initialize Text Splitter for safety
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )

    # 3. Load Data
    metadata_list = load_metadata()
    logger.info(f"Loaded {len(metadata_list)} documents from metadata.")

    # 4. Batch Process
    documents_buffer = []
    metadatas_buffer = []
    ids_buffer = []
    
    total_chunks = 0
    total_docs = 0
    
    for item in tqdm(metadata_list, desc="Processing Documents"):
        if "id" not in item: continue
        
        md_path = item.get("markdown_path")
        content = get_markdown_content(md_path)
        
        if not content:
            continue
            
        # Metadata construction
        keywords_str = ", ".join(item.get("keywords", []))
        questions_str = "\n".join(item.get("questions", []))
        summary_str = item.get("summary", "")
        title_str = item.get("title", "")
        
        base_meta = {
            "title": title_str,
            "filename": item.get("filename", ""),
            "category": item.get("category", "General"),
            "clean_docx_path": item.get("clean_docx_path", ""),
            "original_path": item.get("original_path", ""),
            "summary": summary_str[:5000], # truncation for metadata just in case
            "keywords_str": keywords_str, 
            "questions_str": questions_str
        }

        # Splitting Logic
        # Even with long context models, splitting helps retrieval granularity.
        # But here we mostly want to avoid errors.
        if len(content) > CHUNK_SIZE:
             chunks = text_splitter.split_text(content)
        else:
             chunks = [content]
             
        for i, chunk_content in enumerate(chunks):
            # Hybrid Content construction
            # We prepend metadata to EVERY chunk to ensure semantic hits
            embed_text = f"Title: {title_str}\nSummary: {summary_str}\nKeywords: {keywords_str}\nQuestions: {questions_str}\nContent Chunk {i+1}:\n{chunk_content}"
            
            # Metadata update for chunks
            chunk_meta = base_meta.copy()
            chunk_meta['chunk_index'] = i
            chunk_meta['total_chunks'] = len(chunks)
            
            # ID Strategy: doc_uuid_chunk_i
            chunk_id = f"{item['id']}_{i}"
            
            documents_buffer.append(embed_text)
            metadatas_buffer.append(chunk_meta)
            ids_buffer.append(chunk_id)
            
            total_chunks += 1
            
        total_docs += 1
        
        # Batch Flush
        if len(documents_buffer) >= BATCH_SIZE:
            try:
                # Compute embeddings via API
                embeddings = embeddings_model.embed_documents(documents_buffer)
                
                collection.add(
                    documents=documents_buffer,
                    embeddings=embeddings,
                    metadatas=metadatas_buffer,
                    ids=ids_buffer
                )
                
                # Clear buffers
                documents_buffer = []
                metadatas_buffer = []
                ids_buffer = []
                
            except Exception as e:
                logger.error(f"Batch ingestion failed: {e}")
                # Optional: Retry logic or finer-grained fallback could go here
                # For now, we log and clear buffer to prevent stuck loop
                # Just dumping the buffer effectively skips these docs
                documents_buffer = []
                metadatas_buffer = []
                ids_buffer = []

    # Final Flush
    if documents_buffer:
        try:
            embeddings = embeddings_model.embed_documents(documents_buffer)
            collection.add(
                documents=documents_buffer,
                embeddings=embeddings,
                metadatas=metadatas_buffer,
                ids=ids_buffer
            )
        except Exception as e:
            logger.error(f"Final batch ingestion failed: {e}")

    logger.info(f"Ingestion Complete.")
    logger.info(f"Processed Docs: {total_docs}")
    logger.info(f"Total Chunks Ingested: {total_chunks}")
    logger.info(f"Chroma DB saved at: {CHROMA_PERSIST_DIR}")

if __name__ == "__main__":
    main()
