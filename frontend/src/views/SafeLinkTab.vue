<template>
  <section class="screen-stack safelink-layout">
    <div class="safelink-col-map">
      <section class="safelink-guardian-card">
        <div class="safelink-card-copy">
          <p class="safelink-kicker">
            <span class="safelink-shield" aria-hidden="true">◆</span>
            보호자 연결
          </p>
          <h1>산행자 코드 입력</h1>
          <p>산행자가 알려준 6자리 코드를 입력하면<br>현재 위치를 실시간으로 확인할 수 있습니다.</p>
        </div>

        <div v-if="!guardianResolved" class="safelink-code-area">
          <div class="code-input-wrap" :class="{ focused: inputFocused }" @click="focusGuardianInput">
            <input
              ref="hiddenInput"
              class="code-hidden-input"
              type="text"
              inputmode="text"
              autocomplete="off"
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
              maxlength="6"
              @input="onGuardianInput"
              @keydown="onGuardianKeydown"
              @keydown.enter="lookupCode"
              @paste="onGuardianPaste"
              @focus="inputFocused = true"
              @blur="inputFocused = false"
            />
            <div class="code-input-row">
              <div
                v-for="i in 6" :key="i"
                class="code-digit-input"
                :class="{ filled: guardianCode.length >= i, active: inputFocused && guardianCode.length === i - 1 }"
              >{{ guardianCode[i - 1] || '' }}</div>
            </div>
          </div>

          <p v-if="guardianError" class="guardian-entry-error">{{ guardianError }}</p>

          <button
            class="safelink-primary-btn"
            :disabled="guardianCode.length < 6 || guardianLoading"
            type="button"
            @click="lookupCode"
          >
            <span>{{ guardianLoading ? '확인 중…' : '위치 확인하기' }}</span>
            <span aria-hidden="true">→</span>
          </button>

          <p class="safelink-code-hint">
            <span aria-hidden="true">🔒</span>
            세이프링크 생성 후 코드를 복사하세요.
          </p>
        </div>

        <div v-else class="safelink-loading-note">
          위치 정보를 불러오는 중입니다…
        </div>
      </section>

      <section class="safelink-guide-card">
        <h2>안전 가이드</h2>
        <div class="safelink-guide-grid">
          <article class="safelink-guide-item tone-check">
            <span class="guide-item-icon" aria-hidden="true">☑</span>
            <strong>산행 전 체크리스트</strong>
            <p>안전한 산행을 위한 필수 확인 사항</p>
            <button type="button">자세히 보기 <span aria-hidden="true">→</span></button>
          </article>
          <article class="safelink-guide-item tone-alert">
            <span class="guide-item-icon" aria-hidden="true">🔔</span>
            <strong>긴급 상황 대처법</strong>
            <p>위급 상황 발생 시 대처 요령 안내</p>
            <button type="button">자세히 보기 <span aria-hidden="true">→</span></button>
          </article>
          <article class="safelink-guide-item tone-weather">
            <span class="guide-item-icon" aria-hidden="true">🌧</span>
            <strong>기상 위험 정보</strong>
            <p>실시간 기상과 위험 정보 확인</p>
            <button type="button">자세히 보기 <span aria-hidden="true">→</span></button>
          </article>
          <article class="safelink-guide-item tone-gear">
            <span class="guide-item-icon" aria-hidden="true">🎒</span>
            <strong>장비 점검 가이드</strong>
            <p>필수 장비 점검과 준비 방법</p>
            <button type="button">자세히 보기 <span aria-hidden="true">→</span></button>
          </article>
        </div>
      </section>

      <section class="safelink-info-card">
        <div class="safelink-info-icon" aria-hidden="true">✚</div>
        <div>
          <h2>안전 공유 이용 안내</h2>
          <ul>
            <li><span>✓</span> 산행자는 앱에서 안전공유 코드를 생성할 수 있습니다.</li>
            <li><span>✓</span> 코드를 공유한 보호자는 실시간 위치 확인이 가능합니다.</li>
            <li><span>✓</span> 네트워크가 불안정한 지역에서도 위치가 저장되어 복구됩니다.</li>
          </ul>
        </div>
      </section>
    </div>

    <aside class="safelink-col-ctrl">
      <section class="safelink-side-card share-panel">
        <div class="safelink-side-head">
          <p class="eyebrow">산행 시작</p>
          <h2>세이프링크 생성</h2>
          <p>산행을 시작하면 보호자 전용 실시간 위치 링크가 생성됩니다.</p>
        </div>

        <div v-if="!safeLinkActive && safeLinkStatus !== 'ended'" class="safelink-create-state">
          <p v-if="!selectedMountain" class="safe-link-guide">
            💡 안전코스 탭에서 산을 선택하면 안전 정보도 함께 공유됩니다.
          </p>
          <button
            class="safelink-primary-btn wide"
            type="button"
            :disabled="safeLinkStatus === 'creating'"
            @click="startHiking(mountainAsCourse)"
          >
            <span>{{ safeLinkStatus === 'creating' ? '링크 생성 중…' : '산행 시작 & 세이프링크 생성' }}</span>
            <span aria-hidden="true">→</span>
          </button>
          <p v-if="safeLinkError" class="share-status error">{{ safeLinkError }}</p>
          <p v-if="gpsErrorMsg" class="share-status error">📡 {{ gpsErrorMsg }}</p>
        </div>

        <div v-else-if="safeLinkActive" class="safe-link-active-panel">
          <div class="hike-status-card">
            <div class="hike-status-row">
              <div class="hike-stat">
                <span class="hike-stat-label">경과 시간</span>
                <strong class="hike-stat-val">{{ elapsedLabel }}</strong>
              </div>
              <div class="hike-stat">
                <span class="hike-stat-label">이동 거리</span>
                <strong class="hike-stat-val">{{ distanceLabel }}</strong>
              </div>
              <div class="hike-stat">
                <span class="hike-stat-label">걸음 수</span>
                <strong class="hike-stat-val">{{ stepCount.toLocaleString() }}</strong>
              </div>
            </div>
            <div class="hike-status-footer">
              <span class="status-dot dot-green"></span>
              <span>산행 중 · {{ wakeLockActive ? '화면 유지 활성' : '화면 꺼짐 주의' }}</span>
            </div>
          </div>

          <div v-if="!wakeLockActive" class="wakelock-warn">
            ⚠️ 화면이 꺼지면 GPS 추적이 중단됩니다. 산행 중에는 화면을 켜두세요.
          </div>
          <p v-if="gpsErrorMsg" class="share-status error">📡 {{ gpsErrorMsg }}</p>

          <div v-if="shareCode" class="share-code-box">
            <p class="share-code-label">보호자에게 이 코드를 알려주세요</p>
            <div class="share-code-display">
              <span v-for="ch in shareCode" :key="ch + Math.random()" class="share-code-char">{{ ch }}</span>
            </div>
            <button class="copy-code-btn" type="button" @click="copyShareCode">
              <span v-if="codeCopied">✓ 복사됨</span>
              <span v-else>코드 복사</span>
            </button>
            <p class="share-code-hint">보호자는 앱에서 <strong>보호자 연결</strong>을 눌러 코드를 입력합니다</p>
          </div>

          <details class="share-url-details">
            <summary>링크로 공유하기</summary>
            <div class="safe-link-url-box">
              <span class="safe-link-url-text">{{ safeLinkUrl }}</span>
            </div>
            <button class="outline-btn" type="button" @click="copyAndShare">링크 복사</button>
          </details>

          <button class="outline-btn danger wide-field" type="button" @click="stopAndRecord">산행 종료</button>
          <p v-if="shareStatus" class="share-status">{{ shareStatus }}</p>
        </div>

        <div v-else class="safe-link-ended">
          <p>산행이 종료되었습니다.</p>
          <button class="safelink-primary-btn wide" type="button" @click="resetSafeLink">
            <span>새 산행 시작하기</span>
            <span aria-hidden="true">→</span>
          </button>
        </div>

        <details class="share-message-details" v-if="selectedMountain">
          <summary>문자 공유 문구 보기</summary>
          <textarea class="share-message" :value="safeLinkMessage" readonly aria-label="보호자 공유 메시지"></textarea>
          <div class="share-actions">
            <button class="outline-btn" type="button" @click="shareMessage">문자 공유</button>
            <button class="outline-btn" type="button" @click="copyMessage">문구 복사</button>
          </div>
        </details>
      </section>

      <section class="safelink-side-card kakao-actions">
        <a :class="['map-action', !selectedMountain ? 'disabled' : '']" :href="selectedMountain ? kakaoMapUrl : undefined" target="_blank" rel="noreferrer">
          <span class="map-action-icon pin" aria-hidden="true">●</span>
          <span class="map-action-copy">
            <strong>카카오맵에서 위치 보기</strong>
            <span>보호자가 산행자의 위치를 카카오맵으로 바로 확인합니다.</span>
          </span>
          <span class="map-action-chevron" aria-hidden="true">›</span>
        </a>
        <a :class="['map-action', !selectedMountain ? 'disabled' : '']" :href="selectedMountain ? 'https://m.map.kakao.com/scheme/open?page=locationsharing' : undefined" target="_blank" rel="noreferrer">
          <span class="map-action-icon people" aria-hidden="true">●</span>
          <span class="map-action-copy">
            <strong>카카오맵 친구위치 공유</strong>
            <span>현재 나의 위치를 친구들과 카카오맵으로 실시간 공유합니다.</span>
          </span>
          <span class="map-action-chevron" aria-hidden="true">›</span>
        </a>
        <a class="map-action emergency" href="tel:119">
          <span class="map-action-icon siren" aria-hidden="true">●</span>
          <span class="map-action-copy">
            <strong>119 신고</strong>
            <span>산악 사고 발생 시 즉시 119에 신고하세요.</span>
          </span>
          <span class="map-action-chevron" aria-hidden="true">›</span>
        </a>

        <div class="sos-divider">긴급 연락처</div>

        <div v-if="!authUser" class="map-action sos-unset">
          <span class="map-action-icon phone" aria-hidden="true">●</span>
          <span class="map-action-copy">
            <strong>로그인 후 이용 가능</strong>
            <span>로그인하면 긴급 연락처를 등록할 수 있습니다.</span>
          </span>
          <span class="map-action-chevron" aria-hidden="true">›</span>
        </div>
        <div v-else-if="emergencyContacts.length === 0" class="map-action sos-unset">
          <span class="map-action-icon phone" aria-hidden="true">●</span>
          <span class="map-action-copy">
            <strong>긴급 연락처 미등록</strong>
            <span>내 정보 탭에서 연락처를 추가하세요.</span>
          </span>
          <span class="map-action-chevron" aria-hidden="true">›</span>
        </div>
        <template v-else>
          <a
            v-for="contact in emergencyContacts.slice(0, 2)"
            :key="contact.id"
            class="map-action sos-contact"
            :href="`tel:${contact.phone}`"
            @click.prevent="callWithLocation(contact)"
          >
            <span class="map-action-icon phone" aria-hidden="true">●</span>
            <span class="map-action-copy">
              <strong>{{ contact.name }}<span v-if="contact.relation" class="sos-relation"> · {{ contact.relation }}</span></strong>
              <span>{{ contact.phone }}<template v-if="safeLinkActive && currentLat"> · 전화 전 GPS 위치 자동 복사</template></span>
            </span>
            <span class="map-action-chevron" aria-hidden="true">›</span>
          </a>
        </template>
      </section>
    </aside>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { selectedMountain, weatherData } from '../composables/useGuide.js';
