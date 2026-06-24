<template>
  <main class="app-shell">
    <header v-if="showSafetyHero" class="app-hero">
      <LiveSafetyHero
        :safety-items="liveSafetyItems"
        :slides="heroThemeSlides"
        @select-theme="handleThemeSelect"
      />
    </header>

    <div v-if="globalError" class="error-banner" role="alert">
      <span>⚠️ {{ globalError }}</span>
      <button class="error-close" type="button" aria-label="닫기" @click="globalError = ''">×</button>
    </div>

    <nav class="tabbar" aria-label="주요 화면">
      <div class="sidebar-brand" style="cursor:pointer" @click="goHome">
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

      <router-link
        v-if="authUser"
        to="/my-page"
        class="tabbar-item"
        active-class="active"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>마이페이지</span>
      </router-link>

      <router-link
        v-else
        to="/login"
        class="tabbar-item"
        active-class="active"
        @click="openLogin"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>로그인</span>
      </router-link>

      <section class="sidebar-search-panel" aria-label="산 검색하기">
        <div class="sidebar-search-head">
          <h2>산 검색하기</h2>
        </div>

        <div class="bfp-search-row sidebar-search-row">
          <svg class="bfp-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            v-model="mountainSearch"
            class="bfp-search-input"
            type="text"
            placeholder="산 이름 또는 지역 검색"
            autocomplete="off"
          />
        </div>

        <div v-if="loading && !filteredMountains.length" class="community-loading sidebar-search-loading">분석 중…</div>
        <p v-else-if="!filteredMountains.length && mountainSearch" class="tag-filter-empty sidebar-search-empty">
          조건에 맞는 산이 없어요.
        </p>

        <div class="mountain-browse-list sidebar-mountain-list">
          <button
            v-for="mountain in filteredMountains"
            :key="mountain.mountain_key || mountain.id"
            class="mountain-browse-row sidebar-mountain-row"
            type="button"
            @click="handleSidebarMountainSelect(mountain)"
          >
            <i class="mbr-diff-dot" :style="{ background: diffDotColor(mountain.difficulty) }"></i>
            <div class="mbr-body">
              <strong class="mbr-name">{{ mountain.name }}</strong>
              <span class="mbr-meta">{{ mountain.region }}&nbsp;·&nbsp;{{ mountain.elevation_m }}m</span>
            </div>
            <svg class="mbr-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>

        <div v-if="mlRiskInfo" class="ml-risk-card sidebar-ml-risk-card">
          <div class="ml-risk-header">
            <span class="ml-risk-title">📊 소방청 사고 데이터 분석</span>
            <span
              :class="['ml-risk-badge',
                mlRiskInfo.risk_index >= 0.70 ? 'mlr-high' :
                mlRiskInfo.risk_index >= 0.45 ? 'mlr-medium' :
                mlRiskInfo.risk_index >= 0.20 ? 'mlr-low' : 'mlr-safe']"
            >
              {{ mlRiskInfo.risk_index >= 0.70 ? '1인당 사고율 높음' :
                 mlRiskInfo.risk_index >= 0.45 ? '주의 구간' :
                 mlRiskInfo.risk_index >= 0.20 ? '보통' : '상대적 안전' }}
            </span>
          </div>
          <p class="ml-risk-warn">{{ mlRiskInfo.warning }}</p>

          <!-- 24시간 추이 그래프 -->
          <div v-if="mlRiskInfo.hourly_risks" class="ml-risk-chart-container">
            <div class="ml-risk-chart-title">
              <span>24시간 사고 위험도 추이</span>
              <span style="color:#ef4444; font-weight:700">
                {{ activePointer ? `${activePointer.hour}시: 위험 지수 ${(activePointer.risk_index * 100).toFixed(0)}` : '' }}
              </span>
            </div>
            <svg class="ml-risk-svg" viewBox="0 0 240 60">
              <defs>
                <linearGradient id="mlRiskAreaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#ef4444" stop-opacity="0.35" />
                  <stop offset="100%" stop-color="#ef4444" stop-opacity="0.0" />
                </linearGradient>
              </defs>
              <line x1="10" y1="50" x2="230" y2="50" stroke="rgba(75, 85, 99, 0.3)" stroke-width="0.5" stroke-dasharray="2 2" />
              <line x1="10" y1="27.5" x2="230" y2="27.5" stroke="rgba(75, 85, 99, 0.3)" stroke-width="0.5" stroke-dasharray="2 2" />
              <line x1="10" y1="5" x2="230" y2="5" stroke="rgba(75, 85, 99, 0.3)" stroke-width="0.5" stroke-dasharray="2 2" />

              <path :d="mlRiskAreaPath" fill="url(#mlRiskAreaGrad)" />
              <path :d="mlRiskLinePath" fill="none" stroke="#ef4444" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />

              <g v-if="activePointer">
                <line :x1="activePointer.x" y1="5" :x2="activePointer.x" y2="50" stroke="#ef4444" stroke-width="1" stroke-dasharray="2 2" />
                <circle :cx="activePointer.x" :cy="activePointer.y" r="8" class="ml-pointer-pulse" />
                <circle :cx="activePointer.x" :cy="activePointer.y" r="4.5" class="ml-pointer-dot" />
              </g>

              <text x="10" y="58" class="ml-chart-label" text-anchor="start">00시</text>
              <text x="67.4" y="58" class="ml-chart-label" text-anchor="middle">06시</text>
              <text x="124.8" y="58" class="ml-chart-label" text-anchor="middle">12시</text>
              <text x="182.2" y="58" class="ml-chart-label" text-anchor="middle">18시</text>
              <text x="230" y="58" class="ml-chart-label" text-anchor="end">24시</text>
            </svg>
          </div>

          <div class="ml-risk-types">
            <span
              v-for="(prob, type) in mlRiskInfo.type_proba"
              :key="type"
              class="ml-type-chip"
              :class="type === mlRiskInfo.top_type ? 'ml-type-top' : ''"
            >
              {{ { '부상사고':'실족·추락', '조난수색':'길잃음·조난', '질환':'탈진·질환', '기타':'기타' }[type] }}
              {{ Math.round(prob * 100) }}%
            </span>
          </div>
          <p class="ml-risk-note">* {{ mlTrainingNote }} 기반 1인당 사고율 분석</p>
        </div>
      </section>
    </nav>

    <router-view />

    <AuthModal v-if="showAuthModal" />
    <OnboardingModal v-if="showOnboarding" @close="showOnboarding = false" />
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authMode, authUser, loadMe, showAuthModal } from './composables/useAuth.js';
import { activeInfoPost, communityError, communityView } from './composables/useCommunity.js';
import { loadMyPageData } from './composables/useUserData.js';
import {
  guideError,
  guideStep,
  diffDotColor,
  filteredMountains,
  loadMountains,
  loadWeather,
  loading,
  mlRiskInfo,
  mlTrainingNote,
  mountainSearch,
  selectedMountain,
  weatherData,
  profile,
} from './composables/useGuide.js';
import AuthModal from './components/AuthModal.vue';
import LiveSafetyHero from './components/LiveSafetyHero.vue';
import OnboardingModal from './components/OnboardingModal.vue';
import { heroThemeSlides } from './data/heroCuration.js';

