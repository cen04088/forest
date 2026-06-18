<template>
  <main class="guardian-shell">
    <header class="guardian-header">
      <img src="/logo.png" alt="올라" class="guardian-logo-img" />
      <span :class="['guardian-status-chip', statusClass]">{{ statusLabel }}</span>
    </header>

    <!-- 위치 미수신 경고 배너 -->
    <div v-if="isLocationStale && session?.status !== 'ended'" class="guardian-stale-banner" role="alert">
      <span class="stale-icon">⚠️</span>
      <div>
        <strong>위치 업데이트가 {{ locationStaleMins }}분째 없습니다</strong>
        <p>산행자의 GPS 신호가 끊겼거나 배터리가 부족할 수 있습니다. 직접 연락을 시도해 보세요.</p>
      </div>
      <a href="tel:119" class="stale-119">119</a>
    </div>

    <div v-if="loading" class="guardian-loading">위치 정보를 불러오는 중입니다…</div>
    <div v-else-if="session">
      <div ref="guardianMapEl" class="guardian-map kakao-map" aria-label="산행자 현재 위치 지도"></div>

      <section class="guardian-card">
        <div class="guardian-info-row">
          <div>
            <p class="eyebrow">산행 중</p>
            <h2>{{ session.course_name }}</h2>
            <p class="guardian-mountain">{{ session.mountain }}</p>
          </div>
          <span :class="['safety-badge', statusClass]">{{ session.safety_label }}</span>
        </div>

        <div class="guardian-meta-row">
          <span>📍 마지막 위치 수신: <strong>{{ lastUpdateLabel }}</strong></span>
          <span>🕐 {{ session.duration_min }}분 코스</span>
          <span v-if="session.trail?.length">🗺️ 위치 {{ session.trail.length }}회 기록됨</span>
        </div>

        <div v-if="session.risk_factors?.length" class="risk-tags guardian-risks">
          <span v-for="f in session.risk_factors" :key="f">{{ f }}</span>
        </div>

        <!-- 자동 새로고침 상태 -->
        <div class="guardian-refresh-status">
          <span class="refresh-dot"></span>
          <span>{{ lastRefreshedLabel }}</span>
          <span class="refresh-next">· {{ nextRefreshLabel }}</span>
        </div>

        <div v-if="session.status === 'ended'" class="guardian-ended-banner">
          산행이 종료되었습니다.
        </div>
      </section>

      <section class="guardian-actions">
        <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
        <button class="outline-btn" type="button" @click="manualRefresh">새로고침</button>
      </section>

      <p v-if="pollError" class="guardian-error">{{ pollError }}</p>
    </div>
    <div v-else class="guardian-not-found">
      <p>세이프 링크를 찾을 수 없습니다.<br>산행자에게 링크를 다시 받으세요.</p>
    </div>
  </main>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useGuardianView } from '../composables/useSafeLink.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';

const route = useRoute();
const sessionId = route.params.sessionId;

const guardianMapEl = ref(null);
const {
  session, loading, pollError,
  lastUpdateLabel, statusLabel, statusClass,
  lastRefreshedLabel, nextRefreshLabel,
  locationStaleMins, isLocationStale,
  startPolling, stopPolling, manualRefresh,
} = useGuardianView(sessionId);
const { renderGuardianMap } = useLeafletMap();

// 위치 미수신 10분 시 브라우저 알림
let _notifiedStale = false;
watch(isLocationStale, async (stale) => {
  if (!stale || _notifiedStale) return;
  _notifiedStale = true;
  if ('Notification' in window) {
    const perm = Notification.permission === 'default'
      ? await Notification.requestPermission()
      : Notification.permission;
    if (perm === 'granted') {
      new Notification('올라 — 위치 업데이트 없음', {
        body: `산행자의 위치가 ${locationStaleMins.value}분째 갱신되지 않았습니다. 직접 연락해 보세요.`,
        icon: '/logo.png',
      });
    }
  }
});

// 위치가 다시 갱신되면 알림 플래그 초기화
watch(() => session.value?.location_ts, () => { _notifiedStale = false; });

watch(session, async (val) => {
  if (!val) return;
  await nextTick();
  if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, val);
});

onMounted(() => startPolling());
onUnmounted(() => stopPolling());
</script>
