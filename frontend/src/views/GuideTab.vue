<template>
  <section class="screen-stack guide-layout">

    <!-- ── 왼쪽: 입력 폼 + 날씨 ── -->
    <div class="guide-left">

      <section class="panel planner-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Course</p>
            <h2>약자 동반 안전코스추천</h2>
          </div>
          <span class="mini-status">{{ loading ? '분석 중' : '준비됨' }}</span>
        </div>

        <form class="planner" @submit.prevent="submit">
          <div class="field wide-field gps-field">
            <span>산 선택</span>
            <div class="gps-row">
              <select v-model="profile.mountainName" @change="handleMountainChange">
                <option v-for="m in mountainOptions" :key="m.name" :value="m.name">
                  {{ m.name }} · {{ m.count }}개 코스
                </option>
              </select>
              <button
                class="gps-btn" type="button"
                :class="gpsStatus" :disabled="gpsStatus === 'loading'"
                :title="gpsBtnTitle" @click="handleGPS"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
                  <path v-if="gpsStatus === 'loading'" d="M12 6a6 6 0 0 1 6 6" class="gps-spin" />
                </svg>
              </button>
            </div>
            <p v-if="gpsStatus === 'success'" class="gps-message success">📍 현재 위치 감지 완료 — 가장 가까운 코스를 우선합니다</p>
            <p v-if="gpsStatus === 'error'" class="gps-message error">⚠️ {{ gpsError }}</p>
          </div>

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
            </select>
          </label>
          <div class="field wide-field">
            <span>동반자 유형</span>
            <div class="segment-group wrap">
              <label v-for="type in companionTypes" :key="type.value" class="segment-btn">
                <input type="radio" v-model="profile.companion" :value="type.value" name="companion_form" @change="submit" />
                <span>{{ type.label }}</span>
              </label>
            </div>
          </div>
          <div class="field wide-field">
            <span>산행 목적</span>
            <div class="segment-group wrap">
              <label v-for="p in purposeTypes" :key="p.value" class="segment-btn">
                <input type="radio" v-model="profile.purpose" :value="p.value" name="purpose_form" />
                <span>{{ p.label }}</span>
              </label>
            </div>
          </div>
          <div class="field wide-field">
            <span>이동 수단</span>
            <div class="segment-group">
              <label class="segment-btn">
                <input type="radio" v-model="profile.transport" value="public" name="transport_form" />
                <span>🚌 대중교통</span>
              </label>
              <label class="segment-btn">
                <input type="radio" v-model="profile.transport" value="car" name="transport_form" />
                <span>🚗 차량</span>
              </label>
            </div>
          </div>
          <button class="primary-btn wide-field" :class="{ loading }" type="submit" :disabled="loading">
            {{ loading ? '안전 등급 계산 중…' : '동반자 기준 안전코스 찾기' }}
          </button>
        </form>
      </section>

      <!-- 실시간 날씨 조건 -->
      <section v-if="weatherData" class="panel conditions-card">
        <div class="conditions-header">
          <div>
            <p class="eyebrow">오늘의 조건</p>
            <h2>실시간 산행 환경</h2>
          </div>
          <span :class="weatherData?.source === 'mock' ? 'live-badge mock-badge' : 'live-badge'">
            {{ weatherData?.source === 'mock' ? '추정 데이터' : '● LIVE' }}
          </span>
        </div>

        <div class="weather-safety-gauge">
          <div class="gauge-label-row">
            <span class="gauge-label">기상 안전도</span>
            <span :class="['gauge-badge', weatherSafetyClass]">{{ weatherSafetyLabel }}</span>
          </div>
          <div class="gauge-track">
            <div class="gauge-fill" :class="weatherSafetyClass" :style="{ width: weatherSafetyPct + '%' }"></div>
          </div>
          <span class="gauge-reason">{{ weatherSafetyReason }}</span>
        </div>

        <div class="conditions-grid">
          <div class="condition-item">
            <span class="condition-icon">{{ weatherIcon }}</span>
            <span class="condition-label">날씨</span>
            <strong class="condition-value">{{ weatherLabel }}<br/>{{ weatherData.temperature_c }}°C</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">🌅</span>
            <span class="condition-label">오늘 일몰</span>
            <strong class="condition-value">{{ weatherData.sunset || '확인 중' }}</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💧</span>
            <span class="condition-label">강수량</span>
            <strong :class="['condition-value', weatherData.rainfall_mm > 0 ? 'warning' : '']">{{ weatherData.rainfall_mm ?? 0 }}mm</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💨</span>
            <span class="condition-label">풍속</span>
            <strong :class="['condition-value', weatherData.wind_speed_ms >= 5 ? 'warning' : '']">{{ weatherData.wind_speed_ms }}m/s</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💦</span>
            <span class="condition-label">습도</span>
            <strong class="condition-value">{{ weatherData.humidity_pct ?? '-' }}%</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">🔥</span>
            <span class="condition-label">산불 위험</span>
            <strong :class="['condition-value', wildfireClass]">{{ wildfireLabel }}</strong>
          </div>
        </div>
      </section>
    </div>

    <!-- ── 오른쪽: 결과 목록 ── -->
    <div class="guide-right">

      <!-- 로딩 스켈레톤 -->
      <section v-if="loading" class="panel">
        <div class="skeleton-card"><div class="skeleton-line short"></div><div class="skeleton-line full"></div><div class="skeleton-line medium"></div></div>
        <div class="skeleton-card"><div class="skeleton-line short"></div><div class="skeleton-line full"></div><div class="skeleton-line medium"></div></div>
      </section>

      <!-- 준비 화면 -->
      <div v-if="resultState === 'idle' && !loading" class="idle-screen">
        <div class="idle-quick-mountains">
          <p class="idle-section-label">⚡ 인기 산 바로 선택</p>
          <div class="mountain-chip-row">
            <button
              v-for="m in quickMountains" :key="m"
              class="mountain-chip" :class="{ active: profile.mountainName === m }"
              type="button" @click="selectQuickMountain(m)"
            >{{ m }}</button>
          </div>
        </div>
        <div class="idle-how">
          <p class="idle-section-label">📋 이용 방법</p>
          <div class="how-steps">
            <div class="how-step"><span class="how-num">1</span><span class="how-text">산 선택<br><small>날씨 자동 로드</small></span></div>
            <div class="how-arrow">→</div>
            <div class="how-step"><span class="how-num">2</span><span class="how-text">조건 입력<br><small>동반자·시간</small></span></div>
            <div class="how-arrow">→</div>
            <div class="how-step"><span class="how-num">3</span><span class="how-text">안전 등급<br><small>추천 코스 확인</small></span></div>
            <div class="how-arrow">→</div>
            <div class="how-step"><span class="how-num">4</span><span class="how-text">보호자 공유<br><small>세이프 링크</small></span></div>
          </div>
        </div>
        <div class="idle-tip"><span class="idle-tip-icon">💡</span><span class="idle-tip-text">{{ dailyTip }}</span></div>
        <div class="idle-sources">
          <p class="idle-section-label">📡 연동 데이터</p>
          <div class="source-chips">
            <span class="source-chip">기상청 초단기실황</span>
            <span class="source-chip">한국천문연구원 일몰</span>
            <span class="source-chip">산림청 산불예보</span>
            <span class="source-chip">국립공원 탐방로</span>
            <span class="source-chip">재난위험지구</span>
            <span class="source-chip">브이월드 등산로</span>
          </div>
        </div>
      </div>

      <!-- 비추천 공지 -->
      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에서 권장할 코스가 없습니다</h3>
        <p>{{ agentSummary }}</p>
        <div class="chip-row">
          <button v-for="action in alternativeActions" :key="action" type="button">{{ action }}</button>
        </div>
      </article>

      <!-- AI 안전 브리핑 카드 (결과 최상단) -->
      <div v-if="!loading && agentSummary && resultState === 'has_recommendations'" class="briefing-card">
        <div class="briefing-icon">🤖</div>
        <div class="briefing-body">
          <p class="briefing-eyebrow">AI 안전 브리핑</p>
          <p class="briefing-text">{{ agentSummary }}</p>
        </div>
      </div>

      <!-- 추천 코스 목록 -->
      <section v-if="!loading && recommendations.length" class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Recommended</p><h2>추천 코스</h2></div>
          <span class="mini-status">{{ displayPrimaryCourses.length }}개</span>
        </div>
        <div class="personalization-line">
          <span class="companion-chip">{{ companionChipLabel }}</span>
          <span class="personalization-dots">
            <span>날씨·일몰·동반자 조건 반영</span>
            <span v-if="weatherData">·</span>
            <span v-if="weatherData">{{ weatherLabel }} {{ weatherData.temperature_c }}°C</span>
          </span>
        </div>
        <p v-if="!strictMountainMatch" class="notice">선택한 산과 정확히 일치하는 후보가 부족해 주변 안전 후보를 함께 보여줍니다.</p>
        <div class="course-list">
          <CourseCard
            v-for="(course, index) in displayPrimaryCourses"
            :key="course.id" :course="course" :rank="index + 1"
            :is-selected="selectedCourse?.id === course.id"
            :is-favorite="favorites.some((f) => f.course_id === course.id)"
            @select="selectCourse" @toggle-favorite="handleToggleFavorite"
          />
        </div>
      </section>

      <!-- 대체 코스 -->
      <section v-if="!loading && nearbyAlternativeCourses.length" class="panel subtle-panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Alternative</p><h2>주변 대체 코스</h2></div>
          <span class="mini-status">{{ nearbyAlternativeCourses.length }}개</span>
        </div>
        <button
          v-for="course in nearbyAlternativeCourses" :key="course.id"
          class="alternative-row" type="button" @click="selectCourse(course)"
        >
          <span>
            <strong>{{ course.name }}</strong>
            <small>{{ course.mountain }} · {{ course.distance_km }}km · {{ durationLabel(course.duration_min) }}</small>
          </span>
          <span :class="['safety-badge', safetyClass(course)]">{{ course.safety_label || fallbackSafetyLabel(course) }}</span>
        </button>
      </section>

      <!-- 코스 상세 -->
      <section v-if="selectedCourse" class="panel detail-panel">
        <div class="section-title">
          <div><p class="eyebrow">Course Detail</p><h2>{{ selectedCourse.name }}</h2></div>
          <router-link to="/safe-link" class="outline-btn">공유 카드</router-link>
        </div>
        <div class="detail-map">
          <div ref="detailMapEl" class="kakao-map" aria-label="선택 코스 카카오 지도"></div>
          <div class="legend">
            <span><i class="line green-line"></i>안전</span>
            <span><i class="line yellow-line"></i>주의</span>
            <span><i class="line red-line"></i>위험</span>
          </div>
        </div>
        <div v-if="mapStatus" class="map-status-msg"><span class="info-icon">ℹ️</span><span>{{ mapStatus }}</span></div>
        <div class="route-summary">
          <div><strong>코스 단계</strong></div>
          <span class="mini-status">{{ courseTimelineItems.length }}단계</span>
        </div>
        <ol class="route-timeline" aria-label="코스 진행 단계">
          <li v-for="item in courseTimelineItems" :key="item.label + item.value">
            <span>{{ item.label }}</span><strong>{{ item.value }}</strong>
          </li>
        </ol>
        <p class="detail-copy">{{ selectedCourse.agent_briefing }}</p>
        <div v-if="disasterZones.length" class="disaster-zone-panel">
          <p class="disaster-zone-title">⚠️ 인근 재난위험지구 {{ disasterZones.length }}개</p>
          <ul class="disaster-zone-list">
            <li v-for="zone in disasterZones.slice(0, 4)" :key="zone.id">
              <strong>{{ zone.district || zone.location }}</strong>
              <span v-if="zone.risk_factor"> · {{ zone.risk_factor }}</span>
            </li>
          </ul>
        </div>

        <!-- 커뮤니티 안전 제보 -->
        <div v-if="safetyReports.length" class="safety-report-panel">
          <p class="safety-report-title">📢 커뮤니티 안전 제보 {{ safetyReports.length }}건</p>
          <ul class="safety-report-list">
            <li v-for="r in safetyReports" :key="r.id">
              <strong>{{ r.title }}</strong>
              <span class="report-meta">{{ r.author }} · {{ formatReportTime(r.created_at) }}</span>
              <p class="report-content">{{ r.content }}</p>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import {
  agentSummary, alternativeActions, disasterZones, displayPrimaryCourses,
  gpsError, gpsStatus, guideError, loading, loadCourses, loadWeather,
  maxDepartureDate, minDepartureDate, mountainOptions, nearbyAlternativeCourses,
  profile, recommendations, resultState, selectedCourse, strictMountainMatch,
  submit, syncLocationToMountain, weatherData, location, detectGPS,
} from '../composables/useGuide.js';
import { fetchSafetyReports } from '../api.js';
import { favorites, toggleFavorite } from '../composables/useUserData.js';
import { useKakaoMap } from '../composables/useKakaoMap.js';
import { safetyClass, fallbackSafetyLabel, durationLabel } from '../utils/courseHelpers.js';
import CourseCard from '../components/CourseCard.vue';
import { addMinutes, formatTimeForInput } from '../utils/dateHelpers.js';