const showOnboarding = ref(!localStorage.getItem('ollaOnboarded'));
const router = useRouter();
const route = useRoute();

const showSafetyHero = computed(() => route.path === '/guide');

function goHome() {
  guideStep.value = 'browse';
  selectedMountain.value = null;
  router.push('/guide');
}

function handleThemeSelect(slide) {
  communityView.value = 'list';
  activeInfoPost.value = slide.id;
  router.push('/community');
}

function openLogin() {
  authMode.value = 'login';
  showAuthModal.value = true;
}

function handleSidebarMountainSelect(mountain) {
  guideStep.value = 'courses';
  selectedMountain.value = mountain;
  router.push('/guide');
}

function syncLoginRoute() {
  if (route.path !== '/login') return;
  if (authUser.value) {
    router.replace('/my-page');
    return;
  }
  openLogin();
}

const WILDFIRE_LABEL = { low: '낮음', medium: '보통', high: '높음', very_high: '매우높음' };

const liveSafetyItems = computed(() => {
  const w = weatherData.value;
  if (!w) return [{ id: 'loading', label: '날씨 정보', value: '불러오는 중…' }];

  const rainfall = w.rainfall_mm ?? 0;
  const wind = w.wind_speed_ms ?? 0;
  const weatherIcon = rainfall >= 10 ? '🌧' : rainfall > 0 ? '🌦' : wind >= 8 ? '💨' : '☀️';
  const weatherLabel = rainfall >= 10 ? '비' : rainfall > 0 ? '흐림' : '맑음';

  const items = [
    { id: 'temp',      label: '현재기온',  value: `${weatherIcon} ${weatherLabel} ${w.temperature_c}°C` },
    { id: 'rain',      label: '강수',      value: `${rainfall}mm` },
    { id: 'wind',      label: '풍속',      value: `${wind}m/s` },
    { id: 'humidity',  label: '습도',      value: `${w.humidity_pct ?? '-'}%` },
    { id: 'wildfire',  label: '산불위험',  value: WILDFIRE_LABEL[w.wildfire_risk] || '낮음' },
    { id: 'sunset',    label: '일몰',      value: w.sunset || '-' },
    { id: 'sunrise',   label: '일출',      value: w.sunrise || '-' },
  ];

  if (w.pm10_ugm3 != null) {
    items.push({ id: 'dust', label: '미세먼지', value: `${w.pm10_ugm3}㎍ · ${w.grade_pm10 || '-'}` });
  }
  if (w.pm25_ugm3 != null) {
    items.push({ id: 'fine-dust', label: '초미세먼지', value: `${w.pm25_ugm3}㎍ · ${w.grade_pm25 || '-'}` });
  }

  return items;
});

