# Bitcoin Blockchain Analysis Service - Technical Specification

> **참고**: 이 프로젝트는 웹 애플리케이션 개발을 위한 **예시 샘플 프로젝트**입니다.
> React + FastAPI 풀스택 개발의 구조, 패턴, 베스트 프랙티스를 보여주는 학습 및 참고용 자료입니다.

---

## 0. Data Flow Definition (필수 - 프로젝트 시작 전 정의)

> **IMPORTANT**: 프로젝트 개발 전에 이 섹션을 먼저 작성하세요.
> 데이터 소스와 흐름을 명확히 정의하지 않으면 개발 중 큰 삽질이 발생합니다.

### 0.1 Data Source (데이터 소스)

| 항목 | 내용 |
|------|------|
| **소스 타입** | External API / 크롤링 / 파일 업로드 / 사용자 입력 / 로컬 서버 |
| **소스 이름** | Bitcoin Core RPC (예시) |
| **접근 방법** | RPC 호출 (localhost:8332) |
| **인증 필요** | Yes (rpcuser, rpcpassword) |
| **비용** | 무료 (로컬 노드) |
| **Rate Limit** | 없음 |

#### 데이터 소스 타입 가이드

| 타입 | 예시 | 난이도 | 비용 |
|------|------|--------|------|
| **Public API (무료)** | CoinGecko, JSONPlaceholder | 쉬움 | 무료 |
| **Public API (유료)** | Alpha Vantage, OpenAI | 쉬움 | 유료 |
| **API 키 필요** | Twitter API, Google Maps | 보통 | 무료/유료 |
| **OAuth 필요** | Google Calendar, Notion | 어려움 | 무료 |
| **크롤링** | 뉴스 사이트, 쇼핑몰 | 보통 | 무료 |
| **로컬 서버/DB** | Bitcoin Core, PostgreSQL | 어려움 | 무료 |
| **파일 업로드** | CSV, Excel, JSON | 쉬움 | 무료 |
| **사용자 입력** | 폼 데이터, 설정값 | 쉬움 | 무료 |

### 0.2 Input (사용자 입력)

| 입력 항목 | 타입 | 예시 | 필수 여부 |
|-----------|------|------|----------|
| Bitcoin 주소 | String | bc1qxy2kgdygjr... | 필수 |
| 검색 깊이 | Number | 1-10 (기본값: 3) | 선택 |
| 날짜 범위 | Date Range | 2024-01-01 ~ 2024-12-31 | 선택 |

### 0.3 Output (결과 출력)

| 출력 항목 | 형태 | 설명 |
|-----------|------|------|
| 주소 정보 | 카드 UI | 잔액, 트랜잭션 수, 클러스터 ID |
| 네트워크 그래프 | 시각화 | 주소 간 연결 관계 |
| 트랜잭션 목록 | 테이블 | 시간순 입출금 내역 |
| 클러스터 통계 | 차트 | 클러스터 크기 분포 |

### 0.4 Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │  Frontend   │     │   Backend   │     │ Data Source │
│   Input     │────▶│   (React)   │────▶│  (FastAPI)  │────▶│ (Bitcoin    │
│             │     │             │     │             │     │  Core RPC)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │
                           │                   │                   │
                           ▼                   ▼                   │
                    ┌─────────────┐     ┌─────────────┐            │
                    │   Output    │◀────│  Database   │◀───────────┘
                    │ (UI 렌더링) │     │  (SQLite3)  │
                    └─────────────┘     └─────────────┘
```

### 0.5 Data Refresh (데이터 갱신 주기)

| 데이터 | 갱신 주기 | 방법 |
|--------|----------|------|
| 블록체인 데이터 | 10분마다 | Background polling |
| 클러스터 정보 | 새 블록 발견 시 | Event-driven |
| 캐시 데이터 | 1시간마다 | TTL 기반 |

### 0.6 Data Access Checklist (개발 전 확인사항)

프로젝트 시작 전 반드시 확인하세요:

- [ ] 데이터 소스에 접근 가능한가? (API 키, 계정 등)
- [ ] Rate limit이 있는가? (있다면 어떻게 처리할 것인가?)
- [ ] 데이터 형식은 무엇인가? (JSON, XML, CSV 등)
- [ ] 인증 방식은 무엇인가? (API Key, OAuth, Basic Auth 등)
- [ ] 비용이 발생하는가? (무료 tier 한도는?)
- [ ] 데이터 갱신 주기는 어떻게 되는가?
- [ ] 오프라인/에러 시 대체 방안은?

---

## 1. Project Overview

### 1.1 Purpose
Bitcoin 블록체인 분석 및 추적 서비스는 Bitcoin 주소 간의 관계를 분석하고, 동일한 소유자에 속한 주소들을 클러스터링하며, 자금의 흐름을 시각적으로 추적하는 도구입니다.

**이 프로젝트의 목적**:
1. **학습 자료**: React + FastAPI 풀스택 웹 개발의 실전 예제
2. **참고 샘플**: 프로젝트 구조, API 설계, 데이터베이스 스키마 설계의 좋은 예시
3. **템플릿**: 새로운 웹 프로젝트 시작 시 참고할 수 있는 boilerplate

### 1.2 Goals
- Bitcoin 주소 간의 소유권 관계 파악
- Co-spending 휴리스틱을 활용한 주소 클러스터링
- 트랜잭션 입출력 추적 및 자금 흐름 시각화
- 직관적인 네트워크 그래프 인터페이스 제공

### 1.3 Target Users
- 블록체인 연구자
- 암호화폐 포렌식 분석가
- 개인 투자자 및 보안 전문가
- 교육 및 학습 목적 사용자

### 1.4 Key Use Cases
- 특정 주소가 속한 클러스터 식별
- 의심스러운 자금 흐름 추적
- 주소 간 연결 관계 시각화
- 트랜잭션 히스토리 분석

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Network Graph│  │   Timeline   │  │    Search    │      │
│  │ Visualization│  │   Component  │  │  Interface   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Dashboard  │  │Address Detail│                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Layer   │  │   Analysis   │  │    Data      │      │
│  │  (FastAPI)   │  │    Engine    │  │  Collector   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
           ↕                    ↕                    ↕
┌──────────────────┐  ┌─────────────────────────────────────┐
│   SQLite3        │  │     Bitcoin Core Full Node          │
│   (Database)     │  │         (RPC Interface)              │
└──────────────────┘  └─────────────────────────────────────┘
```

