# Naive RAG/Advanced RAG 伪代码对比 + Modular RAG/Agentic RAG 深度分析

你需要包含伪代码的 RAG 技术对比，同时延伸分析 Modular RAG 和 Agentic RAG，下面将按「伪代码对比拆解」+「高阶 RAG 深度分析」的结构展开，所有伪代码采用 Python 风格，兼顾易懂性和技术完整性。

## 一、 Naive RAG（朴素 RAG）：伪代码实现与核心拆解

### 1. 伪代码完整实现

```python
# 依赖说明：通用向量模型、向量数据库、基础LLM
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI

# 1. 初始化基础组件
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # 通用轻量嵌入模型
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="naive_rag_collection")
llm_client = OpenAI()

def naive_rag_pipeline(raw_documents, user_query):
    """
    Naive RAG 核心流程：固定分块 → 简单嵌入 → 单一向量检索 → 直接拼接生成
    """
    # 步骤1：固定长度文档分块（核心缺陷：破坏语义完整性）
    def split_documents_fixed_length(documents, chunk_size=512, chunk_overlap=50):
        chunks = []
        for doc in documents:
            # 按字符数固定切割，不考虑语义边界
            for i in range(0, len(doc), chunk_size - chunk_overlap):
                chunk = doc[i:i+chunk_size]
                chunks.append(chunk)
        return chunks

    # 步骤2：生成向量嵌入（无领域优化，静态嵌入）
    document_chunks = split_documents_fixed_length(raw_documents)
    chunk_embeddings = embedding_model.encode(document_chunks)  # 批量生成嵌入

    # 步骤3：构建静态索引（无元数据增强，仅存储chunk与嵌入）
    collection.add(
        documents=document_chunks,
        embeddings=chunk_embeddings.tolist(),
        ids=[f"chunk_{i}" for i in range(len(document_chunks))]
    )

    # 步骤4：单一向量相似度检索（仅余弦相似度，无混合策略）
    query_embedding = embedding_model.encode(user_query).tolist()
    retrieval_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5  # 固定top-k，无动态调整
    )
    retrieved_context = "\n".join(retrieval_results["documents"][0])  # 简单拼接上下文

    # 步骤5：直接生成答案（无上下文过滤/重排序，易引入噪声）
    prompt = f"基于以下上下文回答问题：\n{retrieved_context}\n问题：{user_query}"
    response = llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content, retrieved_context

# 测试调用（极简流程，无任何优化）
if __name__ == "__main__":
    raw_docs = ["人工智能（AI）是一门旨在使机器模拟人类智能的技术科学，涵盖机器学习、自然语言处理等领域。机器学习是AI的核心分支，其中深度学习又占据主导地位。"]
    query = "人工智能的核心分支是什么？"
    answer, context = naive_rag_pipeline(raw_docs, query)
    print("Naive RAG 答案：", answer)
    print("检索上下文：", context)
```

### 2. Naive RAG 核心拆解

- **流程本质**：线性单向流程（分块 → 嵌入 → 检索 → 生成），无任何反馈或优化环节
- **关键缺陷（对应伪代码）**：
  1.  分块：`split_documents_fixed_length` 按固定字符数切割，易拆分完整语义（如跨段落的知识点）
  2.  检索：仅用向量余弦相似度，无关键词匹配，对歧义查询/短查询支持差
  3.  上下文处理：直接拼接 `retrieved_context`，无去重、压缩、过滤，易引入无关信息
  4.  生成：基础 prompt，无链式思考（CoT），易产生幻觉

## 二、 Advanced RAG（高级 RAG）：伪代码实现与核心拆解

### 1. 伪代码完整实现

