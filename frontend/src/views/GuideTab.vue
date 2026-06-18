<template>
  <section class="screen-stack guide-layout">

    <!-- ── 메인 지도 (왼쪽) ── -->
    <div class="guide-map">
      <div ref="overviewMapEl" class="overview-map-container" aria-label="등산 추천 지도"></div>
      <div class="map-legend">
        <span class="map-legend-item"><i class="legend-dot" style="background:#22c55e"></i>추천</span>
        <span class="map-legend-item"><i class="legend-dot" style="background:#f97316"></i>주의</span>
        <span class="map-legend-item"><i class="legend-dot" style="background:#9ca3af"></i>비추천</span>
        <span v-if="!recommendedMountains.length" class="map-legend-hint">핀 = 산 위치</span>
        <span v-else class="map-legend-hint">색상 = 안전등급</span>
      </div>
    </div>

    <!-- ── 오른쪽 패널 ── -->
    <div class="guide-panel">

      <!-- 선택 산 상세 (핀 클릭 시 최상단 표시) -->
      <section v-if="selectedMountain" class="panel detail-panel">
        <div class="section-title">
          <div><p class="eyebrow">Mountain Detail</p><h2>{{ selectedMountain.name }}</h2></div>
          <button class="outline-btn" type="button" @click="selectedMountain = null">✕ 닫기</button>
        </div>
        <div class="mountain-detail-stats">
          <div class="mds-item">
            <span class="mds-icon">⛰</span>
            <span class="mds-label">해발고도</span>
            <strong>{{ selectedMountain.elevation_m }}m</strong>
          </div>
          <div class="mds-item">
            <span class="mds-icon">⏱</span>
            <span class="mds-label">산행 시간</span>
            <strong>{{ Math.floor(selectedMountain.walk_time_min/60) }}~{{ Math.floor(selectedMountain.walk_time_max/60) }}시간</strong>
          </div>
          <div class="mds-item">
            <span class="mds-icon">🗺</span>
            <span class="mds-label">탐방로</span>
            <strong>{{ selectedMountain.trail_count }}개</strong>
          </div>
          <div class="mds-item">
            <span class="mds-icon">👥</span>
            <span class="mds-label">혼잡도</span>
            <strong>{{ crowdingLabel(selectedMountain.crowding) }}</strong>
          </div>
        </div>
        <p class="detail-copy">{{ selectedMountain.description }}</p>
        <div class="mc-highlights" style="margin-top:10px">
          <span v-for="h in selectedMountain.highlights" :key="h" class="mc-tag">{{ h }}</span>
        </div>
        <div v-if="selectedDisasterZones.length" class="disaster-zone-panel">
          <p class="disaster-zone-title">⚠️ 인근 재난위험지구 {{ selectedDisasterZones.length }}개</p>
          <ul class="disaster-zone-list">
            <li v-for="zone in selectedDisasterZones.slice(0, 4)" :key="zone.id">
              <strong>{{ zone.district || zone.location }}</strong>
              <span v-if="zone.risk_factor"> · {{ zone.risk_factor }}</span>
            </li>
          </ul>
        </div>

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

        <button class="community-link-btn" type="button" @click="goToCommunity(selectedMountain.name)">
          💬 {{ selectedMountain.name }} 커뮤니티 후기 보기
        </button>
      </section>

      <!-- 입력 폼 -->
      <section class="panel planner-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Mountain Finder</p>
            <h2>나에게 맞는 산 추천</h2>
          </div>
          <button
            class="gps-refresh-btn" type="button"
            :class="gpsStatus" :disabled="gpsStatus === 'loading'"
            :title="gpsBtnTitle" @click="handleGPS"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" :class="gpsStatus === 'loading' ? 'spin' : ''">
              <polyline points="1 4 1 10 7 10"/>
              <path d="M3.51 15a9 9 0 1 0 .49-4.5"/>
            </svg>
            <span>{{ gpsStatus === 'loading' ? '감지 중…' : gpsStatus === 'success' ? '위치 갱신' : '위치 갱신' }}</span>
          </button>
        </div>

        <form class="planner" @submit.prevent="handleSubmit">
          <label class="field">
            <span>출발 일자</span>
            <input v-model="profile.departureDate" type="date" :min="minDepartureDate" :max="maxDepartureDate" />
          </label>
          <label class="field">
            <span>출발 시간</span>
            <input v-model="profile.departureTime" type="time" :min="minDepartureTime" @change="ensureFutureDepartureTime" />
          </label>
          <label class="field">
            <span>희망 산행 시간</span>
            <select v-model.number="profile.desiredHikingMinutes">
              <option :value="60">1시간</option>
              <option :value="120">2시간</option>
              <option :value="180">3시간</option>
              <option :value="240">4시간</option>
              <option :value="300">5시간</option>
              <option :value="360">6시간</option>
              <option :value="480">8시간</option>
              <option :value="600">10시간</option>
              <option :value="720">12시간</option>
            </select>
          </label>
          <div class="field wide-field">
            <span>난이도</span>
            <div class="segment-group wrap">
              <label v-for="d in difficultyFilters" :key="d.value" class="segment-btn">
                <input type="radio" v-model="profile.difficultyFilter" :value="d.value" name="difficulty_filter" />
                <span>{{ d.label }}</span>
              </label>
            </div>
          </div>

          <!-- 출발지 지정 -->
          <div class="field wide-field start-location-field">
            <span>출발지</span>
            <div class="start-location-toggle">
              <button
                type="button"
                :class="['sl-tab', !useCustomStart && 'sl-tab-active']"
                @click="useCustomStart = false"
              >📍 내 현재 위치</button>
              <button
                type="button"
                :class="['sl-tab', useCustomStart && 'sl-tab-active']"
                @click="useCustomStart = true"
              >🗺 직접 지정</button>
            </div>
            <div v-if="useCustomStart" class="start-search-row">
              <input
                v-model="startQuery"
                class="start-search-input"
                type="text"
                placeholder="예: 서울역, 수원시청, 강남구…"
                @keydown.enter.prevent="searchStartLocation"
              />
              <button type="button" class="start-search-btn" :disabled="startSearching" @click="searchStartLocation">
                {{ startSearching ? '검색 중…' : '검색' }}
              </button>
            </div>
            <div v-if="useCustomStart && startResults.length" class="start-results">
              <button
                v-for="r in startResults" :key="r.place_id"
                type="button"
                :class="['start-result-item', customStartLocation?.name === r.display_name && 'selected']"
                @click="selectStartResult(r)"
              >
                <span class="sr-name">{{ r.name }}</span>
                <span class="sr-detail">{{ r.detail }}</span>
              </button>
            </div>
            <p v-if="useCustomStart && startError" class="start-error">{{ startError }}</p>
            <p v-if="useCustomStart && customStartLocation" class="start-confirmed">
              ✅ {{ customStartLocation.name }}
            </p>
          </div>

          <p v-if="gpsStatus === 'error' && !useCustomStart" class="gps-message error" style="margin-bottom:4px">⚠️ {{ gpsError }}</p>

          <button class="primary-btn wide-field" :class="{ loading }" type="submit" :disabled="loading">
            {{ loading ? '최적 산 분석 중…' : '나에게 맞는 산 찾기' }}
          </button>
        </form>
      </section>


      <!-- 로딩 스켈레톤 -->
      <section v-if="loading" class="panel">
        <div class="skeleton-card"><div class="skeleton-line short"></div><div class="skeleton-line full"></div><div class="skeleton-line medium"></div></div>
        <div class="skeleton-card"><div class="skeleton-line short"></div><div class="skeleton-line full"></div><div class="skeleton-line medium"></div></div>
      </section>

      <!-- 준비 화면 -->
      <div v-if="resultState === 'idle' && !loading" class="idle-screen">
        <div class="idle-tip"><span class="idle-tip-icon">💡</span><span class="idle-tip-text">{{ dailyTip }}</span></div>
        <div class="idle-sources">
          <p class="idle-section-label">📡 연동 데이터</p>
          <div class="source-chips">
            <span class="source-chip">기상청 실황</span>
            <span class="source-chip">산림청 산불예보</span>
            <span class="source-chip">국립공원 탐방로</span>
            <span class="source-chip">재난위험지구</span>
          </div>
        </div>
      </div>

      <!-- 비추천 공지 -->
      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에 적합한 산이 없습니다</h3>
        <p>{{ agentSummary }}</p>
      </article>

      <!-- AI 안전 브리핑 -->
      <div v-if="!loading && agentSummary && resultState === 'has_recommendations'" class="briefing-card">
        <div class="briefing-icon">🤖</div>
        <div class="briefing-body">
          <p class="briefing-eyebrow">AI 산 추천 브리핑</p>
          <p class="briefing-text">{{ agentSummary }}</p>
        </div>
      </div>

      <!-- 추천 산 목록 -->
      <section v-if="!loading && recommendedMountains.length" class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Recommended</p><h2>추천 산</h2></div>
          <span class="mini-status">{{ recommendedMountains.length }}개</span>
        </div>
        <div class="personalization-line">
          <span class="companion-chip">{{ difficultyChipLabel }}</span>
        </div>
        <div class="course-list">
          <MountainCard
            v-for="(mountain, index) in recommendedMountains"
            :key="mountain.id"
            :mountain="mountain"
            :rank="index + 1"
            :is-selected="selectedMountain?.id === mountain.id"
            @select="selectMountain"
          />
        </div>
      </section>

      <!-- 대체 산 -->
      <section v-if="!loading && alternativeMountains.length" class="panel subtle-panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Alternative</p><h2>조건 완화 시 고려 가능</h2></div>
        </div>
        <button
          v-for="m in alternativeMountains" :key="m.id"
          class="alternative-row" type="button" @click="selectMountain(m)"
        >
          <span>
            <strong>{{ m.name }}</strong>
            <small>{{ m.region }} · 해발 {{ m.elevation_m }}m</small>
          </span>
          <span :class="['safety-badge', m.safety_class]">{{ m.safety_label }}</span>
        </button>
      </section>

    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  agentSummary, guideError, loading,
  loadMountains, publicMountains, recommendedMountains, alternativeMountains,
  selectedMountain, submitMountainRecommendation, resultState,
  profile, minDepartureDate, maxDepartureDate,
  location, gpsStatus, gpsError, detectGPS, loadWeather, weatherData,
  customStartLocation,
} from '../composables/useGuide.js';
import { communitySearch, communityCategory } from '../composables/useCommunity.js';
import { fetchDisasterZones, fetchSafetyAdvice } from '../api.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';
import MountainCard from '../components/MountainCard.vue';
import { addMinutes, formatTimeForInput } from '../utils/dateHelpers.js';

