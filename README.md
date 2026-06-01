# 올라 (Olla)

AI 기반 산행 안전 진단 서비스. "산을 올라가다"와 스페인어 인사 Hola의 친근함을 동시에 담은 이름.

## 구조

```
forest/
├── backend/          Django 5 API 서버
│   └── recommendations/
│       ├── services.py        추천·안전 스코어링 핵심 로직
│       ├── weather_api.py     기상청 초단기실황
│       ├── sun_api.py         한국천문연구원 일몰
│       ├── wildfire_api.py    산림청 산불위험예보
│       ├── forest_api.py      산림청 산림공간정보
│       ├── vworld_api.py      국토부 브이월드 등산로
│       ├── local_road_api.py  지방도로 등산로
│       ├── landslide_api.py   산사태 예측
│       ├── disaster_risk.py   재난위험지구 매칭
│       ├── community_views.py 커뮤니티·사용자 API
│       ├── models.py          User, Post, Comment, HikingRecord, FavoriteCourse, EmergencyContact
│       └── safe_links.py      세이프 링크 세션 관리
├── frontend/         Vue 3 + Vite 웹 앱
│   ├── src/App.vue   단일 페이지 앱 (탭 기반)
│   ├── src/api.js    백엔드 API 호출
│   └── public/logo.png  올라 브랜드 로고
└── docs/             설계 문서
```

## 실행

### Backend

```powershell
cd backend
python -m venv venv && venv\Scripts\activate
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

Vite 프록시가 `/api` → `http://127.0.0.1:8000` 으로 전달.

## 필요 환경 변수

| 변수 | 설명 |
|------|------|
| `PUBLIC_SERVICE_KEY` | 공공데이터포털 일반 인증키 |
| `KAKAO_MAPS_KEY` | Kakao Maps JavaScript API 키 (`frontend/.env.local`의 `VITE_KAKAO_MAPS_KEY`) |
| `DATABASE_URL` | Railway PostgreSQL 연결 문자열 (로컬 미설정 시 SQLite 자동 사용) |

## 배포 (Railway)

- Backend: Dockerfile 기반. `CMD`에서 `python manage.py migrate --noinput` 후 gunicorn 실행
- PostgreSQL: Railway 서비스 추가 시 `DATABASE_URL` 자동 주입 → `dj-database-url`로 파싱
- Frontend: Vite 빌드 정적 파일 또는 별도 서비스

---

## API 엔드포인트

### 코어

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health/` | 서비스 상태, 공공데이터키 로드 확인 |
| GET | `/api/courses/` | 전체 탐방로 목록 (CSV 기반) |
| POST | `/api/recommendations/` | 안전 코스 추천 (body: profile + location) |
| GET | `/api/weather/?lat=&lng=` | 기상청 초단기실황 |
| GET | `/api/sun-times/?lat=&lng=` | 한국천문연구원 일출·일몰 |
| GET | `/api/wildfire/` | 산림청 산불위험예보 |
| GET | `/api/landslide/?sgg=` | 산사태 예측 |
| GET | `/api/disaster-zones/?mountain=` | 재난위험지구 조회 |
| GET | `/api/forest-spatial/?mountain=` | 산림청 산림공간정보 |
| GET | `/api/vworld-trails/?lat=&lng=&mountain=` | 브이월드 등산로 |
| GET | `/api/mountain-story/?mountain=` | 산 정보 |
| GET | `/api/mountain-weather/?mountain=` | 산악 날씨 |
| GET | `/api/data-sources/` | 데이터 소스 상태 |

### 세이프 링크

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/safe-links/` | 세션 생성 (course 정보 포함) |
| GET | `/api/safe-links/{id}/` | 보호자용 세션 조회 |
| POST | `/api/safe-links/{id}/` | 위치 업데이트 또는 세션 종료 |

### 인증

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auth/register/` | 회원가입 |
| POST | `/api/auth/login/` | 로그인 (토큰 반환) |
| POST | `/api/auth/logout/` | 로그아웃 |
| GET | `/api/auth/me/` | 내 정보 |

### 커뮤니티

| Method | Path | 설명 |
|--------|------|------|
| GET/POST | `/api/posts/` | 게시글 목록 (search 파라미터 지원) · 작성 |
| GET/PUT/DELETE | `/api/posts/{id}/` | 게시글 상세·수정·삭제 |
| POST | `/api/posts/{id}/like/` | 좋아요 토글 |
| GET/POST | `/api/posts/{id}/comments/` | 댓글 목록·작성 |
| PUT/DELETE | `/api/comments/{id}/` | 댓글 수정·삭제 |
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

## 점수 스코어링 상세

`backend/recommendations/services.py`에 구현된 실제 로직.

### 1단계: 4개 원점수 (각 0~100)

#### 기상 안전도 `weather_safety_score(weather)`

시작 100점에서 감점:

| 조건 | 감점 |
|------|------|
| 강수량 ≥ 10mm | -45 |
| 강수량 > 0mm | -20 |
| 풍속 ≥ 8m/s | -30 |
| 풍속 ≥ 5m/s | -15 |
| 기온 ≤ 0°C 또는 ≥ 32°C | -20 |
| 비+강풍 동시 (rainfall≥5 & wind≥5) | -20 추가 |
| 영하+강수 (temp≤2 & rainfall>0) | -15 추가 (결빙) |
| 폭염+무풍 (temp≥30 & wind<2) | -10 추가 (열사병) |

최솟값 0점.

#### 체력 적합도 `fitness_score(course, profile)`

```
target = round((경험레벨 + 활동강도 + max(컨디션-1, 1)) / 3)
  경험: beginner=1, intermediate=2, advanced=3
  강도: light=1, moderate=2, strong=3
  컨디션: 사용자 입력 1~5

