# ── 1단계: 프론트엔드 빌드 ────────────────────────────────────────────────
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./

# Railway 환경변수로 주입 (Variables 탭에서 VITE_KAKAO_MAP_APP_KEY 설정 필요)
ARG VITE_KAKAO_MAP_APP_KEY
ENV VITE_KAKAO_MAP_APP_KEY=${VITE_KAKAO_MAP_APP_KEY}

RUN npm run build


# ── 2단계: Python 런타임 ──────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=False

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# 소스 전체 복사 후 빌드된 프론트엔드 덮어쓰기
COPY . ./
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# collectstatic: frontend/dist/assets → staticfiles/
RUN cd backend && python manage.py collectstatic --noinput

# gunicorn으로 서비스
CMD ["sh", "-c", "cd backend && gunicorn forestrx.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
