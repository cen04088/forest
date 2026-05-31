import { ref, computed, onUnmounted } from 'vue';
import { createSafeLink, updateSafeLinkLocation, endSafeLink, getSafeLink } from '../api.js';

export function useSafeLink() {
  const sessionId = ref(null);
  const sessionStatus = ref('idle'); // idle | creating | active | ended | error
  const errorMsg = ref('');
  const watchId = ref(null);
  const lastLocationTs = ref(null);

  const shareUrl = computed(() => {
    if (!sessionId.value) return '';
    return `${window.location.origin}${window.location.pathname}#/safe/${sessionId.value}`;
  });

  const isActive = computed(() => sessionStatus.value === 'active');

  async function startHiking(course) {
    sessionStatus.value = 'creating';
    errorMsg.value = '';
    try {
      const data = await createSafeLink(course);
      sessionId.value = data.id;
      sessionStatus.value = 'active';
      _startTracking();
    } catch (err) {
      sessionStatus.value = 'error';
      errorMsg.value = '세이프 링크 생성에 실패했습니다.';
    }
  }

  function _startTracking() {
    if (!navigator.geolocation) return;
    watchId.value = navigator.geolocation.watchPosition(
      (pos) => {
        if (!sessionId.value) return;
        const { latitude, longitude } = pos.coords;
        updateSafeLinkLocation(sessionId.value, latitude, longitude)
          .then(() => { lastLocationTs.value = Date.now(); })
          .catch(() => {});
      },
      () => {},
      { enableHighAccuracy: true, maximumAge: 30000, timeout: 15000 },
    );
  }

  async function stopHiking() {
    if (watchId.value !== null) {
      navigator.geolocation.clearWatch(watchId.value);
      watchId.value = null;
    }
    if (sessionId.value) {
      try { await endSafeLink(sessionId.value); } catch {}
    }
    sessionStatus.value = 'ended';
  }

  onUnmounted(() => {
    if (watchId.value !== null) {
      navigator.geolocation.clearWatch(watchId.value);
    }
  });

  return { sessionId, sessionStatus, shareUrl, isActive, errorMsg, lastLocationTs, startHiking, stopHiking };
}

// ── 보호자 뷰 훅 ─────────────────────────────────────────────────────────────
export function useGuardianView(sessionId) {
  const session = ref(null);
  const loading = ref(true);
  const pollError = ref('');
  let pollTimer = null;

  async function fetchSession() {
    try {
      session.value = await getSafeLink(sessionId);
      pollError.value = '';
    } catch {
      pollError.value = '위치 정보를 불러오지 못했습니다.';
    } finally {
      loading.value = false;
    }
  }

  function startPolling() {
    fetchSession();
    pollTimer = setInterval(fetchSession, 20000);
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer);
  }

  const lastUpdateLabel = computed(() => {
    const ts = session.value?.location_ts;
    if (!ts) return '위치 미수신';
    const elapsed = Math.floor((Date.now() / 1000) - ts);
    if (elapsed < 60) return `${elapsed}초 전`;
    return `${Math.floor(elapsed / 60)}분 전`;
  });

  const statusLabel = computed(() => {
    if (!session.value) return '연결 중';
    if (session.value.status === 'ended') return '산행 종료';
    const decision = session.value.safety_decision;
    if (decision === 'not_recommended') return '주의 필요';
    if (decision === 'caution') return '주의 구간';
    return '정상 이동';
  });

  const statusClass = computed(() => {
    if (!session.value || session.value.status === 'ended') return 'gray';
    const decision = session.value.safety_decision;
    if (decision === 'not_recommended') return 'red';
    if (decision === 'caution') return 'yellow';
    return 'green';
  });

  return { session, loading, pollError, lastUpdateLabel, statusLabel, statusClass, startPolling, stopPolling };
}
