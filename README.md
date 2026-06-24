# 올라 (Olla)

> "산을 올라가다" + 스페인어 인사 Hola — 동반자가 있는 모든 산행을 안전하게

AI 기반 산행 안전 진단 서비스. 날씨·코스·재난위험·일몰 데이터를 종합해 추천(초록)/주의(노랑)/비추천(빨강) 3단계 안전 등급을 실시간으로 산출하고, 산행 중 6자리 코드 기반 세이프링크로 보호자와 위치를 공유한다.

---

## 목차

1. [서비스 개요](#1-서비스-개요)
2. [구현 완료 기능](#2-구현-완료-기능)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [실행 방법](#4-실행-방법)
5. [환경 변수](#5-환경-변수)
6. [API 엔드포인트](#6-api-엔드포인트)
7. [DB 모델](#7-db-모델)
8. [아키텍처](#8-아키텍처)
9. [안전 등급 스코어링](#9-안전-등급-스코어링)
10. [세이프링크 동작 방식](#10-세이프링크-동작-방식)
11. [AI 도우미 (RAG 채팅)](#11-ai-도우미-rag-채팅)
12. [등산로 경로 데이터](#12-등산로-경로-데이터)
13. [데이터 소스](#13-데이터-소스)
14. [배포 (Railway)](#14-배포-railway)
15. [알려진 제약사항](#15-알려진-제약사항)
16. [잔여 과제](#16-잔여-과제)

---

## 1. 서비스 개요

### 핵심 원칙

- **안전 등급 우선**: 점수(숫자)는 내부 계산에만 사용하고, 사용자에게는 등급(추천/주의/비추천) + 이유 텍스트만 노출
- **목적 맞춤 추천**: 힐링·운동·전망·균형 목적에 따라 5개 평가 요소의 가중치를 동적으로 조정
- **코드 기반 위치 공유**: URL 대신 6자리 코드로 보호자와 공유 → 전화로도 구두 전달 가능
- **AI 통합**: Gemini 2.5 Flash Lite 기반 RAG 채팅 + Claude Haiku 안전 브리핑

### 시연 흐름

1. **산 선택** → 날씨 자동 로드 (138개 추천 산 직접 찾기 또는 AI 추천)
2. **태그 필터** → 조망·계곡·단풍 등 15종 매력 태그로 원하는 산 필터링
3. **조건 입력** → 산행 목적(힐링/운동/전망/균형) · 출발 시간
4. **안전코스 찾기** → AI 브리핑 카드 최상단 + Top3 추천
5. **코스 카드 클릭** → Leaflet 지형도 + 3색 등산로 + 위험 마커 + 커뮤니티 안전 제보
6. **안전공유 탭** → "산행 시작" → **6자리 코드** 생성 (예: `A3K7PQ`)
7. **코드 공유** → 보호자가 "보호자" 탭에서 코드 입력 → 실시간 위치 확인
8. **AI 도우미 탭** → 산행 안전·코스·장비 질문 → Gemini RAG 답변
9. **산행 종료** → 기록 자동 저장 → 내정보 탭에서 확인

---

## 2. 구현 완료 기능

| 기능 | 상태 | 비고 |
|------|------|------|
| 산·코스 선택 + 프로필 입력 | ✅ | 산행 목적(힐링/운동/전망/균형) · 경험 수준 포함 |
| **15종 매력 태그 시스템** | ✅ | 138개 산 DB 저장, 검색 필터·상세 헤더 표시 |
| 기상청 초단기실황 실시간 연동 | ✅ | 10분 캐시 |
| 안전 등급 기반 Top3 추천 | ✅ | 점수 숫자 비표시 |
| AI 안전 브리핑 (Claude Haiku) | ✅ | 결과 최상단 카드, 1시간 캐시 |
| **AI 개인화 안전 조언 (Gemini 2.5 Flash Lite)** | ✅ | 산·날씨·목적·일몰 맞춤 3줄 조언 |
| **AI 도우미 채팅 탭 (Gemini 2.5 Flash Lite + RAG)** | ✅ | 멀티턴, 실시간 안전 현황 컨텍스트 주입 |
| **플로팅 ChatWidget** | ✅ | 채팅 탭 외 모든 탭에 상시 노출 |
| **온보딩 모달 (첫 방문)** | ✅ | localStorage `ollaOnboarded` |
| 한국천문연구원 일몰 연동 | ✅ | |
| 산림청 산불위험예보 연동 | ✅ | |
| **NIFOS 산악기상 연동** | ✅ | 국립산림과학원, AI 컨텍스트 주입 |
| **에어코리아 대기질 연동** | ✅ | PM2.5·PM10 실시간, AI 컨텍스트 주입 |
| **산 스토리 API** | ✅ | 선택 산 정보·역사 제공 |
| **산악기상 전용 API** | ✅ | 산 기준 날씨 조회 |
| 재난위험지구 매칭·감점 | ✅ | |
| Leaflet + OSM 지도 | ✅ | 카카오맵 키 불필요 |
| 등산로 경로 3색 표시 | ✅ | 안전(초록)/주의(주황)/위험(빨강 점선) |
| VWorld 경로 on-demand fetch | ✅ | 코스 선택 시 자동 조회·캐시 |
| OSM Overpass 경로 폴백 | ✅ | VWorld 없을 때, 24시간 캐시 |
| 커뮤니티 안전 제보 → 지도 연동 | ✅ | 코스 상세에 경고 패널 |
| **세이프링크 6자리 코드** | ✅ | URL 공유 대신 코드 입력 방식 |
| 세이프링크 GPS 궤적 저장 | ✅ | LocationLog, 보호자 지도에 파란 선 |
| Wake Lock (화면 꺼짐 방지) | ✅ | 산행 중 화면 유지 |
| 보호자 코드 입력 전용 화면 | ✅ | `/guardian` 라우트, 6칸 입력 UI |
| 커뮤니티 게시판·댓글·좋아요 | ✅ | |
| 좋아요한 게시글 목록 | ✅ | |
| 산행 기록 자동 저장 | ✅ | |
| 즐겨찾기 코스 | ✅ | |
| 긴급 연락처 관리 | ✅ | |
| 출발 전 체크리스트 | ✅ | localStorage 저장 |
| 인증 토큰 30일 만료 | ✅ | |
| Vue Router URL 기반 라우팅 | ✅ | 해시 히스토리, 뒤로가기·딥링크 지원 |
| Railway PostgreSQL 연동 | ✅ | |
| **사이드바 실시간 날씨 위젯** | ✅ | 선택 산 날씨·산불 미니 게이지 상시 표시 |

---

## 3. 프로젝트 구조

```
forest/
├── backend/
│   ├── forestrx/
│   │   └── settings.py          환경 변수 기반 보안 설정
│   └── recommendations/
│       ├── models.py             DB 모델 전체
│       ├── views.py              코어·세이프링크 뷰
│       ├── community_views.py    커뮤니티·사용자·안전제보 뷰
│       ├── urls.py               URL 라우팅
│       ├── services.py           추천·안전 스코어링 핵심 로직
│       ├── safe_links.py         세이프링크 세션 관리 (DB 기반)
│       ├── chat_ai.py            Gemini 2.5 Flash Lite 채팅 (RAG 포함)
│       ├── safety_advice_ai.py   Gemini 안전 조언 생성 (3줄 맞춤형)
│       ├── rag_retriever.py      BM25 RAG 엔진 (지식베이스 31개 문서)
│       ├── llm_briefing.py       Claude Haiku 안전 브리핑 (1시간 캐시)
│       ├── osm_trail_api.py      OSM Overpass 등산로 경로 조회
│       ├── weather_api.py        기상청 초단기실황
│       ├── mountain_weather_api.py  산악기상 전용 조회
│       ├── sun_api.py            한국천문연구원 일몰
│       ├── wildfire_api.py       산림청 산불위험예보
│       ├── forest_api.py         산림청 산림공간정보
│       ├── nifos_api.py          국립산림과학원 산악기상
│       ├── airquality_api.py     에어코리아 대기질 (PM2.5·PM10 실시간)
│       ├── vworld_api.py         국토부 브이월드 등산로
│       ├── local_road_api.py     지방도로 등산로
│       ├── landslide_api.py      산사태 예측
│       ├── disaster_risk.py      재난위험지구 매칭
│       ├── mountain_story_api.py 산 정보·스토리 제공
│       ├── mountain_data.py      138개 추천 산 정적 데이터
│       ├── mountain_tags.py      15종 매력 태그 정의 및 산별 배치
│       ├── mountain_recommend.py 산 추천 로직
│       ├── mountain_coordinates.py 산 좌표 데이터
│       ├── data_sources.py       데이터 소스 목록 API
│       └── migrations/           0001 ~ 0010
├── frontend/
│   └── src/
│       ├── App.vue               셸 (히어로·사이드바 날씨위젯·탭바·router-view)
│       ├── router.js             Vue Router 4 (해시 히스토리)
│       ├── api.js                백엔드 API 호출 레이어
│       ├── views/
│       │   ├── GuideTab.vue          안전코스 추천 탭 (태그 필터·산 상세 포함)
│       │   ├── SafeLinkTab.vue       안전공유 탭 (2컬럼)
│       │   ├── CommunityTab.vue      커뮤니티 탭 (포스트 그리드)
│       │   ├── MyPageTab.vue         내정보 탭 (3컬럼 그리드)
│       │   ├── ChatTab.vue           AI 도우미 탭 (Gemini RAG 채팅)
│       │   ├── GuardianView.vue      보호자 실시간 위치
│       │   └── GuardianCodeView.vue  코드 입력 화면
│       ├── composables/
│       │   ├── useGuide.js           안전코스·추천·날씨 (싱글톤)
│       │   ├── useSafeLink.js        세이프링크·GPS 추적·Wake Lock (싱글톤)
│       │   ├── useAuth.js            인증 (싱글톤)
│       │   ├── useCommunity.js       커뮤니티 (싱글톤)
│       │   ├── useUserData.js        기록·즐겨찾기·연락처 (싱글톤)
│       │   ├── useChat.js            AI 채팅 메시지·로딩 상태 (싱글톤)
│       │   ├── useAppState.js        탭 간 공유 전역 상태
│       │   ├── useLeafletMap.js      Leaflet + OSM 지도
│       │   ├── useKakaoMap.js        카카오맵 (선택적)
│       │   └── useLocation.js        GPS 위치
│       ├── components/
│       │   ├── CourseCard.vue        코스 카드
│       │   ├── MountainCard.vue      산 선택 카드 (태그 표시 포함)
│       │   ├── AuthModal.vue         로그인/회원가입 모달
│       │   ├── OnboardingModal.vue   첫 방문 온보딩 모달
│       │   └── ChatWidget.vue        플로팅 AI 챗봇 위젯
│       └── utils/
│           ├── courseHelpers.js      코스 데이터 유틸
│           └── dateHelpers.js        날짜 포맷 유틸
├── data/
│   └── 국립공원공단_탐방로_20240911.csv
├── requirements.txt
└── docs/                         (참고용 설계 문서)
```

---

## 4. 실행 방법

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mountain_tags   # 15종 태그 DB 시드
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

## 5. 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `PUBLIC_SERVICE_KEY` | ✅ | 공공데이터포털 일반 인증키 (기상청·한국천문연구원·산림청·NIFOS 산악기상 공통) |
| `DJANGO_SECRET_KEY` | 프로덕션 필수 | 미설정 시 개발용 키 자동 사용. `DATABASE_URL` 또는 `RAILWAY_PUBLIC_DOMAIN` 존재 시 미설정이면 즉시 오류 |
| `DJANGO_DEBUG` | 선택 | `true` / `false` (기본값 `false`) |
| `DATABASE_URL` | 프로덕션 필수 | Railway PostgreSQL 연결 문자열. 미설정 시 SQLite 자동 사용 |
| `ANTHROPIC_API_KEY` | 선택 | Claude Haiku 안전 브리핑 생성. 없으면 템플릿 폴백 |
| `GEMINI_API_KEY` | 선택 | Gemini 2.5 Flash Lite AI 도우미 채팅 및 개인화 안전 조언. 없으면 안내 메시지 반환 |
| `RAILWAY_PUBLIC_DOMAIN` | 자동 주입 | 프로덕션 환경 감지용 |

---

## 6. API 엔드포인트

### 코어

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health/` | 서비스 상태, 공공데이터키 로드 확인 |
| GET | `/api/data-sources/` | 연동 데이터 소스 목록 및 상태 |
| GET | `/api/courses/` | 전체 탐방로 목록 (302개) |
| GET | `/api/mountains/` | 올라 추천 산 목록 (138개, 태그 포함) |
| POST | `/api/recommend-mountains/` | 프로필 기반 산 추천 |
| POST | `/api/recommendations/` | 안전 코스 추천 (body: profile + location) |
| GET | `/api/weather/?lat=&lng=` | 기상청 초단기실황 (10분 캐시) |
| GET | `/api/mountain-weather/?mountain=` | 산악기상 전용 조회 |
| GET | `/api/sun-times/?lat=&lng=` | 한국천문연구원 일출·일몰 |
| GET | `/api/wildfire/` | 산림청 산불위험예보 |
| GET | `/api/landslide/?sgg=` | 산사태 예측 |
| GET | `/api/disaster-zones/?mountain=` | 재난위험지구 조회 |
| GET | `/api/forest-spatial/?mountain=` | 산림청 산림공간정보 |
| GET | `/api/vworld-trails/?lat=&lng=&mountain=` | 브이월드 등산로 (경로 geometry 포함) |
| GET | `/api/osm-trails/?lat=&lng=&mountain=&radius=` | OSM 등산로 경로 (24시간 캐시) |
| GET | `/api/mountain-story/?mountain=` | 산 정보·역사·소개 |
| GET | `/api/safety-reports/?mountain=` | 커뮤니티 안전 제보 게시글 |
| GET | `/api/air-quality/?sido=` | 에어코리아 대기질 (PM2.5·PM10) |
| GET | `/api/nifos-mountain-weather/?mountain=` | NIFOS 산악기상 (기온·풍속·강수·습도·적설) |

### AI

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/chat/` | Gemini 2.5 Flash Lite 멀티턴 채팅 (RAG + 실시간 안전 현황 컨텍스트) |
| POST | `/api/safety-advice/` | Gemini 개인화 안전 조언 3줄 생성 (산·날씨·목적·일몰 기반) |

### 세이프링크

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/safe-links/` | 세션 생성 → `{id, share_code}` 반환 |
| GET | `/api/safe-links/{id}/` | 보호자용 세션 조회 (trail 궤적 포함) |
| POST | `/api/safe-links/{id}/` | 위치 업데이트 `{lat,lng}` 또는 종료 `{action:"end"}` |
| GET | `/api/safe-links/by-code/?code=` | **6자리 코드로 세션 조회** |

### 인증

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auth/register/` | 회원가입 |
| POST | `/api/auth/login/` | 로그인 (토큰 반환, 30일 만료) |
| POST | `/api/auth/logout/` | 로그아웃 |
| GET | `/api/auth/me/` | 내 정보 |

### 커뮤니티

| Method | Path | 설명 |
|--------|------|------|
| GET/POST | `/api/posts/` | 게시글 목록·작성 |
| GET/PUT/DELETE | `/api/posts/{id}/` | 게시글 상세·수정·삭제 |
| POST | `/api/posts/{id}/like/` | 좋아요 토글 |
| GET/POST | `/api/posts/{id}/comments/` | 댓글 목록·작성 |
| PUT/DELETE | `/api/comments/{id}/` | 댓글 수정·삭제 |
| GET | `/api/safety-reports/` | 안전 제보 게시글 조회 |
| GET | `/api/my-posts/` | 내 게시글 |
| GET | `/api/liked-posts/` | 좋아요한 게시글 |

### 내 활동

| Method | Path | 설명 |
|--------|------|------|
| GET/POST | `/api/hiking-records/` | 산행 기록 목록·저장 |
| DELETE | `/api/hiking-records/{id}/` | 산행 기록 삭제 |
| GET/POST | `/api/favorites/` | 즐겨찾기 목록·추가 |
| DELETE | `/api/favorites/{course_id}/` | 즐겨찾기 삭제 |
| GET/POST | `/api/emergency-contacts/` | 긴급 연락처 목록·추가 |
| DELETE | `/api/emergency-contacts/{id}/` | 긴급 연락처 삭제 |

---

## 7. DB 모델

| 모델 | 주요 필드 | 설명 |
|------|-----------|------|
| `AuthToken` | user, key, expires_at | 인증 토큰 (30일 만료) |
| `Post` | author, title, content, mountain, category | 커뮤니티 게시글 |
| `Comment` | post, author, content | 댓글 |
| `PostLike` | post, user | 좋아요 (unique: post+user) |
| `HikingRecord` | user, mountain, course_name, hiked_date, safety_label | 산행 기록 |
| `FavoriteCourse` | user, course_id, course_name (unique: user+course_id) | 즐겨찾기 |
| `EmergencyContact` | user, name, phone, relation | 긴급 연락처 |
| `SafeLinkSession` | id(UUID), **share_code**(6자리 unique), course 정보, current_lat/lng, status | 세이프링크 세션 |
| `LocationLog` | session(FK), lat, lng, recorded_at | GPS 궤적 로그 |
| `MountainTags` | mountain_name(unique), tags(JSONField) | 산별 15종 매력 태그 |

---

## 8. 아키텍처

### 프론트엔드 상태 관리

Pinia/Vuex 없이 **모듈 레벨 싱글톤 composable** 패턴 사용.  
탭 이동(언마운트/마운트)에도 상태가 유지된다.

| Composable | 역할 |
|------------|------|
| `useGuide` | 코스·추천·날씨·GPS 상태 |
| `useSafeLink` | 세이프링크 세션·GPS 추적·Wake Lock |
| `useAuth` | 로그인 상태·토큰 |
| `useCommunity` | 게시글·댓글 |
| `useUserData` | 기록·즐겨찾기·연락처 |
| `useChat` | AI 채팅 메시지·로딩·에러 상태 |
| `useAppState` | 탭 간 공유 전역 상태 (selectedCourse, weatherData 등) |
| `useLeafletMap` | 지도 인스턴스 재사용 (깜빡임 없음) |

### 백엔드 AI 구성

| 역할 | 모델 | 키 | 캐시 |
|------|------|----|------|
| 안전 브리핑 카드 | Claude Haiku | `ANTHROPIC_API_KEY` | 1시간 Django cache |
| AI 도우미 채팅 | Gemini 2.5 Flash Lite | `GEMINI_API_KEY` | 없음 (멀티턴) |
| 개인화 안전 조언 | Gemini 2.5 Flash Lite | `GEMINI_API_KEY` | 없음 |

### 백엔드 API 호출 구조

```
추천 요청 시 ThreadPoolExecutor(max_workers=3) 병렬 호출:
├── local_road_api   지방도로 등산로
├── vworld_api       국토부 브이월드
└── forest_api       산림청 산림공간정보

별도 캐시:
├── weather_api          기상청 (10분 Django cache)
├── osm_trail_api        OSM Overpass (24시간 Django cache)
├── llm_briefing         Claude 브리핑 (1시간 Django cache)
├── nifos_api            NIFOS 산악기상 (lru_cache)
└── airquality_api       에어코리아 대기질 (lru_cache)
```

### 데스크톱 레이아웃 (1024px+)

| 탭 | 레이아웃 |
|---|---|
| 안전코스 | 좌(폼+날씨 sticky) / 우(결과목록) 2컬럼 |
| 안전공유 | 좌(지도+카드) / 우(컨트롤+외부링크) 2컬럼 |
| 커뮤니티 | 포스트 카드 3컬럼 그리드 (1440px+에서 4컬럼) |
| 내정보 | 상단 3컬럼(개인설정/즐겨찾기/산행기록) + 하단 2컬럼(긴급연락처+체크리스트) |
| AI 도우미 | 풀 채팅 쉘 (메시지 리스트 + 하단 입력창) |

---

## 9. 안전 등급 스코어링

### 코스 추천 스코어링 (services.py)

#### 1단계: 5개 세부 점수 (모두 0.0~1.0)

| 점수 | 계산 방식 |
|------|-----------|
| **난이도 적합** | 경험(초보1/중급2/숙련3) vs 코스 난이도 차이(gap)마다 -0.45. gap=0→1.0, gap=1→0.55, gap=2→0.1 |
| **시간 적합** | 가용시간 초과 시 급감. 65% 이상 활용 시 1.0, 35~65% 구간 0.7~1.0 |
| **접근성** | max_km 이내 0.70~1.0 선형. 초과 시 급감 (최저 0.0) |
| **날씨** | weather_safety_score(0~100) ÷ 100 |
| **일조 여유** | 일몰까지 ≥90분:1.0 / ≥60분:0.85 / ≥30분:0.65 / ≥0분:0.35 / ≥-30분:0.10 / 초과:0.0 |

#### 2단계: 목적별 가중치 (합계 1.0)

| 목적 | 난이도 | 시간 | 접근성 | 날씨 | 일조 |
|------|--------|------|--------|------|------|
| 균형 / 전망 | 30% | 20% | 20% | 20% | 10% |
| 힐링 | 20% | 20% | 20% | **30%** | 10% |
| 운동 | **35%** | 20% | 15% | 20% | 10% |

#### 3단계: 보정 및 최종 점수

```
raw = 5개 요소 가중 합산 (0.0~1.0)
raw × 데이터 품질 배수: 거리<0.3km → 0.50 / 좌표없음 → 0.75 / 일반명 → 0.82 / 정상 → 1.0
raw -= 재난위험 감점 (고위험 1개당 -0.06, 주의 1개당 -0.02, 최대 -0.15)
total = min(max(raw, 0.0), 1.0) × 100
```

#### 4단계: 룰 기반 안전 등급 (점수와 독립)

**비추천(빨강)** — 하나라도 해당 시:
- 강수량 ≥ 10mm / 풍속 ≥ 8m/s
- 일몰 전 하산 불가 또는 여유 < 30분
- 산불 very_high / 재난위험지구 고위험 / 고도 상승 ≥ 900m

**주의(노랑)** — 빨강 없고:
- 노랑플래그 ≥ 2개 또는 날씨점수 < 75 또는 난이도 적합도 < 0.40

**추천(초록)** — 위 조건 모두 해당 없음

---

### 산 추천 스코어링 (mountain_recommend.py)

#### 가중치 (합계 1.0)

| 요소 | 가중치 |
|------|--------|
| 날씨 | 32% |
| 소요시간 적합 | 24% |
| 일몰 여유 | 23% |
| 이동 거리 | 18% |

#### 하드 오버라이드

| 조건 | 결과 |
|------|------|
| 산사태 경보 지역 | 비추천 강제 |
| 날씨점수 < 0.20 | 비추천 강제 |
| 날씨점수 < 0.45 + 종합점수 ≥ 72 | 주의 상한 강제 |

---

## 10. 세이프링크 동작 방식

### 산행자 흐름

```
1. 코스 선택 후 "산행 시작" 클릭
2. DB에 SafeLinkSession 생성
3. 6자리 코드 발급 (예: A3K7PQ)  ← 화면에 크게 표시
4. Wake Lock 활성화 (화면 꺼짐 방지)
5. GPS watchPosition으로 위치 전송 → LocationLog 누적
6. "산행 종료" → GPS 중단, Wake Lock 해제, 기록 저장
```

### 보호자 흐름

```
1. 탭바 "보호자" 클릭
2. 6자리 코드 입력 (구두/문자로 받은 코드)
3. GET /api/safe-links/by-code/?code=A3K7PQ
4. 실시간 위치 지도 (20초 폴링)
5. 파란 폴리라인으로 이동 궤적 표시
```

### 코드 생성 규칙

- 6자리 대문자+숫자, 혼동 문자(0·O·I·1) 제외
- 문자 집합: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (32자)
- 기존 활성 세션과 충돌 검사 후 발급

---

## 11. AI 도우미 (RAG 채팅)

### 구성

- **모델**: Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`)
- **멀티턴**: 이전 대화 메시지 전체를 contents로 전달
- **컨텍스트 주입**: 선택 산(이름·고도·난이도·소요 시간), 날씨, 산불위험, 산사태, NIFOS 산악기상, 에어코리아 대기질

### RAG 파이프라인

```
사용자 메시지
  ↓
BM25 검색 (rag_retriever.py)
  ├── 정적 지식 베이스 (31개 문서: 응급처치·날씨·장비·코스·계절·국립공원 등)
  ├── 탐방로 데이터 (국립공원공단 CSV 302개)
  └── 재난위험 데이터 (선택 산 해당 위험지구)
  ↓
시스템 프롬프트에 [참고 정보] 섹션 추가
  ↓
Gemini API 호출 (max_output_tokens: 400)
```

### 플로팅 ChatWidget

- 채팅 탭(`/chat`) 외 모든 탭 우하단에 버블 버튼으로 상시 노출
- 클릭 시 채팅 탭으로 이동하거나 인라인 패널로 펼쳐짐

---

## 12. 등산로 경로 데이터

### 현황

| 소스 | 커버리지 | 비고 |
|------|----------|------|
| CSV (국립공원공단) | 302개 코스, 42개 산 | 좌표 포함, 경로선 별도 fetch |
| VWorld API | ~30% 추정 | 코스 선택 시 on-demand, 경로선 포함 |
| **OSM Overpass** | **~65% 추정** | VWorld 없을 때 폴백, 24시간 캐시 |

### 경로 fetch 흐름

```
코스 선택
  ↓
CSV에 route_geometry 있음? → 즉시 표시
  ↓ 없으면
VWorld API (반경 2km) → 있으면 캐시 후 표시
  ↓ 없으면
OSM Overpass (반경 3km) → 있으면 캐시 후 표시
  ↓ 없으면
위치 점(마커)만 표시
```

### 지도 3색 경로 표시

| 색상 | 의미 |
|------|------|
| 🟢 초록 실선 | 안전 구간 |
| 🟠 주황 실선 | 주의 구간 (risk_factors 존재 시) |
| 🔴 빨강 점선 | 위험 구간 (강수·강풍·낙석 등) |

---

## 13. 데이터 소스

| 데이터 | 연동 방식 | 상태 |
|--------|-----------|------|
| 국립공원공단 탐방로 CSV | 로컬 파일 파싱 | ✅ 302개 코스 (42개 산) |
| 기상청 초단기실황 | 공공데이터포털 API | ✅ 실시간 |
| 한국천문연구원 일몰 | 공공데이터포털 API | ✅ |
| 산림청 산불위험예보 | 공공데이터포털 API | ✅ |
| 산림청 산림공간정보 | 공공데이터포털 API | ✅ |
| 국토부 브이월드 등산로 | OpenAPI | ✅ 경로 geometry 포함 |
| OSM Overpass 등산로 | 무료 퍼블릭 API | ✅ 24시간 캐시 |
| 재난위험지구 | 로컬 CSV/JSON | ✅ |
| 산사태 예측 | 공공데이터포털 API | ✅ |
| **NIFOS 산악기상** | 공공데이터포털 API | ✅ AI 컨텍스트 주입 |
| **에어코리아 대기질** | 공공데이터포털 API | ✅ PM2.5·PM10 실시간, AI 컨텍스트 주입 |
| Leaflet + OSM 타일 | 무료 (키 불필요) | ✅ |
| Claude Haiku | Anthropic API | ✅ 안전 브리핑, 키 선택 사항 |
| **Gemini 2.5 Flash Lite** | Google AI API | ✅ 채팅·안전 조언, 키 선택 사항 |

---

## 14. 배포 (Railway)

```
Backend:  requirements.txt 기반
          python manage.py migrate --noinput
          python manage.py seed_mountain_descriptions
          python manage.py seed_mountain_tags        ← 15종 태그 시드
          gunicorn forestrx.wsgi

Frontend: npm run build → Django WhiteNoise로 정적 서빙

PostgreSQL: DATABASE_URL 자동 주입 → dj-database-url 파싱
```

### 마이그레이션 이력

| 번호 | 내용 |
|------|------|
| 0001 | 초기 모델 생성 |
| 0002 | 커뮤니티 샘플 데이터 |
| 0003 | EmergencyContact, HikingRecord, FavoriteCourse |
| 0004 | AuthToken.expires_at + SafeLinkSession |
| 0005 | LocationLog (GPS 궤적) |
| 0006 | SafeLinkSession.share_code (3단계: 컬럼 추가 → 기존 행 코드 채우기 → unique 제약) |
| 0007 | MountainKnowledge, TrailCourse, DisasterRiskZone |
| 0008 | MountainIntro |
| 0009 | MountainIntro 필드 보완 |
| 0010 | MountainTags (15종 태그 JSONField) |

---

## 15. 알려진 제약사항

### GPS 백그라운드 추적

웹 브라우저는 구조적으로 백그라운드 GPS를 지원하지 않는다.

| 상황 | iOS Safari | Android Chrome |
|------|-----------|----------------|
| 화면 켜짐 (Wake Lock 활성) | ✅ 추적 | ✅ 추적 |
| 다른 앱 전환 | ❌ 즉시 중단 | ⚠️ 수분 후 중단 |
| 화면 잠금 | ❌ 중단 | ❌ 중단 |

**완전한 백그라운드 추적은 React Native / Flutter 네이티브 앱으로만 가능하다.**

### 등산로 경로 커버리지

CSV 302개 코스 중 실제 경로선 보유율은 낮음. VWorld + OSM on-demand fetch로 약 65% 보완.  
나머지는 위치 점(마커)만 표시된다.

### Gemini API 무료 한도

Gemini 2.5 Flash Lite 무료 티어는 분당 요청 수 제한이 있다. 한도 초과 시 429 오류가 반환되며, 사용자에게 "잠시 후 다시 시도" 안내 메시지를 표시한다.

---

## 16. 잔여 과제

### 단기 (웹 앱 내 구현 가능)

- [ ] 정기 생존 확인 (30분마다 "괜찮으세요?" Dead Man's Switch)
- [ ] 비상 연락처 자동 알림 (산행 시작 시 SMS/카카오 문자 공유)
- [ ] 예상 하산 시간 카운트다운 + 초과 경고
- [ ] AI 도우미 답변 마크다운 렌더링

### 장기 (네이티브 앱 전환 시)

- [ ] React Native / Flutter 포팅
- [ ] 백그라운드 GPS 추적 (`expo-location` Background Location)
- [ ] 푸시 알림 (위험 구간 진입, 하산 지연)
- [ ] 오프라인 지도 캐시

### 데이터 보완

- [ ] 소방청 산악 구조 이력 데이터 확보 (사고 다발 구간 표시)
- [ ] 국토지리정보원 DEM 경사도 연동 (정밀 지형 분석)
- [ ] 탐방로 통제·폐쇄 정보 자동 반영