```python
# 依赖说明：新增关键词检索（BM25）、重排序模型、查询改写能力
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi
import nltk
nltk.download('punkt')

# 1. 初始化增强组件
embedding_model = SentenceTransformer("E5-large-v2")  # 更强的语义嵌入模型
rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")  # 重排序模型
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="advanced_rag_collection")
llm_client = OpenAI()

def advanced_rag_pipeline(raw_documents, user_query):
    """
    Advanced RAG 核心流程：检索前优化 → 混合检索 → 检索后优化 → 增强生成
    """
    # ====================== 检索前优化（Pre-Retrieval） ======================
    # 步骤1：语义分块（优化Naive的固定分块，保留语义完整性）
    def split_documents_semantic(documents):
        semantic_chunks = []
        for doc in documents:
            # 按句子拆分，再按主题合并（简单语义分块示例，实际可使用LangChain的RecursiveCharacterTextSplitter）
            sentences = nltk.sent_tokenize(doc)
            current_chunk = []
            current_length = 0
            for sent in sentences:
                sent_length = len(sent)
                if current_length + sent_length > 512:  # 阈值内保留语义
                    semantic_chunks.append(" ".join(current_chunk))
                    current_chunk = [sent]
                    current_length = sent_length
                else:
                    current_chunk.append(sent)
                    current_length += sent_length
            if current_chunk:
                semantic_chunks.append(" ".join(current_chunk))
        return semantic_chunks

    # 步骤2：查询改写（优化原始查询，提升检索精度，解决歧义/短查询问题）
    def rewrite_query(raw_query):
        rewrite_prompt = f"请将以下用户查询改写为更清晰、更适合知识库检索的问句，保留核心含义：{raw_query}"
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": rewrite_prompt}]
        )
        return response.choices[0].message.content

    # 步骤3：生成语义分块与增强嵌入（带元数据，优化索引）
    document_chunks = split_documents_semantic(raw_documents)
    chunk_embeddings = embedding_model.encode(document_chunks)
    # 新增元数据（来源标识，提升过滤能力）
    metadata = [{"source": "custom_kb", "chunk_id": i} for i in range(len(document_chunks))]
    collection.add(
        documents=document_chunks,
        embeddings=chunk_embeddings.tolist(),
        ids=[f"chunk_{i}" for i in range(len(document_chunks))],
        metadatas=metadata
    )
    rewritten_query = rewrite_query(user_query)  # 获取优化后的查询

    # ====================== 检索中优化（Retrieval） ======================
    # 步骤4：混合检索（向量检索 + BM25关键词检索，互补优势）
    # 4.1 向量检索
    query_embedding = embedding_model.encode(rewritten_query).tolist()
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )
    vector_chunks = vector_results["documents"][0]
    vector_ids = vector_results["ids"][0]

    # 4.2 BM25关键词检索
    tokenized_chunks = [nltk.word_tokenize(chunk.lower()) for chunk in document_chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    tokenized_query = nltk.word_tokenize(rewritten_query.lower())
    bm25_scores = bm25.get_scores(tokenized_query)
    # 取BM25 top10 chunk
    bm25_top_indices = bm25_scores.argsort()[-10:][::-1]
    bm25_chunks = [document_chunks[i] for i in bm25_top_indices]
    bm25_ids = [f"chunk_{i}" for i in bm25_top_indices]

    # 4.3 结果融合（去重，保留更多相关信息）
    all_chunks = vector_chunks + bm25_chunks
    all_ids = vector_ids + bm25_ids
    # 去重：按id去重，保留先出现的chunk（向量检索优先级略高）
    unique_chunk_dict = dict(zip(all_ids, all_chunks))
    unique_chunks = list(unique_chunk_dict.values())

    # ====================== 检索后优化（Post-Retrieval） ======================
    # 步骤5：重排序（用CrossEncoder提升相关性排序精度）
    if len(unique_chunks) > 1:
        # 构造（查询，chunk）对，用于重排序
        rerank_pairs = [(rewritten_query, chunk) for chunk in unique_chunks]
        rerank_scores = rerank_model.predict(rerank_pairs)
        # 按分数排序，取top5
        chunk_score_pairs = list(zip(unique_chunks, rerank_scores))
        chunk_score_pairs.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [pair[0] for pair in chunk_score_pairs[:5]]
    else:
        top_chunks = unique_chunks

    # 步骤6：上下文压缩（减少token消耗，去除冗余信息）
    def compress_context(chunks):
        compress_prompt = f"请提炼以下文本的核心信息，去除冗余内容，保留与问答相关的关键知识点：\n{chr(10).join(chunks)}"
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": compress_prompt}]
        )
        return response.choices[0].message.content

    compressed_context = compress_context(top_chunks)

    # ====================== 增强生成（Generation） ======================
    # 步骤7：带CoT的增强生成（减少幻觉，提升可解释性）
    enhanced_prompt = f"""
    请基于以下压缩后的核心上下文，采用链式思考的方式回答问题：
    1.  先梳理上下文与问题相关的关键信息
    2.  再逐步推导答案
    3.  最后给出清晰、准确的回答
    上下文：{compressed_context}
    问题：{user_query}
    """
    response = llm_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": enhanced_prompt}]
    )
    return response.choices[0].message.content, compressed_context

# 测试调用
if __name__ == "__main__":
    raw_docs = ["人工智能（AI）是一门旨在使机器模拟人类智能的技术科学，涵盖机器学习、自然语言处理等领域。机器学习是AI的核心分支，其中深度学习又占据主导地位，典型框架有TensorFlow、PyTorch。"]
    query = "AI的核心分支是什么？有哪些典型工具？"
    answer, context = advanced_rag_pipeline(raw_docs, query)
    print("Advanced RAG 答案：", answer)
    print("压缩后上下文：", context)
```