### 2.2 Component Breakdown

#### Frontend (React)
- **역할**: 사용자 인터페이스 제공 및 데이터 시각화
- **기술**: React, D3.js/vis.js, Axios
- **주요 컴포넌트**:
  - Network Graph Viewer
  - Transaction Timeline
  - Search Interface
  - Cluster Dashboard
  - Address Detail View

#### Backend API (FastAPI)
- **역할**: 비즈니스 로직 처리, API 제공
- **기술**: Python, FastAPI, SQLAlchemy
- **주요 모듈**:
  - REST API endpoints
  - Request validation
  - Response serialization
  - Authentication (선택사항)

#### Analysis Engine
- **역할**: 블록체인 데이터 분석 및 클러스터링
- **기술**: Python, NetworkX (그래프 분석)
- **주요 기능**:
  - Co-spending 휴리스틱 알고리즘
  - Cluster 생성 및 병합
  - 트랜잭션 추적 로직

#### Data Collector
- **역할**: Bitcoin Core로부터 데이터 수집
- **기술**: Python, python-bitcoinrpc
- **주요 기능**:
  - RPC 연결 관리
  - 블록/트랜잭션 인덱싱
  - 주기적 데이터 동기화

#### Database (SQLite3)
- **역할**: 분석된 데이터 저장
- **기술**: SQLite3 (파일 기반 경량 데이터베이스)
- **저장 데이터**:
  - Bitcoin 주소
  - 트랜잭션
  - 클러스터 정보
  - 주소-클러스터 매핑

**SQLite3 선택 이유**:
- 설치 및 설정이 간단함 (별도 서버 불필요)
- 파일 기반으로 백업/복원이 쉬움
- 개인/소규모 사용에 최적화
- Python 표준 라이브러리 포함
- 예시 샘플 프로젝트에 적합

#### Bitcoin Core Node
- **역할**: 블록체인 데이터 소스
- **요구사항**:
  - Full node (전체 블록체인 동기화)
  - txindex=1 설정 (트랜잭션 인덱싱)
  - RPC 접근 허용

---

## 3. Data Flow

### 3.1 Data Ingestion Flow
```
Bitcoin Core → RPC Call → Data Collector → Parse & Validate →
Database → Analysis Engine → Clustering Results → Database
```

1. **Data Collector**가 Bitcoin Core RPC를 통해 새 블록 감지
2. 블록 내 트랜잭션 파싱
3. 주소 및 트랜잭션 정보를 Database에 저장
4. **Analysis Engine**이 새 데이터 감지 시 클러스터링 수행
5. 클러스터링 결과를 Database에 업데이트

### 3.2 User Query Flow
```
Frontend → API Request → Backend API → Database Query →
Analysis (if needed) → Response → Frontend Rendering
```

1. 사용자가 Frontend에서 주소 검색
2. Frontend가 Backend API에 요청
3. Backend가 Database에서 데이터 조회
4. 필요시 실시간 분석 수행
5. 결과를 JSON으로 반환
6. Frontend가 그래프/테이블로 렌더링

---

## 4. Core Features & Functionality

### 4.1 Address Clustering

#### Co-spending Heuristic Algorithm
**원리**: 동일한 트랜잭션의 여러 입력에 사용된 주소들은 같은 개인이 제어한다고 가정

**알고리즘**:
1. 트랜잭션의 모든 입력 주소 추출
2. 입력 주소가 2개 이상인 경우, 해당 주소들을 같은 클러스터로 그룹화
3. Union-Find 자료구조로 클러스터 병합 관리
4. 각 클러스터에 고유 ID 부여

**데이터 구조**:
```python
class Cluster:
    id: UUID
    addresses: Set[str]
    created_at: datetime
    updated_at: datetime
    transaction_count: int
    total_btc_volume: Decimal
```

#### Cluster Merging Logic
- 새로운 co-spending 관계 발견 시 기존 클러스터 병합
- 병합 이력 추적 (감사 로그)
- 클러스터 크기 제한 (성능 최적화)

### 4.2 Transaction Tracking

#### Input/Output Tracking
- 각 트랜잭션의 입력(UTXO) 및 출력 추적
- 이전 트랜잭션 역추적 (backward tracking)
- 이후 트랜잭션 순추적 (forward tracking)
- 최대 추적 깊이 설정 (기본 5-hop)

