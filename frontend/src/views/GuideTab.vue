<template>
  <section class="screen-stack guide-layout">

    <!-- ── 지도 (왼쪽, 양 단계 공통) ── -->
    <div class="guide-map">
      <div ref="overviewMapEl" class="overview-map-container" aria-label="등산 추천 지도"></div>
      <div class="map-legend">
        <span class="map-legend-item"><i class="legend-dot" style="background:#22c55e"></i>초급</span>
        <span class="map-legend-item"><i class="legend-dot" style="background:#f97316"></i>중급</span>
        <span class="map-legend-item"><i class="legend-dot" style="background:#ef4444"></i>고급</span>
        <span v-if="hasRecommendationResult" class="map-legend-item"><i class="legend-dot" style="background:#f59e0b;box-shadow:0 0 0 2px #f59e0b55"></i>추천</span>
        <span class="map-legend-hint">{{ guideStep === 'browse' ? '산을 선택하세요' : selectedMountain?.name }}</span>
      </div>
    </div>

    <!-- ── 오른쪽 패널 ── -->
    <div class="guide-panel">

      <!-- ════════════════════════════════
           PHASE 1: 산 선택
           ════════════════════════════════ -->
      <template v-if="guideStep === 'browse'">

        <!-- ── 통합 찾기 패널 ── -->
        <section class="panel browse-find-panel">
          <h2 class="bfp-title">오늘의 산 찾기</h2>

          <!-- 산 검색 -->
          <div class="bfp-search-row">
            <svg class="bfp-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="mountainSearch"
              class="bfp-search-input"
              type="text"
              placeholder="산 이름 또는 지역 검색…"
              autocomplete="off"
            />
          </div>

          <div class="bfp-divider"><span>AI 맞춤 추천</span></div>

          <!-- 출발지 -->
          <div class="bfp-field">
            <span class="bfp-label">출발지</span>
            <div class="bfp-loc-row">
              <div class="bfp-loc-status" :class="{ active: !!location || !!customStartLocation }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                <span>{{ locationLabel }}</span>
              </div>
              <div class="bfp-loc-actions">
                <button
                  type="button"
                  class="bfp-loc-btn"
                  :class="{ loading: gpsStatus === 'loading', error: gpsStatus === 'error' }"
                  :disabled="gpsStatus === 'loading'"
                  @click="handleGPS"
                  title="현재 위치 감지"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" :class="gpsStatus === 'loading' ? 'spin' : ''"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/></svg>
                  GPS
                </button>
                <select class="bfp-city-select" v-model="manualCity" @change="applyManualCity">
                  <option value="">도시 선택</option>
                  <option value="seoul">서울</option>
                  <option value="suwon">수원</option>
                  <option value="incheon">인천</option>
                  <option value="chuncheon">춘천</option>
                  <option value="gangneung">강릉</option>
                  <option value="daejeon">대전</option>
                  <option value="jeonju">전주</option>
                  <option value="gwangju">광주</option>
                  <option value="daegu">대구</option>
                  <option value="busan">부산</option>
                  <option value="jeju">제주</option>
                </select>
              </div>
            </div>
            <p v-if="gpsStatus === 'error'" class="bfp-error">⚠️ {{ gpsError }}</p>
          </div>

          <!-- 산행 강도 -->
          <div class="bfp-field">
            <span class="bfp-label">산행 강도</span>
            <div class="chips">
              <button type="button" :class="['chip diff-easy', profile.difficultyFilter === 'easy' ? 'active' : '']" @click="setDifficulty('easy')">초급</button>
              <button type="button" :class="['chip diff-medium', profile.difficultyFilter === 'medium' ? 'active' : '']" @click="setDifficulty('medium')">중급</button>
              <button type="button" :class="['chip diff-hard', profile.difficultyFilter === 'hard' ? 'active' : '']" @click="setDifficulty('hard')">고급</button>
            </div>
          </div>

          <button class="primary-btn wide-field" type="button" :disabled="loading" @click="handleMountainRecommend">
            {{ loading ? '분석 중…' : '🏔 AI 맞춤 추천받기' }}
          </button>
        </section>

        <!-- ── AI 추천 결과 ── -->
        <section v-if="hasRecommendationResult && recommendedMountains.length" class="panel">
          <div class="section-title compact">
            <div><p class="eyebrow">AI Picks</p><h2>오늘의 추천 산</h2></div>
            <button class="clear-rec-btn" type="button" @click="hasRecommendationResult = false">✕ 닫기</button>
          </div>
          <p v-if="agentSummary" class="rec-summary">{{ agentSummary }}</p>
          <div class="mountain-card-list">
            <MountainCard
              v-for="(mountain, idx) in recommendedMountains.slice(0, 3)"
              :key="mountain.id"
              :mountain="mountain"
              :rank="idx + 1"
              :is-selected="false"
              @select="enterCourseStep"
            />
          </div>
        </section>

        <!-- ── 전체 산 목록 ── -->
        <section class="panel mountain-list-panel">
          <div class="section-title compact">
            <h2>전체 산<span class="mini-status" style="margin-left:6px">{{ filteredMountains.length }}</span></h2>
          </div>

          <div v-if="loading && !filteredMountains.length" class="community-loading">분석 중…</div>

          <div class="mountain-browse-list">
            <button
              v-for="mountain in filteredMountains"
              :key="mountain.id"
              class="mountain-browse-row"
              type="button"
              @click="enterCourseStep(mountain)"
            >
              <i class="mbr-diff-dot" :style="{ background: diffDotColor(mountain.difficulty) }"></i>
              <div class="mbr-body">
                <strong class="mbr-name">{{ mountain.name }}</strong>
                <span class="mbr-meta">{{ mountain.region }}&nbsp;·&nbsp;{{ mountain.elevation_m }}m</span>
              </div>
              <span v-if="mountain.national_park" class="mc-np-badge" style="flex-shrink:0">국립공원</span>
              <svg class="mbr-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </section>

      </template>

      <!-- ════════════════════════════════
           PHASE 2: 산 정보 대시보드
           ════════════════════════════════ -->
      <template v-else-if="selectedMountain">

        <!-- 산 헤더 -->
        <section class="panel course-step-header">
          <!-- 상단 내비 행: 뒤로가기 + 후기 버튼 -->
          <div class="csh-nav">
            <button class="back-to-browse-btn" type="button" @click="backToBrowse">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              산 목록
            </button>
            <button class="community-link-btn" type="button" @click="goToCommunity(selectedMountain.name)">
              💬 후기
            </button>
          </div>

          <!-- 산 제목 -->
          <div class="csh-title-block">
            <p class="eyebrow">{{ selectedMountain.region }}</p>
            <div class="csh-title-row">
              <h2 class="csh-mountain-name">{{ selectedMountain.name }}</h2>
              <span v-if="selectedMountain.national_park" class="mc-np-badge">국립공원</span>
            </div>
          </div>

          <!-- 오늘 산행 안전 등급 -->
          <div class="mountain-safety-rating" v-if="mountainSafetyDecision">
            <span :class="['safety-badge', mountainSafetyDecision.class]">
              {{ mountainSafetyDecision.label }}
            </span>
            <p class="msr-sub">오늘 {{ selectedMountain.name }} 산행 안전 평가</p>
          </div>

          <!-- 통계 -->
          <div class="mountain-detail-stats">
            <div class="mds-item"><span class="mds-icon">⛰</span><span class="mds-label">해발</span><strong>{{ selectedMountain.elevation_m }}m</strong></div>
            <div class="mds-item"><span class="mds-icon">⏱</span><span class="mds-label">산행 시간</span><strong>{{ Math.floor(selectedMountain.walk_time_min/60) }}~{{ Math.floor(selectedMountain.walk_time_max/60) }}h</strong></div>
            <div class="mds-item"><span class="mds-icon">🏔</span><span class="mds-label">난이도</span><strong>{{ { easy:'초급', medium:'중급', hard:'고급' }[selectedMountain.difficulty] || '-' }}</strong></div>
            <div class="mds-item"><span class="mds-icon">👥</span><span class="mds-label">혼잡도</span><strong>{{ crowdingLabel(selectedMountain.crowding) }}</strong></div>
          </div>

          <!-- 날씨 카드 -->
          <div v-if="weatherData" class="mountain-weather-card">
            <div class="mwc-header">
              <span class="mwc-label">📡 {{ selectedMountain.name }} 날씨</span>
              <span class="mwc-source">{{ weatherData.source === 'mock' ? '추정값' : '기상청 실황' }}</span>
            </div>
            <div class="mwc-row">
              <span class="mwc-item">
                <span class="mwc-icon">🌡</span>
                <span>{{ weatherData.temperature_c }}°C</span>
              </span>
              <span class="mwc-item" :class="weatherData.rainfall_mm > 0 ? 'mwc-warn' : ''">
                <span class="mwc-icon">💧</span>
                <span>강수 {{ weatherData.rainfall_mm ?? 0 }}mm</span>
              </span>
              <span class="mwc-item" :class="weatherData.wind_speed_ms >= 5 ? 'mwc-warn' : ''">
                <span class="mwc-icon">💨</span>
                <span>풍속 {{ weatherData.wind_speed_ms }}m/s</span>
              </span>
              <span class="mwc-item">
                <span class="mwc-icon">🌄</span>
                <span>일출 {{ weatherData.sunrise || '-' }}</span>
              </span>
              <span class="mwc-item" :class="sunsetWarning ? 'mwc-warn' : ''">
                <span class="mwc-icon">🌅</span>
                <span>일몰 {{ weatherData.sunset || '-' }}</span>
              </span>
            </div>
            <p v-if="selectedMountainSunsetNote" class="mwc-sunset-note">{{ selectedMountainSunsetNote }}</p>
          </div>

          <!-- 산 소개 -->
          <div v-if="storyText" class="mountain-story-card">
            <div class="msc-summary-wrap" :class="{ collapsed: storyNeedsToggle && !storyExpanded }">
              <p class="mountain-story-summary">{{ storyText }}</p>
              <div v-if="storyNeedsToggle && !storyExpanded" class="msc-fade"></div>
            </div>
            <button v-if="storyNeedsToggle" class="msc-toggle" type="button" @click="storyExpanded = !storyExpanded">
              {{ storyExpanded ? '접기 ▲' : '더 보기 ▼' }}
            </button>

            <div v-if="mountainStory?.selection_reason" class="msc-selection">
              <span class="msc-selection-label">🏆 100대 명산 선정 이유</span>
              <p class="msc-selection-text">{{ mountainStory.selection_reason }}</p>
            </div>
          </div>

          <!-- 재난위험지구 -->
          <div v-if="selectedDisasterZones.length" class="disaster-zone-panel">
            <p class="disaster-zone-title">⚠️ 인근 재난위험지구 {{ selectedDisasterZones.length }}개</p>
            <ul class="disaster-zone-list">
              <li v-for="zone in selectedDisasterZones.slice(0, 3)" :key="zone.id">
                <strong>{{ zone.district || zone.location }}</strong>
                <span v-if="zone.risk_factor"> · {{ zone.risk_factor }}</span>
              </li>
            </ul>
          </div>

          <!-- 커뮤니티 안전 제보 -->
          <div v-if="mountainSafetyReports.length" class="disaster-zone-panel">
            <p class="disaster-zone-title">📢 커뮤니티 안전 제보 {{ mountainSafetyReports.length }}건</p>
            <ul class="disaster-zone-list">
              <li v-for="r in mountainSafetyReports.slice(0, 3)" :key="r.id">
                <strong>{{ r.title }}</strong>
                <span> · 👍 {{ r.like_count }} 💬 {{ r.comment_count }}</span>
              </li>
            </ul>
          </div>
        </section>

        <!-- AI 맞춤 안전 조언 -->
        <div class="safety-advice-panel" v-if="safetyAdviceLines.length || safetyAdviceLoading">
          <div class="safety-advice-header">
            <span class="safety-advice-icon">🧭</span>
            <p class="safety-advice-title">AI 맞춤 안전 조언</p>
            <span v-if="safetyAdviceLoading" class="advice-loading-dot"></span>
          </div>
          <ul class="safety-advice-list">
            <li v-for="(line, i) in safetyAdviceLines" :key="i">{{ line }}</li>
          </ul>
        </div>

        <!-- 하이라이트 -->
        <section v-if="selectedMountain.highlights?.length" class="panel">
          <div class="section-title compact">
            <div><p class="eyebrow">Highlights</p><h2>이 산의 매력</h2></div>
          </div>
          <ul class="highlight-list">
            <li v-for="h in selectedMountain.highlights" :key="h">{{ h }}</li>
          </ul>
        </section>

        <!-- AI 도우미 CTA -->
        <div class="chat-cta-panel">
          <p class="chat-cta-text">{{ selectedMountain.name }} 산행, AI에게 더 물어보세요</p>
          <button class="chat-cta-btn" type="button" @click="goToChat">
            🤖 AI 도우미에게 물어보기
          </button>
        </div>

      </template>

    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  loadMountains, publicMountains, recommendedMountains, alternativeMountains,
  selectedMountain, gpsStatus, gpsError, detectGPS, loadWeather, weatherData,
  submitMountainRecommendation, loading, profile, agentSummary,
  location, customStartLocation,
} from '../composables/useGuide.js';
import { communitySearch, communityCategory } from '../composables/useCommunity.js';
import { fetchDisasterZones, fetchSafetyAdvice, fetchMountainStory, fetchSafetyReports, fetchMountainIntro } from '../api.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';
import MountainCard from '../components/MountainCard.vue';