const router = useRouter();
const overviewMapEl = ref(null);
const selectedDisasterZones = ref([]);
const { renderOverviewMap, focusOverviewCourse } = useLeafletMap();

const safetyAdviceText = ref('');
const safetyAdviceLoading = ref(false);

// 출발지 직접 지정
const useCustomStart = ref(false);
const startQuery = ref('');
const startSearching = ref(false);
const startResults = ref([]);
const startError = ref('');

watch(useCustomStart, (v) => {
  if (!v) {
    customStartLocation.value = null;
    startResults.value = [];
    startError.value = '';
  }
});

async function searchStartLocation() {
  const q = startQuery.value.trim();
  if (!q) return;
  startSearching.value = true;
  startError.value = '';
  startResults.value = [];
  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=4&countrycodes=kr&accept-language=ko`;
    const res = await fetch(url, { headers: { 'Accept-Language': 'ko' } });
    const json = await res.json();
    if (!json.length) {
      startError.value = '검색 결과가 없습니다. 더 구체적인 지명을 입력해 보세요.';
      return;
    }
    startResults.value = json.map((item) => {
      const parts = item.display_name.split(',').map((s) => s.trim());
      return {
        place_id: item.place_id,
        lat: parseFloat(item.lat),
        lng: parseFloat(item.lon),
        display_name: item.display_name,
        name: parts[0],
        detail: parts.slice(1, 3).join(', '),
      };
    });
  } catch {
    startError.value = '검색 중 오류가 발생했습니다. 네트워크를 확인해 주세요.';
  } finally {
    startSearching.value = false;
  }
}

function selectStartResult(r) {
  customStartLocation.value = { lat: r.lat, lng: r.lng, name: r.name };
  startResults.value = [];
  startQuery.value = r.name;
}
const safetyAdviceLines = computed(() =>
  safetyAdviceText.value
    ? safetyAdviceText.value.split('\n').map((l) => l.trim()).filter(Boolean)
    : [],
);

const difficultyFilters = [
  { value: 'all',    label: '🏔 전체' },
  { value: 'easy',   label: '🌿 초급' },
  { value: 'medium', label: '🥾 중급' },
  { value: 'hard',   label: '⛰ 고급' },
];

const minDepartureTime = computed(() =>
  profile.departureDate === minDepartureDate
    ? formatTimeForInput(addMinutes(new Date(), 5))
    : undefined,
);

const difficultyChipLabel = computed(() => {
  const map = { all: '🏔 전체 난이도 기준', easy: '🌿 초급 기준', medium: '🥾 중급 기준', hard: '⛰ 고급 기준' };
  return map[profile.difficultyFilter] || '난이도 기준';
});

const dailyTip = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '이른 새벽 산행은 일출 후 시작하세요. 저체온과 시야 확보가 중요합니다.';
  if (h < 10) return '오전 이른 출발이 가장 안전합니다. 일몰 전 여유 있는 하산을 꼭 지켜주세요.';
  if (h < 14) return '한낮 산행 시 충분한 수분 보충과 그늘 휴식을 챙기세요.';
  if (h < 17) return '오후 출발 시 일몰 시간을 반드시 확인하세요.';
  return '일몰이 가까운 시간입니다. 오늘 산행은 내일 아침으로 연기를 권장합니다.';
});


const gpsBtnTitle = computed(() => {
  if (gpsStatus.value === 'loading') return '위치 감지 중...';
  if (gpsStatus.value === 'success') return '위치 감지 완료';
  if (gpsStatus.value === 'error') return '위치 감지 실패 — 다시 시도';
  return '내 위치 자동 감지';
});

function crowdingLabel(c) {
  if (c < 0.4) return '한산';
  if (c < 0.65) return '보통';
  return '혼잡';
}

// 지도에 표시할 산 목록 — 추천 후 safety 정보 반영
const mapMountains = computed(() => {
  if (!recommendedMountains.value.length && !alternativeMountains.value.length) {
    return publicMountains.value;
  }
  const scored = new Map(
    [...recommendedMountains.value, ...alternativeMountains.value].map((m) => [m.id, m])
  );
  return publicMountains.value.map((m) => {
    const s = scored.get(m.id);
    return s ? { ...m, ...s } : { ...m, _muted: true };
  });
});

function refreshOverviewMap() {
  if (!overviewMapEl.value) return;
  renderOverviewMap(
    overviewMapEl.value,
    mapMountains.value,
    selectedMountain.value?.id,
    selectMountain,
  );
}

async function selectMountain(mountain) {
  selectedMountain.value = mountain;
  safetyAdviceText.value = '';
  if (mountain?.lat && mountain?.lng) loadWeather(mountain.lat, mountain.lng);
  await nextTick();
  focusOverviewCourse(mountain);
  refreshOverviewMap();

  selectedDisasterZones.value = [];
  try {
    const data = await fetchDisasterZones(mountain.name);
    selectedDisasterZones.value = data.zones || [];
  } catch {}

  // AI 맞춤 안전 조언 비동기 로드
  loadSafetyAdvice(mountain);
}

async function loadSafetyAdvice(mountain) {
  safetyAdviceLoading.value = true;
  try {
    const data = await fetchSafetyAdvice({
      mountain,
      weather: weatherData.value || {},
      profile: {
        departureTime: profile.departureTime || '',
        desiredHikingMinutes: profile.desiredHikingMinutes || 120,
        companion: profile.companion || '',
      },
      sunTimes: null,
    });
    safetyAdviceText.value = data.advice || '';
  } catch {
    safetyAdviceText.value = '';
  } finally {
    safetyAdviceLoading.value = false;
  }
}

async function handleSubmit() {
  await submitMountainRecommendation();
  await nextTick();
  refreshOverviewMap();
  if (selectedMountain.value) focusOverviewCourse(selectedMountain.value);
}

async function handleGPS() {
  await detectGPS();
  loadWeather();
}

function goToCommunity(mountainName) {
  communitySearch.value = mountainName;
  communityCategory.value = '';
  router.push('/community');
}

function ensureFutureDepartureTime() {
  if (profile.departureDate !== minDepartureDate) return;
  const minimum = minDepartureTime.value;
  if (minimum && (!profile.departureTime || profile.departureTime < minimum)) {
    profile.departureTime = minimum;
  }
}

watch(mapMountains, () => refreshOverviewMap());
watch(selectedMountain, () => refreshOverviewMap());
watch(() => [profile.departureDate, profile.departureTime], () => ensureFutureDepartureTime());

onMounted(async () => {
  await loadMountains();
  loadWeather();
  await nextTick();
  refreshOverviewMap();
});
</script>