### 2. Advanced RAG 与 Naive RAG 关键差异拆解（对应伪代码）

| 对比维度 | Naive RAG                | Advanced RAG                                                                                 | 差异核心                                   |
| -------- | ------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------ |
| 检索前   | 固定字符分块，无查询优化 | 1. 语义分块（`split_documents_semantic`）<br>2. 查询改写（`rewrite_query`）<br>3. 元数据增强 | 保留语义完整性，提升查询与文档的对齐度     |
| 检索中   | 单一向量余弦相似度检索   | 1. 混合检索（向量+BM25）<br>2. 结果去重融合                                                  | 兼顾语义匹配与关键词匹配，覆盖更多相关信息 |
| 检索后   | 直接拼接上下文，无优化   | 1. CrossEncoder 重排序（`rerank_model`）<br>2. 上下文压缩（`compress_context`）              | 提升相关性，减少冗余 token，降低噪声干扰   |
| 生成阶段 | 基础 prompt，直接生成    | 带链式思考（CoT）的增强 prompt                                                               | 减少幻觉，提升答案逻辑性与可解释性         |
| 流程特性 | 线性单向，无反馈         | 全流程闭环优化，多环节互补                                                                   | 显著提升检索精度与答案质量                 |

## 三、 Modular RAG（模块化 RAG）：深度分析

### 1. 核心定义

Modular RAG 是在 Advanced RAG 基础上的**架构升级**，将 RAG 全流程拆分为独立、可插拔、可复用的功能模块，每个模块可单独优化、替换、部署，无需改动整体流程，是企业级 RAG 的主流落地形态。

### 2. 核心特征

- **模块解耦**：按功能边界拆分，无强耦合依赖
- **可插拔性**：每个模块支持多实现方案，按需切换（如分块模块可切换「固定分块」/「语义分块」/「层级分块」）
- **标准化接口**：模块间通过统一接口交互（如输入/输出格式标准化）
- **独立运维**：每个模块可单独监控、扩容、迭代（如嵌入模块升级模型，不影响检索模块）

### 3. 架构设计（核心模块）

```
┌─────────────────────────────────────────────────────────┐
│  Modular RAG 架构                                      │
├─────────────┬─────────────┬─────────────┬─────────────┤
│  前置处理模块  │  嵌入索引模块  │  检索匹配模块  │  后处理模块  │
│  1.  文档清洗  │  1.  嵌入模型  │  1.  向量检索  │  1.  重排序  │
│  2.  分块策略  │  2.  向量数据库 │  2.  关键词检索 │  2.  上下文压缩 │
│  3.  查询改写  │  3.  索引管理  │  3.  结果融合  │  3.  噪声过滤  │
├─────────────┴─────────────┴─────────────┴─────────────┤
│  生成模块  │  监控反馈模块                          │
│  1.  提示词工程 │  1.  性能监控  │
│  2.  CoT/反思  │  2.  质量评估  │
│  3.  格式输出  │  3.  模块优化  │
└─────────────────────────────────────────────────────────┘
```

