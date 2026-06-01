<template>
  <article
    :class="['course-card', isSelected ? 'selected' : '', rank === 1 ? 'top-course' : '']"
    role="button"
    tabindex="0"
    @click="$emit('select', course)"
    @keydown.enter="$emit('select', course)"
    @keydown.space.prevent="$emit('select', course)"
  >
    <!-- ── 미니맵 ────────────────────────────────────────────────── -->
    <div v-if="miniMap" class="course-minimap" :style="miniMap.style">
      <span :class="['minimap-pin', `pin-${course.difficulty}`]"></span>
      <span class="minimap-attr">© OpenStreetMap</span>
    </div>
    <div v-else-if="course.lat && course.lng" class="course-minimap course-minimap--loading">
      <span class="minimap-placeholder">🗺️ 지도 로딩 중</span>
    </div>

    <!-- ── 1위 강조 배너 ──────────────────────────────────────────── -->
    <div v-if="rank === 1" class="top-banner">
      <span class="top-badge">🏆 오늘의 추천 1위</span>
      <span class="top-reason">{{ topReason }}</span>
    </div>

    <!-- ── 안전 등급 + 즐겨찾기 ──────────────────────────────────── -->
    <div class="course-meta">
      <div class="meta-left">
        <span v-if="rank && rank > 1" class="rank-badge">{{ rank }}위</span>
        <span :class="['safety-badge', safetyClass(course)]">
          {{ course.safety_label || fallbackSafetyLabel(course) }}
        </span>
      </div>
      <div class="meta-right">
        <span class="vulnerable-label">{{ course.safe_for_vulnerable ? '✅ 취약자 동반 가능' : '⚠️ 취약자 주의' }}</span>
        <button
          :class="['fav-heart-btn', { favorited: isFavorite }]"
          type="button"
          :title="isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가'"
          @click.stop="$emit('toggleFavorite', course)"
        >{{ isFavorite ? '♥' : '♡' }}</button>
      </div>
    </div>

    <!-- ── 코스명 ──────────────────────────────────────────────────── -->
    <h3>{{ course.name }}</h3>
    <p class="course-sub">{{ course.mountain }} · {{ course.distance_km }}km · 약 {{ durationLabel(course.duration_min) }}</p>

    <!-- ── 핵심 이유 칩 (새로 추가) ──────────────────────────────── -->
    <div v-if="reasonChips.length" class="reason-chips">
      <span v-for="chip in reasonChips" :key="chip.text" :class="['reason-chip', chip.type]">
        {{ chip.text }}
      </span>
    </div>

    <!-- ── 칩 메트릭 ──────────────────────────────────────────────── -->
    <div class="metric-row-compact">
      <span title="하산 여유">⏱️ {{ daylightLabel(course.daylight_margin_min) }}</span>
      <span title="접근 거리">📍 {{ course.distance_from_user_km ?? '-' }}km</span>
      <span title="데이터 출처">ℹ️ {{ course.sourceLabel || sourceLabel(course) }}</span>
    </div>

    <!-- ── 위험 요인 태그 ──────────────────────────────────────────── -->
    <div class="risk-tags">
      <span v-for="factor in (course.risk_factors || []).slice(0, 2)" :key="factor">{{ factor }}</span>
      <span v-if="!(course.risk_factors || []).length" class="safe-tag">위험 요인 없음</span>
    </div>

  </article>
</template>

<script setup>
import { ref, computed } from 'vue';
import {
  safetyClass,
  fallbackSafetyLabel,
  durationLabel,
  daylightLabel,
  sourceLabel,
} from '../utils/courseHelpers.js';

const props = defineProps({
  course: { type: Object, required: true },
  isSelected: { type: Boolean, default: false },
  rank: { type: Number, default: null },
  isFavorite: { type: Boolean, default: false },
});

defineEmits(['select', 'toggleFavorite']);

// ── OSM 타일 미니맵 ──────────────────────────────────────────────────────
const TILE_DISPLAY = 160; // 렌더 크기(px). 2×2 = 320px → 컨테이너를 항상 가득 덮음

