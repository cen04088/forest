<template>
  <main class="guardian-shell">
    <SharedSidebar />

    <div class="guardian-dashboard">

    <!-- 헤더 (고정 높이) -->
    <header class="guardian-header">
      <button class="guardian-back-btn" type="button" @click="$router.push('/')">← 나가기</button>
      <img src="/logo.png" alt="올라" class="guardian-logo-img" />
      <span :class="['guardian-status-chip', displayStatusClass]">{{ displayStatusLabel }}</span>
    </header>

    <!-- 위치 미수신 / 시뮬레이션 경고 배너 -->
    <div v-if="showStaleWarning" class="guardian-stale-banner" role="alert">
      <span class="stale-icon">🚨</span>
      <div class="stale-body">
        <strong>{{ simActive ? '[시뮬레이션] ' : '' }}위치 업데이트가 {{ staleMinutes }}분째 없습니다</strong>
        <p>GPS 신호가 끊겼거나 배터리 부족일 수 있습니다. 직접 연락해 보세요.</p>
      </div>
      <a href="tel:119" class="stale-119">📞 119</a>
    </div>

    <!-- 맵 영역: Leaflet 컨테이너(항상 빈 div) + 오버레이를 형제로 분리 -->
    <div class="guardian-map-wrap">
      <!-- Leaflet은 이 div 안에서만 동작, 자식 없이 항상 깨끗하게 유지 -->
      <div ref="guardianMapEl" class="guardian-map-leaflet" aria-label="산행자 현재 위치 지도"></div>
      <div class="guardian-map-tools" aria-hidden="true">
        <span>+</span>
        <span>−</span>
        <span>⌖</span>
      </div>
      <!-- 세션 없을 때 오버레이 (Leaflet 컨테이너와 형제 관계) -->
      <div v-if="loading && !displaySession" class="guardian-map-overlay guardian-map-loading">
        <div class="guardian-loading-spinner"></div>
        <p>위치 정보를 불러오는 중…</p>
      </div>
      <div v-else-if="!loading && !displaySession" class="guardian-map-overlay guardian-map-empty">
        <p class="guardian-empty-msg">세이프 링크를 찾을 수 없습니다.<br>산행자에게 링크를 다시 받으세요.</p>
      </div>
    </div>

    <!-- 하단 정보 시트 -->
    <section class="guardian-sheet">

      <!-- 시뮬레이션 진행 바 -->
      <div v-if="simActive" class="sim-progress-bar">
        <div class="sim-progress-fill" :style="{ width: simProgressPct + '%' }"></div>
      </div>

      <div class="guardian-info-card" v-if="displaySession">
        <div class="guardian-card-title">
          <span class="guardian-card-icon">📍</span>
          <strong>현재 위치 정보</strong>
        </div>

        <div class="gbs-info-row">
          <div class="gbs-text">
            <h2 class="gbs-course">{{ displayLocationText }}</h2>
            <p class="gbs-mountain">위치 정확도 10m · 마지막 업데이트 {{ displayLastUpdate }}</p>
          </div>
          <button v-if="session && !simActive" class="guardian-refresh-btn" type="button" @click="manualRefresh">
            위치 새로고침
          </button>
          <span :class="['safety-badge', displayStatusClass]">{{ displayStatusLabel }}</span>
        </div>
      </div>

      <div class="gbs-meta" v-if="displaySession">
        <span>📍 마지막 수신 <strong>{{ displayLastUpdate }}</strong></span>
        <span v-if="displaySession.trail?.length">🗺️ {{ displaySession.trail.length }}회 기록</span>
        <span v-if="displaySession.duration_min">🕐 {{ displaySession.duration_min }}분 코스</span>
      </div>

      <!-- 자동 새로고침 상태 (실제 세션) -->
      <div v-if="!simActive && session" class="guardian-refresh-status">
        <span class="refresh-dot"></span>
        <span>{{ lastRefreshedLabel }}</span>
        <span class="refresh-next">· {{ nextRefreshLabel }}</span>
      </div>

      <!-- 시뮬레이션 단계 표시 -->
      <div v-if="simActive" :class="['guardian-sim-status', simIsStale ? 'sim-status-alert' : '']">
        <span :class="simIsStale ? 'sim-dot-red' : 'sim-dot'"></span>
        <span v-if="simStep < SIM_WAYPOINTS.length">이동 중 — {{ currentWaypointName }}</span>
        <span v-else-if="!simIsStale">하루재 도착 — 대기 중 ({{ Math.floor(simStuckSecs / 60) }}분 경과)</span>
        <span v-else>⚠️ {{ Math.floor(simStuckSecs / 60) }}분째 위치 미갱신</span>
      </div>

      <!-- 시뮬레이션 시작 버튼 (시뮬레이션 꺼진 상태) -->
      <div v-if="!simActive" class="gbs-sim-row">
        <button class="sim-start-btn" type="button" @click="startSim">
          🎬 북한산 산행 시뮬레이션
        </button>
        <p class="sim-start-desc">보호자 화면 동작을 체험해보세요</p>
      </div>

      <!-- 액션 버튼 -->
      <h3 class="guardian-emergency-title">긴급 상황</h3>
      <div class="gbs-actions">
        <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
        <button v-if="simActive" class="outline-btn danger" type="button" @click="stopSim">🔴 종료</button>
        <button v-else-if="session" class="outline-btn" type="button" @click="manualRefresh">새로고침</button>
      </div>

    </section>
    </div>

    <!-- 60분 경고 팝업 -->
    <Transition name="modal-fade">
      <div v-if="simEndModal" class="sim-end-overlay" role="dialog" aria-modal="true" @click.self="dismissSimEnd">
        <div class="sim-end-modal">
          <button class="sem-close-btn" type="button" @click="dismissSimEnd" aria-label="닫기">✕</button>
          <div class="sem-icon">⚠️</div>
          <h3 class="sem-title">위치 미갱신 60분</h3>
          <p class="sem-body">
            산행자의 위치가 <strong>60분째 갱신되지 않았습니다.</strong><br>
            직접 연락하거나 119에 신고하세요.
          </p>
          <div class="sem-actions">
            <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
            <button class="outline-btn" type="button" @click="dismissSimEnd">시뮬레이션 종료</button>
          </div>
        </div>
      </div>
    </Transition>

  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import SharedSidebar from '../components/SharedSidebar.vue';