### 4. 伪代码实现（体现模块化特性）

```python
# 模块化设计：每个模块独立封装，可插拔
class ChunkingModule:
    """分块模块：支持多策略切换"""
    def __init__(self, strategy="semantic", chunk_size=512):
        self.strategy = strategy
        self.chunk_size = chunk_size

    def run(self, documents):
        if self.strategy == "fixed":
            return self._fixed_chunk(documents)
        elif self.strategy == "semantic":
            return self._semantic_chunk(documents)
        else:
            raise ValueError("不支持的分块策略")

    def _fixed_chunk(self, documents):
        # 固定分块实现（同Naive RAG）
        chunks = []
        for doc in documents:
            for i in range(0, len(doc), self.chunk_size - 50):
                chunks.append(doc[i:i+self.chunk_size])
        return chunks

    def _semantic_chunk(self, documents):
        # 语义分块实现（同Advanced RAG）
        semantic_chunks = []
        for doc in documents:
            sentences = nltk.sent_tokenize(doc)
            current_chunk = []
            current_length = 0
            for sent in sentences:
                if current_length + len(sent) > self.chunk_size:
                    semantic_chunks.append(" ".join(current_chunk))
                    current_chunk = [sent]
                    current_length = len(sent)
                else:
                    current_chunk.append(sent)
                    current_length += len(sent)
            if current_chunk:
                semantic_chunks.append(" ".join(current_chunk))
        return semantic_chunks

class EmbeddingModule:
    """嵌入模块：支持多模型切换"""
    def __init__(self, model_name="E5-large-v2"):
        self.model = SentenceTransformer(model_name)

    def run(self, texts):
        return self.model.encode(texts).tolist()

class RetrievalModule:
    """检索模块：支持混合检索切换"""
    def __init__(self, retrieval_type="hybrid", top_k=10):
        self.retrieval_type = retrieval_type
        self.top_k = top_k
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(name="modular_rag_collection")

    def run(self, query_embedding, query_text, document_chunks):
        if self.retrieval_type == "vector":
            return self._vector_retrieval(query_embedding)
        elif self.retrieval_type == "hybrid":
            return self._hybrid_retrieval(query_embedding, query_text, document_chunks)
        else:
            raise ValueError("不支持的检索类型")

    def _vector_retrieval(self, query_embedding):
        results = self.collection.query(query_embeddings=[query_embedding], n_results=self.top_k)
        return results["documents"][0]

    def _hybrid_retrieval(self, query_embedding, query_text, document_chunks):
        # 混合检索实现（同Advanced RAG）
        vector_chunks = self._vector_retrieval(query_embedding)
        tokenized_chunks = [nltk.word_tokenize(chunk.lower()) for chunk in document_chunks]
        bm25 = BM25Okapi(tokenized_chunks)
        tokenized_query = nltk.word_tokenize(query_text.lower())
        bm25_top_indices = bm25.get_scores(tokenized_query).argsort()[-self.top_k:][::-1]
        bm25_chunks = [document_chunks[i] for i in bm25_top_indices]
        # 去重融合
        all_chunks = list(set(vector_chunks + bm25_chunks))
        return all_chunks

class GenerationModule:
    """生成模块：支持多提示词策略切换"""
    def __init__(self, model_name="gpt-3.5-turbo", prompt_strategy="cot"):
        self.client = OpenAI()
        self.model_name = model_name
        self.prompt_strategy = prompt_strategy

    def run(self, context, query):
        if self.prompt_strategy == "basic":
            prompt = f"基于上下文回答：{context}\n问题：{query}"
        elif self.prompt_strategy == "cot":
            prompt = f"基于上下文，用链式思考回答：{context}\n问题：{query}"
        else:
            raise ValueError("不支持的提示词策略")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# 模块化RAG流水线：按需组装模块，可灵活替换
def modular_rag_pipeline(documents, query):
    # 1. 初始化模块（可灵活切换策略/模型）
    chunk_module = ChunkingModule(strategy="semantic", chunk_size=512)
    embedding_module = EmbeddingModule(model_name="E5-large-v2")
    retrieval_module = RetrievalModule(retrieval_type="hybrid", top_k=10)
    generation_module = GenerationModule(model_name="gpt-3.5-turbo", prompt_strategy="cot")

    # 2. 按流程调用模块（接口统一，无需关注内部实现）
    chunks = chunk_module.run(documents)
    chunk_embeddings = embedding_module.run(chunks)
    # 先写入索引（简化示例）
    retrieval_module.collection.add(
        documents=chunks,
        embeddings=chunk_embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    query_embedding = embedding_module.run([query])[0]
    retrieved_chunks = retrieval_module.run(query_embedding, query, chunks)
    context = "\n".join(retrieved_chunks)
    answer = generation_module.run(context, query)

    return answer

# 测试调用：替换模块策略仅需修改初始化参数
if __name__ == "__main__":
    docs = ["人工智能（AI）核心分支是机器学习，深度学习是机器学习的主流方向。"]
    query = "AI的核心分支是什么？"
    answer = modular_rag_pipeline(docs, query)
    print("Modular RAG 答案：", answer)
```

