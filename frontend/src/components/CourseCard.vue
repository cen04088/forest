<template>
  <article
    :class="['course-card', isSelected ? 'selected' : '']"
    role="button"
    tabindex="0"
    @click="$emit('select', course)"
    @keydown.enter="$emit('select', course)"
    @keydown.space.prevent="$emit('select', course)"
  >
    <!-- 안전 등급 + 취약자 동반 여부 -->
    <div class="course-meta">
      <span :class="['safety-badge', safetyClass(course)]">
        {{ course.safety_label || fallbackSafetyLabel(course) }}
      </span>
      <span>{{ course.safe_for_vulnerable ? '취약자 동반 가능' : '취약자 주의' }}</span>
    </div>

    <!-- 코스명 -->
    <h3>{{ course.name }}</h3>

    <!-- 기본 정보 한 줄 -->
    <p>{{ course.mountain }} · {{ course.distance_km }}km · 약 {{ durationLabel(course.duration_min) }}</p>

    <!-- 칩 메트릭 -->
    <div class="metric-row-compact">
      <span title="하산 여유">⏱️ {{ daylightLabel(course.daylight_margin_min) }}</span>
      <span title="접근 거리">📍 {{ course.distance_from_user_km ?? '-' }}km</span>
      <span title="데이터 출처">ℹ️ {{ course.sourceLabel || sourceLabel(course) }}</span>
    </div>

    <!-- 위험 요인 태그 -->
    <div class="risk-tags">
      <span v-for="factor in (course.risk_factors || []).slice(0, 3)" :key="factor">{{ factor }}</span>
      <span v-if="!(course.risk_factors || []).length">위험 요인 없음</span>
    </div>

    <!-- 점수 상세 토글 -->
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
import { ref } from 'vue';
import {
  safetyClass,
  fallbackSafetyLabel,
  durationLabel,
  daylightLabel,
  sourceLabel,
  scoreLabel,
  scoreBarClass,
} from '../utils/courseHelpers.js';

defineProps({
  course: { type: Object, required: true },
  isSelected: { type: Boolean, default: false },
});

defineEmits(['select']);

const showScores = ref(false);
</script>