const detailMapEl = ref(null);
const safetyReports = ref([]);
const { mapStatus, renderDetailMap } = useKakaoMap();

const companionTypes = [
  { value: 'vulnerable', label: '어린이·노약자 동반' },
  { value: 'family', label: '가족 동반' },
  { value: 'solo', label: '혼자 산행' },
];
const purposeTypes = [
  { value: 'balanced', label: '🎯 균형' },
  { value: 'healing', label: '🌿 힐링' },
  { value: 'workout', label: '💪 운동' },
  { value: 'view', label: '🏔️ 전망' },
];
const quickMountains = ['관악산', '북한산', '청계산', '도봉산', '남산', '수락산', '설악산', '지리산'];

const minDepartureTime = computed(() =>
  profile.departureDate === minDepartureDate
    ? formatTimeForInput(addMinutes(new Date(), 5))
    : undefined,
);

const companionChipLabel = computed(() => {
  const map = { vulnerable: '👨‍👧 어린이·노약자 동반 기준', family: '👨‍👩‍👦 가족 동반 기준', solo: '🧍 개인 산행 기준' };
  return map[profile.companion] || '동반자 기준';
});

const dailyTip = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '이른 새벽 산행은 일출 후 시작하세요. 저체온과 시야 확보가 중요합니다.';
  if (h < 10) return '오전 이른 출발이 가장 안전합니다. 일몰 전 여유 있는 하산을 꼭 지켜주세요.';
  if (h < 14) return '한낮 산행 시 충분한 수분 보충과 그늘 휴식을 챙기세요. 자외선 차단도 필수입니다.';
  if (h < 17) return '오후 출발 시 일몰 시간을 반드시 확인하세요.';
  return '일몰이 가까운 시간입니다. 오늘 산행은 내일 아침으로 연기하거나 짧은 산책 코스를 선택하세요.';
});

