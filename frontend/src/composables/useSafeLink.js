import { ref, computed } from 'vue';
import { createSafeLink, updateSafeLinkLocation, endSafeLink, getSafeLink } from '../api.js';

// ── 모듈 레벨 싱글톤 (탭 이동해도 상태 유지) ────────────────────────────────
const sessionId = ref(null);
const shareCode = ref('');
const sessionStatus = ref('idle'); // idle | creating | active | ended | error
const errorMsg = ref('');
const lastLocationTs = ref(null);
const gpsErrorMsg = ref('');
const wakeLockActive = ref(false);
let _watchId = null;
let _wakeLock = null;

// ── Wake Lock (화면 꺼짐 방지) ───────────────────────────────────────────────
async function _acquireWakeLock() {
  if (!('wakeLock' in navigator)) return;
  try {
    _wakeLock = await navigator.wakeLock.request('screen');
    wakeLockActive.value = true;
    _wakeLock.addEventListener('release', () => { wakeLockActive.value = false; });
    // 화면이 다시 켜지면 자동 재취득
    document.addEventListener('visibilitychange', _reacquireWakeLock);
  } catch {}
}

async function _reacquireWakeLock() {
  if (document.visibilityState === 'visible' && sessionStatus.value === 'active') {
    await _acquireWakeLock();
  }
}

function _releaseWakeLock() {
  document.removeEventListener('visibilitychange', _reacquireWakeLock);
  if (_wakeLock) { _wakeLock.release(); _wakeLock = null; }
  wakeLockActive.value = false;
}

// ── GPS 추적 (내부) ──────────────────────────────────────────────────────────
function _startTracking() {
  if (!navigator.geolocation) {
    gpsErrorMsg.value = '이 브라우저는 위치 서비스를 지원하지 않습니다.';
    return;
  }
  if (_watchId !== null) return; // 이미 추적 중

  _watchId = navigator.geolocation.watchPosition(
    (pos) => {
      if (!sessionId.value) return;
      const { latitude, longitude } = pos.coords;
      updateSafeLinkLocation(sessionId.value, latitude, longitude)
        .then(() => { lastLocationTs.value = Date.now(); })
        .catch(() => {});
    },
    (err) => {
      const msgs = {
        1: 'GPS 권한이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해 주세요.',
        2: 'GPS 신호를 찾을 수 없습니다. 실외로 이동해 다시 시도해 주세요.',
        3: 'GPS 응답 시간이 초과되었습니다.',
      };
      gpsErrorMsg.value = msgs[err.code] || `GPS 오류 (코드 ${err.code})`;
    },
    { enableHighAccuracy: true, maximumAge: 30000, timeout: 15000 },
  );
}

function _stopTracking() {
  if (_watchId !== null) {
    navigator.geolocation?.clearWatch(_watchId);
    _watchId = null;
  }
}

// ── 공개 composable ───────────────────────────────────────────────────────────
export function useSafeLink() {
  const shareUrl = computed(() => {
    if (!sessionId.value) return '';
    const base = `${window.location.origin}${window.location.pathname}`;
    return `${base}#/safe/${sessionId.value}`;
  });

  const isActive = computed(() => sessionStatus.value === 'active');

  async function startHiking(course) {
    sessionStatus.value = 'creating';
    errorMsg.value = '';
    gpsErrorMsg.value = '';
    try {
      const data = await createSafeLink(course);
      sessionId.value = data.id;
      shareCode.value = data.share_code || '';
      sessionStatus.value = 'active';
      _startTracking();
      _acquireWakeLock();
    } catch (err) {
      sessionStatus.value = 'error';
      errorMsg.value = err.message || '세이프 링크 생성에 실패했습니다.';
    }
  }

  async function stopHiking() {
    _releaseWakeLock();
    _stopTracking();
    if (sessionId.value) {
      try { await endSafeLink(sessionId.value); } catch {}
    }
    sessionStatus.value = 'ended';
    sessionId.value = null;
    shareCode.value = '';
    lastLocationTs.value = null;
    gpsErrorMsg.value = '';
  }

  function resetSafeLink() {
    _releaseWakeLock();
    _stopTracking();
    sessionId.value = null;
    shareCode.value = '';
    sessionStatus.value = 'idle';
    errorMsg.value = '';
    gpsErrorMsg.value = '';
    lastLocationTs.value = null;
  }

  return {
    sessionId,
    shareCode,
    sessionStatus,
    shareUrl,
    isActive,
    errorMsg,
    gpsErrorMsg,
    lastLocationTs,
    wakeLockActive,
    startHiking,
    stopHiking,
    resetSafeLink,
  };
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
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
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
    if (session.value.safety_decision === 'not_recommended') return '주의 필요';
    if (session.value.safety_decision === 'caution') return '주의 구간';
    return '정상 이동';
  });

  const statusClass = computed(() => {
    if (!session.value || session.value.status === 'ended') return 'gray';
    if (session.value.safety_decision === 'not_recommended') return 'red';
    if (session.value.safety_decision === 'caution') return 'yellow';
    return 'green';
  });

  return { session, loading, pollError, lastUpdateLabel, statusLabel, statusClass, startPolling, stopPolling };
}
