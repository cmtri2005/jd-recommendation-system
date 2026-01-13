# 🎯 JD Recommendation System

Hệ thống AI sử dụng LangGraph và RAG để phân tích độ phù hợp giữa CV và tin tuyển dụng IT, đồng thời theo dõi xu hướng việc làm real-time.

## ✨ Tính năng chính

### 🤖 AI Job Fit Analysis
- Phân tích độ phù hợp giữa CV và Job Description (JD)
- Đánh giá kỹ năng và kinh nghiệm
- Đưa ra khuyến nghị học tập (Learning Path)
- Tóm tắt phân tích chi tiết

### 📊 Dashboard Analytics
- Theo dõi xu hướng việc làm IT
- Thống kê theo kỹ năng, vị trí, mức lương
- Biểu đồ trực quan hóa dữ liệu

### 🕷️ Job Crawler
- Thu thập dữ liệu từ TopCV, ITViec
- Xử lý real-time với Kafka + Spark
- Làm giàu dữ liệu bằng LLM

### 🔍 Vector Search
- Tìm kiếm công việc phù hợp bằng embedding
- RAG (Retrieval-Augmented Generation) cho chatbot
- ChromaDB làm vector database

## 🏗️ Kiến trúc

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Crawler   │────▶│ Kafka+Spark  │────▶│  Vector DB  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                  │
┌─────────────┐     ┌──────────────┐            │
│  Frontend   │◀───▶│ Backend API  │◀───────────┘
│  (React)    │     │   (FastAPI)  │
└─────────────┘     └──────────────┘
```

### Tech Stack

**Backend:**
- FastAPI + LangGraph (AI Agent)
- ChromaDB (Vector Database)
- AWS Bedrock / Groq (LLM)

**Data Pipeline:**
- Apache Airflow (Orchestration)
- Apache Spark (Processing)
- Kafka (Streaming)

**Frontend:**
- React + TypeScript
- TailwindCSS + shadcn/ui
- React Query + React Router

**Infrastructure:**
- Docker Compose
- PostgreSQL
- MinIO (Object Storage)

## 🚀 Cài đặt

### Yêu cầu
- Docker & Docker Compose
- Node.js 18+ (cho frontend)
- Python 3.11+ (nếu chạy local)

### Khởi động dự án

1. **Clone repository**
```bash
git clone <repo-url>
cd jd-recommendation-system
```

2. **Cấu hình environment**
```bash
cp .env_example .env
# Điền các API keys cần thiết (AWS, Groq, MinIO)
```

3. **Khởi động services**
```bash
docker-compose up -d
```

4. **Chạy frontend**
```bash
cd frontend
pnpm install
pnpm dev
```

### Truy cập ứng dụng

- **Frontend**: http://localhost:5173
- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Kafka UI**: http://localhost:9021
- **Spark Master**: http://localhost:8088

## 📁 Cấu trúc thư mục

```
.
├── apps/
│   ├── chatbot/          # FastAPI backend + LangGraph
│   ├── crawler/          # Airflow DAGs + Crawlers
│   ├── ingest_data/      # Vector DB ingestion
│   └── dashboard/        # Analytics dashboard
├── frontend/             # React SPA
└── docker-compose.yaml   # Infrastructure setup
```

## 🔧 Cấu hình

### LLM Providers
Hệ thống hỗ trợ nhiều LLM providers:
- **AWS Bedrock**: Claude 3.5 Sonnet (production)
- **Groq**: Llama 3.3 70B (development)

### Vector Database
- ChromaDB với embedding model: `amazon.titan-embed-text-v2:0`
- Persistent storage trong Docker volume

## 📝 Sử dụng

1. **Upload CV**: Tải lên file PDF/DOCX
2. **Nhập JD**: Copy/paste Job Description
3. **Phân tích**: Hệ thống AI sẽ đánh giá độ phù hợp
4. **Xem kết quả**: 
   - Điểm số phù hợp
   - Phân tích kỹ năng
   - Khuyến nghị học tập
   - Gap analysis


## 📄 License

MIT License