### 5. 优缺点与适用场景

| 特性     | 详情                                                                                                                                                                                                |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 优点     | 1. 灵活性高：模块可按需替换/升级，适配业务变化<br>2. 可维护性强：故障定位精准，迭代成本低<br>3. 可扩展性好：支持新增模块（如新增「合规检查模块」）<br>4. 多团队协作：不同团队负责不同模块，并行开发 |
| 缺点     | 1. 初期搭建成本高：需设计标准化接口与模块边界<br>2. 架构复杂度提升：需管理模块依赖与交互<br>3. 运维成本略增：需监控多个模块的运行状态                                                               |
| 适用场景 | 1. 大型企业级 RAG 应用（如企业知识库、智能客服）<br>2. 多团队协作开发的项目<br>3. 需长期迭代、按需优化的场景<br>4. 多业务线复用 RAG 能力的场景                                                      |

## 四、 Agentic RAG（智能体 RAG）：深度分析

### 1. 核心定义

Agentic RAG 是 RAG 技术的**最高阶形态**，将 LLM 智能体（Agent）与 RAG 深度融合，赋予系统「自主决策、自主规划、自主迭代、工具调用」的能力，能够处理超复杂的查询需求（如多跳推理、跨知识库检索、逻辑分析）。

### 2. 核心特征

- **自主决策**：Agent 可根据查询复杂度，自主选择是否使用 RAG、使用哪种检索策略、是否需要工具辅助
- **规划能力**：对复杂查询进行拆分（如将「AI 核心分支及典型工具」拆分为两个子查询），分步执行
- **迭代反思**：生成答案后自主验证正确性，若存在信息缺失/错误，将重新检索并优化答案
- **工具调用**：可调用外部工具（如计算器、搜索引擎、数据库）补充 RAG 知识库之外的信息
- **上下文记忆**：保留对话历史，支持多轮连续问答的上下文一致性

### 3. 架构设计（核心闭环：规划 → 执行 → 反思）

```
┌─────────────────────────────────────────────────────────┐
│  Agentic RAG 架构（核心：Agent 闭环）                  │
├─────────────────────────────────────────────────────────┤
│  1.  规划层（Planning）                                │
│     -  查询理解与意图识别                              │
│     -  复杂查询拆分子任务                              │
│     -  制定执行步骤（如：先检索A，再检索B，最后融合）  │
├─────────────────────────────────────────────────────────┤
│  2.  执行层（Execution）                               │
│     -  调用RAG模块（按需选择检索策略）                  │
│     -  调用外部工具（计算器、搜索引擎等）              │
│     -  执行子任务，收集结果                            │
├─────────────────────────────────────────────────────────┤
│  3.  反思层（Reflection）                              │
│     -  验证结果正确性（是否匹配问题需求、是否存在幻觉）│
│     -  检查信息完整性（是否缺失关键内容）              │
│     -  若不满足要求，重新规划并执行                    │
├─────────────────────────────────────────────────────────┤
│  4.  生成层（Generation）                              │
│     -  融合所有有效信息                                │
│     -  生成清晰、准确、可解释的最终答案                │
└─────────────────────────────────────────────────────────┘
```

