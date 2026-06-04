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
11. [등산로 경로 데이터](#11-등산로-경로-데이터)
12. [데이터 소스](#12-데이터-소스)
13. [배포 (Railway)](#13-배포-railway)
14. [알려진 제약사항](#14-알려진-제약사항)
15. [잔여 과제](#15-잔여-과제)

---

## 1. 서비스 개요

### 핵심 원칙

- **안전 등급 우선**: 점수(숫자)는 내부 계산에만 사용하고, 사용자에게는 등급(추천/주의/비추천) + 이유 텍스트만 노출
- **약자 동반 특화**: 어린이·노약자 동반 시 체력 가중치(0.45) 극대화, 비추천 기준 강화
- **코드 기반 위치 공유**: URL 대신 6자리 코드로 보호자와 공유 → 전화로도 구두 전달 가능

### 시연 흐름

1. **산 선택** → 날씨 자동 로드 (설악산·지리산 등 인기 산 바로 선택)
2. **조건 입력** → 동반자 유형 · 산행 목적(힐링/운동/전망/균형) · 출발 시간
3. **안전코스 찾기** → AI 브리핑 카드 최상단 + Top3 추천
4. **코스 카드 클릭** → Leaflet 지형도 + 3색 등산로 + 위험 마커 + 커뮤니티 안전 제보
5. **안전공유 탭** → "산행 시작" → **6자리 코드** 생성 (예: `A3K7PQ`)
6. **코드 공유** → 보호자가 "보호자" 탭에서 코드 입력 → 실시간 위치 확인
7. **산행 종료** → 기록 자동 저장 → 내정보 탭에서 확인

---

## 2. 구현 완료 기능

| 기능 | 상태 | 비고 |
|------|------|------|
| 산·코스 선택 + 프로필 입력 | ✅ | 산행 목적(힐링/운동/전망/균형) 포함 |
| 기상청 초단기실황 실시간 연동 | ✅ | 10분 캐시 |
| 안전 등급 기반 Top3 추천 | ✅ | 점수 숫자 비표시 |
| AI 안전 브리핑 (Claude Haiku) | ✅ | 결과 최상단 카드, 1시간 캐시 |
| 한국천문연구원 일몰 연동 | ✅ | |
| 산림청 산불위험예보 연동 | ✅ | |
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
| 산행 기록 자동 저장 | ✅ | |
| 즐겨찾기 코스 | ✅ | |
| 긴급 연락처 관리 | ✅ | |
| 출발 전 체크리스트 | ✅ | localStorage 저장 |
| 인증 토큰 30일 만료 | ✅ | |
| Vue Router URL 기반 라우팅 | ✅ | 해시 히스토리, 뒤로가기·딥링크 지원 |
| Railway PostgreSQL 연동 | ✅ | |

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
│       ├── osm_trail_api.py      OSM Overpass 등산로 경로 조회
│       ├── llm_briefing.py       Claude AI 안전 브리핑 (캐싱)
│       ├── weather_api.py        기상청 초단기실황
│       ├── sun_api.py            한국천문연구원 일몰
│       ├── wildfire_api.py       산림청 산불위험예보
│       ├── forest_api.py         산림청 산림공간정보
│       ├── vworld_api.py         국토부 브이월드 등산로
│       ├── local_road_api.py     지방도로 등산로
│       ├── landslide_api.py      산사태 예측
│       ├── disaster_risk.py      재난위험지구 매칭
│       └── migrations/           0001 ~ 0006
├── frontend/
│   └── src/
│       ├── App.vue               셸 (히어로·탭바·router-view)
│       ├── router.js             Vue Router 4 (해시 히스토리)
│       ├── api.js                백엔드 API 호출 레이어
│       ├── views/
│       │   ├── GuideTab.vue          안전코스 추천 탭
│       │   ├── SafeLinkTab.vue       안전공유 탭 (2컬럼)
│       │   ├── CommunityTab.vue      커뮤니티 탭 (포스트 그리드)
│       │   ├── MyPageTab.vue         내정보 탭 (3컬럼 그리드)
│       │   ├── GuardianView.vue      보호자 실시간 위치
│       │   └── GuardianCodeView.vue  코드 입력 화면
│       ├── composables/
│       │   ├── useGuide.js           안전코스·추천·날씨 (싱글톤)
│       │   ├── useSafeLink.js        세이프링크·GPS·Wake Lock (싱글톤)
│       │   ├── useAuth.js            인증 (싱글톤)
│       │   ├── useCommunity.js       커뮤니티 (싱글톤)
│       │   ├── useUserData.js        기록·즐겨찾기·연락처 (싱글톤)
│       │   ├── useLeafletMap.js      Leaflet + OSM 지도
│       │   └── useLocation.js        GPS 위치
│       └── components/
│           ├── CourseCard.vue        코스 카드
│           └── AuthModal.vue         로그인/회원가입 모달
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
| `PUBLIC_SERVICE_KEY` | ✅ | 공공데이터포털 일반 인증키 |
| `DJANGO_SECRET_KEY` | 프로덕션 필수 | 미설정 시 개발용 키 자동 사용. `DATABASE_URL` 또는 `RAILWAY_PUBLIC_DOMAIN` 존재 시 미설정이면 즉시 오류 |
| `DJANGO_DEBUG` | 선택 | `true` / `false` (기본값 `false`) |
| `DATABASE_URL` | 프로덕션 필수 | Railway PostgreSQL 연결 문자열. 미설정 시 SQLite 자동 사용 |
| `ANTHROPIC_API_KEY` | 선택 | Claude AI 안전 브리핑 생성. 없으면 템플릿 폴백 |
| `RAILWAY_PUBLIC_DOMAIN` | 자동 주입 | 프로덕션 환경 감지용 |

---

## 6. API 엔드포인트

### 코어

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health/` | 서비스 상태, 공공데이터키 로드 확인 |
| GET | `/api/courses/` | 전체 탐방로 목록 (631개, CSV 기반) |
| POST | `/api/recommendations/` | 안전 코스 추천 (body: profile + location) |
| GET | `/api/weather/?lat=&lng=` | 기상청 초단기실황 (10분 캐시) |
| GET | `/api/sun-times/?lat=&lng=` | 한국천문연구원 일출·일몰 |
| GET | `/api/wildfire/` | 산림청 산불위험예보 |
| GET | `/api/landslide/?sgg=` | 산사태 예측 |
| GET | `/api/disaster-zones/?mountain=` | 재난위험지구 조회 |
| GET | `/api/forest-spatial/?mountain=` | 산림청 산림공간정보 |
| GET | `/api/vworld-trails/?lat=&lng=&mountain=` | 브이월드 등산로 (경로 geometry 포함) |
| GET | `/api/osm-trails/?lat=&lng=&mountain=&radius=` | OSM 등산로 경로 (24시간 캐시) |
| GET | `/api/safety-reports/?mountain=` | 커뮤니티 안전 제보 게시글 |

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
| GET | `/api/my-posts/` | 내 게시글 |

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
| `HikingRecord` | user, mountain, course_name, hiked_date, safety_label | 산행 기록 |
| `FavoriteCourse` | user, course_id, course_name (unique: user+course_id) | 즐겨찾기 |
| `EmergencyContact` | user, name, phone, relation | 긴급 연락처 |
| `SafeLinkSession` | id(UUID), **share_code**(6자리 unique), course 정보, current_lat/lng, status | 세이프링크 세션 |
| `LocationLog` | session(FK), lat, lng, recorded_at | GPS 궤적 로그 |

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
| `useLeafletMap` | 지도 인스턴스 재사용 (깜빡임 없음) |

### 백엔드 API 호출 구조

```
추천 요청 시 ThreadPoolExecutor(max_workers=3) 병렬 호출:
├── local_road_api   지방도로 등산로
├── vworld_api       국토부 브이월드
└── forest_api       산림청 산림공간정보

별도 캐시:
├── weather_api      기상청 (10분 Django cache)
├── osm_trail_api    OSM Overpass (24시간 Django cache)
└── llm_briefing     Claude 브리핑 (1시간 Django cache)
```

### 데스크톱 레이아웃 (1024px+)

| 탭 | 레이아웃 |
|---|---|
| 안전코스 | 좌(폼+날씨 sticky) / 우(결과목록) 2컬럼 |
| 안전공유 | 좌(지도+카드) / 우(컨트롤+외부링크) 2컬럼 |
| 커뮤니티 | 포스트 카드 3컬럼 그리드 (1440px+에서 4컬럼) |
| 내정보 | 상단 3컬럼(개인설정/즐겨찾기/산행기록) + 하단 2컬럼(긴급연락처+체크리스트) |

---

## 9. 안전 등급 스코어링

### 1단계: 4개 원점수 (각 0~100)

**기상 안전도** — 100점에서 감점:

| 조건 | 감점 |
|------|------|
| 강수량 ≥ 10mm | -45 |
| 강수량 > 0mm | -20 |
| 풍속 ≥ 8m/s | -30 |
| 풍속 ≥ 5m/s | -15 |
| 기온 ≤ 0°C 또는 ≥ 32°C | -20 |
| 비+강풍 동시 | -20 추가 |
| 영하+강수 (결빙) | -15 추가 |
| 폭염+무풍 (열사병) | -10 추가 |

**체력 적합도**: `max(100 - |난이도-목표| × 28 - 고도상승m / 25, 35)`

**접근성**: `max(100 - 거리km × 3.2, 20)`

**시간 적합도**: 코스 소요 vs 가용 시간 비교 + 일몰 여유 반영 (< 30분: -25, < 0분: -45)

### 2단계: 동반자·목적별 가중치

| 조건 | 체력 | 기상 | 시간 | 접근성 |
|------|------|------|------|--------|
| 취약자 동반 | **0.45** | 0.25 | 0.25 | 0.05 |
| 힐링 | 0.25 | **0.35** | 0.15 | 0.25 |
| 운동 | **0.40** | 0.25 | 0.15 | 0.20 |
| 기본 | 0.35 | 0.30 | 0.15 | 0.20 |

### 3단계: 보너스·페널티

| 항목 | 가감 |
|------|------|
| 검색 산 이름 일치 | +45 |
| 목적: healing + easy | +10 |
| 목적: workout + medium/hard + 90분↑ | +12 |
| 혼잡도 | crowding × -8 |
| 재난위험지구 고위험 1개당 | -6 |
| 데이터 품질: 좌표 없음 | -28 |
| 데이터 품질: 거리 < 0.3km | -35 |

### 4단계: 룰 기반 안전 등급 (점수와 독립)

**비추천(빨강)** — 하나라도 해당 시:
- 강수량 ≥ 10mm / 풍속 ≥ 8m/s / 일몰 여유 < 30분
- 산불 very_high / 재난위험지구 고위험 / 취약자 동반 + hard 난이도

**주의(노랑)** — 빨강 없고, 취약자: 노랑플래그 ≥ 1개 또는 기상 < 85 또는 체력 < 75

**추천(초록)** — 위 조건 모두 해당 없음

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

## 11. 등산로 경로 데이터

### 현황

| 소스 | 커버리지 | 비고 |
|------|----------|------|
| CSV (국립공원공단) | 631개 코스 | 좌표 44.8%, 경로선 0% |
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

## 12. 데이터 소스

| 데이터 | 연동 방식 | 상태 |
|--------|-----------|------|
| 국립공원공단 탐방로 CSV | 로컬 파일 파싱 | ✅ 631개 코스 |
| 기상청 초단기실황 | 공공데이터포털 API | ✅ 실시간 |
| 한국천문연구원 일몰 | 공공데이터포털 API | ✅ |
| 산림청 산불위험예보 | 공공데이터포털 API | ✅ |
| 산림청 산림공간정보 | 공공데이터포털 API | ✅ |
| 국토부 브이월드 등산로 | OpenAPI | ✅ 경로 geometry 포함 |
| OSM Overpass 등산로 | 무료 퍼블릭 API | ✅ 24시간 캐시 |
| 재난위험지구 | 로컬 JSON | ✅ |
| 산사태 예측 | 공공데이터포털 API | ✅ |
| Leaflet + OSM 타일 | 무료 (키 불필요) | ✅ |
| Claude Haiku | Anthropic API | ✅ 키 선택 사항 |

---

## 13. 배포 (Railway)

```
Backend:  requirements.txt 기반
          python manage.py migrate --noinput
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

---

## 14. 알려진 제약사항

### GPS 백그라운드 추적

웹 브라우저는 구조적으로 백그라운드 GPS를 지원하지 않는다.

| 상황 | iOS Safari | Android Chrome |
|------|-----------|----------------|
| 화면 켜짐 (Wake Lock 활성) | ✅ 추적 | ✅ 추적 |
| 다른 앱 전환 | ❌ 즉시 중단 | ⚠️ 수분 후 중단 |
| 화면 잠금 | ❌ 중단 | ❌ 중단 |

**완전한 백그라운드 추적은 React Native / Flutter 네이티브 앱으로만 가능하다.**  
React Native 전환 시 `expo-location` Background Location으로 해결 가능.

### 등산로 경로 커버리지

CSV 631개 코스 중 실제 경로선 보유율은 0%. VWorld + OSM on-demand fetch로 약 65% 보완.  
나머지는 위치 점(마커)만 표시된다.

---

## 15. 잔여 과제

### 단기 (웹 앱 내 구현 가능)

- [ ] 정기 생존 확인 (30분마다 "괜찮으세요?" Dead Man's Switch)
- [ ] 비상 연락처 자동 알림 (산행 시작 시 SMS/카카오 문자 공유)
- [ ] 예상 하산 시간 카운트다운 + 초과 경고

### 장기 (네이티브 앱 전환 시)

- [ ] React Native / Flutter 포팅
- [ ] 백그라운드 GPS 추적 (`expo-location` Background Location)
- [ ] 푸시 알림 (위험 구간 진입, 하산 지연)
- [ ] 오프라인 지도 캐시

### 데이터 보완

- [ ] 소방청 산악 구조 이력 데이터 확보 (사고 다발 구간 표시)
- [ ] 국토지리정보원 DEM 경사도 연동 (정밀 지형 분석)
- [ ] 탐방로 통제·폐쇄 정보 자동 반영
