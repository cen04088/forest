# 13-pjt — 올라 (Olla)

> "산을 올라가다" + 스페인어 인사 Hola  
> AI 기반 산행 안전 진단 및 실시간 위치 공유 서비스

---

## 목차

1. [팀원 정보 및 업무 분담](#1-팀원-정보-및-업무-분담)
2. [목표 서비스 및 실제 구현 정도](#2-목표-서비스-및-실제-구현-정도)
3. [데이터베이스 모델링 (ERD)](#3-데이터베이스-모델링-erd)
4. [추천 알고리즘 기술 설명](#4-추천-알고리즘-기술-설명)
5. [핵심 기능 설명](#5-핵심-기능-설명)
6. [기능별 소스코드 및 실행 화면](#6-기능별-소스코드-및-실행-화면)
7. [생성형 AI 활용](#7-생성형-ai-활용)
8. [배포 서비스 URL](#8-배포-서비스-url)
9. [프로젝트 구조](#9-프로젝트-구조)
10. [실행 방법](#10-실행-방법)
11. [환경 변수](#11-환경-변수)
12. [구현 과정 회고](#12-구현-과정-회고)

---

## 1. 팀원 정보 및 업무 분담

| 이름 | 역할 | 담당 기능 |
|------|------|-----------|
| 장민준 | 팀장 | 전체 아키텍처 설계, 안전 스코어링 알고리즘, Railway 배포 |
| 황도경 | 팀원 | 세이프링크 시스템, 프론트엔드 UI/UX 전반, AI 연동| |


> Git 저장소: ([주소](http://forest-production-10d0.up.railway.app/#/))

---

## 2. 목표 서비스 및 실제 구현 정도

### 목표 서비스

등산 중 발생하는 안전사고를 예방하기 위해:
- **출발 전**: AI가 날씨·재난·일몰 데이터를 종합해 산행 안전 등급(추천/주의/비추천)을 산출
- **산행 중**: 6자리 코드 기반 세이프링크로 보호자와 실시간 위치 공유
- **보호자**: 위치 미갱신 30분·60분 경고로 사고 골든타임 확보

### 실제 구현 정도

| 목표 기능 | 구현 여부 | 비고 |
|-----------|-----------|------|
| 산·코스 선택 + 프로필 입력 | ✅ 완료 | 138개 추천 산, 15종 매력 태그 필터 |
| 실시간 날씨 기반 안전 등급 | ✅ 완료 | 기상청·산불·산사태·미세먼지 5개 지표 종합 |
| AI 산행 안전 브리핑 | ✅ 완료 | Claude Haiku, 1시간 캐시 |
| AI 개인화 안전 조언 | ✅ 완료 | Gemini 2.5 Flash Lite, 산·날씨·목적 기반 3줄 |
| AI 도우미 RAG 채팅 | ✅ 완료 | BM25 31개 지식문서, 멀티턴, 실시간 컨텍스트 주입 |
| 세이프링크 6자리 코드 공유 | ✅ 완료 | URL 없이 구두 전달 가능 |
| 보호자 실시간 위치 지도 | ✅ 완료 | Leaflet + 20초 폴링, GPS 궤적 표시 |
| 30분·60분 위치 미갱신 경고 | ✅ 완료 | 경고 마커 + 긴급 팝업 |
| 보호자 뷰 북한산 시뮬레이션 | ✅ 완료 | 발표·데모용 5단계 이동 시뮬레이션 |
| 등산로 경로 3색 지도 표시 | ✅ 완료 | VWorld + OSM Overpass 폴백 |
| 커뮤니티 게시판 | ✅ 완료 | 게시글·댓글·좋아요·팔로우 |
| 산행 기록 자동 저장 | ✅ 완료 | |
| 즐겨찾기·긴급 연락처 관리 | ✅ 완료 | |
| 산 추천 알고리즘 | ✅ 완료 | 프로필 기반 138개 산 중 개인화 추천 |
| 앱 전역 플로팅 AI 챗봇 | ✅ 완료 | 모든 탭에서 접근 가능 |
| Wake Lock (화면 꺼짐 방지) | ✅ 완료 | 산행 중 화면 유지 |
| Railway 배포 | ✅ 완료 | PostgreSQL + WhiteNoise 정적 서빙 |
| 네이티브 앱 수준 백그라운드 GPS | ❌ 미구현 | 웹 브라우저 구조적 한계 |
| 비상 연락처 자동 SMS 발송 | ❌ 미구현 | 외부 SMS API 필요 |
| 오프라인 지도 캐시 | ❌ 미구현 | Service Worker 추가 필요 |

---

## 3. 데이터베이스 모델링 (ERD)

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   User       │       │   Post           │       │   Comment       │
│──────────────│  1:N  │──────────────────│  1:N  │─────────────────│
│ id (PK)      │──────▶│ id (PK)          │──────▶│ id (PK)         │
│ username     │       │ author (FK→User) │       │ post (FK→Post)  │
│ password     │       │ title            │       │ author (FK→User)│
│ nickname     │       │ content          │       │ content         │
│ email        │       │ category         │       │ created_at      │
│ created_at   │       │ mountain         │       └─────────────────┘
└──────┬───────┘       │ like_count       │
       │               │ created_at       │       ┌─────────────────┐
       │               └──────────────────┘       │   PostLike      │
       │                                          │─────────────────│
       │  1:N          ┌──────────────────┐       │ id (PK)         │
       │               │ AuthToken        │       │ post (FK→Post)  │
       │               │──────────────────│       │ user (FK→User)  │
       ├──────────────▶│ user (FK→User)   │       │ UNIQUE(post,user│
       │               │ key              │       └─────────────────┘
       │               │ expires_at       │
       │               └──────────────────┘       ┌─────────────────┐
       │                                          │  HikingRecord   │
       │  1:N          ┌──────────────────┐       │─────────────────│
       ├──────────────▶│ FavoriteCourse   │       │ id (PK)         │
       │               │──────────────────│       │ user (FK→User)  │
       │               │ user (FK→User)   │       │ mountain        │
       │               │ course_id        │       │ course_name     │
       │               │ course_name      │       │ distance_km     │
       │               │ mountain         │       │ duration_min    │
       │               │ UNIQUE(user,     │       │ hiked_date      │
       │               │   course_id)     │       │ safety_label    │
       │               └──────────────────┘       └─────────────────┘
       │
       │  1:N          ┌──────────────────┐
       ├──────────────▶│ EmergencyContact │
       │               │──────────────────│
       │               │ user (FK→User)   │
       │               │ name             │
       │               │ phone            │
       │               │ relation         │
       │               └──────────────────┘
       │
       │               ┌──────────────────────┐       ┌──────────────────┐
       │               │  SafeLinkSession      │  1:N  │  LocationLog     │
       │               │──────────────────────│──────▶│──────────────────│
       │               │ id (UUID, PK)         │       │ id (PK)          │
       │               │ share_code (6자리     │       │ session (FK→SLS) │
       │               │   UNIQUE)             │       │ lat, lng         │
       │               │ mountain_name        │       │ recorded_at      │
       │               │ course_name          │       └──────────────────┘
       │               │ current_lat, lng     │
       │               │ status (active/ended)│
       │               │ created_at           │
       │               │ last_updated         │
       │               └──────────────────────┘

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  MountainTags    │   │  TrailCourse     │   │  MountainIntro   │
│──────────────────│   │──────────────────│   │──────────────────│
│ mountain_name    │   │ course_id (PK)   │   │ mountain_key     │
│   (UNIQUE)       │   │ mountain         │   │   (UNIQUE)       │
│ tags (JSONField) │   │ name             │   │ intro            │
└──────────────────┘   │ difficulty       │   │ summary          │
                       │ distance_km      │   │ detail           │
                       │ duration_min     │   └──────────────────┘
                       │ elevation_gain_m │
                       │ lat, lng         │
                       │ source           │
                       └──────────────────┘
```

---

## 4. 추천 알고리즘 기술 설명

### 4-1. 코스 추천 알고리즘 (`services.py`)

사용자 프로필(경험 수준, 희망 소요 시간, 이동 가능 거리, 목적, 출발 시간)과
실시간 외부 데이터(날씨, 산불, 재난위험지구)를 결합해 각 등산로에 점수를 매긴다.

#### 1단계 — 5개 세부 점수 산출 (각 0.0~1.0)

**① 날씨 안전도**

기상 데이터를 100점에서 감점하는 방식으로 계산한다.

| 조건 | 감점 |
|------|------|
| 강수량 ≥ 10mm | -45 |
| 강수량 > 0mm | -20 |
| 풍속 ≥ 8m/s | -30 |
| 풍속 ≥ 5m/s | -15 |
| 기온 ≤ 0°C 또는 ≥ 32°C | -20 |
| 비 + 강풍 동시 발생 | -20 추가 |
| 영하 + 강수 (결빙) | -15 추가 |
| 불쾌지수 ≥ 80 | -12 |
| PM2.5 ≥ 75μg/m³ | -18 |
| PM2.5 ≥ 35μg/m³ | -9 |

> 불쾌지수(DI) = 0.81×기온 + 0.01×습도×(0.99×기온 − 14.99) + 46.3

**② 소요시간 적합도**

코스 소요 시간이 사용자의 가용 시간에 얼마나 맞는지 측정한다.
- 코스 시간 ≤ 가용 시간: 활용률 65% 이상 → 1.0, 미만은 선형 감소
- 코스 시간 > 가용 시간: 초과율에 따라 최소 0.0까지 급격히 감소

**③ 난이도 적합도**

사용자 경험(beginner=1, intermediate=2, advanced=3)과 코스 난이도(easy=1, medium=2, hard=3)의 차이로 계산한다.
- 격차 0 → 1.00 / 격차 1 → 0.55 / 격차 2 → 0.10

**④ 접근성**

사용자 최대 이동 거리 내에서는 거리에 비례해 0.70~1.0 점수 부여. 초과 시 급감.

**⑤ 일조 여유**

일몰까지 남은 시간(코스 소요 시간 감산 후 기준):
- 90분 이상 → 1.0 / 30분 미만 → 0.35 / 일몰 후 → 0.0

#### 2단계 — 목적별 가중치 적용

| 목적 | 난이도 | 소요시간 | 접근성 | 날씨 | 일조 |
|------|--------|----------|--------|------|------|
| 균형·전망 | 30% | 20% | 20% | 20% | 10% |
| 힐링 | 20% | 20% | 20% | **30%** | 10% |
| 운동 | **35%** | 20% | 15% | 20% | 10% |

#### 3단계 — 재난 보정 및 데이터 품질 배수

```
raw = 5개 요소 가중 합산 (0.0~1.0)
raw × 데이터 품질 배수 (거리 < 0.3km → 0.50 / 좌표 없음 → 0.75 / 정상 → 1.0)
raw -= 재난위험 감점 (고위험 1개당 -0.06, 최대 -0.15)
total = min(max(raw, 0.0), 1.0) × 100
```

#### 4단계 — 룰 기반 안전 등급 (점수와 독립적으로 적용)

점수가 높아도 아래 조건 중 하나라도 해당하면 강제 등급 하향.

| 등급 | 조건 |
|------|------|
| 🔴 비추천 | 강수 ≥ 10mm, 풍속 ≥ 8m/s, 일몰 여유 < 30분, 산불 very_high 중 하나라도 |
| 🟡 주의 | 날씨 점수 < 75, 난이도 적합도 < 0.40, 노랑 플래그 2개 이상 중 하나라도 |
| 🟢 추천 | 위 조건 없음 |

---

### 4-2. 산 추천 알고리즘 (`mountain_recommend.py`)

138개 산 중 사용자 조건에 맞는 산을 날씨·소요시간·일몰·거리 4개 요소로 순위를 매긴다.

| 요소 | 가중치 | 계산 방식 |
|------|--------|-----------|
| 날씨 안전도 | 32% | 코스 날씨 점수와 동일 |
| 소요시간 적합도 | 24% | 산의 min/max 소요 시간 vs 희망 시간 |
| 일몰 여유 | 23% | 코스와 동일 기준 |
| 이동 거리 | 18% | 30km 이하 → 1.0, 거리에 비례해 최저 0.20 |

**하드 오버라이드**: 산사태 경보 지역이거나 날씨 점수 < 0.20이면 비추천 강제.

---

## 5. 핵심 기능 설명

### 5-1. 안전 코스 추천 탭

- 출발 시간·희망 소요 시간·최대 이동 거리·경험 수준 입력
- 15종 매력 태그(조망·계곡·단풍·가족·야경 등)로 산 필터링
- AI 산 추천 → 오늘의 날씨·안전 지표 기반 산 순위 정렬
- 산 클릭 시: 등산로 목록, Leaflet 지도(3색 경로), 재난위험지구 패널, 커뮤니티 안전 제보 표시
- Claude Haiku 안전 브리핑 카드 (상단 고정)

### 5-2. 세이프링크 (안전 공유 탭)

```
산행자                          보호자
───────                         ────────
산행 시작 클릭
  ↓
SafeLinkSession DB 생성
  ↓
6자리 코드 발급 (예: A3K7PQ)
  ↓
코드 구두/문자 전달 ──────────▶  코드 6자리 입력
                                  ↓
GPS watchPosition 전송             20초 폴링으로 위치 수신
  ↓                               ↓
LocationLog 누적              파란 폴리라인으로 궤적 표시
  ↓                               ↓
  ·                           30분 미갱신 → 경고 마커·배너
  ·                           60분 미갱신 → 긴급 팝업
산행 종료 클릭
```

**코드 생성 규칙**: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` 32자 (혼동 문자 0·O·I·1 제외), 6자리, 활성 세션과 충돌 검사 후 발급

### 5-3. 보호자 뷰

- `position: fixed` 풀스크린 지도 + 하단 정보 시트
- Teleport to body로 사이드바 레이아웃 외부에 렌더링
- 30분 미갱신: 빨간 Pulsing 마커 + 상단 경고 배너
- 60분 미갱신: 긴급 모달 (119 신고 버튼)
- 북한산 데모 시뮬레이션: 도선사→하루재 5단계 이동 체험

### 5-4. 커뮤니티

- 게시글 작성(일반·등산 후기·산 정보·안전 제보)·수정·삭제
- 댓글·좋아요·팔로우 / 팔로잉 피드
- 안전 제보 게시글은 코스 상세 화면에 연동

### 5-5. 마이페이지

- 즐겨찾기 코스 카드 그리드 → "산 정보 보기" 클릭 시 GuideTab 연결
- 챌린지 배지 시스템
- 내 활동: 작성글·좋아요한 글·댓글 탭 분리
- 긴급 연락처 카드 (전화번호 tel: 링크)

---

## 6. 기능별 소스코드 및 실행 화면

> 스크린샷은 `docs/screenshots/` 폴더에 이미지를 넣으면 아래 항목에 자동 표시됩니다.

---

### 6-1. 안전 코스 추천

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/GuideTab.vue` | 프로필 입력 폼, 산 선택, 탐방로 목록, 지도 표시 |
| `backend/recommendations/services.py` | 5개 지표 점수 계산, 안전 등급 판정 |
| `backend/recommendations/mountain_recommend.py` | 138개 산 순위 정렬 알고리즘 |
| `backend/recommendations/llm_briefing.py` | Claude Haiku 브리핑 카드 생성 |

```python
# services.py — 안전 등급 강제 하향 룰 (점수와 무관)
if rain_mm >= 10 or wind_ms >= 8 or sunlight_margin_min < 30 or wildfire == 'very_high':
    grade = 'danger'
elif weather_score < 0.75 or difficulty_fit < 0.40 or yellow_flags >= 2:
    grade = 'caution'
else:
    grade = 'safe'
```

**실행 화면**

![안전 코스 추천 — 메인](docs/screenshots/guide_main.png)
![안전 코스 추천 — 탐방로 선택](docs/screenshots/guide_trail.png)

---

### 6-2. 세이프링크 (안전 공유)

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/SafeLinkTab.vue` | 산행 시작/종료, GPS 전송, 코드 공유 UI |
| `backend/recommendations/safe_links.py` | 6자리 코드 발급, 세션 관리 |
| `backend/recommendations/views.py` | `/api/safe-link/` 엔드포인트 |

```python
# safe_links.py — 혼동 문자 제외 6자리 코드 발급
CHARSET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 0·O·I·1 제외

def generate_share_code():
    while True:
        code = ''.join(random.choices(CHARSET, k=6))
        if not SafeLinkSession.objects.filter(share_code=code, status='active').exists():
            return code
```

**실행 화면**

![세이프링크 — 산행 시작](docs/screenshots/safelink_start.png)
![세이프링크 — 코드 공유](docs/screenshots/safelink_code.png)

---

### 6-3. 보호자 실시간 뷰

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/GuardianView.vue` | 풀스크린 지도, 20초 폴링, 경고 로직 |
| `frontend/src/views/GuardianCodeView.vue` | 6자리 코드 입력 화면 |

```javascript
// GuardianView.vue — 30분·60분 미갱신 경고
const minutesSinceUpdate = computed(() =>
  Math.floor((Date.now() - new Date(session.value.last_updated)) / 60000)
);
const isWarning = computed(() => minutesSinceUpdate.value >= 30);
const isEmergency = computed(() => minutesSinceUpdate.value >= 60);
```

**실행 화면**

![보호자 뷰 — 실시간 지도](docs/screenshots/guardian_map.png)
![보호자 뷰 — 긴급 경고](docs/screenshots/guardian_alert.png)

---

### 6-4. AI 도우미 채팅 (RAG)

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/ChatTab.vue` | 멀티턴 채팅 UI |
| `backend/recommendations/chat_ai.py` | Gemini API 호출, 시스템 프롬프트 조립 |
| `backend/recommendations/rag_retriever.py` | BM25 검색, 31개 지식문서 |

```python
# rag_retriever.py — 순수 파이썬 BM25 (외부 라이브러리 없음)
def bm25_score(query_tokens, doc_tokens, avg_dl, k1=1.5, b=0.75):
    score = 0.0
    dl = len(doc_tokens)
    for term in query_tokens:
        tf = doc_tokens.count(term)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
    return score
```

**실행 화면**

![AI 도우미 — 채팅](docs/screenshots/chat_main.png)

---

### 6-5. 커뮤니티

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/CommunityTab.vue` | 게시판 목록·상세·작성 UI |
| `backend/recommendations/community_views.py` | 게시글 CRUD, 댓글, 좋아요, 팔로우 |

```python
# community_views.py — 팔로잉 피드 (팔로우한 사람 글만 조회)
@api_view(['GET'])
@require_auth
def following_posts(request):
    following_ids = UserFollow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)
    posts = Post.objects.filter(author_id__in=following_ids).order_by('-created_at')
    return paginate_posts(posts, request)
```

**실행 화면**

![커뮤니티 — 게시판](docs/screenshots/community_list.png)
![커뮤니티 — 게시글 상세](docs/screenshots/community_detail.png)

---

### 6-6. 마이페이지

**주요 소스코드**

| 파일 | 역할 |
|------|------|
| `frontend/src/views/MyPageTab.vue` | 즐겨찾기, 배지, 산행 기록, 긴급 연락처 |
| `backend/recommendations/views.py` | 사용자 프로필, 즐겨찾기, 연락처 API |

**실행 화면**

![마이페이지 — 메인](docs/screenshots/mypage_main.png)
![마이페이지 — 산행 기록](docs/screenshots/mypage_records.png)

---

## 7. 생성형 AI 활용

### 사용 모델

| 역할 | 모델 | API 키 |
|------|------|--------|
| 산행 안전 브리핑 카드 | Claude Haiku (`claude-haiku-4-5-20251001`) | `ANTHROPIC_API_KEY` |
| AI 도우미 멀티턴 채팅 | Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`) | `GEMINI_API_KEY` |
| 개인화 안전 조언 3줄 | Gemini 2.5 Flash Lite | `GEMINI_API_KEY` |

### 6-1. Claude Haiku — 안전 브리핑 (`llm_briefing.py`)

코스 추천 결과 최상단에 표시되는 카드. 선택 산·날씨·난이도·재난 정보를 프롬프트에 주입해 "지금 이 산에 가도 되는가"를 3문장으로 요약한다. 동일 조건에 대해 1시간 Django 캐시 적용.

### 6-2. Gemini — AI 도우미 채팅 (`chat_ai.py`)

**RAG(Retrieval-Augmented Generation) 파이프라인**:

```
사용자 메시지
  ↓
BM25 검색 (rag_retriever.py)
  ├── 정적 지식베이스 31개 문서
  │     (응급처치·날씨·장비·코스·계절별 주의사항·국립공원 규정 등)
  ├── 탐방로 데이터 (국립공원공단 CSV 302개 코스)
  └── 재난위험지구 (현재 선택 산 기준)
  ↓
시스템 프롬프트에 [참고 정보] 섹션 삽입
  + 실시간 컨텍스트 주입
    (선택 산 이름·고도·난이도, 현재 날씨, 산불위험, 산사태, NIFOS 산악기상, 에어코리아 대기질)
  ↓
Gemini API 호출 (max_output_tokens: 400)
  ↓
멀티턴 대화 (이전 메시지 전체 contents로 전달)
```

BM25는 외부 의존성 없이 순수 파이썬으로 구현해 서버 리소스를 최소화했다.

### 6-3. Gemini — 개인화 안전 조언 (`safety_advice_ai.py`)

산 선택 직후 사이드바에 표시. 선택 산·실시간 날씨·산행 목적·일몰 시간을 기반으로 "오늘 이 산을 오를 때 특히 주의할 점" 3줄을 생성한다.

### 개발 과정에서의 AI 활용

- 프롬프트 설계 시 키/값 구조로 컨텍스트를 구조화해 환각을 줄이고 일관성을 높였다.
- 캐시 전략(1시간 Django cache)으로 동일 조건에 대한 반복 API 호출 비용을 절감했다.
- 키 미설정 시 안전한 폴백(템플릿 텍스트 반환)을 구현해 API 없는 환경에서도 서비스가 동작하도록 했다.

---

## 8. 배포 서비스 URL

| 항목 | 내용 |
|------|------|
| 서비스 URL | Railway 배포 ([주소](http://forest-production-10d0.up.railway.app/#/)) |
| 백엔드 | gunicorn + Django + PostgreSQL (Railway) |
| 프론트엔드 | Vite 빌드 → WhiteNoise 정적 서빙 |

### 배포 구성

```
Backend:  pip install -r requirements.txt
          python manage.py migrate --noinput
          python manage.py seed_mountain_descriptions
          python manage.py seed_mountain_tags
          gunicorn forestrx.wsgi

Frontend: npm run build
          → Django STATIC_ROOT에 번들 복사
          → WhiteNoise로 서빙
```

### 커뮤니티 샘플 데이터

Railway PostgreSQL에 fixture 데이터 적재 완료.

| 항목 | 내용 |
|------|------|
| 사용자 | 5개 계정 (트레일버디·정상정복·안전산행·주말등산러·산악엄마) |
| 게시글 | 8개 (북한산 백운대 후기, 설악산 단풍, 낙석 안전제보, 장비 추천 등) |
| 댓글 | 9개 |

---

## 9. 프로젝트 구조

```
forest/
├── backend/
│   ├── forestrx/
│   │   └── settings.py              환경 변수 기반 보안 설정
│   └── recommendations/
│       ├── models.py                DB 모델 전체
│       ├── views.py                 코어·세이프링크 뷰
│       ├── community_views.py       커뮤니티·사용자·안전제보 뷰
│       ├── urls.py                  URL 라우팅
│       ├── services.py              코스 추천·안전 스코어링 핵심 로직
│       ├── mountain_recommend.py    산 추천 로직
│       ├── safe_links.py            세이프링크 세션 관리
│       ├── chat_ai.py               Gemini 채팅 (RAG 포함)
│       ├── rag_retriever.py         BM25 RAG 엔진 (31개 문서)
│       ├── llm_briefing.py          Claude Haiku 안전 브리핑
│       ├── weather_api.py           기상청 초단기실황
│       ├── sun_api.py               한국천문연구원 일몰
│       ├── wildfire_api.py          산림청 산불위험예보
│       ├── nifos_api.py             NIFOS 산악기상
│       ├── airquality_api.py        에어코리아 대기질
│       ├── vworld_api.py            국토부 브이월드 등산로
│       ├── local_road_api.py        지방도로 SHP 등산로
│       ├── osm_trail_api.py         OSM Overpass 등산로
│       ├── landslide_api.py         산사태 예측
│       ├── disaster_risk.py         재난위험지구 매칭
│       ├── mountain_data.py         138개 추천 산 정적 데이터
│       ├── mountain_tags.py         15종 매력 태그
│       └── migrations/              0001 ~ 0010
├── frontend/
│   └── src/
│       ├── App.vue                  셸 (사이드바·탭바·router-view)
│       ├── router.js                Vue Router 4 (해시 히스토리)
│       ├── api.js                   백엔드 API 호출 레이어
│       ├── styles.css               전역 스타일
│       ├── views/
│       │   ├── GuideTab.vue         안전코스 추천 탭
│       │   ├── SafeLinkTab.vue      안전공유 탭
│       │   ├── CommunityTab.vue     커뮤니티 탭
│       │   ├── MyPageTab.vue        마이페이지 탭
│       │   ├── ChatTab.vue          AI 도우미 탭
│       │   ├── GuardianView.vue     보호자 실시간 지도 + 시뮬레이션
│       │   └── GuardianCodeView.vue 코드 입력 화면
│       ├── composables/
│       │   ├── useGuide.js          안전코스·추천·날씨 (싱글톤)
│       │   ├── useSafeLink.js       세이프링크·GPS·Wake Lock (싱글톤)
│       │   ├── useAuth.js           인증 (싱글톤)
│       │   ├── useCommunity.js      커뮤니티 (싱글톤)
│       │   ├── useUserData.js       기록·즐겨찾기·연락처 (싱글톤)
│       │   ├── useChat.js           AI 채팅 상태 (싱글톤)
│       │   └── useLeafletMap.js     Leaflet 지도 인스턴스 재사용
│       └── components/
│           ├── MountainCard.vue     산 선택 카드
│           ├── AuthModal.vue        로그인/회원가입 모달
│           ├── OnboardingModal.vue  첫 방문 온보딩
│           └── ChatWidget.vue       플로팅 AI 챗봇 위젯
├── data/
│   └── 국립공원공단_탐방로_20240911.csv
└── requirements.txt
```

---

## 10. 실행 방법

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mountain_tags    # 15종 태그 DB 시드
python manage.py runserver 127.0.0.1:8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite 개발 서버가 `/api` 요청을 `http://127.0.0.1:8000`으로 프록시한다.

---

## 11. 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `PUBLIC_SERVICE_KEY` | ✅ | 공공데이터포털 일반 인증키 (기상청·한국천문연구원·산림청·NIFOS 공통) |
| `DJANGO_SECRET_KEY` | 프로덕션 필수 | 미설정 시 개발용 키 자동 사용 |
| `DATABASE_URL` | 프로덕션 필수 | Railway PostgreSQL. 미설정 시 SQLite 자동 사용 |
| `ANTHROPIC_API_KEY` | 선택 | Claude Haiku 안전 브리핑. 없으면 템플릿 폴백 |
| `GEMINI_API_KEY` | 선택 | Gemini AI 도우미·안전 조언. 없으면 안내 메시지 반환 |
| `DJANGO_DEBUG` | 선택 | `true` / `false` (기본 `false`) |

---

## 12. 구현 과정 회고

### 학습한 내용 및 새로 배운 것들

**Vue 3 Composition API & 싱글톤 Composable 패턴**  
Pinia/Vuex 없이 모듈 레벨 `ref`·`reactive`를 export해 탭 간 상태를 공유하는 패턴을 익혔다. 탭 전환(언마운트/마운트) 시에도 데이터가 유지된다는 점이 SPA에서 특히 유용했다.

**CSS `position: fixed`와 containing block 문제**  
조상 엘리먼트에 `overflow-x: hidden`과 `position: relative`가 동시에 적용되면 Chrome에서 fixed 자식의 containing block이 뷰포트가 아닌 해당 조상으로 바뀐다. Vue의 `<Teleport to="body">`로 DOM 트리 외부에 렌더링해 해결했다.

**BM25 RAG 구현**  
벡터 DB 없이 순수 파이썬으로 BM25 검색을 구현했다. 질의와 문서 간 단어 빈도 기반 유사도만으로도 산행 안전 도메인에서 충분한 검색 정확도를 얻을 수 있었다.

**공공데이터 API 신뢰성 처리**  
기상청·산림청 등 공공 API는 응답 지연·형식 오류가 잦다. `ThreadPoolExecutor`로 병렬 호출해 전체 대기 시간을 줄이고, 개별 API 실패 시 서비스 전체가 중단되지 않도록 try/except로 격리했다.

**Leaflet 지도 경로 on-demand fetch**  
지도 경로를 전부 미리 로드하면 초기 응답이 느려진다. 코스 선택 시에만 VWorld → OSM Overpass 순서로 경로를 요청하고 결과를 캐시에 저장하는 on-demand 패턴을 적용했다.

### 어려웠던 부분

- **GPS 백그라운드 추적 한계**: 웹 브라우저는 화면이 꺼지거나 다른 앱으로 전환되면 GPS 추적이 중단된다. Wake Lock API로 화면 꺼짐은 막았지만, 앱 전환은 막을 수 없어 사용자에게 명확히 안내하는 것으로 대응했다.
- **다중 미디어 쿼리 CSS 우선순위**: 디자이너 합류 이후 동일 클래스에 대한 `@media` 블록이 파일 곳곳에 산재해 후순위 규칙이 의도치 않게 덮어쓰는 문제가 반복됐다. 미디어 쿼리의 소스 순서 우선 원칙을 재확인했다.
- **공공 API 키 1개로 여러 API 사용**: 기상청·한국천문연구원·산림청이 모두 동일한 공공데이터포털 키를 사용하지만 서비스별 등록이 필요하다. 초기 설정 누락으로 특정 API만 인증 오류가 발생하는 상황을 겪었다.

### 느낀 점

세이프링크의 6자리 코드 방식은 URL보다 구두 전달이 쉬워 등산 상황에 적합하다고 판단했는데, 실제로 사용해보니 코드 발급 순간에 보호자에게 전달하는 행동 자체가 자연스러운 "산행 시작 의식"이 된다는 것을 느꼈다. 기술적 구현보다 사용자 행동 흐름 설계가 더 중요하다는 점을 배웠다.  

AI 브리핑 기능은 같은 산이라도 날씨·시간대·목적에 따라 다른 조언을 생성하는데, 이를 위해 컨텍스트를 얼마나 구조화해 전달하느냐가 응답 품질을 결정한다는 것을 반복적인 프롬프트 실험을 통해 체감했다.

---

## 데이터 소스

| 데이터 | 연동 방식 | 상태 |
|--------|-----------|------|
| 국립공원공단 탐방로 CSV | 로컬 파일 파싱 | ✅ 302개 코스 (42개 산) |
| 기상청 초단기실황 | 공공데이터포털 API | ✅ 10분 캐시 |
| 한국천문연구원 일몰 | 공공데이터포털 API | ✅ |
| 산림청 산불위험예보 | 공공데이터포털 API | ✅ |
| 국토부 브이월드 등산로 | OpenAPI | ✅ 경로 geometry 포함 |
| OSM Overpass 등산로 | 무료 퍼블릭 API | ✅ 24시간 캐시 |
| 재난위험지구 | 로컬 CSV/JSON | ✅ |
| 산사태 예측 | 공공데이터포털 API | ✅ |
| NIFOS 산악기상 | 공공데이터포털 API | ✅ AI 컨텍스트 주입 |
| 에어코리아 대기질 | 공공데이터포털 API | ✅ PM2.5·PM10 실시간 |
| Claude Haiku | Anthropic API | ✅ 안전 브리핑 |
| Gemini 2.5 Flash Lite | Google AI API | ✅ 채팅·안전 조언 |
| Leaflet + OSM 타일 | 무료 (키 불필요) | ✅ |
