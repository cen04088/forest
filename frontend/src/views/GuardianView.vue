<template>
  <main class="guardian-shell">

    <!-- 헤더 (고정 높이) -->
    <header class="guardian-header">
      <button class="guardian-back-btn" type="button" @click="$router.push('/')">← 나가기</button>
      <img src="/logo.png" alt="올라" class="guardian-logo-img" />
      <span :class="['guardian-status-chip', displayStatusClass]">{{ displayStatusLabel }}</span>
    </header>

    <!-- 위치 미수신 / 시뮬레이션 경고 배너 -->
    <div v-if="showStaleWarning" class="guardian-stale-banner" role="alert">
      <span class="stale-icon">⚠️</span>
      <div class="stale-body">
        <strong>{{ simActive ? '[시뮬레이션] ' : '' }}위치 업데이트가 {{ staleMinutes }}분째 없습니다</strong>
        <p>GPS 신호가 끊겼거나 배터리 부족일 수 있습니다. 직접 연락해 보세요.</p>
      </div>
      <a href="tel:119" class="stale-119">119</a>
    </div>

    <!-- 맵 (flex-grow로 남은 공간 채움) -->
    <div
      v-if="displaySession"
      ref="guardianMapEl"
      class="guardian-map"
      aria-label="산행자 현재 위치 지도"
    ></div>
    <div v-else-if="loading" class="guardian-map guardian-map-loading">
      <div class="guardian-loading-spinner"></div>
      <p>위치 정보를 불러오는 중…</p>
    </div>
    <div v-else class="guardian-map guardian-map-empty">
      <p class="guardian-empty-msg">세이프 링크를 찾을 수 없습니다.<br>산행자에게 링크를 다시 받으세요.</p>
    </div>

    <!-- 하단 정보 시트 -->
    <section class="guardian-sheet">

      <!-- 시뮬레이션 진행 바 -->
      <div v-if="simActive" class="sim-progress-bar">
        <div class="sim-progress-fill" :style="{ width: simProgressPct + '%' }"></div>
      </div>

      <div class="gbs-info-row" v-if="displaySession">
        <div class="gbs-text">
          <h2 class="gbs-course">{{ displaySession.course_name || '경로 정보 없음' }}</h2>
          <p class="gbs-mountain">⛰️ {{ displaySession.mountain || '산 정보 없음' }}</p>
        </div>
        <span :class="['safety-badge', displayStatusClass]">{{ displayStatusLabel }}</span>
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
      <div v-if="simActive" class="guardian-sim-status">
        <span class="sim-dot"></span>
        <span>체크포인트 {{ simStep }}/{{ SIM_WAYPOINTS.length }} — {{ currentWaypointName }}</span>
        <span v-if="simStep >= SIM_WAYPOINTS.length && simStuckTicks > 0" class="sim-stuck-label">⚠️ 정상 대기 중</span>
      </div>

      <!-- 시뮬레이션 시작 버튼 (시뮬레이션 꺼진 상태) -->
      <div v-if="!simActive" class="gbs-sim-row">
        <button class="sim-start-btn" type="button" @click="startSim">
          🎬 북한산 산행 시뮬레이션
        </button>
        <p class="sim-start-desc">보호자 화면 동작을 체험해보세요</p>
      </div>

      <!-- 액션 버튼 -->
      <div class="gbs-actions">
        <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
        <button v-if="simActive" class="outline-btn danger" type="button" @click="stopSim">🔴 종료</button>
        <button v-else-if="session" class="outline-btn" type="button" @click="manualRefresh">새로고침</button>
      </div>

    </section>

  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
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
const SIM_WAYPOINTS = [
  { lat: 37.6647, lng: 127.0162, name: '우이동 탐방지원센터' },
  { lat: 37.6624, lng: 127.0107, name: '도선사' },
  { lat: 37.6601, lng: 127.0061, name: '지장암 갈림길' },
  { lat: 37.6581, lng: 127.0019, name: '하루재' },
  { lat: 37.6572, lng: 126.9975, name: '인수봉 갈림길' },
  { lat: 37.6570, lng: 126.9930, name: '위문 아래' },
  { lat: 37.6575, lng: 126.9888, name: '위문 (백운봉 암문)' },
  { lat: 37.6580, lng: 126.9808, name: '백운대 아래' },
  { lat: 37.6584, lng: 126.9726, name: '백운대 정상 (836m)' },
];