gap = |코스 난이도 - target|
  easy=1, medium=2, hard=3

점수 = max(100 - gap×28 - 고도상승m/25, 35)
```

#### 접근성 `accessibility_score(course, lat, lng, profile)`

```
distance = haversine 거리 (km)
점수 = max(100 - distance×3.2, 20)
maxDistanceKm 초과 시: min((초과km)×3, 35) 추가 감점
좌표 없는 코스: 70점 고정
```

#### 시간 적합도 `time_fit_score(course, profile, weather)`

```
available = 사용자 이동 가능 시간(분)
desired   = 희망 등산 시간(분, 없으면 available)

코스 > available: max(100 - 초과분×1.8, 15)

버퍼 범위: [desired-30, desired+버퍼]
  버퍼: 취약자 동반 = +15분, 일반 = +30분
  범위 미달: min(미달분×0.5, 15) 감점
  범위 초과: min(초과분×0.8, 25) 감점

일몰 여유(sunset - 예상하산시각):
  < 0분: -45  (일몰 후 하산)
  < 30분: -25
  < 60분: -10

최솟값 15점.
```

### 2단계: 가중 합산

동반자 유형·목적에 따라 가중치 동적 결정:

| 조건 | 체력(fit) | 기상(weather) | 시간(time) | 접근성(access) |
|------|-----------|---------------|------------|----------------|
| 취약자 동반 (family/vulnerable) | **0.45** | 0.25 | 0.25 | 0.05 |
| 힐링 (healing) | 0.25 | **0.35** | 0.15 | 0.25 |
| 운동 (workout) | **0.40** | 0.25 | 0.15 | 0.20 |
| 기본 (balanced 등) | 0.35 | 0.30 | 0.15 | 0.20 |

```
total = fit×w_fit + weather×w_weather + access×w_access + time×w_time
```

### 3단계: 보너스·페널티 가감

| 항목 | 가감 |
|------|------|
| 혼잡도 | `crowding × -8` |
| 재난위험지구 고위험 구역 1개당 | -6 |
| 재난위험지구 주의 구역 1개당 | -2 |
| 검색 산과 이름 일치 | +45 |
| 목적: healing + easy | +10 |
| 목적: healing + 90분 이하 | +8 |
| 목적: workout + medium/hard + 90분 이상 | +12 |
| 목적: view + 좌표 또는 지도URL 있음 | +10 |
| 대중교통 + 15km 이내 | +6 |
| 차량 + 45km 이내 | +5 |
| 좌표 없음 + 대중교통 | -8 |
| 데이터 품질: 이름이 일반명(탐방로 등) | -18 |
| 데이터 품질: 산이름 "국립공원" | -10 |
| 데이터 품질: 거리 < 0.3km | -35 |
| 데이터 품질: 거리 < 0.8km | -15 |
| 데이터 품질: 좌표 없음 | -28 |
| 데이터 품질: 좌표 있음 | +5 |

최종 total은 100점으로 cap.

### 4단계: 안전 등급 결정 (점수와 별개 룰 기반)

`safety_decision_for_course()`가 red_flags / yellow_flags로 판단.

**비추천(빨강)** — 아래 중 하나라도 해당:
- 재난위험지구 고위험 등급
- 강수량 ≥ 10mm
- 풍속 ≥ 8m/s
- 일몰 여유 < 30분
- 산불 위험 very_high
- 취약자 동반 + 코스 난이도 hard

**주의(노랑)** — 빨강 없고 아래 충족:
- 취약자 동반: 노랑 플래그 ≥ 1개 OR 기상점수 < 85 OR 체력점수 < 75 OR 시간점수 < 75
- 일반: 노랑 플래그 ≥ 2개 OR 기상 < 80 OR 체력 < 65 OR 시간 < 70

**추천(초록)** — 빨강·노랑 모두 해당 없음

### 5단계: 최종 정렬

```python
recommendations.sort(
    key=lambda item: (safety_rank(item["safety_decision"]), item["score"]),
    reverse=True
)
# safety_rank: recommend=3, caution=2, not_recommended=1
```

안전 등급이 같을 때 total 점수로 2차 정렬.
검색 산 이름이 있으면 해당 산 코스를 상단으로 재배치 후 Top3 선정.

---

## 주요 데이터 모델

### 추천 관련 (loaders.py + CSV)

코스 필드: `id, name, mountain, difficulty, distance_km, duration_min, elevation_gain_m, lat, lng, crowding, map_url`

### DB 모델 (models.py)

- `User`: nickname, token, experience, condition, created_at
- `Post`: user, title, content, likes(M2M), created_at
- `Comment`: post, user, content, created_at
- `HikingRecord`: user, mountain, course_name, hiked_date, duration_min, weather_summary, safety_label
- `FavoriteCourse`: user, course_id, course_name, mountain, distance_km, duration_min, difficulty (unique: user+course_id)
- `EmergencyContact`: user, name, phone, relation

## 시연 흐름

1. 산 이름 선택 → 날씨 자동 로드 (검색 전에도 표시)
2. 동반자 유형·목적·이동수단·출발 시간 설정
3. "동반자 기준 안전코스 찾기" 클릭
4. Top3 추천 + 안전 등급(추천/주의/비추천) 확인
5. 코스 카드 클릭 → Kakao Map 지형도 + 상세 정보
6. "산행 시작" → 세이프 링크 생성 → 보호자와 URL 공유
7. 산행 종료 → 기록 자동 저장 → 내정보 탭에서 확인
