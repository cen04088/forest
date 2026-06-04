<template>
  <section class="screen-stack safelink-layout">
    <!-- 왼쪽 컬럼: 지도 + 상태 카드 -->
    <div class="safelink-col-map">
    <section class="panel">
      <div class="section-title">
        <div><p class="eyebrow">Safe Link</p><h2>보호자 공유카드</h2></div>
      </div>

      <article class="safe-link-card">
        <div class="safe-link-map">
          <div ref="safeLinkMapEl" class="kakao-map" aria-label="보호자 공유 카카오 지도"></div>
        </div>
        <div v-if="safeLinkMapStatus" class="map-status-msg">
          <span class="info-icon">ℹ️</span><span>{{ safeLinkMapStatus }}</span>
        </div>
        <div class="safe-link-status">
          <span :class="['safety-badge', selectedCourse ? safetyClass(selectedCourse) : 'yellow']">
            {{ selectedCourse?.safety_label || '진단 대기' }}
          </span>
          <h3>{{ selectedCourse?.name || '안전 진단 후 공유 가능' }}</h3>
          <p>{{ safeLinkSummary }}</p>
        </div>
      </article>

      <div v-if="selectedCourse" class="safe-link-status-bar">
        <div class="status-dot" :class="selectedCourse.safety_decision === 'recommend' ? 'dot-green' : 'dot-yellow'"></div>
        <span>{{ selectedCourse.safe_link_preview?.status || '정상 이동' }}</span>
        <span class="status-time">마지막 확인: 방금 전</span>
      </div>
    </section>
    </div><!-- /safelink-col-map -->

    <!-- 오른쪽 컬럼: 산행 시작 컨트롤 + 외부 링크 -->
    <div class="safelink-col-ctrl">
    <!-- 산행 시작 / 세이프링크 패널 -->
    <section class="panel share-panel">
      <div class="section-title compact">
        <div><p class="eyebrow">산행 시작</p><h2>세이프링크 생성</h2></div>
      </div>
      <div v-if="!safeLinkActive && safeLinkStatus !== 'ended'">
        <p class="safe-link-guide">코스를 선택한 뒤 산행을 시작하면 보호자 전용 실시간 위치 링크가 생성됩니다.</p>
        <button
          class="primary-btn wide-field" type="button"
          :disabled="!selectedCourse || safeLinkStatus === 'creating'"
          @click="startHiking(selectedCourse)"
        >
          {{ safeLinkStatus === 'creating' ? '링크 생성 중…' : '산행 시작 &amp; 세이프링크 생성' }}
        </button>
        <p v-if="safeLinkError" class="share-status error">{{ safeLinkError }}</p>
      </div>

      <div v-else-if="safeLinkActive" class="safe-link-active-panel">
        <div class="safe-link-live-badge">
          <span class="status-dot dot-green"></span> 산행 중 · GPS 추적 활성
          <span v-if="lastLocationTs" class="status-time">방금 전 갱신</span>
        </div>
        <p class="safe-link-url-label">보호자 링크 (공유하면 실시간 위치 확인 가능)</p>
        <div class="safe-link-url-box">
          <span class="safe-link-url-text">{{ safeLinkUrl }}</span>
        </div>
        <div class="share-actions">
          <button class="primary-btn" type="button" @click="copyAndShare">링크 공유</button>
          <button class="outline-btn danger" type="button" @click="stopAndRecord">산행 종료</button>
        </div>
      </div>

      <div v-else class="safe-link-ended">
        <p>산행이 종료되었습니다. 새 산행을 시작하려면 코스를 다시 선택하세요.</p>
      </div>

      <details class="share-message-details" v-if="selectedCourse">
        <summary>문자 공유 문구 보기</summary>
        <textarea class="share-message" :value="safeLinkMessage" readonly aria-label="보호자 공유 메시지"></textarea>
        <div class="share-actions">
          <button class="outline-btn" type="button" @click="shareMessage">문자 공유</button>
          <button class="outline-btn" type="button" @click="copyMessage">문구 복사</button>
        </div>
      </details>
    </section>

    <section class="panel kakao-actions">
      <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? kakaoMapUrl : undefined" target="_blank" rel="noreferrer">
        <strong>카카오맵에서 위치 보기</strong>
        <span>보호자가 코스 위치를 바로 확인합니다.</span>
      </a>
      <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? 'https://m.map.kakao.com/scheme/open?page=locationsharing' : undefined" target="_blank" rel="noreferrer">
        <strong>카카오맵 친구위치 공유</strong>
        <span>현재 나의 위치를 친구들과 카카오맵으로 실시간 공유합니다.</span>
      </a>
      <a class="map-action emergency" href="tel:119">
        <strong>🚨 119 신고</strong>
        <span>산악 사고 발생 시 즉시 119에 신고하세요.</span>
      </a>
    </section>
    </div><!-- /safelink-col-ctrl -->
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { selectedCourse, weatherData, fetchCourseGeometry } from '../composables/useGuide.js';
import { saveHikingRecord } from '../composables/useUserData.js';
import { useSafeLink } from '../composables/useSafeLink.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';
import { safetyClass, durationLabel, daylightLabel } from '../utils/courseHelpers.js';