const globalError = computed({
  get: () => guideError.value || communityError.value,
  set: (v) => {
    guideError.value = v;
    communityError.value = v;
  },
});

const peakHourInfo = computed(() => {
  const risks = mlRiskInfo.value?.hourly_risks;
  if (!risks || risks.length === 0) return null;
  let maxRisk = -1;
  let maxHour = 12;
  for (const r of risks) {
    if (r.risk_index > maxRisk) {
      maxRisk = r.risk_index;
      maxHour = r.hour;
    }
  }
  return { hour: maxHour, riskIndex: maxRisk };
});

const selectedHour = computed(() => {
  if (!profile.departureTime) return 12;
  const parts = profile.departureTime.split(':');
  return parseInt(parts[0], 10) || 0;
});

const mlRiskChartPoints = computed(() => {
  const risks = mlRiskInfo.value?.hourly_risks;
  if (!risks || risks.length === 0) return [];
  
  const width = 220;
  const height = 45;
  const paddingX = 10;
  const paddingY = 5;
  
  return risks.map((r) => {
    const x = paddingX + (r.hour * width) / 23;
    const y = (paddingY + height) - (r.risk_index * height);
    return { hour: r.hour, risk_index: r.risk_index, x, y };
  });
});

const mlRiskLinePath = computed(() => {
  const pts = mlRiskChartPoints.value;
  if (pts.length === 0) return '';
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
});

const mlRiskAreaPath = computed(() => {
  const pts = mlRiskChartPoints.value;
  if (pts.length === 0) return '';
  const first = pts[0];
  const last = pts[pts.length - 1];
  const linePath = mlRiskLinePath.value;
  return `${linePath} L ${last.x.toFixed(1)} 50 L ${first.x.toFixed(1)} 50 Z`;
});

const activePointer = computed(() => {
  const h = selectedHour.value;
  const pts = mlRiskChartPoints.value;
  if (pts.length === 0) return null;
  return pts.find(p => p.hour === h) || pts[h] || pts[0];
});

onMounted(async () => {
  await loadMe();
  if (authUser.value) loadMyPageData();
  loadMountains();
  loadWeather();
  syncLoginRoute();
});

watch(() => route.path, syncLoginRoute);
watch(authUser, syncLoginRoute);
</script>