import { emergencyContacts, loadMyPageData, saveHikingRecord } from '../composables/useUserData.js';
import { authUser } from '../composables/useAuth.js';
import { useSafeLink } from '../composables/useSafeLink.js';
import { getSafeLinkByCode } from '../api.js';

const router = useRouter();
const shareStatus = ref('');
const codeCopied = ref(false);

async function copyShareCode() {
  if (!shareCode.value) return;
  try {
    await navigator.clipboard.writeText(shareCode.value);
  } catch {
    const el = document.createElement('textarea');
    el.value = shareCode.value;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
  }
  codeCopied.value = true;
  setTimeout(() => { codeCopied.value = false; }, 2000);
}

// ── 보호자 코드 입력 ──────────────────────────────────────────────────────────
const hiddenInput = ref(null);
const guardianCode = ref('');
const guardianLoading = ref(false);
const guardianError = ref('');
const guardianResolved = ref(false);
const inputFocused = ref(false);

onMounted(() => {
  nextTick(() => hiddenInput.value?.focus());
  if (authUser.value && emergencyContacts.value.length === 0) loadMyPageData();
});

function focusGuardianInput() {
  hiddenInput.value?.focus();
}

function onGuardianKeydown(event) {
  if (event.key === 'Backspace') {
    event.preventDefault();
    guardianCode.value = guardianCode.value.slice(0, -1);
    if (hiddenInput.value) hiddenInput.value.value = guardianCode.value;
  }
}