import { useGuardianView } from '../composables/useSafeLink.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';

const route = useRoute();
const router = useRouter();
const sessionId = route.params.sessionId;

const guardianMapEl = ref(null);
const {
  session, loading,
  lastUpdateLabel, statusLabel, statusClass,
  lastRefreshedLabel, nextRefreshLabel,
  locationStaleMins, isLocationStale,
  startPolling, stopPolling, manualRefresh,
} = useGuardianView(sessionId);
const { renderGuardianMap } = useLeafletMap();

// ── 북한산 시뮬레이션 ─────────────────────────────────────────────────────────
// 중간 지점(하루재)까지만 이동 후 정지 시뮬레이션 — 도선사부터 시작
const SIM_WAYPOINTS = [
  { lat: 37.6624, lng: 127.0107, name: '🚩 도선사 (출발)' },
  { lat: 37.6612, lng: 127.0080, name: '📍 계곡 구간' },
  { lat: 37.6601, lng: 127.0061, name: '📍 지장암 갈림길' },
  { lat: 37.6590, lng: 127.0040, name: '📍 능선 합류' },
  { lat: 37.6581, lng: 127.0019, name: '⛺ 하루재 (중간 지점)' },
];

const simActive     = ref(false);
const simStep       = ref(0);
const simStuckTicks = ref(0);
const simTrail      = ref([]);
const simEndModal   = ref(false); // 60분 경고 팝업
let _simInterval    = null;

const currentWaypointName = computed(() => {
  if (simStep.value === 0) return '';
  return SIM_WAYPOINTS[simStep.value - 1]?.name ?? '';
});

const simProgressPct = computed(() => {
  const total = SIM_WAYPOINTS.length + 4;
  return Math.min(100, Math.round(((simStep.value + simStuckTicks.value) / total) * 100));
});

// 틱당 5분(300초) 시뮬레이션 → 6틱 = 30분 경과 → 경고
const SIM_SECS_PER_STUCK_TICK = 300;
const SIM_STALE_THRESHOLD_SECS = 1800; // 30분

function _buildSimSession(trail, stuckSecs = 0) {
  const last = trail[trail.length - 1] ?? SIM_WAYPOINTS[0];
  const now = Math.floor(Date.now() / 1000);
  return {
    course_name: '우이동 → 하루재',
    mountain: '북한산',
    duration_min: 120,
    safety_decision: stuckSecs >= SIM_STALE_THRESHOLD_SECS ? 'caution' : 'ok',
    status: 'active',
    current_lat: last.lat,
    current_lng: last.lng,
    location_ts: stuckSecs > 0 ? now - stuckSecs : now,
    trail: trail.map((p, i) => ({
      lat: p.lat,
      lng: p.lng,
      recorded_at: now - (trail.length - 1 - i) * 300,
    })),
    risk_factors: [],
  };
}

function startSim() {
  simActive.value = true;
  simStep.value = 0;
  simStuckTicks.value = 0;
  simEndModal.value = false;
  simTrail.value = [];
  _doSimTick();
  _simInterval = setInterval(_doSimTick, 1600);
}