const router = useRouter();
const overviewMapEl = ref(null);
const { renderOverviewMap, focusOverviewCourse } = useLeafletMap();

// ── 단계 상태 ────────────────────────────────────────────────────────────────
const guideStep = ref('browse'); // 'browse' | 'courses'

// ── 브라우즈 상태 ─────────────────────────────────────────────────────────────
const mountainSearch = ref('');
const hasRecommendationResult = ref(false);

// ── 출발지 선택 ───────────────────────────────────────────────────────────────
const CITY_COORDS = {
  seoul:     { lat: 37.5665, lng: 126.9780, name: '서울' },
  suwon:     { lat: 37.2636, lng: 127.0286, name: '수원' },
  incheon:   { lat: 37.4563, lng: 126.7052, name: '인천' },
  chuncheon: { lat: 37.8813, lng: 127.7298, name: '춘천' },
  gangneung: { lat: 37.7519, lng: 128.8761, name: '강릉' },
  daejeon:   { lat: 36.3504, lng: 127.3845, name: '대전' },
  jeonju:    { lat: 35.8242, lng: 127.1480, name: '전주' },
  gwangju:   { lat: 35.1595, lng: 126.8526, name: '광주' },
  daegu:     { lat: 35.8714, lng: 128.6014, name: '대구' },
  busan:     { lat: 35.1796, lng: 129.0756, name: '부산' },
  jeju:      { lat: 33.4996, lng: 126.5312, name: '제주' },
};

