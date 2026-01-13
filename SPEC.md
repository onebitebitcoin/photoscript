# PhotoScript — SPEC.md

## 0) 한 줄 요약
PhotoScript는 유튜브 스크립트를 입력하면 스크립트를 **블록 단위로 자동 분할**하고, 각 블록에 어울리는 **이미지/영상 후보**를 오른쪽 패널에 매핑해주는 “스크립트-비주얼 매칭” 웹앱이다.

---

## 1) 목표(Goals)
- 사용자는 스크립트를 붙여 넣고 **생성 버튼 한 번**으로 블록 분할 + 이미지/영상 매칭 결과를 얻는다.
- UI는 단순: **메인 입력(스크립트)** + **생성 버튼** + **결과 화면(좌: 스크립트 블록 / 우: 비주얼)**.
- “자동 매칭”이 기본이되, 사용자가 손쉽게 대체 후보를 선택/교체할 수 있는 확장 구조를 제공한다.
- 결과를 프로젝트로 저장하고 재편집할 수 있도록 데이터 모델과 API를 구성한다(MVP에서도 최소 저장 지원).

## 2) 비목표(Non-Goals)
- 영상 편집(타임라인, 컷 편집, 자막 싱크) 자체를 앱에서 완결하는 것은 범위 밖(후속).
- 저작권이 필요한 유료 스톡 라이브러리의 결제/라이선스 자동 구매는 후속.
- 완벽한 “감독 수준”의 장면 연출/스토리보드 자동 생성은 후속(초기에는 후보 추천 중심).

---

## 3) 핵심 개념(Domain)
- **Project**: 하나의 유튜브 영상 제작 단위(스크립트 + 블록 + 매칭 결과)
- **Script**: 사용자가 입력한 전체 원문 텍스트
- **Block**: 스크립트를 의미 단위로 나눈 조각(문장/문단/씬)
- **Asset**: 이미지/영상 후보(썸네일/URL/출처/라이선스 메타)
- **Mapping**: 특정 블록에 선택된 대표 Asset과 후보 리스트

---

## 4) 사용자 플로우(User Flow)

### 4.1 메인 화면 `/`
1) 사용자는 스크립트 입력 영역에 텍스트를 입력(또는 붙여넣기)
2) `Generate` 버튼 클릭
3) 로딩 상태 표시(블록 분할 → 키워드/검색 → 매칭)
4) 결과 화면:
   - 좌측: Block 리스트
   - 우측: 선택된 Block의 매칭 비주얼(대표 1개 + 후보들)

### 4.2 결과 편집 플로우(확장)
- 좌측에서 블록 선택 → 우측 후보 갤러리에서 교체(클릭)
- (옵션) 블록 분할 조정: 블록 합치기/나누기(후속)
- (옵션) Export: 블록별 사용 Asset 리스트 다운로드(CSV/JSON) 또는 스토리보드 PDF(후속)

---

## 5) UI/페이지 스펙(UI Spec)

## 5.1 메인 입력 화면 `/`
- 구성:
  - 상단 헤더: `PhotoScript` + (옵션) Projects 메뉴
  - 중앙:
    - 멀티라인 텍스트 입력(Textarea): “Paste your YouTube script…”
    - 버튼: `Generate`
- 동작:
  - 빈 입력이면 버튼 비활성화 또는 에러 안내
  - 클릭 후 로딩 스피너/프로그레스(“Splitting script… Matching visuals…”)

## 5.2 결과 화면 `/project/:projectId`
레이아웃: 2열 Split View

### 좌측(스크립트 블록 리스트)
- Block 카드 리스트:
  - `Block #`, 텍스트 미리보기(2~3줄)
  - (옵션) 추출 키워드/태그 3~5개 표시
  - 상태 배지: `MATCHED` / `NO_RESULT` / `CUSTOM`
- 블록 클릭 시 해당 블록 선택

### 우측(비주얼 패널)
- 선택된 블록의 대표 Asset 표시(크게):
  - 이미지면 이미지 프리뷰
  - 영상이면 썸네일 + 재생 링크(또는 짧은 미리보기)
- 후보 Asset 갤러리(카드/그리드):
  - 썸네일
  - 출처(Source)
  - 라이선스/사용조건(가능하면)
  - 버튼: `Use this`(대표로 선택)
- (옵션) 검색 재시도/키워드 편집: `Refine keywords` (후속)

---

## 6) 기능 요구사항(Functional Requirements)

### 6.1 Script 입력/저장
- 스크립트는 프로젝트 단위로 저장 가능
- 입력 텍스트 길이 제한(예: 50k chars) + 초과 시 안내
- 자동 저장(후속) 또는 Generate 시 저장

### 6.2 블록 분할(Script Block Split)
- 기본 분할 정책(MVP):
  - 빈 줄(공백 라인) 기준으로 문단 분할
  - 문단이 너무 길면(예: 400~600자 이상) 문장 단위로 추가 분할
- 출력:
  - `blocks[] = { id, index, text }`

### 6.3 키워드/쿼리 생성
각 block에서 검색용 쿼리를 만든다.
- MVP 전략:
  - 간단: TF-IDF/키워드 추출(명사 중심) + 상위 3~7개
  - LLM 보조(옵션): “이 블록을 한 문장 장면 묘사 + 검색 키워드 5개” 생성
- 안전장치:
  - 너무 일반적인 키워드(“사람”, “좋은”, “생각”)는 제거/후순위

### 6.4 Asset 검색 및 후보 수집
이미지/영상 후보를 수집한다.
- 이미지 소스 후보:
  - Unsplash / Pexels / Pixabay 등(라이선스 친화적)
