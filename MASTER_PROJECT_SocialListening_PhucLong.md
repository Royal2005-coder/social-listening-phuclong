# 🎯 MASTER PROJECT DOCUMENT
# SOCIAL LISTENING VỚI HỌC MÁY: PHÂN TÍCH PHẢN ỨNG KHÁCH HÀNG
# VÀ ĐỀ XUẤT CHIẾN LƯỢC NỘI DUNG SỐ CHO PHÚC LONG COFFEE & TEA

> **Môn học**: Phân tích Marketing số | **Mã LHP**: 253BIM502601
> **GVHD**: ThS. Văn Đức Sơn Hà | **Trường**: ĐH Kinh tế — Luật (UEL)
> **Nhóm**: Gia (PM/DevOps), Hân, Khải, Hiển | **Timeline**: 5 tuần (12/05 → 15/06/2026)
> **Ngày tạo**: 12/05/2026 | **Phiên bản**: v1.0

---

## 📋 MỤC LỤC MASTER DOCUMENT

1. [TỔNG QUAN DỰ ÁN](#1-tổng-quan-dự-án)
2. [DATA CRAWL — KẾT QUẢ HOÀN TẤT](#2-data-crawl)
3. [KIẾN TRÚC KỸ THUẬT](#3-kiến-trúc-kỹ-thuật)
4. [PHASE 1 — BATCH ANALYSIS](#4-phase-1)
5. [PHASE 2 — NEAR REAL-TIME PLATFORM](#5-phase-2)
6. [MỤC LỤC BÁO CÁO CHÍNH THỨC](#6-mục-lục-báo-cáo)
7. [PHÂN CÔNG & TIMELINE](#7-phân-công)
8. [FIRST INSIGHTS TỪ DATA](#8-first-insights)
9. [TECH STACK & TOOLS](#9-tech-stack)
10. [REFERENCE & LINKS](#10-reference)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Đề tài
**"Ứng dụng Social Listening kết hợp Học máy: Phân tích phản ứng khách hàng
và đề xuất chiến lược nội dung số cho Phúc Long Coffee & Tea"**

### 1.2 Scope 2 Phases

```
PHASE 1 (Tuần 1-4): "HIỂU" — Phân tích Batch 6 tháng chiến dịch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Crawl 5,351 records (3 brands × 2 platforms)
→ EDA: 80+ biểu đồ, Viral Paradox, Golden Hours
→ ML: K-Means, Random Forest, Linear Regression
→ NLP: PhoBERT Sentiment 4,751 comments
→ Output: 5 RQ trả lời + 3 chiến lược đề xuất + báo cáo 50-70 trang

PHASE 2 (Tuần 5): "HÀNH ĐỘNG" — Near Real-time Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ BI Dashboard (Metabase): sl.royalai.dev — 12+ cards live data
→ MCP Server: mcp-sl.royalai.dev — 5 tools AI query (SQL Guard)
→ 3 AI Skill Agents: Monitor, Sentiment Analyzer, Content Advisor
→ Data Lakehouse: PostgreSQL Bronze/Silver/Gold + scheduled crawl
→ Output: Hệ thống tự vận hành, chạy hàng tháng/quý
```

### 1.3 Câu hỏi nghiên cứu (RQ1-5)

| RQ | Câu hỏi | Phase | Chương |
|----|---------|-------|--------|
| RQ1 | Mô hình tương tác: thụ động hay tương tác sâu? | P1 | Ch.3, 7 |
| RQ2 | Khung giờ đăng bài ≠ khung giờ ER cao nhất? | P1 | Ch.3, 5 |
| RQ3 | Yếu tố nào ảnh hưởng Engagement Rate? | P1 | Ch.4 |
| RQ4 | Sentiment thay đổi thế nào sau campaign? | P1 | Ch.6 |
| RQ5 | Phúc Long khác đối thủ ở điểm nào? | P1 | Ch.4, 5, 7 |

### 1.4 Thành viên & Vai trò

| MSSV | Họ tên | Vai trò | Chuyên môn |
|------|--------|---------|------------|
| K234060689 | Nguyễn Tô Hoàng Gia | Nhóm trưởng | PM, DevOps, Server, ML Pipeline, Crawler |
| K234060691 | Nguyễn Phan Ngọc Hân | Thành viên | Facebook Analysis, Report Writing |
| K234060700 | Nguyễn Như Khải | Thành viên | TikTok EDA, Visualization, Slide |
| K234060692 | Võ Minh Hiển | Thành viên | NLP/Sentiment, Report, Validation |

---

## 2. DATA CRAWL — KẾT QUẢ HOÀN TẤT ✅

### 2.1 Tổng quan dữ liệu (Crawl date: 12/05/2026)

| Table | Total | Phúc Long | Highlands | Katinat |
|-------|-------|-----------|-----------|---------|
| **raw.tiktok_videos** | **300** | 100 ✅ | 100 ✅ | 100 ✅ |
| **raw.facebook_posts** | **300** | 100 ✅ | 100 ✅ | 100 ✅ |
| **raw.tiktok_comments** | **2,695** | 977 ✅ | 1,169 ✅ | 549 ✅ |
| **raw.facebook_comments** | **2,056** | 554 ✅ | 744 ✅ | 758 ✅ |
| **TOTAL** | **5,351** | 1,731 | 2,113 | 1,507 |
| **Total Comments** | **4,751** | 1,531 | 1,913 | 1,307 |

### 2.2 Phạm vi thời gian thực tế (Bảng 2.x cho báo cáo)

| Brand | Platform | Oldest | Newest | Span | N | Posts/tuần |
|-------|----------|--------|--------|------|---|-----------|
| Phúc Long | TikTok | 2025-12-24 | 2026-05-12 | 139 ngày | 100 | **5.0** |
| Phúc Long | Facebook | 2026-02-27 | 2026-05-12 | 74 ngày | 100 | 9.5 |
| Highlands | TikTok | 2024-12-21 | 2026-05-11 | 506 ngày | 100 | 1.4 |
| Highlands | Facebook | 2026-03-06 | 2026-05-12 | 67 ngày | 100 | 10.4 |
| Katinat | TikTok | 2025-08-02 | 2026-05-12 | 283 ngày | 100 | 2.5 |
| Katinat | Facebook | 2026-03-28 | 2026-05-12 | 45 ngày | 100 | **15.6** |

**OVERALL TIMESPAN**: 2024-12-21 → 2026-05-12

### 2.3 Brand Summary (từ aggregate views)

| Brand | Platform | Avg Views | Avg Likes | Avg Comments | Avg Shares |
|-------|----------|-----------|-----------|--------------|------------|
| Highlands | TikTok | **4,929,318** 🏆 | 2,598 | 49 | 337 |
| Katinat | TikTok | 206,618 | 1,361 | 20 | 216 |
| Phúc Long | TikTok | 127,310 ⚠️ | 796 | 17 | 51 |
| Phúc Long | Facebook | — | **1,048** 🏆 | 78 | 45 |
| Katinat | Facebook | — | 878 | 71 | 28 |
| Highlands | Facebook | — | 625 | 121 | 31 |

### 2.4 Apify Accounts sử dụng

| Account | Token (prefix) | Dùng cho | Status |
|---------|---------------|----------|--------|
| Gia (Account #1) | `apify_api_2QsC...` | TikTok 300 vid + FB 300 posts + PL comments | Hết quota |
| Team #1 (Account #2) | `apify_api_qrv3...` | HL + KT TikTok comments + HL FB comments | Hết quota |
| Team #2 (Account #3) | `apify_api_IFi0...` | KT Facebook comments (bổ sung) | Còn dư |

### 2.5 Exported CSV Files

| File | Rows | Size |
|------|------|------|
| tiktok_videos.csv | 300 | 398 KB |
| facebook_posts.csv | 300 | 537 KB |
| tiktok_comments.csv | 2,695 | 866 KB |
| facebook_comments.csv | 2,056 | 824 KB |
| **Location**: `C:\SocialListening\data\raw\` |

---

## 3. KIẾN TRÚC KỸ THUẬT

### 3.1 Server Infrastructure (PC Gia)

```
Hardware:
  CPU:    Intel i7-14700 (20 cores / 28 threads)
  RAM:    16GB DDR5-5600
  GPU:    NVIDIA RTX 4060 (8GB VRAM)
  Disk:   512GB NVMe SSD
  Net:    1Gbps Ethernet + Tailscale VPN
  OS:     Windows 11 Pro

Software:
  Docker Desktop v29.4.1 + Compose v5.1.3
  Python 3.x + venv (crawler)
  VMware Workstation (docker VM)
```

### 3.2 Docker Compose Stack

```yaml
# C:\SocialListening\docker-compose.yml
Containers (3 active):
  sl-postgres     :5434  PostgreSQL 16-alpine  (512M RAM)  ✅ healthy
  sl-metabase     :3003  Metabase v0.54.3      (1G RAM)    ✅ healthy
  sl-metabase-pg  :5435  PostgreSQL 16-alpine  (256M RAM)  ✅ healthy
  # Phase 2:
  # cf-tunnel-sl         Cloudflare Tunnel     (128M RAM)
  # sl-mcp        :8790  MCP Server            (512M RAM)
```

### 3.3 PostgreSQL Database Schema

```
Database: social_listening (port 5434)
Users: sl_admin (write), sl_reader (read-only)

Schemas (5):
  raw/        → 4 tables (tiktok_videos, facebook_posts, tiktok_comments, facebook_comments)
  clean/      → 3 tables (tiktok, facebook, comments)
  features/   → 1 table (engineered) + 3 views (brand_summary, posting_frequency, comments_summary)
  sentiment/  → 2 tables (results, validation)
  ml/         → 3 tables (model_results, feature_importance, clusters)

Total: 13 tables + 3 views, 7 indexes
```

### 3.4 Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     DATA FLOW PIPELINE                           │
│                                                                  │
│  PHASE 1 (Batch):                                                │
│                                                                  │
│  Apify Cloud ──→ Python Crawler ──→ PostgreSQL (raw.*)           │
│  (3 accounts)    (crawler_*.py)      │                            │
│                                      ├──→ Preprocessing Script   │
│                                      │    → clean.* + features.* │
│                                      │                            │
│                                      ├──→ Export CSV              │
│                                      │    → Google Drive          │
│                                      │    → Google Colab (EDA)    │
│                                      │                            │
│                                      └──→ Metabase BI            │
│                                           (sl.royalai.dev)       │
│                                                                  │
│  PHASE 2 (Near Real-time):                                       │
│                                                                  │
│  Scheduled Crawl ──→ PostgreSQL ──→ Auto PhoBERT ──→ BI Dashboard│
│  (cron daily)        (Bronze/      (sentiment.*)    (live update) │
│                       Silver/                                     │
│                       Gold)        ──→ MCP Server                │
│                                       (AI query)                 │
│                                                                  │
│                                    ──→ Skill Agents              │
│                                       (Monitor/Analyze/Advise)   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.5 Domain Architecture (Cloudflare Tunnel → royalai.dev)

| Domain | Service | Port | Phase | Status |
|--------|---------|------|-------|--------|
| sl.royalai.dev | Metabase BI Dashboard | 3003 | P1-P2 | 🔵 Pending tunnel |
| mcp-sl.royalai.dev | MCP AI Server | 8790 | P2 | 🔵 Tuần 5 |

---

## 4. PHASE 1 — BATCH ANALYSIS (Tuần 1-4)

### 4.1 Phase 1A — Thu thập & Tiền xử lý (Tuần 1: 12-18/05)

#### Status: ✅ CRAWL DONE | 🔵 PREPROCESSING TODO

**Đã hoàn thành:**
- [x] Docker Compose deploy (3 containers healthy)
- [x] PostgreSQL 13 tables + 3 views + 7 indexes
- [x] Crawl TikTok 300 videos (3 brands × 100)
- [x] Crawl Facebook 300 posts (3 brands × 100)
- [x] Crawl TikTok Comments 2,695 (PL:977, HL:1169, KT:549)
- [x] Crawl Facebook Comments 2,056 (PL:554, HL:744, KT:758)
- [x] Export 4 CSV files
- [x] Create 3 aggregate views

**Còn cần làm:**
- [ ] Preprocessing 8 bước → clean.* tables
- [ ] Feature Engineering 12 biến → features.engineered
- [ ] Text preprocessing comments (underthesea)
- [ ] Upload CSV → Google Drive
- [ ] Tạo Colab notebook template
- [ ] Metabase kết nối DB + Dashboard v1
- [ ] Viết Phần 1 + Chương 2 báo cáo

#### Preprocessing Pipeline (8 bước)

```python
# Chạy trên Google Colab hoặc local
# Input: 4 CSV files từ Google Drive
# Output: clean DataFrames + features

Step 1: Load & Merge (pd.read_csv × 4 files)
Step 2: Missing Values (drop text=null, keep views=0)
Step 3: Dedup (video_id/post_id unique)
Step 4: Normalize dtypes (datetime, int, float)
Step 5: Outlier Detection (IQR method → is_outlier flag)
Step 6: Feature Engineering (12 biến mới):
  - engagement_rate = (likes+comments+shares)/views × 100
  - total_engagement = likes + comments + shares
  - posting_hour = extract hour from publish_time
  - time_category = sáng/chiều/tối/khuya
  - day_of_week = Mon-Sun
  - hashtag_count = count hashtags
  - content_type = product/promo/lifestyle/ugc/collab
  - has_music = boolean
  - caption_length = len(video_desc)
  - days_since_published = crawl_date - publish_time
  - views_count (copy)
  - duration_seconds (copy)
Step 7: Text Preprocessing (underthesea word_tokenize)
Step 8: Save clean CSV + insert PostgreSQL clean.*
```

### 4.2 Phase 1B — EDA TikTok từng brand (Tuần 2: 19-25/05)

#### Mỗi brand × 6 nhóm phân tích = 18 sections, 45+ biểu đồ

```
Cho mỗi brand (Phúc Long, Highlands, Katinat):

1. Phân phối chỉ số hiệu suất (Histogram + KDE + Boxplot)
   → views, likes, comments, shares, ER, duration
   → Phát hiện right-skewed, hit-driven pattern
   → Xác định baseline performance (IQR range)

2. Phân tích hashtag (Top 10 + phân nhóm 3 tầng)
   → Branded tags / Niche tags / Discovery tags
   → Chiến lược hashtag riêng mỗi brand

3. Mô hình tương tác: Views × ER Scatter (→ RQ1)
   → Phát hiện "Nghịch lý Lan truyền" (Viral Paradox)
   → Views cao + ER thấp = audience "lạnh", tiêu thụ thụ động
   → Views thấp + ER cao = tương tác sâu, community engagement

4. Tương quan Duration × ER
   → Sweet spot thời lượng video
   → Bimodal = chiến lược 2 mũi nhọn?

5. Ma trận tương quan Pearson
   → Biến nào drive engagement?
   → Comments độc lập hay phụ thuộc views?

6. Khung giờ đăng × Avg ER (→ RQ2)
   → Golden hours TikTok
   → Posting frequency ≠ ER cao (mismatch)
```

#### Pattern viết insight (học từ đồ án mẫu DOL English):
```
"Biểu đồ cho thấy [MÔ TẢ dữ liệu]
 → Điều này phản ánh [PHÂN TÍCH nguyên nhân]
 → Hàm ý chiến lược: [ĐỀ XUẤT marketing actionable]"
```

#### Brand Naming Strategy:
- **Phúc Long** = "Người Giữ Di Sản" (Heritage Guardian)
- **Highlands** = "Người Phổ Cập" (Mass Connector)
- **Katinat** = "Người Tạo Thẩm Mỹ" (Aesthetic Creator)

### 4.3 Phase 1C — Cross-brand + ML (Tuần 3: 26/05-01/06)

#### ML Models Pipeline

```python
# 1. K-Means Clustering
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
# StandardScaler → Elbow + Silhouette → k tối ưu
# Clusters: Low / Medium / High performance
# PCA 2D visualization
# → "Phúc Long nằm ở cluster nào?"

# 2. Multiple Linear Regression
import statsmodels.api as sm
# Target: engagement_rate
# Features: duration, hashtag_count, posting_hour, content_type, ...
# OLS fit → p-value, R², Adjusted R², VIF
# → "Yếu tố nào ảnh hưởng ER có ý nghĩa thống kê?"

# 3. Random Forest Regressor
from sklearn.ensemble import RandomForestRegressor
# n_estimators=100, 5-fold CV, 80/20 split
# Feature Importance plot
# MAE, RMSE, R² comparison với LR
# → "Top 3 yếu tố quan trọng nhất"
```

### 4.4 Phase 1D — Sentiment + Insight (Tuần 4: 02-08/06)

#### PhoBERT Pipeline

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_name = "wonrax/phobert-base-vietnamese-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Input: 4,751 comments (clean, Vietnamese only)
# Output: sentiment_label (Pos/Neg/Neu), sentiment_score (-1→1)
# Runtime: ~10 min on Colab T4 GPU or local RTX 4060

# Validation: 200 comments × 2 annotators → Cohen's Kappa
```

---

## 5. PHASE 2 — NEAR REAL-TIME PLATFORM (Tuần 5: 09-15/06)

### 5.1 Architecture (Mapping từ BĐS Lakehouse)

```
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: NEAR REAL-TIME ARCHITECTURE               │
│                                                                  │
│  ┌──────────┐    ┌──────────┐                                   │
│  │ TikTok   │    │ Facebook │                                   │
│  └────┬─────┘    └────┬─────┘                                   │
│       │               │                                          │
│       ▼               ▼                                          │
│  ┌─────────────────────────────────┐                            │
│  │ CRAWLER SCHEDULER (cron)        │                            │
│  │ • Daily: new posts (incremental)│                            │
│  │ • Weekly: comments top engage   │                            │
│  │ • Monthly: full refresh 100/br  │                            │
│  └───────────────┬─────────────────┘                            │
│                  │                                               │
│                  ▼                                               │
│  ┌─────────────────────────────────┐                            │
│  │ PostgreSQL DATA LAKEHOUSE       │                            │
│  │                                  │                            │
│  │ Bronze: raw.*     (raw data)    │                            │
│  │ Silver: clean.*   (cleaned)     │                            │
│  │ Gold:   features.* sentiment.*  │                            │
│  │         ml.*      (analytics)   │                            │
│  └──┬──────────┬──────────┬────────┘                            │
│     │          │          │                                      │
│     ▼          ▼          ▼                                      │
│  ┌──────┐  ┌──────┐  ┌──────────┐                              │
│  │  BI  │  │ MCP  │  │  SKILL   │                              │
│  │BOARD │  │SERVER│  │ AGENTS   │                              │
│  │      │  │      │  │          │                              │
│  │12+   │  │5 SQL │  │Monitor   │                              │
│  │cards │  │Guard │  │Sentiment │                              │
│  │live  │  │tools │  │Advisor   │                              │
│  └──────┘  └──────┘  └──────────┘                              │
│  sl.royalai  mcp-sl.                                            │
│  .dev        royalai.dev                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 BI Dashboard (Metabase — sl.royalai.dev)

```
Dashboard Layout (12+ cards):

┌──────────┬──────────┬──────────┬──────────┐
│ Total    │ Avg ER   │ Sentiment│ Data     │
│ Content  │ Overall  │ Score    │ Freshness│
│ [scalar] │ [scalar] │ [scalar] │ [scalar] │
├──────────┴──────────┼──────────┴──────────┤
│ ER by Brand         │ Sentiment by Brand  │
│ [grouped bar]       │ [stacked bar]       │
├─────────────────────┼─────────────────────┤
│ Engagement Trend    │ Sentiment Trend     │
│ [time-series]       │ [time-series]       │
├─────────────────────┼─────────────────────┤
│ Top 10 Content      │ Platform Compare    │
│ [table]             │ [grouped bar]       │
├─────────────────────┴─────────────────────┤
│ Content Cluster Map (K-Means PCA 2D)      │
│ [scatter]                                  │
└───────────────────────────────────────────┘
```

### 5.3 MCP Server (mcp-sl.royalai.dev)

```python
# Pattern: trino-mcp từ dự án BĐS Lakehouse
# SQL Guard: read-only (SELECT only, block INSERT/UPDATE/DELETE)

Tools (5):
1. query_engagement(brand, platform)     → ER stats
2. query_sentiment(brand, date_range)    → Pos/Neg/Neu breakdown
3. compare_brands(metric)                → Comparison table
4. get_top_content(brand, n=10)          → Top performing content
5. search_comments(keyword, sentiment)   → Full-text + sentiment filter

# Access: Claude Desktop / OpenCode → mcp-sl.royalai.dev
# Demo: "So sánh ER Phúc Long vs Highlands?" → AI trả lời từ data
```

### 5.4 Skill Agents (3 agents)

```
Agent 1: Social Listening Monitor
  Trigger: Daily cron
  Action:  Apify → new posts → PostgreSQL → alert if spike
  Value:   Phát hiện khủng hoảng truyền thông <24h

Agent 2: Sentiment Analyzer
  Trigger: New comments batch (>50)
  Action:  PhoBERT inference → sentiment.results → dashboard update
  Value:   Sentiment luôn cập nhật, không cần manual

Agent 3: Content Strategy Advisor
  Trigger: On-demand (MCP tool call)
  Action:  LLM reasoning over Phase 1 insights + live data
  Output:  Content suggestions, posting time, hashtag recommendations
  Value:   Data-driven content planning thay vì cảm tính
```

---

## 6. MỤC LỤC BÁO CÁO CHÍNH THỨC

### PHẦN MỞ ĐẦU
- Lời cảm ơn
- Lời cam đoan
- Lời mở đầu
- Danh mục bảng biểu | Danh mục hình vẽ | Danh mục từ viết tắt

### PHẦN 1. LÝ DO CHỌN ĐỀ TÀI
1. Bối cảnh thị trường và vấn đề nghiên cứu
   - 1.1. Tổng quan TikTok và Facebook tại Việt Nam
   - 1.2. Xu hướng truyền thông số trong ngành F&B
   - 1.3. Social Listening — Lắng nghe khách hàng bằng dữ liệu
2. Lý do lựa chọn thương hiệu phân tích
   - 2.1. Phúc Long Coffee & Tea — Thương hiệu nghiên cứu chính
   - 2.2. Highlands Coffee — Thương hiệu cạnh tranh (1)
   - 2.3. Katinat Coffee & Tea House — Thương hiệu cạnh tranh (2)
   - 2.4. Bảng tổng hợp so sánh ba thương hiệu
3. Hiệu quả hiện diện trên nền tảng số
   - 3.1. Kết quả nghiên cứu sơ bộ trên TikTok
   - 3.2. Kết quả nghiên cứu sơ bộ trên Facebook
4. Mục tiêu phân tích
5. Câu hỏi nghiên cứu (RQ1 – RQ5)
6. Giới hạn nghiên cứu

### CHƯƠNG 2. THU THẬP VÀ TIỀN XỬ LÝ DỮ LIỆU
1. Nhận diện yêu cầu dữ liệu và quy mô
2. Kiến trúc hạ tầng dữ liệu
   - 2.1. Tổng quan hệ thống (Docker Compose, PostgreSQL 5 schemas)
   - 2.2. Sơ đồ luồng dữ liệu: Apify → PostgreSQL → Metabase BI
   - 2.3. Chiến lược crawler đa tầng (Multi-Engine Waterfall)
3. Quy trình thu thập dữ liệu
   - 3.1–3.5 (TikTok, Facebook, Comments, Backup tools, Lưu trữ)
4. Kiểm định chất lượng dữ liệu sau thu thập
5. Quy trình tiền xử lý dữ liệu
   - 5.1–5.5 (Merge, Clean, Outlier IQR, Feature Eng 12 biến, Save)

### CHƯƠNG 3. PHÂN TÍCH DỮ LIỆU TIKTOK TỪNG THƯƠNG HIỆU
1. Phúc Long (6 mục: histogram, hashtag, Views×ER, duration, correlation, posting time)
2. Highlands (6 mục tương tự)
3. Katinat (6 mục tương tự)

### CHƯƠNG 4. SO SÁNH CHIẾN LƯỢC NỘI DUNG
1. So sánh hiệu suất tổng quan
2. Đối chiếu hashtag
3. "Nghịch lý Lan truyền" (Viral Paradox)
4. K-Means Clustering
5. Multiple Linear Regression (OLS, p-value, R², VIF)
6. Random Forest Feature Importance (RQ3)

### CHƯƠNG 5. PHÂN TÍCH PHÚC LONG TRÊN FACEBOOK
1. Thu thập và tiền xử lý FB
2. Phân tích dữ liệu FB (6 mục)
3. So sánh FB giữa 3 brands
4. So sánh đa nền tảng TikTok ↔ Facebook

### CHƯƠNG 6. PHÂN TÍCH CẢM XÚC (SENTIMENT ANALYSIS)
1. PhoBERT pipeline
2. Tiền xử lý text tiếng Việt (3 sub)
3. Kết quả sentiment tổng thể (3 sub)
4. Before/After campaign (4 sub: RQ4)
5. Word Cloud (3 sub)
6. Kiểm định PhoBERT accuracy (4 sub: validation, Kappa, F1, confusion)

### CHƯƠNG 7. INSIGHT TỔNG HỢP
1. Đánh giá tổng quan | 2. Cross-platform | 3. Điểm mạnh PL
4. Điểm yếu + cơ hội | 5. Bài học đối thủ | 6. A/B Testing hypotheses

### CHƯƠNG 8. ĐỀ XUẤT CHIẾN LƯỢC
1. CL Tăng cường Tương tác Sâu (RQ1)
2. CL Tối ưu Thời điểm & Tần suất (RQ2)
3. CL Tối ưu Nội dung dựa trên Dữ liệu (RQ3)
4. Chiến dịch truyền thông cụ thể (RQ4)
5. AI Agent + MCP Server (Hướng phát triển — Phase 2)

### KẾT LUẬN + TÀI LIỆU THAM KHẢO + PHỤ LỤC (A-F)

---

## 7. PHÂN CÔNG & TIMELINE

### Tuần 1 (12-18/05) — Thu thập & Tiền xử lý

| Task | Người | Deadline | Status |
|------|-------|----------|--------|
| Server Platform (Docker, PG, Metabase) | Gia | 14/05 | ✅ DONE |
| Crawl 5,351 records (3 accounts Apify) | Gia | 16/05 | ✅ DONE |
| Export 4 CSV files | Gia | 16/05 | ✅ DONE |
| Preprocessing + Feature Engineering | Gia | 18/05 | 🔵 TODO |
| Upload Drive + Colab template | Gia | 18/05 | 🔵 TODO |
| Metabase Dashboard v1 | Gia | 18/05 | 🔵 TODO |
| Viết Phần 1 + Chương 2 | Hân | 18/05 | 🔵 TODO |

### Tuần 2 (19-25/05) — EDA TikTok

| Task | Người | Deadline |
|------|-------|----------|
| EDA Phúc Long TikTok (15+ charts) | Khải | 22/05 |
| EDA Highlands TikTok (15+ charts) | Hân | 22/05 |
| EDA Katinat TikTok (15+ charts) | Hiển | 22/05 |
| Viết Chương 3 (45+ charts) | Khải | 25/05 |
| Server maintain + team support | Gia | 25/05 |

### Tuần 3 (26/05-01/06) — Cross-brand + ML + Facebook

| Task | Người | Deadline |
|------|-------|----------|
| ML Pipeline (LR + RF + K-Means) | Gia | 31/05 |
| Cross-brand comparison (10+ charts) | Khải | 28/05 |
| Facebook EDA (20+ charts) | Hân | 31/05 |
| Viết Chương 4 + 5 | Hiển | 01/06 |

### Tuần 4 (02-08/06) — Sentiment + Insight

| Task | Người | Deadline |
|------|-------|----------|
| PhoBERT Pipeline (4,751 comments) | Gia | 04/06 |
| Before/After + Time-series | Hân | 06/06 |
| Word Cloud + Sentiment Viz | Khải | 06/06 |
| Validation 200 cmt + Viết Ch.6-7 | Hiển | 08/06 |

### Tuần 5 (09-15/06) — Phase 2 + Hoàn thiện

| Task | Người | Deadline |
|------|-------|----------|
| MCP Server + Metabase Final Dashboard | Gia | 12/06 |
| Viết Ch.8 + Kết luận | Hiển | 12/06 |
| Format báo cáo hoàn chỉnh (Word+PDF) | Hân | 13/06 |
| Slide 15-20 trang + Dry-run | Khải | 14/06 |
| **FINAL SUBMISSION** | **Gia** | **15/06** |

---

## 8. FIRST INSIGHTS TỪ DATA

### 8.1 Phát hiện quan trọng nhất (trước EDA)

```
🔴 VẤN ĐỀ CỐT LÕI:
   Phúc Long đăng TikTok GẤP 3.5 LẦN Highlands (5.0 vs 1.4 vid/tuần)
   NHƯNG avg views chỉ bằng 1/39 (127K vs 4.9M)
   → QUANTITY ≠ QUALITY
   → Đây chính là câu hỏi trung tâm của đề tài

🟢 ĐIỂM SÁNG:
   Phúc Long MẠNH NHẤT trên Facebook (avg likes = 1,048, cao nhất 3 brands)
   → Cross-platform strength: TikTok yếu nhưng Facebook mạnh
   → Gợi ý: tận dụng thế mạnh FB, cải thiện TikTok

🟡 INSIGHT TẦN SUẤT:
   Katinat Facebook đăng DÀY NHẤT (15.6 posts/tuần!)
   Highlands TikTok đăng ÍT NHẤT (1.4 vid/tuần) nhưng VIRAL NHẤT
   → "Less is More" cho TikTok?
```

### 8.2 Giả thuyết cần kiểm chứng (EDA Tuần 2-3)

1. Highlands views cao nhưng ER có cao không? → Viral Paradox?
2. Phúc Long đăng nhiều → ER có bị pha loãng? → Diminishing returns?
3. Katinat aesthetic content → ER cao hơn product content?
4. Khung giờ đăng có mismatch với golden hours?
5. Duration sweet spot khác nhau giữa 3 brands?

---

## 9. TECH STACK & TOOLS

### Phase 1 Tools

| Category | Tool | Version | Purpose |
|----------|------|---------|---------|
| Crawl | Apify Cloud | SaaS | Primary crawler (3 accounts) |
| Crawl | clockworks/tiktok-scraper | Latest | TikTok videos + comments |
| Crawl | apify/facebook-posts-scraper | Latest | Facebook posts + comments |
| Storage | PostgreSQL | 16-alpine | Main database (5 schemas) |
| BI | Metabase | v0.54.3 | Dashboard visualization |
| Analysis | Google Colab | Free | Python notebooks (team) |
| Analysis | Pandas | 2.x | Data manipulation |
| Viz | Matplotlib + Seaborn | Latest | Charts (80+) |
| ML | Scikit-learn | 1.3+ | LR, RF, K-Means |
| ML | statsmodels | 0.14+ | OLS, p-value, VIF |
| NLP | PhoBERT | wonrax | Vietnamese sentiment |
| NLP | underthesea | 6.x | Word segmentation |
| NLP | WordCloud | 1.9+ | Pos/Neg word clouds |
| Infra | Docker Desktop | v29.4.1 | Container runtime |
| Infra | Docker Compose | v5.1.3 | Service orchestration |

### Phase 2 Tools (additional)

| Category | Tool | Purpose |
|----------|------|---------|
| Tunnel | Cloudflare Tunnel | sl.royalai.dev, mcp-sl.royalai.dev |
| MCP | FastMCP / custom | AI query server (SQL Guard) |
| Agent | Python scripts | 3 skill agents (cron-based) |

---

## 10. REFERENCE & LINKS

### Project Files

| File | Location | Description |
|------|----------|-------------|
| docker-compose.yml | C:\SocialListening\ | Docker stack definition |
| 01-create-schemas.sql | C:\SocialListening\init-db\ | DB schema init |
| crawler_tiktok.py | C:\SocialListening\crawler\ | TikTok video crawler |
| crawler_facebook.py | C:\SocialListening\crawler\ | Facebook post crawler |
| crawler_comments.py | C:\SocialListening\crawler\ | Comments crawler |
| crawl_remaining.py | C:\SocialListening\crawler\ | HL+KT comments (account #2) |
| crawl_katinat_fb_comments.py | C:\SocialListening\crawler\ | KT FB comments (account #3) |
| tiktok_videos.csv | C:\SocialListening\data\raw\ | 300 TikTok videos |
| facebook_posts.csv | C:\SocialListening\data\raw\ | 300 Facebook posts |
| tiktok_comments.csv | C:\SocialListening\data\raw\ | 2,695 TikTok comments |
| facebook_comments.csv | C:\SocialListening\data\raw\ | 2,056 Facebook comments |

### Academic References
- Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. JMLR.
- Apify Documentation. https://apify.com
- PhoBERT: https://huggingface.co/wonrax/phobert-base-vietnamese-sentiment
- Metabase: https://www.metabase.com/docs/
- MCP Specification: https://modelcontextprotocol.io/specification/

### Đồ án mẫu tham khảo
- "Ứng dụng Apify thu thập và phân tích TikTok: DOL English"
  (Môn PTMKS, GVHD: TS. Lê Hoành Sử, 4 SV, Tháng 7/2025)
  → Pattern: 8 chương, 3 brands TikTok, 300 videos, EDA + insight + đề xuất

---

> **Document version**: v1.0 | **Created**: 12/05/2026
> **Next update**: Sau preprocessing + EDA Tuần 2
