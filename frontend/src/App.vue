<template>
  <main class="app-shell">
    <!-- ─── 히어로 헤더 ──────────────────────────────────────────────────── -->
    <header class="app-hero">
      <div class="hero-nav">
        <div class="hero-nav-actions">
          <button v-if="authUser" class="hero-auth-btn" type="button" @click="showAuthModal = true">
            <span class="auth-avatar">{{ authUser.nickname[0] }}</span>
            <span class="auth-nickname">{{ authUser.nickname }}</span>
          </button>
          <button v-else class="hero-login-btn" type="button" @click="showAuthModal = true">로그인</button>
          <button class="hero-refresh-btn" type="button" title="새로고침" @click="reload">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
            </svg>
          </button>
        </div>
      </div>

      <div class="hero-body">
        <h1 class="hero-title">
          동반자와 함께하는<br>
          <span class="hero-title-accent">모든 산행을 안전하게</span>
        </h1>
        <p class="hero-desc">날씨 · 코스 · 재난 데이터를 종합해<br>출발 전 안전 등급을 진단합니다</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-num">138<span class="hero-stat-unit">개</span></span>
            <span class="hero-stat-label">올라 추천 산</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-num">631<span class="hero-stat-unit">개</span></span>
            <span class="hero-stat-label">실시간 분석 탐방로</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-num">3<span class="hero-stat-unit">단계</span></span>
            <span class="hero-stat-label">추천 · 주의 · 비추천</span>
          </div>
        </div>
      </div>
    </header>

    <!-- ─── 에러 배너 ──────────────────────────────────────────────────── -->
    <div v-if="globalError" class="error-banner" role="alert">
      <span>⚠️ {{ globalError }}</span>
      <button class="error-close" type="button" aria-label="닫기" @click="globalError = ''">✕</button>
    </div>

    <!-- ─── 탭바 ──────────────────────────────────────────────────────── -->
    <nav class="tabbar" aria-label="주요 화면">
      <div class="sidebar-brand">
        <img src="/logo.png" alt="올라" class="sidebar-logo-img" />
      </div>
      <router-link to="/guide" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        <span>안전코스</span>
      </router-link>
      <router-link to="/chat" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        <span>AI 도우미</span>
      </router-link>
      <router-link to="/safe-link" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>안전공유</span>
      </router-link>
      <router-link to="/community" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>커뮤니티</span>
      </router-link>
      <router-link to="/my-page" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </router-link>

      <!-- ─── 실시간 산행 환경 미니 카드 ── -->
      <div class="sidebar-weather">
        <div class="sw-header">
          <span class="sw-title">{{ selectedMountain ? selectedMountain.name + ' 날씨' : '실시간 산행 환경' }}</span>
          <span v-if="weatherData" :class="weatherData.source === 'mock' ? 'live-badge mock-badge' : 'live-badge'" style="font-size:9px;padding:2px 6px">
            {{ weatherData.source === 'mock' ? '추정' : '● LIVE' }}
          </span>
        </div>
        <template v-if="weatherData">
          <div class="sw-gauge-track">
            <div class="sw-gauge-fill" :class="swSafetyClass" :style="{ width: swSafetyPct + '%' }"></div>
          </div>
          <p class="sw-gauge-label">{{ swSafetyLabel }}</p>
          <div class="sw-grid">
            <div class="sw-item">
              <span>{{ swWeatherIcon }}</span>
              <span>{{ swWeatherLabel }} {{ weatherData.temperature_c }}°C</span>
            </div>
            <div class="sw-item">
              <span>🌄</span>
              <span>일출 {{ weatherData.sunrise || '-' }}</span>
            </div>
            <div class="sw-item">
              <span>🌅</span>
              <span>일몰 {{ weatherData.sunset || '-' }}</span>
            </div>
            <div class="sw-item">
              <span>💧</span>
              <span :class="weatherData.rainfall_mm > 0 ? 'sw-warn' : ''">강수 {{ weatherData.rainfall_mm ?? 0 }}mm</span>
            </div>
            <div class="sw-item">
              <span>💨</span>
              <span :class="weatherData.wind_speed_ms >= 5 ? 'sw-warn' : ''">풍속 {{ weatherData.wind_speed_ms }}m/s</span>
            </div>
            <div class="sw-item">
              <span>💦</span>
              <span>습도 {{ weatherData.humidity_pct ?? '-' }}%</span>
            </div>
            <div class="sw-item">
              <span>🔥</span>
              <span :class="swWildfireClass">산불 {{ swWildfireLabel }}</span>
            </div>
            <div v-if="weatherData.pm10_ugm3 != null" class="sw-item" :class="swDustClass">
              <span>🌫</span>
              <span>미세먼지 {{ weatherData.pm10_ugm3 }}㎍ · {{ weatherData.grade_pm10 || '-' }}</span>
            </div>
            <div v-if="weatherData.pm25_ugm3 != null" class="sw-item" :class="swFineDustClass">
              <span>💨</span>
              <span>초미세먼지 {{ weatherData.pm25_ugm3 }}㎍ · {{ weatherData.grade_pm25 || '-' }}</span>
            </div>
          </div>
        </template>
        <p v-else style="font-size:10px;color:#9ca3af;margin:4px 0 0">날씨 불러오는 중...</p>
      </div>
    </nav>

    <!-- ─── 라우터 뷰 ─────────────────────────────────────────────────── -->
    <router-view />

    <!-- ─── 로그인/회원가입 모달 ─────────────────────────────────────── -->
    <AuthModal v-if="showAuthModal" />

    <!-- ─── 온보딩 모달 (첫 방문) ──────────────────────────────────── -->
    <OnboardingModal v-if="showOnboarding" @close="showOnboarding = false" />
  </main>