function onGuardianInput(event) {
  const clean = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
  guardianCode.value = clean;
  event.target.value = clean;
}

function onGuardianPaste(event) {
  event.preventDefault();
  const text = (event.clipboardData || window.clipboardData)
    .getData('text')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 6);
  guardianCode.value = text;
  if (hiddenInput.value) hiddenInput.value.value = text;
}

async function lookupCode() {
  if (guardianCode.value.length < 6 || guardianLoading.value) return;
  guardianLoading.value = true;
  guardianError.value = '';
  try {
    const session = await getSafeLinkByCode(guardianCode.value);
    guardianResolved.value = true;
    router.push(`/safe/${session.id}`);
  } catch (err) {
    guardianError.value = err.message || '오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
    guardianCode.value = '';
    if (hiddenInput.value) hiddenInput.value.value = '';
    await nextTick();
    hiddenInput.value?.focus();
  } finally {
    guardianLoading.value = false;
  }
}

const {
  sessionStatus: safeLinkStatus,
  shareUrl: safeLinkUrl,
  shareCode,
  isActive: safeLinkActive,
  errorMsg: safeLinkError,
  gpsErrorMsg,
  lastLocationTs,
  wakeLockActive,
  waypointCount,
  elapsedSec,
  currentLat, currentLng, liveTrail,
  stepCount, distanceKm,
  startHiking,
  stopHiking,
  resetSafeLink,
} = useSafeLink();

