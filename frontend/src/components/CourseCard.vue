<template>
  <article
    :class="['course-card', isSelected ? 'selected' : '', rank === 1 ? 'top-course' : '']"
    role="button"
    tabindex="0"
    @click="$emit('select', course)"
    @keydown.enter="$emit('select', course)"
    @keydown.space.prevent="$emit('select', course)"
  >
    <!-- ── 1위 강조 배너 ──────────────────────────────────────────── -->
    <div v-if="rank === 1" class="top-banner">
      <span class="top-badge">🏆 오늘의 추천 1위</span>
      <span class="top-reason">{{ topReason }}</span>
    </div>

    <!-- ── 안전 등급 + 취약자 동반 여부 ──────────────────────────── -->
    <div class="course-meta">
      <div class="meta-left">
        <span v-if="rank && rank > 1" class="rank-badge">{{ rank }}위</span>
        <span :class="['safety-badge', safetyClass(course)]">
          {{ course.safety_label || fallbackSafetyLabel(course) }}
        </span>
      </div>
      <span class="vulnerable-label">{{ course.safe_for_vulnerable ? '✅ 취약자 동반 가능' : '⚠️ 취약자 주의' }}</span>
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

    <!-- ── 점수 상세 토글 ─────────────────────────────────────────── -->
    <div v-if="course.scores" class="score-section">
      <button class="score-toggle-btn" type="button" @click.stop="showScores = !showScores">
        <span>점수 상세 보기</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path :d="showScores ? 'M5 15l7-7 7 7' : 'M5 9l7 7 7-7'" />
        </svg>
      </button>
      <div v-if="showScores" class="score-bars">
        <div v-for="(value, key) in course.scores" :key="key" class="score-bar-row">
          <span class="score-bar-label">{{ scoreLabel(key) }}</span>
          <div class="score-bar-track">
            <div
              class="score-bar-fill"
              :class="scoreBarClass(value)"
              :style="{ width: value + '%' }"
            ></div>
          </div>
          <span class="score-bar-value">{{ Math.round(value) }}</span>
        </div>
      </div>
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
  scoreLabel,
  scoreBarClass,
} from '../utils/courseHelpers.js';

const props = defineProps({
  course: { type: Object, required: true },
  isSelected: { type: Boolean, default: false },
  rank: { type: Number, default: null },
});

defineEmits(['select']);

const showScores = ref(false);

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