#### Flow Visualization Data
Frontend 그래프를 위한 데이터 형식:
```json
{
  "nodes": [
    {
      "id": "address_or_tx_id",
      "type": "address|transaction",
      "label": "shortened_address",
      "balance": 1.234,
      "cluster_id": "uuid"
    }
  ],
  "edges": [
    {
      "source": "address1",
      "target": "tx1",
      "amount": 0.5,
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 4.3 Data Collection

#### Bitcoin Core RPC Integration
**필요한 RPC 메서드**:
- `getblockcount()`: 최신 블록 높이
- `getblockhash(height)`: 블록 해시
- `getblock(hash, verbosity=2)`: 블록 상세 정보 (트랜잭션 포함)
- `getrawtransaction(txid, verbose=True)`: 트랜잭션 상세 정보

**인증**:
```python
# bitcoin.conf
rpcuser=your_username
rpcpassword=your_password
rpcallowip=127.0.0.1
txindex=1
```

#### Indexing Strategy
- **초기 동기화**: 특정 블록 높이부터 시작 (예: 최근 1년)
- **증분 업데이트**: 새 블록 감지 시 실시간 인덱싱
- **백그라운드 작업**: Celery 또는 asyncio 활용

#### Update Frequency
- 새 블록 감지: 10분마다 폴링 (또는 ZMQ 알림 사용)
- 클러스터 재계산: 새 블록 인덱싱 후 자동 트리거
- 캐시 갱신: 사용자 요청 시 필요에 따라

---

## 5. API Design

### 5.1 REST Endpoints

#### Address Endpoints
```
GET /api/v1/addresses/{address}
- 특정 주소의 상세 정보 조회
- Response: { address, balance, tx_count, cluster_id, first_seen, last_seen }

GET /api/v1/addresses/{address}/transactions
- 주소의 트랜잭션 히스토리
- Query params: limit, offset, start_date, end_date
- Response: { transactions: [...], total, page }

GET /api/v1/addresses/{address}/cluster
- 주소가 속한 클러스터 정보
- Response: { cluster_id, addresses: [...], stats: {...} }
```

#### Cluster Endpoints
```
GET /api/v1/clusters
- 모든 클러스터 목록 (페이징)
- Query params: limit, offset, min_size
- Response: { clusters: [...], total, page }

GET /api/v1/clusters/{cluster_id}
- 특정 클러스터 상세 정보
- Response: { id, addresses: [...], stats, created_at }

GET /api/v1/clusters/{cluster_id}/graph
- 클러스터 내 주소 간 관계 그래프 데이터
- Response: { nodes: [...], edges: [...] }
```

#### Transaction Endpoints
```
GET /api/v1/transactions/{txid}
- 트랜잭션 상세 정보
- Response: { txid, inputs: [...], outputs: [...], timestamp, block_height }

GET /api/v1/transactions/{txid}/flow
- 트랜잭션 자금 흐름 추적
- Query params: depth (기본 3)
- Response: { nodes: [...], edges: [...] }
```

#### Search Endpoint
```
GET /api/v1/search?q={query}
- 주소, 트랜잭션 ID, 클러스터 검색
- Response: { addresses: [...], transactions: [...], clusters: [...] }
```

#### Analytics Endpoints
```
GET /api/v1/analytics/summary
- 전체 시스템 통계
- Response: { total_addresses, total_clusters, total_transactions, ... }

GET /api/v1/analytics/cluster-distribution
- 클러스터 크기 분포
- Response: { distribution: { "1-10": 150, "11-50": 30, ... } }
```

### 5.2 Response Format
```json
{
  "status": "success|error",
  "data": { ... },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
  }
}
```

### 5.3 Error Codes
- `400`: Bad Request (잘못된 파라미터)
- `404`: Not Found (주소/트랜잭션/클러스터 없음)
- `429`: Too Many Requests (rate limiting)
- `500`: Internal Server Error
- `503`: Service Unavailable (Bitcoin Core 연결 실패)

---

## 6. Database Schema (SQLite3)

### 6.0 SQLite3 사용 가이드

**데이터베이스 파일**: `bitcoin_analysis.db`

**SQLite3 특징**:
- 파일 기반: 단일 파일로 모든 데이터 저장
- 트랜잭션 지원: ACID 보장
- 동시성: 단일 쓰기, 다중 읽기 지원
- 타입: 유연한 타입 시스템 (TEXT, INTEGER, REAL, BLOB)

**제약사항**:
- 대규모 동시 쓰기 작업에는 부적합
- UUID 네이티브 타입 없음 (TEXT로 저장)
- 일부 고급 PostgreSQL 기능 미지원

**프로덕션 전환 시**: SQLite3 → PostgreSQL 마이그레이션 가능

### 6.1 Tables

#### addresses
```sql
CREATE TABLE addresses (
    address TEXT PRIMARY KEY,
    cluster_id TEXT,
    balance REAL DEFAULT 0,
    total_received REAL DEFAULT 0,
    total_sent REAL DEFAULT 0,
    tx_count INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);

CREATE INDEX idx_addresses_cluster ON addresses(cluster_id);
CREATE INDEX idx_addresses_balance ON addresses(balance DESC);
```

**SQLite3 타입 매핑**:
- `TEXT`: 문자열 (주소, UUID, 타임스탬프)
- `REAL`: 부동소수점 (BTC 금액)
- `INTEGER`: 정수 (카운트)

#### transactions
```sql
CREATE TABLE transactions (
    txid TEXT PRIMARY KEY,
    block_height INTEGER,
    block_hash TEXT,
    timestamp TEXT,
    fee REAL,
    size INTEGER,
    input_count INTEGER,
    output_count INTEGER,
    total_input REAL,
    total_output REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_block ON transactions(block_height DESC);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
```

#### transaction_inputs
```sql
CREATE TABLE transaction_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT NOT NULL,
    vout_index INTEGER,
    prev_txid TEXT,
    prev_vout INTEGER,
    address TEXT,
    amount REAL,
    script_sig TEXT,
    sequence INTEGER,
    FOREIGN KEY (txid) REFERENCES transactions(txid),
    FOREIGN KEY (address) REFERENCES addresses(address)
);

