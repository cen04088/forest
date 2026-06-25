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

    <SharedSidebar />

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
import { guideError, loadMountains, loadWeather, weatherData } from './composables/useGuide.js';
import AuthModal from './components/AuthModal.vue';
import LiveSafetyHero from './components/LiveSafetyHero.vue';
import OnboardingModal from './components/OnboardingModal.vue';
import SharedSidebar from './components/SharedSidebar.vue';
import { heroThemeSlides } from './data/heroCuration.js';

const showOnboarding = ref(!localStorage.getItem('ollaOnboarded'));
const router = useRouter();
const route = useRoute();

const showSafetyHero = computed(() => route.path === '/guide');

function handleThemeSelect(slide) {
  communityView.value = 'list';
  activeInfoPost.value = slide.id;
  router.push('/community');
}

function openLogin() {
  authMode.value = 'login';
  showAuthModal.value = true;
}

function syncLoginRoute() {
  if (route.path !== '/login') return;
  if (authUser.value) {
    router.replace('/my-page');
    return;
  }
  openLogin();
}

const WILDFIRE_LABEL = {
  low: '낮음',
  medium: '보통',
  high: '높음',
  very_high: '매우높음',
};

const liveSafetyItems = computed(() => {
  const w = weatherData.value;
  if (!w) {
    return [{ id: 'loading', label: '날씨 정보', value: '불러오는 중' }];
  }

  const rainfall = w.rainfall_mm ?? 0;
  const wind = w.wind_speed_ms ?? 0;
  const weatherLabel = rainfall >= 10 ? '비' : rainfall > 0 ? '흐림' : '맑음';

  const items = [
    { id: 'temp', label: '🌡️ 현재기온', value: `${weatherLabel} ${w.temperature_c}°C` },
    { id: 'rain', label: '🌧️ 강수', value: `${rainfall}mm` },
    { id: 'wind', label: '🍃 풍속', value: `${wind}m/s` },
    { id: 'humidity', label: '💧 습도', value: `${w.humidity_pct ?? '-'}%` },
    { id: 'wildfire', label: '⚠️ 산불위험', value: WILDFIRE_LABEL[w.wildfire_risk] || '낮음' },
    { id: 'sunset', label: '☀️ 일몰', value: w.sunset || '-' },
    { id: 'sunrise', label: '🌅 일출', value: w.sunrise || '-' },
  ];

  if (w.pm10_ugm3 != null) {
    items.push({ id: 'dust', label: '😷 미세먼지', value: `${w.pm10_ugm3}㎍· ${w.grade_pm10 || '-'}` });
  }
  if (w.pm25_ugm3 != null) {
    items.push({ id: 'fine-dust', label: '🫧 초미세먼지', value: `${w.pm25_ugm3}㎍· ${w.grade_pm25 || '-'}` });
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