const weatherIcon = computed(() => {
  const w = weatherData.value;
  if (!w) return '🌤️';
  if (w.rainfall_mm >= 10) return '🌧️';
  if (w.rainfall_mm > 0) return '🌦️';
  if (w.wind_speed_ms >= 8) return '💨';
  return '☀️';
});
const weatherLabel = computed(() => {
  const w = weatherData.value;
  if (!w) return '확인 중';
  if (w.rainfall_mm >= 10) return '비';
  if (w.rainfall_mm > 0) return '흐리고 비';
  if (w.wind_speed_ms >= 8) return '강풍';
  return '맑음';
});
const wildfireClass = computed(() => ({ low: 'safe', medium: 'warning', high: 'danger', very_high: 'danger' }[weatherData.value?.wildfire_risk || 'low'] || 'safe'));
const wildfireLabel = computed(() => ({ low: '낮음', medium: '중간', high: '높음', very_high: '매우 높음' }[weatherData.value?.wildfire_risk] || '낮음'));
const _weatherSafetyScore = computed(() => {
  const w = weatherData.value;
  if (!w) return 100;
  let score = 100;
  const rainfall = parseFloat(w.rainfall_mm ?? 0);
  const wind = parseFloat(w.wind_speed_ms ?? 0);
  const temp = parseFloat(w.temperature_c ?? 15);
  if (rainfall >= 10) score -= 45; else if (rainfall > 0) score -= 20;
  if (wind >= 8) score -= 30; else if (wind >= 5) score -= 15;
  if (temp <= 0 || temp >= 32) score -= 20;
  if (rainfall >= 5 && wind >= 5) score -= 20;
  if (temp <= 2 && rainfall > 0) score -= 15;
  if (temp >= 30 && wind < 2) score -= 10;
  return Math.max(score, 0);
});
// 게이지 바 너비용 (내부 계산에만 사용, 숫자는 노출 안 함)
const weatherSafetyPct = computed(() => _weatherSafetyScore.value);
const weatherSafetyLabel = computed(() => {
  const s = _weatherSafetyScore.value;
  if (s >= 80) return '산행 적합';
  if (s >= 55) return '주의 필요';
  return '산행 부적합';
});
const weatherSafetyClass = computed(() => {
  const s = _weatherSafetyScore.value;
  if (s >= 80) return 'safe';
  if (s >= 55) return 'caution';
  return 'danger';
});
const weatherSafetyReason = computed(() => {
  const w = weatherData.value;
  if (!w) return '';
  const rainfall = parseFloat(w.rainfall_mm ?? 0);
  const wind = parseFloat(w.wind_speed_ms ?? 0);
  const temp = parseFloat(w.temperature_c ?? 15);
  if (rainfall >= 10) return '강수량이 높아 미끄럼 위험이 큽니다';
  if (rainfall >= 5 && wind >= 5) return '비와 강풍이 동시에 있어 주의가 필요합니다';
  if (wind >= 8) return '강풍으로 능선부 보행에 주의가 필요합니다';
  if (temp <= 0) return '기온이 영하여 결빙 위험이 있습니다';
  if (temp >= 32) return '폭염으로 열사병 위험이 있습니다';
  if (rainfall > 0) return '약한 비로 노면이 미끄러울 수 있습니다';
  if (wind >= 5) return '풍속이 다소 높아 노출 구간 주의가 필요합니다';
  return '기상 조건이 산행에 적합합니다';
});

