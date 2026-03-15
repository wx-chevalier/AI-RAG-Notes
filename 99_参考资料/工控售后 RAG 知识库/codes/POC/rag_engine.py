import os
import chromadb
import torch
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Load Environment
POC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(POC_DIR)
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

# --- CONFIGURATION ---
# Force HF Mirror for fast download in China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

CHROMA_PATH = os.path.join(PROJECT_ROOT, 'chroma_db')
COLLECTION_NAME = "industrial_kb"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Rerank Config
USE_LOCAL_RERANK = True
# Fallback to BAAI/bge-reranker-v2-m3 for stability and speed (570MB)
# Path from ModelScope download
LOCAL_RERANK_MODEL_NAME = os.path.join(POC_DIR, 'model_cache', 'AI-ModelScope', 'bge-reranker-v2-m3')

EMBEDDING_MODEL = os.getenv("embeddings_model_name", "qwen/qwen3-embedding-8b")
LLM_MODEL = os.getenv("model_name", "google/gemini-2.5-flash")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class IndustrialRAG:
    def __init__(self):
        self._init_vector_store()
        self._init_llm()
        if USE_LOCAL_RERANK:
            self._init_local_reranker()
            
    def _init_local_reranker(self):
        print(f"   [Init] Loading Rerank model: {LOCAL_RERANK_MODEL_NAME}...")
        try:
            # Determine device (MPS for Mac, CUDA, or CPU)
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
            print(f"   [Init] Using inference device: {self.device}")

            self.rerank_tokenizer = AutoTokenizer.from_pretrained(LOCAL_RERANK_MODEL_NAME)
            self.rerank_model = AutoModelForSequenceClassification.from_pretrained(LOCAL_RERANK_MODEL_NAME)
            self.rerank_model.to(self.device)
            self.rerank_model.eval() # Set to evaluation mode
            print("   [Init] Rerank model loaded successfully.")
        except Exception as e:
            print(f"   [Init] Failed to load local reranker: {e}")
            self.rerank_model = None

    def _init_vector_store(self):
        """Initialize ChromaDB connection"""
        self.embedding_function = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            check_embedding_ctx_length=False
        )
        
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
            persist_directory=CHROMA_PATH
        )
        
    def _init_llm(self):
        """Initialize LLM via OpenRouter"""
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=0.1
        )
        
    def _rerank(self, query, initial_docs, top_n=3):
        """
        Rerank documents using Local Transformers Model.
        """
        if not self.rerank_model:
             print("   [Rerank] Model not initialized, skipping rerank.")
             return initial_docs[:top_n]

        import time
        start_time = time.time()
        try:
            # Prepare pairs for cross-encoder
            pairs = [[query, doc.page_content] for doc in initial_docs]
            
            with torch.no_grad():
                inputs = self.rerank_tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=1024).to(self.device)
                scores = self.rerank_model(**inputs, return_dict=True).logits.view(-1,).float()
            
            # (Rest of logic) ...
            
            # Sort indices based on scores (descending)
            scores_list = scores.cpu().numpy().tolist()
            doc_score_pairs = list(zip(initial_docs, scores_list))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            final_docs = [doc for doc, score in doc_score_pairs[:top_n]]
            
            elapsed = time.time() - start_time
            print(f"   [Rerank] Scored {len(initial_docs)} docs -> Top {top_n} in {elapsed:.4f}s")
            return final_docs
            
        except Exception as e:
            print(f"   [Rerank Warning] Local inference failed: {e}. Fallback to raw results.")
            return initial_docs[:top_n]
        if not initial_docs:
            return []
            
        import requests
        import time
        
        url = "https://api.siliconflow.cn/v1/rerank"
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare documents for API
        doc_texts = [doc.page_content for doc in initial_docs]
        
        payload = {
            "model": RERANK_MODEL,
            "query": query,
            "documents": doc_texts,
            "top_n": top_n,
            "return_documents": False  # Just need indices
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json().get('results', [])
            
            # Map back to Document objects
            reranked_docs = []
            for item in results:
                original_index = item['index']
                score = item['relevance_score']
                
                doc = initial_docs[original_index]
                # Optional: Inject relevance score into metadata for debugging
                doc.metadata['rerank_score'] = score
                reranked_docs.append(doc)
                
            print(f"   [Rerank] Scored {len(initial_docs)} docs -> Top {len(reranked_docs)} in {time.time()-start_time:.2f}s")
            return reranked_docs
            
        except Exception as e:
            print(f"   [Rerank Warning] API call failed: {e}. Fallback to vector search results.")
            # Fallback: just return the top_n from original list
            return initial_docs[:top_n]

    def retrieve(self, query, top_k=3):
        """
        Retrieve documents using 'Search -> Rerank -> Parent Expansion' strategy.
        1. Search Top-N chunks (Broad Recall).
        2. Rerank to Top-k (High Precision).
        3. Fetch Parent Docs (Full Context).
        """
        import time
        t0 = time.time()
        
    def retrieve(self, query, top_k=3):
        """
        Retrieve documents using 'Search -> Rerank -> Parent Expansion' strategy.
        1. Search Top-N chunks (Broad Recall).
        2. Rerank to Top-k (High Precision).
        3. Fetch Parent Docs (Full Context).
        """
        import time
        t0 = time.time()
        
        # 1. Broad Similarity Search (Recall Phase)
        # Update 2024-12-11: Reduced to 10 to balance speed (Rerank is heavy). 
        # MODIFY THIS VALUE to tune performance (Higher = Better Recall, Slower Rerank).
        SEARCH_K = 20
        
        print(f"   [Timing] Starting Vector Search (Embedding API + DB)...")
        initial_docs = self.vector_store.similarity_search(query, k=SEARCH_K)
        t1 = time.time()
        print(f"   [Timing] Vector Search took {t1 - t0:.2f}s. Found {len(initial_docs)} candidates.")
        
        # [DEBUG] Print Candidate Titles to verify Embedding Quality
        print("   [Debug] Top 5 Candidates from Vector Search:")
        for idx, d in enumerate(initial_docs[:5]):
             print(f"       {idx+1}. {d.metadata.get('filename', 'Unknown')} (Score: {d.metadata.get('score', 'N/A')})")

        
        # 2. Rerank (Precision Phase)
        # Always call _rerank. It handles fallback internally.
        selected_docs = self._rerank(query, initial_docs, top_n=top_k)
        
        # 3. Parent Document Expansion (Context Phase)
        # Extract unique document identifiers
        unique_filenames = set()
        
        for doc in selected_docs:
            filename = doc.metadata.get('filename')
            if filename and filename not in unique_filenames:
                unique_filenames.add(filename)
        
        if not unique_filenames:
            print(f"   [Timing] Total Retrieve Time: {time.time() - t0:.2f}s") 
            return []

        print(f"   [Retrieval] Expanding {len(unique_filenames)} parent documents: {list(unique_filenames)}")

        # Fetch ALL chunks for these files from Chroma
        # Using 'get' is much faster than similarity_search
        t_expand_start = time.time()
        collection = self.vector_store._collection
        expanded_results = collection.get(
            where={"filename": {"$in": list(unique_filenames)}},
            include=["documents", "metadatas"]
        )
        t3 = time.time()
        print(f"   [Timing] Parent Expansion (DB Get) took {t3 - t_expand_start:.2f}s")
        
        final_docs = []
        if expanded_results['documents']:
            ids = expanded_results['ids']
            contents = expanded_results['documents']
            metadatas = expanded_results['metadatas']
            
            # Group by filename
            doc_groups = {fname: [] for fname in unique_filenames}
            
            for cid, content, meta in zip(ids, contents, metadatas):
                fname = meta.get('filename')
                if fname in doc_groups:
                    from langchain_core.documents import Document
                    doc_obj = Document(page_content=content, metadata=meta)
                    doc_groups[fname].append(doc_obj)
            
            # Sort each group by chunk_index and Flatten
            for fname in unique_filenames:
                sorted_chunks = sorted(doc_groups[fname], key=lambda x: x.metadata.get('chunk_index', 0))
                final_docs.extend(sorted_chunks)
        
        print(f"   [Timing] Total Retrieve Time: {time.time() - t0:.2f}s")        
        return final_docs
    
    def generate_answer(self, query, context_docs, user_id=None, session_id=None, rewritten_query=None):
        """Generate Answer using LLM with Timing Logs & Telemetry"""
        import time
        from supabase_client import TelemetryLogger
        
        # Init logger lazily or use instance if already init (better to init in __init__)
        if not hasattr(self, 'logger'):
             self.logger = TelemetryLogger()
             
        start_time = time.time()
        
        # Prompt Template
        template = """你是一个工业软件售后技术专家。请基于以下提供的【技术知识库】回答用户的问题。
        
        注意事项：
        1. 请忽略每个文档开头的 Summary/Keywords 等元数据，重点阅读 【Content Chunk】 之后的正文。
        2. 如果用户询问英文术语（如 KeepAlive），请自动关联到文档中的中文术语（如“心跳”、“保活”等）。
        3. 如果必须展示操作界面、步骤图解，且正文中包含 `![...](...)` 格式的图片引用，**请务必直接保留该Markdown图片链接，不要省略！**
        4. 如果是操作步骤，请一步步列出。
        5. 如果知识库中没有相关信息，请直接回答“知识库中未找到相关信息”，不要编造。
        
        【技术知识库】:
        {context}
        
        【用户问题】: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        # Prepare Context String
        print(f"   [Timing] Starting Context Assembly...")
        context_str = "\n\n".join([f"文档[{i+1}]: {d.page_content}" for i, d in enumerate(context_docs)])
        t_assembly = time.time()
        print(f"   [Timing] Context Assembly took {t_assembly - start_time:.2f}s. Total Context Length: {len(context_str)} chars")
        
        # Chain
        print(f"   [Timing] Invoking LLM...")
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({"context": context_str, "question": query})
        t_llm = time.time()
        print(f"   [Timing] LLM Generation took {t_llm - t_assembly:.2f}s")
        
        # --- TELEMETRY / LOGGING ---
        if user_id and session_id:
            # 1. Construct Snapshot of citations
            retrieval_snapshot = []
            for i, doc in enumerate(context_docs):
                retrieval_snapshot.append({
                    "rank": i + 1,
                    "filename": doc.metadata.get('filename', 'unknown'),
                    "chunk_id": doc.metadata.get('chunk_index', -1), # Assumes metadata has this
                    "score": doc.metadata.get('rerank_score', 0) if i < 3 else 0, # Placeholder logic
                    "content_snippet": doc.page_content[:100]
                })

            # 2. Latency Stats
            latency_stats = {
                "total_ms": int((t_llm - start_time) * 1000),
                "assembly_ms": int((t_assembly - start_time) * 1000),
                "llm_ms": int((t_llm - t_assembly) * 1000)
            }
            
            # 3. Assemble Metadata
            meta = {
                "query_context": {
                    "raw_query": query,
                    "rewritten_query": rewritten_query
                },
                "retrieval_snapshot": retrieval_snapshot,
                "latency_stats": latency_stats,
                "system_config": {
                   "model": self.llm.model_name
                }
            }
            
            # 4. Async Log (User Question + Assistant Answer)
            # Log User Query
            self.logger.log_interaction(session_id, user_id, "user", query, metadata=None)
            # Log Assistant Response
            msg_id = self.logger.log_interaction(session_id, user_id, "assistant", response, metadata=meta)
            print(f"   [Telemetry] Logged interaction for Session {session_id}, MsgID: {msg_id}")
            
            return response, msg_id

        return response, None

    def process_markdown_images(self, text):
        """
        Replace local image paths in markdown with MinIO HTTP URLs.
        Original: ![alt](images/xxx.png)
        Target: ![alt](http://localhost:9000/industrial-kb-images/xxx.png)
        Why: Fast, cached, and production-ready.
        """
        import re
        import json
        
        # Load the mapping file once (lazy loading could be better but this is fine for POC)
        mapping_file_path = os.path.join(POC_DIR, "image_url_mapping.json")
        try:
            with open(mapping_file_path, "r", encoding='utf-8') as f:
                image_mapping = json.load(f)
        except Exception as e:
            print(f"   [Image Warning] Failed to load image mapping: {e}")
            image_mapping = {}

        # Regex to find ![...](images/...)
        pattern = r'!\[(.*?)\]\(images/(.*?)\)'
        
        def replace_with_url(match):
            alt_text = match.group(1)
            filename = match.group(2)
            
            # Key in mapping file is "images/filename"
            key = f"images/{filename}"
            
            if key in image_mapping:
                url = image_mapping[key]
                # Fix: Encode spaces in URL to ensure Markdown renders correctly
                url = url.replace(" ", "%20")
                return f'![{alt_text}]({url})'
            else:
                # Fallback: Try fuzzy matching for minor filename typos (e.g. c0220a7b vs c022a0b7)
                # This is a basic recovery strategy.
                pass
                
                print(f"   [Image Warning] Image not found in mapping: {key}")
                return f'![{alt_text}](Image_Not_Found_In_MinIO)'

        # Debugging: Print matches
        matches = re.findall(pattern, text)
        if matches:
            print(f"   [Image Debug] Found {len(matches)} images. Replacng with MinIO URLs...")
        
        # Use re.sub with a callback function
        replaced_text = re.sub(pattern, replace_with_url, text)
            
        return replaced_text

    def rewrite_query(self, history, current_query):
        """
        Rewrite current query based on history for better retrieval.
        Args:
            history (list): List of dicts [{'role': 'user', 'content': '...'}, ...]
            current_query (str): The latest user question
        Returns:
            str: The rewritten standalone query
        """
        if not history:
            return current_query
            
        print(f"   [Rewrite] Rewriting query using last {len(history)} messages...")
        
        # Construct history string
        history_str = ""
        for msg in history[-5:]: # Keep last 5 turns max
            role = "Human" if msg['role'] == 'user' else "Assistant"
            history_str += f"{role}: {msg['content']}\n"
        
        # Debug: Print what the LLM sees
        print(f"   [Rewrite Debug] Context passed to LLM:\n{history_str.strip()}")
            
        prompt_template = """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just rewrite it if needed, otherwise return it as is.
        
        Chat History:
        {history}
        
        Latest Question: {question}
        
        Standalone Question:"""
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            rewritten_query = chain.invoke({"history": history_str, "question": current_query})
            rewritten_query = rewritten_query.strip()
            print(f"   [Rewrite] Original: '{current_query}' -> New: '{rewritten_query}'")
            return rewritten_query
        except Exception as e:
            print(f"   [Rewrite Error] Failed to rewrite: {e}. Using original.")
            return current_query

    def open_local_file(self, file_path):
        """Helper to open local file (Mac only)"""
        if os.path.exists(file_path):
            os.system(f"open '{file_path}'")
            return True
        return False
