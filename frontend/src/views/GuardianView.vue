<template>
  <main class="guardian-shell">
    <header class="guardian-header">
      <img src="/logo.png" alt="올라" class="guardian-logo-img" />
      <span :class="['guardian-status-chip', statusClass]">{{ statusLabel }}</span>
    </header>

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
          <span v-if="session.trail?.length">🗺️ 궤적 {{ session.trail.length }}포인트</span>
        </div>

        <div v-if="session.risk_factors?.length" class="risk-tags guardian-risks">
          <span v-for="f in session.risk_factors" :key="f">{{ f }}</span>
        </div>

        <div v-if="session.status === 'ended'" class="guardian-ended-banner">
          산행이 종료되었습니다.
        </div>
      </section>

      <section class="guardian-actions">
        <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
        <button class="outline-btn" type="button" @click="refresh">새로고침</button>
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
const { session, loading, pollError, lastUpdateLabel, statusLabel, statusClass, startPolling, stopPolling } = useGuardianView(sessionId);
const { renderGuardianMap } = useLeafletMap();

function refresh() {
  loading.value = true;
  stopPolling();
  startPolling();
}

watch(session, async (val) => {
  if (!val) return;
  await nextTick();
  if (guardianMapEl.value) renderGuardianMap(guardianMapEl.value, val);
});

onMounted(() => startPolling());
onUnmounted(() => stopPolling());
</script>