const miniMap = computed(() => {
  const lat = props.course.lat;
  const lng = props.course.lng;
  if (!lat || !lng) return null;

  const zoom = 14;
  const n = Math.pow(2, zoom);
  const globalX = ((lng + 180) / 360) * n * 256;
  const sinLat = Math.sin((lat * Math.PI) / 180);
  const globalY = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * n * 256;
  const tx = Math.floor(globalX / 256);
  const ty = Math.floor(globalY / 256);

  // 타일 내 원본 픽셀(0-255)을 TILE_DISPLAY 스케일로 변환
  const px = Math.round((globalX % 256) * (TILE_DISPLAY / 256));
  const py = Math.round((globalY % 256) * (TILE_DISPLAY / 256));
  const td = TILE_DISPLAY;

  // 2×2 타일: 총 320×320px → 어떤 컨테이너 크기에서도 빈 틈 없음
  const tile = (x, y) => `url(https://tile.openstreetmap.org/${zoom}/${x}/${y}.png)`;
  const bgImage = [tile(tx, ty), tile(tx + 1, ty), tile(tx, ty + 1), tile(tx + 1, ty + 1)].join(', ');
  const pos = (dx, dy) => `calc(50% - ${px}px + ${dx}px) calc(50% - ${py}px + ${dy}px)`;
  const bgPosition = [pos(0, 0), pos(td, 0), pos(0, td), pos(td, td)].join(', ');

  return {
    style: {
      backgroundImage: bgImage,
      backgroundSize: `${td}px ${td}px`,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: bgPosition,
    },
  };
});

// ── 핵심 이유 칩 생성 ────────────────────────────────────────────────────
const reasonChips = computed(() => {
  const chips = [];
  const c = props.course;

  // 일몰 여유
  const daylight = c.daylight_margin_min;
  if (daylight !== null && daylight !== undefined) {
    if (daylight >= 120) {
      const h = Math.floor(daylight / 60);
      const m = daylight % 60;
      chips.push({ text: `🌅 일몰 여유 ${h}시간${m ? ` ${m}분` : ''}`, type: 'chip-green' });
    } else if (daylight >= 60) {
      chips.push({ text: `🌅 일몰 여유 ${daylight}분`, type: 'chip-yellow' });
    } else if (daylight > 0) {
      chips.push({ text: `⚠️ 일몰 여유 ${daylight}분`, type: 'chip-red' });
    }
  }

  // 난이도
  if (c.difficulty === 'easy') {
    chips.push({ text: '🟢 완만한 코스', type: 'chip-green' });
  } else if (c.difficulty === 'medium') {
    chips.push({ text: '🟡 중간 난이도', type: 'chip-yellow' });
  } else if (c.difficulty === 'hard') {
    chips.push({ text: '🔴 고난도 코스', type: 'chip-red' });
  }

  // 접근 거리
  const dist = c.distance_from_user_km;
  if (dist !== null && dist !== undefined) {
    if (dist <= 10) chips.push({ text: `📍 가까운 위치 ${dist}km`, type: 'chip-green' });
    else if (dist <= 25) chips.push({ text: `📍 ${dist}km 거리`, type: 'chip-neutral' });
  }

  return chips.slice(0, 3);
});

// ── 1위 코스 한 줄 이유 ──────────────────────────────────────────────────
const topReason = computed(() => {
  const c = props.course;
  const parts = [];

  const daylight = c.daylight_margin_min;
  if (daylight >= 120) {
    parts.push(`일몰 전 ${Math.floor(daylight / 60)}시간 여유`);
  }

  if (c.difficulty === 'easy') parts.push('완만한 경사');
  else if (c.difficulty === 'medium') parts.push('적당한 운동량');

  const dist = c.distance_from_user_km;
  if (dist !== null && dist !== undefined && dist <= 15) parts.push(`${dist}km 거리`);

  if (c.safe_for_vulnerable) parts.push('취약자 동반 적합');

  return parts.length ? parts.join(' · ') : '현재 조건 최적 코스';
});
</script>