### 4. 伪代码实现（体现 Agent 自主决策与反思）

```python
from openai import OpenAI
# 复用前面的Modular RAG模块（Chunking/Embedding/Retrieval/Generation）
from modular_rag_modules import ChunkingModule, EmbeddingModule, RetrievalModule, GenerationModule

llm_client = OpenAI()
client = OpenAI()

class RagAgent:
    def __init__(self, knowledge_base, tools=None):
        self.knowledge_base = knowledge_base
        self.tools = tools or []
        # 初始化RAG模块
        self.chunk_module = ChunkingModule(strategy="semantic")
        self.embedding_module = EmbeddingModule(model_name="E5-large-v2")
        self.retrieval_module = RetrievalModule(retrieval_type="hybrid")
        self.generation_module = GenerationModule(prompt_strategy="cot")
        # 对话记忆
        self.conversation_history = []

    def _planning_step(self, query):
        """规划层：拆分复杂查询，制定执行计划"""
        plan_prompt = f"""
        你是一个RAG智能体，需要处理用户查询：{query}
        请完成以下任务：
        1.  判断查询是否复杂，是否需要拆分为子查询（若简单，直接返回「无需拆分，直接检索」；若复杂，返回子查询列表）
        2.  制定执行计划（如：先检索子查询1，再检索子查询2，最后融合结果）
        对话历史：{self.conversation_history}
        """
        response = llm_client.chat.completions.create(
            model="gpt-4",  # GPT-4更适合复杂规划
            messages=[{"role": "user", "content": plan_prompt}]
        )
        return response.choices[0].message.content

    def _execution_step(self, sub_queries):
        """执行层：调用RAG模块，执行子查询"""
        sub_results = []
        for sub_q in sub_queries:
            # 调用RAG模块获取子查询结果
            chunks = self.chunk_module.run(self.knowledge_base)
            chunk_embeddings = self.embedding_module.run(chunks)
            # 写入索引
            self.retrieval_module.collection.add(
                documents=chunks,
                embeddings=chunk_embeddings,
                ids=[f"chunk_{i}" for i in range(len(chunks))]
            )
            query_embedding = self.embedding_module.run([sub_q])[0]
            retrieved_chunks = self.retrieval_module.run(query_embedding, sub_q, chunks)
            context = "\n".join(retrieved_chunks)
            sub_answer = self.generation_module.run(context, sub_q)
            sub_results.append((sub_q, sub_answer))
        return sub_results

    def _reflection_step(self, query, sub_results, candidate_answer):
        """反思层：验证答案，判断是否需要重新检索"""
        reflection_prompt = f"""
        用户查询：{query}
        子查询结果：{sub_results}
        候选答案：{candidate_answer}
        请完成以下验证：
        1.  候选答案是否准确？是否存在幻觉？
        2.  候选答案是否完整覆盖用户查询的所有需求？
        3.  若存在问题（不准确/不完整），请返回「需要重新检索」并给出优化建议；若没问题，返回「无需优化」
        """
        response = llm_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": reflection_prompt}]
        )
        reflection_result = response.choices[0].message.content
        return reflection_result

    def run(self, user_query):
        """Agentic RAG 核心流程：规划→执行→反思→生成"""
        # 1. 规划
        plan = self._planning_step(user_query)
        print("Agent 规划结果：", plan)

        # 2. 执行（简化：判断是否拆分子查询）
        if "无需拆分" in plan:
            sub_queries = [user_query]
        else:
            # 提取子查询（实际可通过结构化输出优化，如JSON）
            sub_queries = ["AI的核心分支是什么？", "AI核心分支的典型工具是什么？"]
        sub_results = self._execution_step(sub_queries)
        print("Agent 执行结果（子查询）：", sub_results)

        # 3. 生成候选答案
        sub_answers = [res[1] for res in sub_results]
        candidate_context = "\n".join(sub_answers)
        candidate_answer = self.generation_module.run(candidate_context, user_query)
        print("Agent 候选答案：", candidate_answer)

        # 4. 反思
        reflection_result = self._reflection_step(user_query, sub_results, candidate_answer)
        print("Agent 反思结果：", reflection_result)

        # 5. 最终生成（若需要重新检索，可迭代执行；此处简化为直接返回）
        if "需要重新检索" in reflection_result:
            # 重新执行（示例：调整检索策略，增大top_k）
            self.retrieval_module.top_k = 15
            sub_results = self._execution_step(sub_queries)
            sub_answers = [res[1] for res in sub_results]
            candidate_context = "\n".join(sub_answers)
            final_answer = self.generation_module.run(candidate_context, user_query)
        else:
            final_answer = candidate_answer

        # 更新对话记忆
        self.conversation_history.append({"user": user_query, "assistant": final_answer})
        return final_answer

# 测试调用：复杂查询处理
if __name__ == "__main__":
    knowledge_base = [
        "人工智能（AI）核心分支是机器学习，机器学习主流方向是深度学习。",
        "深度学习的典型工具包括TensorFlow（Google开发）、PyTorch（Meta开发），还有MXNet。"
    ]
    # 复杂查询：多需求融合
    user_query = "AI的核心分支是什么？该分支的主流方向有哪些典型工具？"
    # 初始化Agent
    rag_agent = RagAgent(knowledge_base=knowledge_base)
    final_answer = rag_agent.run(user_query)
    print("Agentic RAG 最终答案：", final_answer)
```