const courseTimelineItems = computed(() => {
  const highlights = selectedCourse.value?.highlights || [];
  const parsed = highlights.map((item) => {
    const text = String(item || '').trim();
    if (!text) return null;
    const [label, ...rest] = text.split(':');
    if (rest.length) return { label: label.trim(), value: rest.join(':').trim() };
    return { label: '정보', value: text };
  }).filter(Boolean);
  if (parsed.length) return parsed;
  if (!selectedCourse.value) return [];
  return [{ label: '코스', value: selectedCourse.value.name }];
});

const gpsBtnTitle = computed(() => {
  if (gpsStatus.value === 'loading') return '위치 감지 중...';
  if (gpsStatus.value === 'success') return '위치 감지 완료';
  if (gpsStatus.value === 'error') return '위치 감지 실패 — 다시 시도';
  return '내 위치 자동 감지';
});

async function selectCourse(course) {
  selectedCourse.value = course;
  renderMap();
  safetyReports.value = [];
  if (course.mountain) {
    try {
      const data = await fetchSafetyReports(course.mountain);
      safetyReports.value = data.reports || [];
    } catch {}
  }
}

function formatReportTime(isoString) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

async function handleToggleFavorite(course) {
  await toggleFavorite(course);
}

async function handleGPS() {
  const success = await detectGPS();
  if (success) { syncLocationToMountain(); await submit(); }
}

function handleMountainChange() {
  syncLocationToMountain();
  loadWeather();
}

function selectQuickMountain(name) {
  profile.mountainName = name;
  handleMountainChange();
}

function ensureFutureDepartureTime() {
  if (profile.departureDate !== minDepartureDate) return;
  const minimum = minDepartureTime.value;
  if (minimum && (!profile.departureTime || profile.departureTime < minimum)) {
    profile.departureTime = minimum;
  }
}

async function renderMap() {
  await nextTick();
  renderDetailMap(detailMapEl.value, selectedCourse.value, disasterZones.value, location.value);
}

watch(selectedCourse, () => renderMap());
watch(() => [profile.departureDate, profile.departureTime], () => ensureFutureDepartureTime());

onMounted(async () => {
  await loadCourses();
  if (!profile.mountainName && mountainOptions.value.length) {
    profile.mountainName = mountainOptions.value[0].name;
  }
  syncLocationToMountain();
  loadWeather();
});
</script>