const manualCity = ref('');

function applyManualCity() {
  const city = CITY_COORDS[manualCity.value];
  if (city) {
    customStartLocation.value = city;
  }
}

const locationLabel = computed(() => {
  if (customStartLocation.value) return customStartLocation.value.name + ' 기준';
  if (location.value) return '현재 위치 감지됨';
  return '위치 미설정';
});

function diffDotColor(difficulty) {
  if (difficulty === 'easy') return '#22c55e';
  if (difficulty === 'medium') return '#f97316';
  if (difficulty === 'hard') return '#ef4444';
  return '#9ca3af';
}

// profile.experience(UI표시용) 와 profile.difficultyFilter(백엔드 필터)를 동기화
function setDifficulty(level) {
  if (profile.difficultyFilter === level) {
    // 같은 칩 재클릭 → 필터 해제
    profile.difficultyFilter = 'all';
    profile.experience = 'beginner';
  } else {
    profile.difficultyFilter = level;
    const expMap = { easy: 'beginner', medium: 'intermediate', hard: 'advanced' };
    profile.experience = expMap[level];
  }
}

async function handleMountainRecommend() {
  await submitMountainRecommendation();
  hasRecommendationResult.value = true;
  await nextTick();
  refreshOverviewMap();
}

// ── 코스 단계 로컬 상태 ───────────────────────────────────────────────────────
const selectedDisasterZones = ref([]);
const safetyAdviceText = ref('');
const safetyAdviceLoading = ref(false);
const mountainStory = ref(null);
const mountainSafetyReports = ref([]);
const storyExpanded = ref(false);
const aiIntro = ref(''); // AI가 변환한 친근한 소개문

