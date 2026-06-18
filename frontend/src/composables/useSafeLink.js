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
const hikingStartTs = ref(null);
const waypointCount = ref(0);
const currentLat = ref(null);       // 가장 최근 GPS 위치
const currentLng = ref(null);
const liveTrail = ref([]);          // 메모리 내 전체 이동 경로 (서버 저장과 별개)
const stepCount = ref(0);           // 걸음 수
const distanceKm = ref(0);          // 이동 거리 (km)
let _watchId = null;
let _wakeLock = null;
let _elapsedTimer = null;
let _lastSavedTs = 0;
const WAYPOINT_INTERVAL = 300;

// ── 거리 계산 (Haversine) ────────────────────────────────────────────────────
function _haversine(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── 걸음 수 카운터 (DeviceMotion) ────────────────────────────────────────────
let _stepListenerAttached = false;
let _lastMag = 0;
let _lastStepTs = 0;
const STEP_THRESHOLD = 11.5; // m/s² 기준 가속도
const STEP_COOLDOWN = 280;   // ms

function _onMotion(e) {
  const a = e.accelerationIncludingGravity;
  if (!a) return;
  const mag = Math.sqrt((a.x ?? 0) ** 2 + (a.y ?? 0) ** 2 + (a.z ?? 0) ** 2);
  const now = Date.now();
  // 상승 엣지(이전 < 임계값, 현재 >= 임계값)에서 한 걸음 카운트
  if (_lastMag < STEP_THRESHOLD && mag >= STEP_THRESHOLD && now - _lastStepTs > STEP_COOLDOWN) {
    stepCount.value += 1;
    _lastStepTs = now;
  }
  _lastMag = mag;
}

async function _startStepCounter() {
  if (_stepListenerAttached) return;
  // iOS 13+ 권한 요청
  if (typeof DeviceMotionEvent?.requestPermission === 'function') {
    try {
      const perm = await DeviceMotionEvent.requestPermission();
      if (perm !== 'granted') return;
    } catch { return; }
  }
  if (!window.DeviceMotionEvent) return;
  window.addEventListener('devicemotion', _onMotion, { passive: true });
  _stepListenerAttached = true;
}

function _stopStepCounter() {
  if (!_stepListenerAttached) return;
  window.removeEventListener('devicemotion', _onMotion);
  _stepListenerAttached = false;
}

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

  _lastSavedTs = 0;
  _watchId = navigator.geolocation.watchPosition(
    (pos) => {
      if (!sessionId.value) return;
      const { latitude, longitude } = pos.coords;

      // 매 GPS 수신마다 실시간 위치·트레일 갱신
      const prev = liveTrail.value.at(-1);
      if (prev) distanceKm.value += _haversine(prev.lat, prev.lng, latitude, longitude);
      currentLat.value = latitude;
      currentLng.value = longitude;
      liveTrail.value = [...liveTrail.value, { lat: latitude, lng: longitude, ts: Date.now() }];

      // 5분 간격으로만 서버 저장
      const nowSec = Date.now() / 1000;
      if (_lastSavedTs !== 0 && nowSec - _lastSavedTs < WAYPOINT_INTERVAL) return;
      _lastSavedTs = nowSec;
      updateSafeLinkLocation(sessionId.value, latitude, longitude)
        .then(() => {
          lastLocationTs.value = Date.now();
          waypointCount.value += 1;
        })
        .catch(() => {
          gpsErrorMsg.value = '위치 전송에 실패했습니다. 네트워크를 확인해 주세요.';
        });
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

  // 경과 시간 (초 단위, 1초마다 갱신)
  const elapsedSec = ref(0);

  async function startHiking(course) {
    sessionStatus.value = 'creating';
    errorMsg.value = '';
    gpsErrorMsg.value = '';
    try {
      const data = await createSafeLink(course);
      sessionId.value = data.id;
      shareCode.value = data.share_code || '';
      sessionStatus.value = 'active';
      hikingStartTs.value = Date.now();
      waypointCount.value = 0;
      elapsedSec.value = 0;
      stepCount.value = 0;
      distanceKm.value = 0;
      liveTrail.value = [];
      currentLat.value = null;
      currentLng.value = null;
      _elapsedTimer = setInterval(() => {
        elapsedSec.value = Math.floor((Date.now() - hikingStartTs.value) / 1000);
      }, 1000);
      _startTracking();
      _startStepCounter();
      _acquireWakeLock();
    } catch (err) {
      sessionStatus.value = 'error';
      errorMsg.value = err.message || '세이프 링크를 생성하지 못했습니다. 네트워크를 확인해 주세요.';
    }
  }

  async function stopHiking() {
    _releaseWakeLock();
    _stopTracking();
    _stopStepCounter();
    if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; }
    if (sessionId.value) {
      try { await endSafeLink(sessionId.value); } catch {
        // 종료 요청 실패해도 클라이언트는 종료 처리
      }
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
    _stopStepCounter();
    if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; }
    sessionId.value = null;
    shareCode.value = '';
    sessionStatus.value = 'idle';
    errorMsg.value = '';
    gpsErrorMsg.value = '';
    lastLocationTs.value = null;
    hikingStartTs.value = null;
    waypointCount.value = 0;
    elapsedSec.value = 0;
    stepCount.value = 0;
    distanceKm.value = 0;
    liveTrail.value = [];
    currentLat.value = null;
    currentLng.value = null;
  }

  return {
    sessionId, shareCode, sessionStatus,
    shareUrl, isActive,
    errorMsg, gpsErrorMsg,
    lastLocationTs, wakeLockActive,
    hikingStartTs, waypointCount, elapsedSec,
    currentLat, currentLng, liveTrail,
    stepCount, distanceKm,
    startHiking, stopHiking, resetSafeLink,
  };
}

// ── 보호자 뷰 훅 ─────────────────────────────────────────────────────────────
const AUTO_REFRESH_INTERVAL = 60_000; // 1분

export function useGuardianView(sessionId) {
  const session = ref(null);
  const loading = ref(true);
  const pollError = ref('');
  const lastRefreshedTs = ref(null);   // 마지막 자동/수동 새로고침 시각 (ms)
  const nextRefreshIn = ref(0);        // 다음 자동 새로고침까지 남은 초
  let pollTimer = null;
  let countdownTimer = null;

  async function fetchSession() {
    try {
      session.value = await getSafeLink(sessionId);
      pollError.value = '';
      lastRefreshedTs.value = Date.now();
      nextRefreshIn.value = AUTO_REFRESH_INTERVAL / 1000;
    } catch {
      pollError.value = '위치 정보를 불러오지 못했습니다.';
    } finally {
      loading.value = false;
    }
  }

  function _startCountdown() {
    if (countdownTimer) clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      nextRefreshIn.value = Math.max(0, nextRefreshIn.value - 1);
    }, 1000);
  }

  function startPolling() {
    fetchSession();
    pollTimer = setInterval(fetchSession, AUTO_REFRESH_INTERVAL);
    _startCountdown();
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
  }

  // 수동 새로고침 — 타이머도 리셋
  async function manualRefresh() {
    stopPolling();
    loading.value = true;
    await fetchSession();
    pollTimer = setInterval(fetchSession, AUTO_REFRESH_INTERVAL);
    _startCountdown();
  }

  const lastRefreshedLabel = computed(() => {
    const ts = lastRefreshedTs.value;
    if (!ts) return '';
    const elapsed = Math.floor((Date.now() - ts) / 1000);
    if (elapsed < 10) return '방금 새로고침';
    if (elapsed < 60) return `${elapsed}초 전 새로고침`;
    return `${Math.floor(elapsed / 60)}분 전 새로고침`;
  });

  const nextRefreshLabel = computed(() => {
    const s = nextRefreshIn.value;
    if (s <= 0) return '새로고침 중…';
    if (s < 60) return `${s}초 후 자동 새로고침`;
    return `${Math.floor(s / 60)}분 ${s % 60}초 후 자동 새로고침`;
  });

  const lastUpdateLabel = computed(() => {
    const ts = session.value?.location_ts;
    if (!ts) return '위치 미수신';
    const elapsed = Math.floor((Date.now() / 1000) - ts);
    if (elapsed < 60) return `${elapsed}초 전`;
    return `${Math.floor(elapsed / 60)}분 전`;
  });

  // 마지막 위치 수신 후 경과 분
  const locationStaleMins = computed(() => {
    const ts = session.value?.location_ts;
    if (!ts || session.value?.status === 'ended') return 0;
    return Math.floor((Date.now() / 1000 - ts) / 60);
  });

  const isLocationStale = computed(() => locationStaleMins.value >= 10);

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

  return {
    session, loading, pollError,
    lastUpdateLabel, statusLabel, statusClass,
    lastRefreshedLabel, nextRefreshLabel,
    locationStaleMins, isLocationStale,
    startPolling, stopPolling, manualRefresh,
  };
}