const simActive    = ref(false);
const simStep      = ref(0);
const simStuckTicks = ref(0);
const simTrail     = ref([]);
let _simInterval   = null;

const currentWaypointName = computed(() => {
  if (simStep.value === 0) return '';
  return SIM_WAYPOINTS[simStep.value - 1]?.name ?? '';
});

const simProgressPct = computed(() => {
  const total = SIM_WAYPOINTS.length + 4;
  return Math.min(100, Math.round(((simStep.value + simStuckTicks.value) / total) * 100));
});

function _buildSimSession(trail, stuckSecs = 0) {
  const last = trail[trail.length - 1] ?? SIM_WAYPOINTS[0];
  const now = Math.floor(Date.now() / 1000);
  return {
    course_name: '우이동 → 백운대',
    mountain: '북한산',
    duration_min: 180,
    safety_decision: stuckSecs >= 660 ? 'caution' : 'ok',
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
  simTrail.value = [];
  _doSimTick();
  _simInterval = setInterval(_doSimTick, 1600);
}

async function _doSimTick() {
  if (simStep.value < SIM_WAYPOINTS.length) {
    simTrail.value = [...simTrail.value, SIM_WAYPOINTS[simStep.value]];
    simStep.value++;
  } else {
    simStuckTicks.value++;
    if (simStuckTicks.value >= 8) { stopSim(); return; }
  }
  const stuckSecs = simStuckTicks.value * 180;
  const sess = _buildSimSession(simTrail.value, stuckSecs);
  await nextTick();
  if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, sess);
}

function stopSim() {
  clearInterval(_simInterval);
  _simInterval = null;
  simActive.value = false;
  simStep.value = 0;
  simStuckTicks.value = 0;
  simTrail.value = [];
  // 실제 세션이 있으면 맵 복구
  if (session.value && guardianMapEl.value) {
    nextTick(() => renderGuardianMap(guardianMapEl.value, session.value));
  }
}

// ── 표시용 합성값 ─────────────────────────────────────────────────────────────
const displaySession = computed(() => {
  if (simActive.value) return _buildSimSession(simTrail.value, simStuckTicks.value * 180);
  return session.value;
});

const displayStatusClass = computed(() => {
  if (!displaySession.value) return 'gray';
  if (simActive.value) return simStuckTicks.value * 180 >= 660 ? 'yellow' : 'green';
  return statusClass.value;
});

const displayStatusLabel = computed(() => {
  if (!displaySession.value) return '연결 중';
  if (simActive.value) {
    if (simStuckTicks.value * 180 >= 660) return '위치 미갱신';
    if (simStep.value >= SIM_WAYPOINTS.length) return '정상 도착';
    return '이동 중';
  }
  return statusLabel.value;
});

const displayLastUpdate = computed(() => {
  if (simActive.value) {
    const secs = simStuckTicks.value * 180;
    if (secs === 0) return '방금';
    return `${Math.floor(secs / 60)}분 전`;
  }
  return lastUpdateLabel.value;
});

const showStaleWarning = computed(() =>
  simActive.value
    ? simStuckTicks.value * 180 >= 660
    : isLocationStale.value && session.value?.status !== 'ended'
);

const staleMinutes = computed(() =>
  simActive.value ? Math.floor(simStuckTicks.value * 3) : locationStaleMins.value
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

onMounted(() => startPolling());
onUnmounted(() => { stopPolling(); stopSim(); });
</script>