const storyText = computed(() =>
  aiIntro.value || mountainStory.value?.summary || selectedMountain.value?.description || ''
);
const storyNeedsToggle = computed(() => storyText.value.length > 160);

// ── 브라우즈 단계: 필터된 산 목록 ────────────────────────────────────────────
const filteredMountains = computed(() => {
  const search = mountainSearch.value.trim().toLowerCase();
  const safetyMap = new Map(
    [...recommendedMountains.value, ...alternativeMountains.value].map((m) => [m.id, m])
  );

  let base = publicMountains.value.map((m) => {
    const scored = safetyMap.get(m.id);
    return scored ? { ...m, ...scored } : m;
  });

  if (search) {
    base = base.filter(
      (m) =>
        m.name.toLowerCase().includes(search) ||
        (m.region || '').toLowerCase().includes(search),
    );
  }

  return base.sort((a, b) => {
    const aRanked = !!a.safety_decision;
    const bRanked = !!b.safety_decision;
    if (aRanked !== bRanked) return aRanked ? -1 : 1;
    if (aRanked && bRanked) {
      const order = { recommend: 0, caution: 1, not_recommended: 2 };
      return (order[a.safety_decision] ?? 3) - (order[b.safety_decision] ?? 3);
    }
    return (b.crowding || 0) - (a.crowding || 0);
  });
});