const safeLinkMapEl = ref(null);
const shareStatus = ref('');

const { safeLinkMapStatus, renderSafeLinkMap } = useLeafletMap();
const { sessionStatus: safeLinkStatus, shareUrl: safeLinkUrl, isActive: safeLinkActive, errorMsg: safeLinkError, lastLocationTs, startHiking, stopHiking } = useSafeLink();

const hasLocation = computed(() => {
  const lat = Number(selectedCourse.value?.lat);
  const lng = Number(selectedCourse.value?.lng);
  return Number.isFinite(lat) && Number.isFinite(lng);
});

const kakaoMapUrl = computed(() => {
  if (!hasLocation.value) return '';
  const c = selectedCourse.value;
  return `https://map.kakao.com/link/map/${encodeURIComponent(c.name)},${c.lat},${c.lng}`;
});

const safeLinkSummary = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 보호자에게 보낼 공유 카드가 생성됩니다.';
  return `${selectedCourse.value.mountain} ${selectedCourse.value.name} 코스의 안전 등급과 카카오 지도 위치를 보호자에게 공유합니다.`;
});

const safeLinkMessage = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 공유 메시지가 생성됩니다.';
  const course = selectedCourse.value;
  const riskFactors = (course.risk_factors || []).slice(0, 2).join(', ') || '특이 위험 요인 없음';
  const locationLine = hasLocation.value ? `카카오맵 위치: ${kakaoMapUrl.value}` : '카카오맵 위치: 좌표 정보 없음';
  return [
    '[올라 안전공유]',
    `산/코스: ${course.mountain} · ${course.name}`,
    `안전 등급: ${course.safety_label || ''}`,
    `예상 산행: 약 ${durationLabel(course.duration_min)} / 거리 ${course.distance_km}km`,
    `하산 여유: ${daylightLabel(course.daylight_margin_min)}`,
    `주의 요인: ${riskFactors}`,
    locationLine,
    '현장 통제, 기상 변화, 입산 제한 여부를 함께 확인해 주세요.',
  ].join('\n');
});

async function stopAndRecord() {
  await stopHiking();
  await saveHikingRecord(selectedCourse.value, weatherData.value);
}

async function copyAndShare() {
  const url = safeLinkUrl.value;
  if (!url) return;
  if (navigator.share) {
    try {
      await navigator.share({ title: '올라 세이프링크', text: `${selectedCourse.value?.mountain} ${selectedCourse.value?.name} 산행 중입니다.`, url });
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
  if (!selectedCourse.value) return;
  try {
    await navigator.clipboard.writeText(safeLinkMessage.value);
    shareStatus.value = '보호자 공유 문구를 복사했습니다.';
  } catch {
    shareStatus.value = '브라우저에서 복사를 허용하지 않았습니다. 문구를 직접 선택해 복사해 주세요.';
  }
}

async function shareMessage() {
  if (!selectedCourse.value) return;
  if (navigator.share) {
    try {
      await navigator.share({ title: '올라 안전공유', text: safeLinkMessage.value, url: hasLocation.value ? kakaoMapUrl.value : window.location.href });
      shareStatus.value = '보호자 공유 창을 열었습니다.';
      return;
    } catch (err) { if (err?.name === 'AbortError') { shareStatus.value = '공유를 취소했습니다.'; return; } }
  }
  await copyMessage();
  if (hasLocation.value) window.open(kakaoMapUrl.value, '_blank', 'noreferrer');
}

async function renderMap() {
  await nextTick();
  const course = selectedCourse.value;
  if (!course) { renderSafeLinkMap(safeLinkMapEl.value, null); return; }

  // geometry 없으면 on-demand fetch
  if (!course.route_geometry || course.route_geometry.length < 2) {
    renderSafeLinkMap(safeLinkMapEl.value, course);
    const geometry = await fetchCourseGeometry(course);
    if (geometry) {
      course.route_geometry = geometry;
      selectedCourse.value = { ...course };
    }
  }
  await nextTick();
  renderSafeLinkMap(safeLinkMapEl.value, selectedCourse.value);
}

watch(selectedCourse, renderMap);
onMounted(renderMap);
</script>