- 영상 소스 후보:
  - Pexels Videos / Pixabay Videos 등(무료 스톡)
- MVP에서는 소스 1~2개만 붙여도 충분.
- 결과:
  - 각 block마다 후보 n개(예: 8~12개) 생성

### 6.5 매칭/랭킹(Matching & Ranking)
- block의 키워드/장면 요약과 asset의 title/tags를 비교해 점수화
- MVP 점수:
  - 키워드 포함 점수 + (옵션) 시맨틱 임베딩 유사도
- 대표 Asset:
  - 최고 점수 1개를 대표로 선택
- NO_RESULT:
  - 후보가 0개면 상태를 `NO_RESULT`로 표시

### 6.6 블록-에셋 매핑 편집
- 사용자는 후보 중 하나를 대표로 선택할 수 있다.
- 선택 시 mapping은 `CUSTOM` 상태로 표시(자동 추천과 구분)

### 6.7 Export(후속)
- 블록별 대표 Asset 링크/출처/라이선스 정보를 CSV/JSON으로 다운로드
- 스토리보드 PDF(블록 텍스트 + 이미지) 생성

---

## 7) 데이터 모델(DB Schema)

### 7.1 projects
- `id` (uuid)
- `title` (optional)
- `script_raw` (text)
- `created_at`, `updated_at`

### 7.2 blocks
- `id`
- `project_id` (FK)
- `index` (int)
- `text` (text)
- `keywords` (json array, optional)
- `status` (`MATCHED` | `NO_RESULT` | `CUSTOM`)
- `created_at`, `updated_at`

### 7.3 assets
(자산은 중복 저장을 줄이기 위해 별도 테이블로 캐싱 가능)
- `id`
- `provider` (unsplash/pexels/...)
- `asset_type` (`IMAGE` | `VIDEO`)
- `source_url`
- `thumbnail_url`
- `title` (optional)
- `license` (optional)
- `meta` (json)
- `created_at`

### 7.4 block_assets
(블록별 후보/대표 연결)
- `id`
- `block_id` (FK)
- `asset_id` (FK)
- `score` (float)
- `is_primary` (bool)
- `chosen_by` (`AUTO` | `USER`)
- `created_at`, `updated_at`

---

## 8) API 스펙(REST, 예시)

Base: `/api/v1`

### 8.1 Project 생성/조회
- `POST /projects`
  - body: `{ script_raw, title? }`
  - response: `{ project_id }`
- `GET /projects/:projectId`
  - response: project + blocks + primary assets

### 8.2 Generate(분할+매칭) 실행
- `POST /projects/:projectId/generate`
  - body: `{ split_policy?, providers?, max_candidates_per_block? }`
  - response: `{ status, job_id }` (비동기 권장)
- `GET /jobs/:jobId`
  - response: `{ status, progress, current_step, error? }`

### 8.3 Block 단위 조작
- `GET /projects/:projectId/blocks`
- `GET /blocks/:blockId/assets`
  - 후보 목록 반환
- `POST /blocks/:blockId/primary`
  - body: `{ asset_id }`  // 유저가 대표 선택

---

## 9) 시스템 아키텍처(System Architecture)

### 9.1 구성(권장)
- Frontend: Next.js(React) + Tailwind
- Backend: FastAPI(or Node/Nest) + PostgreSQL
- Worker: 비동기 작업 큐(RQ/Celery/BullMQ 등)
- Cache: Redis(선택)
- 외부 소스:
  - 이미지/영상 provider API(unsplash/pexels 등)

### 9.2 처리 파이프라인
1) Project 생성/저장
2) Splitter가 blocks 생성
3) Keyword/Query 생성
4) Provider 검색 → 후보 assets 수집
5) Ranking 후 대표 선택
6) DB 저장 → UI에 결과 표시

---

## 10) 오류/엣지 케이스
- 스크립트가 너무 짧으면: 블록 1개로 생성
- provider 응답 실패:
  - 해당 provider만 제외하고 진행
  - 전부 실패 시 `NO_RESULT` 처리
- 특정 블록에서 후보 0개:
  - 우측에 “No results, refine keywords” 안내(후속)
- 동일 asset이 여러 블록에 반복 추천:
  - MVP에서는 허용, 후속으로 중복 페널티 적용 가능

---

## 11) 비기능 요구사항(Non-Functional)
- 심플하고 빠른 인터페이스(스크립트 입력은 즉시 반응)
- Generate는 비동기로 처리(블록 수가 많아도 UI가 멈추지 않음)
- 라이선스/출처 정보는 가능한 한 표시(사용자 신뢰)

---

## 12) MVP 범위(MVP Scope)
필수:
- 메인 입력 + Generate
- 블록 분할
- 블록별 이미지 후보 매칭(최소 1 provider)
- 결과 화면(좌 블록 / 우 이미지)
- 대표 선택(Use this)
- 프로젝트 저장/재접속 시 결과 복원

후속:
- 영상 매칭(2번째 provider)
- 키워드 편집/재검색
- 블록 합치기/나누기
- Export(CSV/JSON/PDF)
- 계정/팀/프로젝트 공유

---

## 13) 개발 난이도 메모
- MVP 난이도: 중
  - 핵심은 “블록 분할 + 검색/랭킹 + 2컬럼 UI”의 파이프라인 연결
- 제품급 난이도: 중상~상
  - 저작권/라이선스 표기, provider 변경 대응, 캐싱/비용 최적화, 편집 UX 고도화

