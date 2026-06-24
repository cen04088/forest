<template>
  <main class="app-shell">
    <!-- ─── 히어로 헤더 ──────────────────────────────────────────────────── -->
    <header class="app-hero">
      <LiveSafetyHero
        :safety-items="liveSafetyItems"
:slides="heroThemeSlides"
        @select-theme="handleThemeSelect"
      />

      <div class="hero-nav">
        <div class="hero-nav-actions">
          <button class="hero-login-btn" type="button" @click="showAuthModal = true">
            {{ authUser ? authUser.nickname : '로그인' }}
          </button>
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
      <router-link to="/my-page" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </router-link>
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
import { useRouter } from 'vue-router';
import { authUser, loadMe, showAuthModal } from './composables/useAuth.js';
import { activeInfoPost, communityError, communityView } from './composables/useCommunity.js';
import { loadMyPageData } from './composables/useUserData.js';
import {
  guideError,
  guideStep,
  loadWeather,
  selectedMountain,
  weatherData,
} from './composables/useGuide.js';
import AuthModal from './components/AuthModal.vue';
import LiveSafetyHero from './components/LiveSafetyHero.vue';
import OnboardingModal from './components/OnboardingModal.vue';
import { heroThemeSlides } from './data/heroCuration.js';

const showOnboarding = ref(!localStorage.getItem('ollaOnboarded'));
const router = useRouter();

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
  set: (v) => { guideError.value = v; communityError.value = v; },
});

onMounted(async () => {
  await loadMe();
  if (authUser.value) loadMyPageData();
  loadWeather();
});
</script>