function _doSimTick() {
  if (simStep.value < SIM_WAYPOINTS.length) {
    simTrail.value = [...simTrail.value, SIM_WAYPOINTS[simStep.value]];
    simStep.value++;
  } else {
    simStuckTicks.value++;
    // 60분(12틱) 도달 시 경고 팝업 표시 후 종료
    if (simStuckTicks.value * SIM_SECS_PER_STUCK_TICK >= 3600) {
      const stuckSecs = simStuckTicks.value * SIM_SECS_PER_STUCK_TICK;
      const sess = _buildSimSession(simTrail.value, stuckSecs);
      if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, sess);
      clearInterval(_simInterval);
      _simInterval = null;
      simEndModal.value = true;
      return;
    }
  }
  const stuckSecs = simStuckTicks.value * SIM_SECS_PER_STUCK_TICK;
  const sess = _buildSimSession(simTrail.value, stuckSecs);
  if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, sess);
}

function stopSim() {
  clearInterval(_simInterval);
  _simInterval = null;
  simActive.value = false;
  simStep.value = 0;
  simStuckTicks.value = 0;
  simTrail.value = [];
  simEndModal.value = false;
  if (session.value && guardianMapEl.value) {
    nextTick(() => renderGuardianMap(guardianMapEl.value, session.value));
  }
}

// 팝업 확인 버튼 → 시뮬레이션 완전 종료
function dismissSimEnd() {
  simEndModal.value = false;
  simActive.value = false;
  simStep.value = 0;
  simStuckTicks.value = 0;
  simTrail.value = [];
  if (session.value && guardianMapEl.value) {
    nextTick(() => renderGuardianMap(guardianMapEl.value, session.value));
  }
}

// ── 표시용 합성값 ─────────────────────────────────────────────────────────────
const displaySession = computed(() => {
  if (simActive.value) return _buildSimSession(simTrail.value, simStuckTicks.value * 180);
  return session.value;
});

const simStuckSecs = computed(() => simStuckTicks.value * SIM_SECS_PER_STUCK_TICK);
const simIsStale   = computed(() => simStuckSecs.value >= SIM_STALE_THRESHOLD_SECS);

const displayStatusClass = computed(() => {
  if (!displaySession.value) return 'gray';
  if (simActive.value) return simIsStale.value ? 'red' : 'green';
  return statusClass.value;
});

const displayStatusLabel = computed(() => {
  if (!displaySession.value) return '연결 중';
  if (simActive.value) {
    if (simIsStale.value) return '위치 미갱신';
    if (simStep.value >= SIM_WAYPOINTS.length) return '하루재 대기 중';
    return '이동 중';
  }
  return statusLabel.value;
});

const displayLastUpdate = computed(() => {
  if (simActive.value) {
    const secs = simStuckSecs.value;
    if (secs === 0) return '방금';
    return `${Math.floor(secs / 60)}분 전`;
  }
  return lastUpdateLabel.value;
});

const displayLocationText = computed(() => {
  const s = displaySession.value;
  if (!s) return '위치 정보 없음';
  if (s.current_lat && s.current_lng) {
    return `현재 좌표 ${Number(s.current_lat).toFixed(5)}, ${Number(s.current_lng).toFixed(5)}`;
  }
  return s.course_name || s.mountain || '현재 위치 확인 중';
});

const showStaleWarning = computed(() =>
  simActive.value
    ? simIsStale.value
    : isLocationStale.value && session.value?.status !== 'ended'
);

const staleMinutes = computed(() =>
  simActive.value
    ? Math.floor(simStuckSecs.value / 60)
    : locationStaleMins.value
);

// ── 실제 세션 맵 갱신 ─────────────────────────────────────────────────────────
watch(session, async (val) => {
  if (!val || simActive.value) return;
  await nextTick();
  if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, val);
});

// ── 브라우저 알림 (실제 세션) ────────────────────────────────────────────────
let _notifiedStale = false;
watch(isLocationStale, async (stale) => {
  if (simActive.value || !stale || _notifiedStale) return;
  _notifiedStale = true;
  if ('Notification' in window && Notification.permission !== 'denied') {
    const perm = Notification.permission === 'default'
      ? await Notification.requestPermission()
      : Notification.permission;
    if (perm === 'granted') {
      new Notification('올라 — 위치 업데이트 없음', {
        body: `산행자 위치가 ${locationStaleMins.value}분째 갱신되지 않았습니다.`,
        icon: '/logo.png',
      });
    }
  }
});
watch(() => session.value?.location_ts, () => { _notifiedStale = false; });

onMounted(async () => {
  startPolling();
  await nextTick();
  // 마운트 시점에 이미 세션이 있으면 즉시 렌더
  if (session.value && guardianMapEl.value) {
    renderGuardianMap(guardianMapEl.value, session.value);
  }
});
onUnmounted(() => { stopPolling(); stopSim(); });
</script>
