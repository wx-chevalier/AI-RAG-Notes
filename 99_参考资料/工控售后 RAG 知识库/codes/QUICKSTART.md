# 工控售后 RAG 知识库 - 快速复现指南

## 项目背景

这是一个面向工业软件售后场景的 RAG 知识库系统，从 1600+ 份 Word 技术文档构建而成。项目分为三个阶段：

1. **数据工程阶段**：原始文档清洗、元数据增强、图片提取与迁移
2. **POC 阶段**：核心检索引擎开发、Rerank 优化、Streamlit 原型验证
3. **MVP 阶段**：前后端分离架构、用户认证、反馈闭环

本指南帮助你快速跑通完整流程。

---

## 环境准备

### 基础要求

- Python 3.11+
- Node.js 18+ (MVP 前端)
- Docker (MinIO、Supabase)

### API Key 配置

在运行前需要配置项目根目录的 env 文件

---

## 阶段一：数据工程

脚本位于 `scripts_archive/` 目录，按编号顺序执行。

### 核心脚本说明

| 脚本                            | 功能             | 输入                     | 输出                                           |
| :------------------------------ | :--------------- | :----------------------- | :--------------------------------------------- |
| `01_kb_analysis.py`             | 原始数据摸底     | 原始文档目录             | 目录树报告                                     |
| `02_noise_sampling.py`          | 噪音抽样分析     | 原始文档                 | 噪音模式清单                                   |
| `04_full_cleaning_pipeline.py`  | **全量清洗**     | 原始文档目录             | Clean Markdown + Clean DOCX + metadata.json    |
| `06_batch_enrichment.py`        | LLM 元数据增强   | metadata.json            | 带 summary/keywords/questions 的 metadata.json |
| `07_vector_ingestion.py`        | 向量化入库       | metadata.json + Markdown | ChromaDB 向量数据库                            |
| `08_migrate_images_to_minio.py` | 图片迁移到 MinIO | images/ 目录             | MinIO 存储 + image_url_mapping.json            |

### 快速复现步骤

```bash
# 1. 进入脚本目录
cd scripts_archive

# 2. 安装依赖
pip install python-docx minio google-generativeai chromadb langchain

# 3. 准备示例数据
# 5 份示例 Word 文档在 sample_data/ 目录中
# 脚本已配置为相对路径，无需手动修改

# 4. 运行清洗
python 04_full_cleaning_pipeline.py

# 5. 运行元数据增强（需要配置 .env 中的 API Key）
python 06_batch_enrichment.py

# 6. 运行向量化入库
python 07_vector_ingestion.py
```

### 可选步骤

- `01_kb_analysis.py`：如果你想先了解原始数据分布
- `02_noise_sampling.py`：如果你想分析新数据集的噪音模式
- `08_migrate_images_to_minio.py`：如果需要图片服务（需要先启动 MinIO）

---

## 阶段二：POC

POC 是一个 Streamlit 原型，用于验证检索效果。代码位于 `POC/` 目录。

### 核心文件说明

| 文件                  | 功能                                                                   |
| :-------------------- | :--------------------------------------------------------------------- |
| `rag_engine.py`       | **核心检索引擎**：向量检索 + Rerank + Parent-Child 连坐召回 + LLM 生成 |
| `app_poc.py`          | Streamlit 前端界面                                                     |
| `supabase_client.py`  | 数据库客户端（用户认证、历史记录、反馈）                               |
| `full_schema.sql`     | Supabase 数据库 Schema                                                 |
| `golden_dataset.json` | 评测数据集（30 条测试用例）                                            |

### 辅助/测试脚本

| 文件                          | 功能             | 是否需要运行                 |
| :---------------------------- | :--------------- | :--------------------------- |
| `debug_retrieve.py`           | 单条查询调试     | 可选，用于排查检索问题       |
| `evaluate_retrieval.py`       | 批量评测召回率   | 可选，用于评估效果           |
| `test_multiturn.py`           | 多轮对话测试     | 可选，用于验证 Query Rewrite |
| `test_supabase_connection.py` | 测试数据库连接   | 可选，首次配置时使用         |
| `download_from_modelscope.py` | 下载 Rerank 模型 | 首次运行需要执行             |

### 快速复现步骤

```bash
# 1. 进入 POC 目录
cd POC

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载 Rerank 模型（首次需要，约 2GB）
# 模型从 ModelScope（阿里云镜像）下载，国内网络可直接访问
pip install modelscope
python download_from_modelscope.py

# 5. 配置 Supabase（可选，跳过则无用户系统）
# 在 Supabase 控制台执行 full_schema.sql

# 6. 启动 POC
streamlit run app_poc.py

# 7. 访问 http://localhost:8501
```

---

## 阶段三：MVP

MVP 是前后端分离架构，提供更好的交互体验。代码位于 `MVP/` 目录。

### 目录结构

```
MVP/
├── backend/
│   ├── main.py          # FastAPI 后端，复用 POC 的 rag_engine
│   └── requirements.txt
├── frontend/            # Next.js 前端
├── start.sh             # 一键启动脚本
└── stop.sh              # 停止脚本
```

### 快速复现步骤

```bash
# 1. 确保 POC 阶段的向量数据库已构建

# 2. 进入 MVP 目录
cd MVP

# 3. 一键启动（后端 + 前端）
./start.sh

# 4. 或者分别启动

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 启动前端（新终端）
cd frontend
npm install
npm run dev

# 5. 访问 http://localhost:3000
```

---

## 基础设施

### MinIO（图片服务）

```bash
# 使用 Docker 启动
docker run -d \
  -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=password123" \
  minio/minio server /data --console-address ":9001"

# 运行图片迁移脚本
python scripts_archive/08_migrate_images_to_minio.py
```

### Supabase（用户系统 + 数据持久化）

推荐使用 Supabase Cloud 快速开始：

1. 注册 supabase.com
2. 创建项目，获取 URL 和 API Key
3. 在 SQL Editor 中执行 `POC/full_schema.sql`
4. 在代码中配置连接信息

---

## 常见问题

### Q: ChromaDB 报错 "Collection not found"

确保已运行 `07_vector_ingestion.py` 完成向量化入库。

### Q: Rerank 模型加载很慢

首次加载需要从 ModelScope 下载约 2GB 模型文件，之后会缓存到本地。

### Q: 图片不显示

检查 MinIO 是否启动，以及 `image_url_mapping.json` 是否生成。

### Q: 多轮对话上下文丢失

确认 Supabase 已配置并连接成功，历史记录需要数据库支持。

---