function browseBadgeClass(mountain) {
  return { recommend: 'green', caution: 'yellow', not_recommended: 'red' }[mountain.safety_decision] || '';
}

// ── 지도 ─────────────────────────────────────────────────────────────────────
const mapMountains = computed(() => {
  // 추천 실행 전: 모든 산을 그대로 (난이도 색상으로 표시)
  if (!hasRecommendationResult.value || !recommendedMountains.value.length) {
    return publicMountains.value;
  }
  // 추천 실행 후: 추천된 산에 _highlighted, 나머지는 _muted
  const recommended = new Set(recommendedMountains.value.map((m) => m.id));
  const alternatives = new Set(alternativeMountains.value.map((m) => m.id));
  return publicMountains.value.map((m) => ({
    ...m,
    _highlighted: recommended.has(m.id),
    _muted: !recommended.has(m.id) && !alternatives.has(m.id),
  }));
});

function refreshOverviewMap() {
  if (!overviewMapEl.value) return;
  renderOverviewMap(
    overviewMapEl.value,
    mapMountains.value,
    selectedMountain.value?.id,
    (mountain) => enterCourseStep(mountain),
  );
}

// ── 단계 전환 ─────────────────────────────────────────────────────────────────
async function enterCourseStep(mountain) {
  guideStep.value = 'courses';
  selectedMountain.value = mountain;
  safetyAdviceText.value = '';
  mountainStory.value = null;
  mountainSafetyReports.value = [];
  selectedDisasterZones.value = [];
  storyExpanded.value = false;
  aiIntro.value = '';

  if (mountain?.lat && mountain?.lng) loadWeather(mountain.lat, mountain.lng, mountain.name);
  await nextTick();
  focusOverviewCourse(mountain);
  refreshOverviewMap();

  const [zonesData, storyData, reportsData] = await Promise.allSettled([
    fetchDisasterZones(mountain.name),
    fetchMountainStory(mountain.name),
    fetchSafetyReports(mountain.name),
  ]);
  selectedDisasterZones.value = zonesData.status === 'fulfilled' ? (zonesData.value.zones || []) : [];
  const story = storyData.status === 'fulfilled' ? (storyData.value.items?.[0] ?? null) : null;
  mountainStory.value = story;
  mountainSafetyReports.value = reportsData.status === 'fulfilled' ? (reportsData.value.posts || []) : [];

  // 산림청 원문 또는 기본 설명을 AI가 친근한 말투로 변환 (DB 캐시)
  const rawSummary = story?.summary || mountain.description || '';
  if (rawSummary) {
    fetchMountainIntro({
      name: mountain.name,
      summary: rawSummary,
      selectionReason: story?.selection_reason || '',
    }).then((res) => {
      if (res?.intro && selectedMountain.value?.name === mountain.name) {
        aiIntro.value = res.intro;
      }
    }).catch(() => {});
  }

  loadSafetyAdvice(mountain);
}

