# ForestRx

GPS 기반 개인 맞춤 등산 코스 추천 서비스 MVP입니다.

## 구조

- `backend/`: Django API 서버
- `frontend/`: Vue 3 + Vite 웹 앱
- `docs/proposal-summary.md`: 제안서 기반 개발 요약

## MVP 범위

- 사용자 상태 입력
- 공공 탐방로 CSV 기반 Top3 추천
- 산림청 산림공간정보 API 기반 좌표 보강
- Kakao Maps SDK 기반 지도 표시
- 기상청 초단기실황, 한국천문연구원 일몰, 산불위험예보 기반 안전 분석
- 추천 이유 및 위험 시 대체 코스 제공
- 모바일 우선 반응형 UI

## 실행

### Backend

```powershell
cd backend
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

프론트엔드는 Vite 프록시를 통해 `/api`를 `http://127.0.0.1:8000`으로 전달합니다.

## 필요 파일

- `key.txt`: 공공데이터포털 일반 인증키와 API 엔드포인트 메모
- `국립공원공단_탐방로_20240911.csv`: 국립공원 탐방로 CSV
- `frontend/.env.local`: Kakao Maps JavaScript 키

## 주요 API

- `GET /api/health/`
- `GET /api/courses/`
- `GET /api/weather/?lat=37.5665&lng=126.978`
- `GET /api/sun-times/?lat=37.5665&lng=126.978`
- `GET /api/wildfire/`
- `GET /api/forest-spatial/?mountain=관악산`
- `POST /api/recommendations/`

## 시연 흐름

1. 프론트에서 산 이름에 `관악산` 입력
2. 목적, 이동수단, 출발 예정 시간 조정
3. `추천 받기` 클릭
4. Top3 추천, 안전 분석, 대체 코스 확인
5. 상세 패널에서 Kakao 지도와 좌표/일몰 여유 확인