### 5. 优缺点与适用场景

| 特性     | 详情                                                                                                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 优点     | 1. 智能性最高：可处理超复杂查询（多跳推理、跨领域分析）<br>2. 自适应能力强：自主调整策略，无需人工干预<br>3. 功能扩展性好：支持工具调用，突破知识库边界<br>4. 多轮对话友好：保留上下文记忆，支持连续问答                        |
| 缺点     | 1. 实现复杂度极高：需整合 Agent 与 RAG，对技术团队要求高<br>2. 延迟最高：多环节迭代（规划 → 执行 → 反思）增加计算成本<br>3. 资源消耗大：依赖高性能 LLM（如 GPT-4），部署成本高<br>4. 可解释性弱：Agent 自主决策过程难以完全追溯 |
| 适用场景 | 1. 复杂多跳推理（如法律文书分析、医疗病例诊断）<br>2. 跨领域/跨知识库问答（如企业跨部门文档检索）<br>3. 专业级决策支持（如金融风控、科研文献分析）<br>4. 智能助手类应用（如个人知识管家、企业智能顾问）                         |

## 五、 四类 RAG 整体对比总结

| 类型         | 核心定位               | 智能程度 | 实现复杂度 | 延迟 | 适用场景                                       |
| ------------ | ---------------------- | -------- | ---------- | ---- | ---------------------------------------------- |
| Naive RAG    | 基础入门，概念验证     | ★☆☆☆☆    | 极低       | 低   | 简单事实问答、小型知识库、原型验证             |
| Advanced RAG | 性能提升，全流程优化   | ★★★☆☆    | 中高       | 中   | 中小型企业应用、中等复杂度问答、高精度需求场景 |
| Modular RAG  | 架构升级，企业级落地   | ★★★☆☆    | 高         | 中   | 大型企业知识库、多团队协作、长期迭代优化       |
| Agentic RAG  | 高阶智能，复杂任务处理 | ★★★★★    | 极高       | 高   | 复杂多跳推理、专业决策支持、智能助手类应用     |

### 总结

1.  从 Naive RAG 到 Advanced RAG：**性能优化**，通过全流程环节提升检索与生成质量；
2.  从 Advanced RAG 到 Modular RAG：**架构优化**，通过模块化解耦提升可维护性与扩展性；
3.  从 Modular RAG 到 Agentic RAG：**智能升级**，通过 LLM 智能体赋予系统自主决策与迭代能力；
4.  选型建议：按需选择，快速验证用 Naive RAG，企业落地用 Modular RAG，复杂任务用 Agentic RAG。
