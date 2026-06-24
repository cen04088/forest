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

          <!-- 시간대별 사고 위험 분석 경보 -->
          <div v-if="mlRiskInfo.hourly_risks && peakHourInfo" class="ml-risk-alert-container">
            <div class="ml-risk-alert-title">🚨 오늘 가장 주의해야 할 시간대</div>
            <div class="ml-risk-alert-box">
              <div class="ml-risk-alert-time">
                ⏱️ <strong>{{ peakTimeRange }} (위험 최고조)</strong>
              </div>
              <p class="ml-risk-alert-desc">
                {{ peakTimeReason }}
              </p>
              <div class="ml-risk-alert-tip">
                💡 <strong>안전 행동 제안:</strong> {{ peakTimeTip }}
              </div>
            </div>
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

const peakTimeRange = computed(() => {
  const info = peakHourInfo.value;
  if (!info) return '';
  const start = info.hour;
  const end = (info.hour + 2) % 24;
  return `${String(start).padStart(2, '0')}:00 ~ ${String(end).padStart(2, '0')}:00`;
});

const peakTimeReason = computed(() => {
  const info = peakHourInfo.value;
  if (!info) return '';
  
  let reason = '';
  if (info.hour >= 12 && info.hour <= 16) {
    reason = '점심 식사 이후 피로가 누적되고 본격적인 하산이 시작되는 시간대로, 신체의 긴장이 풀려 실족이나 추락 사고의 발생 확률이 매우 높습니다.';
  } else if (info.hour >= 17 || info.hour <= 6) {
    reason = '일몰 전후 및 야간 시간대로, 시야가 급격히 차단되고 산속 기온이 하강하여 조난, 저체온증 등 한랭 질환 사고 위험이 최고조에 달합니다.';
  } else {
    reason = '오전 시간대로, 체력 안배 실패나 충분하지 못한 사전 몸풀기로 인해 급작스러운 신체 이상 및 관절 부상 사고율이 상대적으로 높습니다.';
  }

  const w = weatherData.value;
  if (w) {
    const rainfall = w.rainfall_mm ?? 0;
    const wind = w.wind_speed_ms ?? 0;
    if (rainfall > 0 || wind >= 5) {
      reason += ' 특히 현재 현장에 감지되는 비/강풍 등 불리한 기상 조건이 결합되어 평소보다 낙상 및 체온 저하 위험이 더욱 심각합니다.';
    }
  }
  return reason;
});

const peakTimeTip = computed(() => {
  const info = peakHourInfo.value;
  if (!info) return '';
  const topType = mlRiskInfo.value?.top_type || '부상사고';
  
  if (topType === '부상사고') {
    return '하산 시 보폭을 좁혀 무릎 충격을 줄이고, 낙엽이나 젖은 돌을 디디지 않도록 등산 스틱을 양손에 꼭 쥐고 체중을 분산해 주세요.';
  } else if (topType === '조난수색') {
    return '지정된 등산로(탐방로)로만 보행하며, 일몰 2시간 전 조기 하산을 완수하시거나 여분의 랜턴/보조배터리를 꼭 휴대해 주세요.';
  } else if (topType === '질환') {
    return '페이스 조절에 유의하고 무리하게 속도를 내지 마세요. 이온음료나 따뜻한 음료를 마시고 에너지를 보충할 초콜릿류를 자주 드셔야 합니다.';
  }
  return '일기예보를 예의주시하고 급박한 비구름이나 기상 변화 조짐이 느껴질 경우 산행을 즉시 멈추고 대피소로 이동하세요.';
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