const elapsedLabel = computed(() => {
  const s = elapsedSec.value;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}시간 ${String(m).padStart(2,'0')}분`;
  if (m > 0) return `${m}분 ${String(sec).padStart(2,'0')}초`;
  return `${sec}초`;
});

const distanceLabel = computed(() => {
  const d = distanceKm.value;
  if (d < 1) return `${Math.round(d * 1000)}m`;
  return `${d.toFixed(2)}km`;
});


// 산 → 세이프링크 API가 기대하는 형태로 변환
// 산 미선택 시에도 현재 위치 추적용 세션 생성 가능
const mountainAsCourse = computed(() => {
  const m = selectedMountain.value;
  if (!m) return { name: '현재 위치 추적', safety_label: '위치 추적 중', safety_decision: 'caution' };
  return {
    id: m.id,
    name: m.name,
    mountain: m.name,
    lat: m.lat,
    lng: m.lng,
    safety_label: m.safety_label || '확인 중',
    safety_decision: m.safety_decision || 'caution',
    elevation_m: m.elevation_m,
    region: m.region,
    difficulty: m.difficulty,
    duration_min: m.walk_time_min || 0,
  };
});

const hasLocation = computed(() => {
  const m = selectedMountain.value;
  return m && Number.isFinite(Number(m.lat)) && Number.isFinite(Number(m.lng));
});

const kakaoMapUrl = computed(() => {
  if (!hasLocation.value) return '';
  const m = selectedMountain.value;
  return `https://map.kakao.com/link/map/${encodeURIComponent(m.name)},${m.lat},${m.lng}`;
});