</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { authUser, loadMe, showAuthModal } from './composables/useAuth.js';
import { loadMyPageData } from './composables/useUserData.js';
import { guideError, weatherData, loadWeather, selectedMountain } from './composables/useGuide.js';
import { communityError } from './composables/useCommunity.js';
import AuthModal from './components/AuthModal.vue';
import OnboardingModal from './components/OnboardingModal.vue';

const showOnboarding = ref(!localStorage.getItem('ollaOnboarded'));

const swWeatherIcon = computed(() => {
  const w = weatherData.value;
  if (!w) return '🌤️';
  if (w.rainfall_mm >= 10) return '🌧️';
  if (w.rainfall_mm > 0) return '🌦️';
  if (w.wind_speed_ms >= 8) return '💨';
  return '☀️';
});
const swWeatherLabel = computed(() => {
  const w = weatherData.value;
  if (!w) return '';
  if (w.rainfall_mm >= 10) return '비';
  if (w.rainfall_mm > 0) return '흐림';
  return '맑음';
});
const swSafetyClass = computed(() => {
  const w = weatherData.value;
  if (!w) return 'safe';
  const r = w.rainfall_mm ?? 0;
  const wind = w.wind_speed_ms ?? 0;
  if (r >= 10 || wind >= 10) return 'danger';
  if (r > 0 || wind >= 5) return 'warning';
  return 'safe';
});
const swSafetyPct = computed(() => {
  return swSafetyClass.value === 'safe' ? 95 : swSafetyClass.value === 'warning' ? 55 : 20;
});
const swSafetyLabel = computed(() => {
  return swSafetyClass.value === 'safe' ? '산행 적합' : swSafetyClass.value === 'warning' ? '주의 필요' : '산행 위험';
});
const swWildfireClass = computed(() => ({ low: '', medium: 'sw-warn', high: 'sw-danger', very_high: 'sw-danger' }[weatherData.value?.wildfire_risk || 'low'] || ''));
const swWildfireLabel = computed(() => ({ low: '낮음', medium: '보통', high: '높음', very_high: '매우높음' }[weatherData.value?.wildfire_risk || 'low'] || '낮음'));
const swDustClass = computed(() => ({ '보통': '', '나쁨': 'sw-warn', '매우나쁨': 'sw-danger' }[weatherData.value?.grade_pm10 || ''] || ''));
const swFineDustClass = computed(() => ({ '보통': '', '나쁨': 'sw-warn', '매우나쁨': 'sw-danger' }[weatherData.value?.grade_pm25 || ''] || ''));

// 전역 에러 — 어느 탭의 에러든 하나로 모음
const globalError = computed({
  get: () => guideError.value || communityError.value,
  set: (v) => { guideError.value = v; communityError.value = v; },
});

function reload() {
  window.location.reload();
}

onMounted(async () => {
  await loadMe();
  if (authUser.value) loadMyPageData();
  loadWeather();
});
</script>