CREATE INDEX idx_tx_inputs_txid ON transaction_inputs(txid);
CREATE INDEX idx_tx_inputs_address ON transaction_inputs(address);
```

#### transaction_outputs
```sql
CREATE TABLE transaction_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT NOT NULL,
    vout INTEGER,
    address TEXT,
    amount REAL,
    script_pubkey TEXT,
    spent INTEGER DEFAULT 0,  -- SQLite에서 BOOLEAN은 0/1 INTEGER
    spent_in_txid TEXT,
    FOREIGN KEY (txid) REFERENCES transactions(txid),
    FOREIGN KEY (address) REFERENCES addresses(address)
);

CREATE INDEX idx_tx_outputs_txid ON transaction_outputs(txid);
CREATE INDEX idx_tx_outputs_address ON transaction_outputs(address);
CREATE INDEX idx_tx_outputs_spent ON transaction_outputs(spent);
```

#### clusters
```sql
CREATE TABLE clusters (
    id TEXT PRIMARY KEY,  -- UUID를 TEXT로 저장 (Python에서 생성)
    label TEXT,
    address_count INTEGER DEFAULT 0,
    total_balance REAL DEFAULT 0,
    total_received REAL DEFAULT 0,
    total_sent REAL DEFAULT 0,
    tx_count INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clusters_address_count ON clusters(address_count DESC);
CREATE INDEX idx_clusters_balance ON clusters(total_balance DESC);
```

**UUID 생성 (Python)**:
```python
import uuid

cluster_id = str(uuid.uuid4())  # SQLite에 TEXT로 저장
```

#### cluster_edges
```sql
-- 클러스터 간 트랜잭션 관계 (선택사항)
CREATE TABLE cluster_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_cluster_id TEXT NOT NULL,
    target_cluster_id TEXT NOT NULL,
    tx_count INTEGER DEFAULT 0,
    total_amount REAL DEFAULT 0,
    first_tx_timestamp TEXT,
    last_tx_timestamp TEXT,
    FOREIGN KEY (source_cluster_id) REFERENCES clusters(id),
    FOREIGN KEY (target_cluster_id) REFERENCES clusters(id)
);

CREATE INDEX idx_cluster_edges_source ON cluster_edges(source_cluster_id);
CREATE INDEX idx_cluster_edges_target ON cluster_edges(target_cluster_id);
```

### 6.2 SQLite3 최적화

#### PRAGMA 설정
```sql
-- WAL 모드: 읽기 성능 향상, 동시성 개선
PRAGMA journal_mode = WAL;

-- 외래 키 제약 활성화
PRAGMA foreign_keys = ON;

-- 캐시 크기 증가 (메모리 사용)
PRAGMA cache_size = -64000;  -- 64MB

-- 동기화 모드 (속도 vs 안전성)
PRAGMA synchronous = NORMAL;  -- 개발: NORMAL, 프로덕션: FULL

-- 임시 저장소
PRAGMA temp_store = MEMORY;
```

#### 인덱스 전략
- 주소 및 트랜잭션 ID는 자주 검색되므로 Primary Key
- 클러스터 ID, 블록 높이, 타임스탬프에 인덱스
- 잔액 및 트랜잭션 수로 정렬 쿼리를 위한 인덱스
- 복합 인덱스 고려 (address + timestamp)

**복합 인덱스 예시**:
```sql
-- 주소별 시간순 트랜잭션 조회
CREATE INDEX idx_tx_outputs_address_time
ON transaction_outputs(address, txid);

-- 클러스터별 잔액 조회
CREATE INDEX idx_addresses_cluster_balance
ON addresses(cluster_id, balance DESC);
```

### 6.3 데이터베이스 초기화

**스크립트**: `backend/scripts/init_db.py`

```python
import sqlite3
from pathlib import Path