const safeLinkMessage = computed(() => {
  if (!selectedMountain.value) return '안전 진단 후 공유 메시지가 생성됩니다.';
  const m = selectedMountain.value;
  const loH = Math.floor((m.walk_time_min || 0) / 60);
  const hiH = Math.floor((m.walk_time_max || 0) / 60);
  const timeText = (loH || hiH) ? `약 ${loH}~${hiH}시간` : '확인 필요';
  const diffLabel = { easy: '초급', medium: '중급', hard: '고급' }[m.difficulty] || '';
  const highlights = (m.highlights || []).slice(0, 2).join(', ') || '';
  const locationLine = hasLocation.value ? `카카오맵 위치: ${kakaoMapUrl.value}` : '';
  return [
    '[올라 안전공유]',
    `산: ${m.name} (${m.region})`,
    `안전 등급: ${m.safety_label || '확인 중'} · 난이도 ${diffLabel}`,
    `해발 ${m.elevation_m ?? '-'}m · 소요시간 ${timeText}`,
    highlights ? `특징: ${highlights}` : '',
    locationLine,
    '현장 통제, 기상 변화, 입산 제한 여부를 함께 확인해 주세요.',
  ].filter(Boolean).join('\n');
});

async function stopAndRecord() {
  await stopHiking();
  if (mountainAsCourse.value) {
    await saveHikingRecord(mountainAsCourse.value, weatherData.value);
  }
}

async function copyAndShare() {
  const url = safeLinkUrl.value;
  if (!url) return;
  if (navigator.share) {
    try {
      await navigator.share({ title: '올라 세이프링크', text: `${selectedMountain.value?.name} 산행 중입니다.`, url });
      return;
    } catch (err) { if (err?.name === 'AbortError') return; }
  }
  try {
    await navigator.clipboard.writeText(url);
    shareStatus.value = '보호자 링크를 복사했습니다.';
  } catch {
    shareStatus.value = '링크를 직접 복사해 주세요: ' + url;
  }
}

async function copyMessage() {
  if (!selectedMountain.value) return;
  try {
    await navigator.clipboard.writeText(safeLinkMessage.value);
    shareStatus.value = '보호자 공유 문구를 복사했습니다.';
  } catch {
    shareStatus.value = '문구를 직접 선택해 복사해 주세요.';
  }
}

async function callWithLocation(contact) {
  if (safeLinkActive.value && currentLat.value && currentLng.value) {
    try {
      await navigator.clipboard.writeText(
        `현재 위치: https://maps.google.com/?q=${currentLat.value},${currentLng.value}`
      );
      shareStatus.value = '위치를 클립보드에 복사했습니다. 통화 중 알려주세요.';
    } catch {}
  }
  window.location.href = `tel:${contact.phone}`;
}

async function shareMessage() {
  if (!selectedMountain.value) return;
  if (navigator.share) {
    try {
      await navigator.share({ title: '올라 안전공유', text: safeLinkMessage.value, url: hasLocation.value ? kakaoMapUrl.value : window.location.href });
      shareStatus.value = '공유 창을 열었습니다.';
      return;
    } catch (err) { if (err?.name === 'AbortError') { shareStatus.value = '공유를 취소했습니다.'; return; } }
  }
  await copyMessage();
  if (hasLocation.value) window.open(kakaoMapUrl.value, '_blank', 'noreferrer');
}


</script>