function backToBrowse() {
  guideStep.value = 'browse';
  selectedMountain.value = null;
  safetyAdviceText.value = '';
  refreshOverviewMap();
}

// ── 산행 안전 등급 (추천 결과 or 날씨 기반) ──────────────────────────────────
const mountainSafetyDecision = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;

  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find(
    (r) => r.id === m.id,
  );
  if (scored?.safety_decision) {
    return {
      class: { recommend: 'green', caution: 'yellow', not_recommended: 'red' }[scored.safety_decision] || '',
      label: scored.safety_label || scored.safety_decision,
    };
  }

  const w = weatherData.value;
  if (!w) return null;
  const rain = w.rainfall_mm ?? 0;
  const wind = w.wind_speed_ms ?? 0;
  if (rain >= 20 || wind >= 10) return { class: 'red', label: '비추천' };
  if (rain > 0 || wind >= 5) return { class: 'yellow', label: '주의' };
  return { class: 'green', label: '추천' };
});

// ── 일몰 경고 ────────────────────────────────────────────────────────────────
const sunsetWarning = computed(() => {
  const w = weatherData.value;
  const m = selectedMountain.value;
  if (!w?.sunset || !m) return false;
  const [sh, sm] = w.sunset.split(':').map(Number);
  const sunsetMin = sh * 60 + sm;
  const now = new Date();
  const nowMin = now.getHours() * 60 + now.getMinutes();
  const walkMax = m.walk_time_max ?? 180;
  return (nowMin + walkMax) > (sunsetMin - 30); // 30분 여유 이하
});

const selectedMountainSunsetNote = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;
  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find((r) => r.id === m.id);
  return scored?.sunset_note || null;
});

// ── AI 안전 조언 ──────────────────────────────────────────────────────────────
async function loadSafetyAdvice(mountain) {
  safetyAdviceLoading.value = true;
  try {
    const data = await fetchSafetyAdvice({
      mountain,
      weather: weatherData.value || {},
      profile: {},
      sunTimes: null,
    });
    safetyAdviceText.value = data.advice || '';
  } catch {
    safetyAdviceText.value = '';
  } finally {
    safetyAdviceLoading.value = false;
  }
}

const safetyAdviceLines = computed(() =>
  safetyAdviceText.value
    ? safetyAdviceText.value.split('\n').map((l) => l.trim()).filter(Boolean)
    : [],
);

// ── 유틸 ──────────────────────────────────────────────────────────────────────
function crowdingLabel(c) {
  if (c < 0.4) return '한산';
  if (c < 0.65) return '보통';
  return '혼잡';
}

function goToCommunity(mountainName) {
  communitySearch.value = mountainName;
  communityCategory.value = '';
  router.push('/community');
}

function goToChat() {
  router.push('/chat');
}

async function handleGPS() {
  customStartLocation.value = null; // GPS 사용 시 수동 도시 초기화
  manualCity.value = '';
  await detectGPS();
  loadWeather();
}

// ── 반응성 ────────────────────────────────────────────────────────────────────
watch(mapMountains, () => refreshOverviewMap());
watch(selectedMountain, () => refreshOverviewMap());

onMounted(async () => {
  await loadMountains();
  loadWeather();
  await nextTick();
  refreshOverviewMap();
});
</script>