def init_database(db_path: str = "bitcoin_analysis.db"):
    """SQLite3 데이터베이스 초기화"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # PRAGMA 설정
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA cache_size = -64000")

    # 테이블 생성
    with open("schema.sql", "r") as f:
        schema = f.read()
        cursor.executescript(schema)

    conn.commit()
    conn.close()

    print(f"✓ 데이터베이스 초기화 완료: {db_path}")

if __name__ == "__main__":
    init_database()
```

### 6.4 SQLAlchemy 연결

**설정**: `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# SQLite3 연결 URL
DATABASE_URL = "sqlite:///./bitcoin_analysis.db"

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # FastAPI용
    poolclass=StaticPool,  # 단일 연결 풀
    echo=True  # SQL 로그 출력 (개발 시)
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 6.5 백업 및 복원

**백업**:
```bash
# 온라인 백업 (서비스 중단 없음)
sqlite3 bitcoin_analysis.db ".backup backup.db"

# 또는 파일 복사
cp bitcoin_analysis.db backup_$(date +%Y%m%d).db
```

**복원**:
```bash
cp backup.db bitcoin_analysis.db
```

**자동 백업 스크립트**:
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="./backups"
DB_FILE="bitcoin_analysis.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_FILE ".backup $BACKUP_DIR/backup_$DATE.db"
echo "✓ 백업 완료: $BACKUP_DIR/backup_$DATE.db"

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "backup_*.db" -mtime +7 -delete
```

---

## 7. Design Reference

### 7.0 UI/UX Design Guidelines

**디자인 컨셉**: 따뜻하고 친근한 비트코인 분석 도구

이 프로젝트는 제공된 디자인 레퍼런스를 기반으로 구현됩니다:

#### 색상 팔레트
- **Primary Colors**:
  - 베이지/크림 (#F5F1E8, #FFF9ED)
  - 오렌지/골드 (#E67E22, #F39C12, #D68910)
  - 다크 브라운 (#8B4513, #5D4037)
- **Accent Colors**:
  - 밝은 오렌지 (버튼, 아이콘)
  - 따뜻한 노란색 (강조 요소)

#### 디자인 원칙
1. **따뜻하고 친근한 느낌**
   - 레트로/빈티지 감성
   - 부드러운 곡선과 둥근 모서리 (border-radius: 12-24px)
   - 재미있는 베이킹/요리 테마 은유 (Toasty, Mixing Bowl, Golden Sink 등)

2. **카드 기반 레이아웃 (중첩 금지)**
   - 각 섹션을 독립적인 카드로 구성
   - **CRITICAL: Card 내부에 Card를 중첩하지 않음**
   - 섹션 구분은 Divider, Background color, Spacing으로 처리
   - 최대 레이아웃 깊이: 2단계

3. **타이포그래피**
   - 헤더: 크고 굵은 폰트 (24-32px, bold)
   - 본문: 가독성 높은 폰트 (14-16px)
   - 라벨: 대문자 + 작은 크기 (12px, uppercase, letter-spacing)
   - 모노스페이스: 주소/트랜잭션 ID (Courier/Monaco)

4. **아이콘**
   - 이모지 사용 금지
   - Lucide React 아이콘 컴포넌트 사용
   - 아이콘 배경에 둥근 박스 적용 (골드/오렌지 색상)

5. **인터랙션**
   - 부드러운 호버 효과 (transition: all 0.3s ease)
   - 그림자 효과로 깊이 표현 (box-shadow)
   - 터치 친화적인 버튼 크기 (최소 44x44px)

#### 주요 컴포넌트 스타일

**Network Settings Panel** (왼쪽 패널)
- 크림색 배경 카드
- 입력 필드: 베이지 배경, 둥근 모서리
- 큰 저장 버튼: 골드색, 전체 너비
- 섹션 헤더: 오렌지 점 + 대문자 라벨

**Dashboard** (메인 화면)
- 검색 바: 크림색 배경, 오렌지 액센트 버튼
- "The Golden Trail" 카드:
  - 큰 타이틀 + 부제목
  - 중앙 네트워크 그래프 시각화 (Mixing Bowl)
  - 하단 통계 카드들 (Crispiness, Temp)
- "Clustering Mode" 섹션:
  - 토글 스위치 (오렌지)
  - 동심원 클러스터 시각화
- "Baking Stats" 섹션:
  - 아이콘 + 라벨 + 값
  - 화살표로 증감 표시

#### 레이아웃 구조 예시
```jsx
// ✅ 올바른 구조 (중첩 없음)
<div className="dashboard">
  <Card className="search-section">
    <SearchBar />
  </Card>

  <Card className="golden-trail">
    <CardHeader>The Golden Trail</CardHeader>
    {/* Card 내부에 섹션 구분은 div + background로 */}
    <div className="graph-section">
      <NetworkGraph />
    </div>
    <div className="stats-section border-t">
      <StatItem />
      <StatItem />
    </div>
  </Card>

  <Card className="clustering">
    <Toggle />
    <ClusterVisualization />
  </Card>
</div>

// ❌ 잘못된 구조 (중첩 카드)
<Card>
  <Card>  {/* 이렇게 하지 말 것! */}
    <Content />
  </Card>
</Card>
```

#### 모바일 반응형
- Mobile-first 디자인
- Breakpoints:
  - Mobile: < 640px
  - Tablet: 640px - 1024px
  - Desktop: > 1024px
- 모바일에서는 세로 스택 레이아웃
- 터치 타깃 최소 44x44px
- 폰트 크기 자동 조절

---

## 8. Frontend Components

### 7.1 Network Graph Viewer

**기능**:
- 주소 및 트랜잭션을 노드로 표시
- 자금 흐름을 간선(edge)으로 표시
- 확대/축소, 드래그 이동
- 노드 클릭 시 상세 정보 표시
- 클러스터별 색상 구분

**기술 스택**:
- D3.js force-directed graph 또는 vis.js
- React wrapper component

**인터랙션**:
- Hover: 노드 정보 툴팁
- Click: 상세 패널 열기
- Double-click: 해당 노드에서 확장 (추가 연결 로드)
- Filter: 특정 기간, 금액 범위 필터링

### 7.2 Transaction Timeline

**기능**:
- 시간순으로 트랜잭션 표시
- 입출금 방향 표시 (입금: 녹색, 출금: 빨간색)
- 금액 및 상대방 주소 표시
- 클릭 시 트랜잭션 상세 정보

**UI 구성**:
```
[타임라인 바]
    |-- 2024-01-01: +0.5 BTC from addr_xyz
    |-- 2024-01-05: -0.3 BTC to addr_abc
    |-- 2024-01-10: +1.2 BTC from addr_def
```

### 7.3 Search Interface

**기능**:
- 주소, 트랜잭션 ID, 클러스터 ID 검색
- 자동완성 (debounced)
- 최근 검색 히스토리
- 고급 필터 (기간, 금액, 클러스터 크기)

**UI**:
```
┌────────────────────────────────────────┐
│  🔍  Search address, tx, cluster...    │
└────────────────────────────────────────┘
[Filters] Date: ___  Amount: ___  Type: ___
```

### 7.4 Cluster Dashboard

**기능**:
- 전체 클러스터 통계
- 상위 클러스터 목록 (주소 수, 잔액 기준)
- 클러스터 크기 분포 차트
- 최근 활동 클러스터

**차트**:
- Pie chart: 클러스터 크기 분포
- Bar chart: 상위 10 클러스터
- Line chart: 시간별 클러스터 생성 추이

### 7.5 Address Detail View

**표시 정보**:
- 주소 문자열
- 현재 잔액
- 총 수신/송신 금액
- 트랜잭션 수
- 속한 클러스터 정보
- 최초/최근 활동 시간
- 연결된 주소 목록
- 트랜잭션 히스토리 테이블

---

## 8. Technical Considerations

### 8.1 Bitcoin Core Setup

**시스템 요구사항**:
- 최소 500GB 디스크 공간 (full blockchain)
- 8GB+ RAM
- 안정적인 인터넷 연결

**bitcoin.conf 설정**:
```ini
# RPC 설정
server=1
rpcuser=bitcoinrpc
rpcpassword=<strong_password>
rpcallowip=127.0.0.1

# 트랜잭션 인덱싱
txindex=1

# 성능 최적화
dbcache=4096
maxmempool=300
```

**동기화 시간**:
- 초기 동기화: 1-3일 (하드웨어에 따라)
- 증분 업데이트: 10분마다

### 8.2 RPC Authentication

**보안 고려사항**:
- RPC 비밀번호는 환경 변수로 관리
- TLS/SSL 사용 (원격 접근 시)
- IP whitelist 설정
- Rate limiting 적용

**Python 연결 예시**:
```python
from bitcoinrpc.authproxy import AuthServiceProxy

rpc_connection = AuthServiceProxy(
    f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
)
```

### 8.3 Data Synchronization Strategy

**초기 동기화**:
1. 특정 블록 높이부터 시작 (예: 최근 1년)
2. 배치 처리 (블록 100개씩)
3. 진행률 표시 및 체크포인트 저장

**증분 업데이트**:
1. 10분마다 `getblockcount()` 호출
2. 새 블록 감지 시 자동 인덱싱
3. 실패 시 재시도 로직

**재시작 복구**:
- 마지막 처리된 블록 높이 저장
- 재시작 시 해당 지점부터 재개

### 8.4 Performance Optimization

#### Database Query Optimization
- 적절한 인덱스 설정
- 쿼리 결과 캐싱 (Redis 사용 고려)
- 페이지네이션으로 대량 데이터 처리
- EXPLAIN ANALYZE로 쿼리 성능 분석

#### Graph Query Optimization
- 그래프 깊이 제한 (기본 3-5 hop)
- BFS/DFS 알고리즘 최적화
- 자주 조회되는 경로는 미리 계산 (materialized view)

#### Caching Strategy
- **API 레벨**: FastAPI response cache
- **Database 레벨**: PostgreSQL query cache
- **Application 레벨**: Redis로 주소/클러스터 정보 캐싱
- TTL 설정: 블록 확정 후 (6 confirmations) 데이터는 장기 캐싱

#### Async Processing
- FastAPI의 async/await 활용
- 백그라운드 작업: Celery + Redis/RabbitMQ
- 무거운 클러스터링 작업은 백그라운드에서 처리

---

## 9. Development Phases

### Phase 1: Foundation (Week 1-2)
**목표**: 기본 인프라 구축

**작업**:
- [ ] Bitcoin Core 노드 설정 및 동기화
- [ ] PostgreSQL 데이터베이스 스키마 생성
- [ ] FastAPI 프로젝트 초기 설정
- [ ] Bitcoin RPC 연결 테스트
- [ ] 기본 데이터 모델 (SQLAlchemy) 정의

**산출물**:
- 동작하는 Bitcoin Core full node
- 데이터베이스 스키마
- 기본 FastAPI 앱 구조

### Phase 2: Analysis Engine (Week 3-4)
**목표**: 코어 분석 로직 구현

**작업**:
- [ ] Data Collector 모듈 개발
  - [ ] 블록 파싱
  - [ ] 트랜잭션 파싱
  - [ ] 데이터베이스 저장
- [ ] Co-spending 클러스터링 알고리즘 구현
  - [ ] Union-Find 자료구조
  - [ ] 클러스터 생성/병합 로직
- [ ] 트랜잭션 추적 로직 구현
  - [ ] Input/output 추적
  - [ ] 그래프 생성 함수

**산출물**:
- 블록체인 데이터 수집 파이프라인
- 동작하는 클러스터링 엔진
- 단위 테스트

### Phase 3: Backend API (Week 5-6)
**목표**: RESTful API 구현

**작업**:
- [ ] API 엔드포인트 구현
  - [ ] Address endpoints
  - [ ] Cluster endpoints
  - [ ] Transaction endpoints
  - [ ] Search endpoint
  - [ ] Analytics endpoints
- [ ] Request validation (Pydantic models)
- [ ] Response serialization
- [ ] Error handling
- [ ] API 문서 (OpenAPI/Swagger)
- [ ] 통합 테스트

**산출물**:
- 완전한 RESTful API
- API 문서
- Postman/Insomnia 테스트 컬렉션

### Phase 4: Frontend UI (Week 7-9)
**목표**: React 사용자 인터페이스 구현

**작업**:
- [ ] React 프로젝트 초기 설정 (Vite 또는 CRA)
- [ ] 컴포넌트 개발
  - [ ] Network Graph Viewer (D3.js/vis.js)
  - [ ] Transaction Timeline
  - [ ] Search Interface
  - [ ] Cluster Dashboard
  - [ ] Address Detail View
- [ ] API 연동 (Axios/Fetch)
- [ ] 상태 관리 (Context API 또는 Zustand)
- [ ] 라우팅 (React Router)
- [ ] 스타일링 (TailwindCSS 또는 Material-UI)

**산출물**:
- 동작하는 React 애플리케이션
- 반응형 UI
- 사용자 매뉴얼

### Phase 5: Integration & Polish (Week 10-11)
**목표**: 통합 테스트 및 최적화

**작업**:
- [ ] End-to-end 테스트
- [ ] 성능 최적화
  - [ ] 데이터베이스 쿼리 최적화
  - [ ] API 응답 시간 개선
  - [ ] Frontend 렌더링 최적화
- [ ] 캐싱 구현 (Redis)
- [ ] 에러 핸들링 개선
- [ ] 로깅 및 모니터링 설정
- [ ] 배포 준비
  - [ ] Docker 컨테이너화
  - [ ] docker-compose 설정
  - [ ] 환경 변수 관리

**산출물**:
- 프로덕션 준비 완료된 애플리케이션
- Docker 이미지
- 배포 가이드

---

## 10. Future Enhancements (Out of Scope for MVP)

### 10.1 Advanced Clustering Algorithms
- **Change Address Detection**: 거스름돈 주소를 식별하여 정확도 향상
- **Time Pattern Analysis**: 트랜잭션 타이밍 패턴으로 연관성 찾기
- **Amount Pattern Analysis**: 특정 금액 패턴으로 연관성 찾기
- **Machine Learning**: 더 정교한 클러스터링을 위한 ML 모델 적용

### 10.2 Enhanced Visualization
- 3D 네트워크 그래프
- 애니메이션 자금 흐름 시각화
- 히트맵 (주소 활동 빈도)
- Sankey diagram (자금 흐름)

### 10.3 Additional Features
- **Labeling System**: 주소/클러스터에 라벨 부여 (거래소, 믹서 등)
- **Alert System**: 특정 주소/클러스터 활동 시 알림
- **Export Functionality**: 분석 결과 CSV/JSON 내보내기
- **Reporting**: 자동 리포트 생성 (PDF)
- **Multi-user Support**: 사용자 계정 및 권한 관리
- **API Key Management**: 외부 접근을 위한 API 키 발급

### 10.4 Multiple Cryptocurrency Support
- Ethereum 블록체인 분석
- Litecoin, Bitcoin Cash 등 다른 암호화폐 지원
- Cross-chain 추적 (체인 간 자금 이동)

### 10.5 Performance Enhancements
- Distributed processing (Spark, Dask)
- Graph database (Neo4j) 도입 고려
- Real-time streaming (ZMQ 활용)
- Elasticsearch for advanced search

---

## 11. Testing Strategy

### 11.1 Unit Tests
- Data Collector 함수들
- Clustering 알고리즘
- API endpoint 로직
- Database query 함수

### 11.2 Integration Tests
- Bitcoin RPC 연결
- Database CRUD 작업
- API 전체 플로우
- Frontend-Backend 통신

### 11.3 End-to-End Tests
- 사용자 시나리오 기반 테스트
- 주소 검색 → 클러스터 조회 → 그래프 시각화 전체 흐름

### 11.4 Performance Tests
- 대량 데이터 로딩 시간
- API 응답 시간
- 그래프 렌더링 성능
- 동시 사용자 부하 테스트

---

## 12. Project Structure & Scripts

### 12.1 Directory Structure
```
bitcoin-cracker/
├── frontend/                # React 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── api/            # API 클라이언트
│   │   ├── utils/          # 유틸리티 함수
│   │   └── App.jsx         # 메인 앱
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── utils/          # 유틸리티
│   │   └── main.py         # FastAPI 앱
│   ├── tests/              # 테스트
│   ├── requirements.txt
│   └── pyproject.toml
│
├── scripts/                 # 유틸리티 스크립트
├── .claude/                 # Claude 설정
├── SPEC.md                  # 이 문서
├── AGENTS.md                # Agent 규칙
├── README.md                # 프로젝트 소개
├── dev.sh                   # 개발 서버 실행
├── test.sh                  # 테스트 실행
├── install.sh               # 의존성 설치
└── deploy.sh                # 배포 스크립트
```

### 12.2 Development Scripts

#### install.sh
**목적**: 프로젝트 의존성 설치

**기능**:
- Python 가상환경 생성 및 활성화
- Backend pip 패키지 설치 (requirements.txt)
- Frontend npm 패키지 설치 (package.json)
- 환경 변수 파일 생성 (.env)
- 데이터베이스 초기화

**사용법**:
```bash
./install.sh
```

#### dev.sh
**목적**: 개발 서버 실행

**기능**:
- Backend FastAPI 서버 시작 (포트 8000)
- Frontend Vite 개발 서버 시작 (포트 3000)
- 두 서버를 동시에 실행 (백그라운드)
- 로그 출력

**사용법**:
```bash
./dev.sh           # 백엔드 + 프론트엔드 모두 실행
./dev.sh backend   # 백엔드만 실행
./dev.sh frontend  # 프론트엔드만 실행
```

#### test.sh
**목적**: 테스트 실행

**기능**:
- 유닛 테스트: 개별 함수/클래스 테스트
- 통합 테스트: API 엔드포인트 테스트
- E2E 테스트: 전체 플로우 테스트
- 커버리지 리포트 생성

**사용법**:
```bash
./test.sh              # 모든 테스트 실행
./test.sh unit         # 유닛 테스트만
./test.sh integration  # 통합 테스트만
./test.sh e2e          # E2E 테스트만
./test.sh --coverage   # 커버리지 포함
```

#### deploy.sh
**목적**: Railway 배포

**기능**:
1. install.sh 실행 (의존성 설치)
2. 테스트 실행 (test.sh)
3. Frontend 빌드 (npm run build)
4. Railway CLI로 배포
5. 환경 변수 설정
6. 배포 URL 출력

**사용법**:
```bash
./deploy.sh            # Railway 배포
./deploy.sh --prod     # 프로덕션 배포
./deploy.sh --staging  # 스테이징 배포
```

**Railway 설정**:
```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
```

### 12.3 Environment Variables
```bash
# .env.example
# Backend
DATABASE_URL=sqlite:///./bitcoin_analysis.db
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=<strong_password>
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
SECRET_KEY=<random_secret>

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Bitcoin Cracker

# Railway (production)
RAILWAY_ENVIRONMENT=production
PORT=8000
# Railway에서 SQLite3 파일 영구 저장을 위해 Volume 마운트 필요
```

**SQLite3 데이터베이스 파일 위치**:
- 개발: `./bitcoin_analysis.db` (프로젝트 루트)
- 프로덕션: Railway Volume에 마운트된 경로

### 12.4 Docker Compose Setup

**참고**: SQLite3 사용 시 별도 데이터베이스 컨테이너 불필요

```yaml
version: '3.8'
services:
  bitcoin-core:
    image: btcpayserver/bitcoin:24.0
    volumes:
      - bitcoin-data:/data
    ports:
      - "8332:8332"

  backend:
    build: ./backend
    depends_on:
      - bitcoin-core
    volumes:
      - ./data:/app/data  # SQLite3 DB 파일 저장
    environment:
      DATABASE_URL: sqlite:///./data/bitcoin_analysis.db
      BITCOIN_RPC_URL: http://bitcoin-core:8332
      BITCOIN_RPC_USER: ${BITCOIN_RPC_USER}
      BITCOIN_RPC_PASSWORD: ${BITCOIN_RPC_PASSWORD}
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://backend:8000/api/v1

volumes:
  bitcoin-data:
```

**SQLite3 장점** (Docker 환경):
- 데이터베이스 컨테이너 불필요
- 설정 간소화
- 리소스 사용량 감소
- 백업/복원 용이 (단일 파일)

### 12.2 Environment Variables
```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/bitcoin_analysis
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=<strong_password>
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

---

## 13. Security Considerations

### 13.1 Bitcoin RPC Security
- 강력한 비밀번호 사용
- IP 화이트리스트 제한
- TLS/SSL 암호화 (원격 접근 시)

### 13.2 API Security
- Rate limiting (per IP)
- Input validation
- SQL injection 방지 (ORM 사용)
- XSS 방지
- CORS 설정

### 13.3 Data Privacy
- 민감한 데이터 암호화 (필요시)
- 로그에 비밀번호/키 노출 방지
- 환경 변수로 credential 관리

---

## 14. Monitoring & Logging

### 14.1 Logging
- Application logs (INFO, ERROR)
- API request/response logs
- Bitcoin RPC 호출 로그
- 클러스터링 작업 로그

### 14.2 Monitoring Metrics
- API 응답 시간
- 데이터베이스 쿼리 성능
- Bitcoin Core RPC 가용성
- 클러스터 생성/업데이트 속도
- 디스크 사용량

### 14.3 Tools
- **Logging**: Python logging module, structlog
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry

---

## 15. Documentation

### 15.1 User Documentation
- 설치 가이드
- 사용자 매뉴얼
- FAQ

### 15.2 Developer Documentation
- 아키텍처 설계 문서
- API 레퍼런스 (OpenAPI/Swagger)
- 데이터베이스 스키마 문서
- 개발 환경 설정 가이드
- 기여 가이드

### 15.3 Operations Documentation
- 배포 가이드
- 백업 및 복구 절차
- 트러블슈팅 가이드
- 성능 튜닝 가이드

---

## 16. Success Metrics

### 16.1 Functional Metrics
- ✅ Bitcoin Core 노드와 안정적으로 연결
- ✅ 블록체인 데이터 정확하게 인덱싱
- ✅ Co-spending 클러스터링 정확도 > 90%
- ✅ API 응답 시간 < 500ms (95 percentile)
- ✅ 그래프 렌더링 < 2초 (1000 노드 기준)

### 16.2 Non-Functional Metrics
- ✅ 시스템 가동률 > 99%
- ✅ 데이터 동기화 지연 < 20분
- ✅ 사용자 인터페이스 반응성 (60fps)

---

## 17. Risks & Mitigation

### 17.1 Technical Risks
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Bitcoin Core 동기화 실패 | High | 체크포인트 저장, 자동 재시도 |
| 대용량 데이터 처리 성능 저하 | Medium | 인덱싱, 캐싱, 페이징 |
| 클러스터링 알고리즘 정확도 부족 | Medium | 알고리즘 개선, 검증 데이터셋 |
| API 과부하 | Medium | Rate limiting, 로드 밸런싱 |

### 17.2 Operational Risks
| Risk | Impact | Mitigation |
|------|--------|-----------|
| 디스크 공간 부족 | High | 모니터링, 자동 알림 |
| Bitcoin Core 노드 다운타임 | Medium | 헬스체크, 자동 재시작 |
| 데이터베이스 장애 | High | 정기 백업, 복제 설정 |

---

## 18. Appendix

### 18.1 Glossary
- **Co-spending**: 동일한 트랜잭션의 여러 입력에 사용되는 주소들
- **UTXO**: Unspent Transaction Output (미사용 트랜잭션 출력)
- **Cluster**: 같은 소유자로 추정되는 주소들의 그룹
- **RPC**: Remote Procedure Call
- **txindex**: Bitcoin Core에서 모든 트랜잭션을 인덱싱하는 옵션

### 18.2 References
- Bitcoin Core RPC Documentation: https://developer.bitcoin.org/reference/rpc/
- Bitcoin Clustering Research Papers
- FastAPI Documentation: https://fastapi.tiangolo.com/
- React Documentation: https://react.dev/

### 18.3 Contact & Support
- Project Repository: [GitHub URL]
- Issue Tracker: [GitHub Issues URL]
- Email: [contact email]

---

**Document Version**: 1.0
**Last Updated**: 2024-01-12
**Author**: Development Team
**Status**: Draft → Review → Approved
