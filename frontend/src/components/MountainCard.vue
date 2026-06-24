<template>
  <article
    :class="['mountain-card', isSelected ? 'selected' : '', rank === 1 ? 'top-mountain' : '']"
    role="button"
    tabindex="0"
    @click="$emit('select', mountain)"
    @keydown.enter="$emit('select', mountain)"
    @keydown.space.prevent="$emit('select', mountain)"
  >
    <!-- 1위 배너 -->
    <div v-if="rank === 1" class="mc-top-banner">
      <span class="mc-top-badge">🏆 오늘의 추천 1위</span>
      <span class="mc-top-reason">{{ topReason }}</span>
    </div>

    <!-- 등급 + 순위 -->
    <div class="mc-meta">
      <div class="mc-meta-left">
        <span v-if="rank && rank > 1" class="rank-badge">{{ rank }}위</span>
        <span :class="['safety-badge', safetyColorClass]">{{ mountain.safety_label }}</span>
        <span v-if="mountain.national_park" class="mc-np-badge">국립공원</span>
      </div>
      <div class="mc-meta-right">
        <span v-if="mountain.distance_from_user_km != null" class="mc-dist">
          📍 {{ mountain.distance_from_user_km }}km
        </span>
        <button
          :class="['mc-fav-btn', { favorited: isFavorite }]"
          type="button"
          :title="isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가'"
          @click.stop="$emit('toggleFavorite', mountain)"
        >{{ isFavorite ? '♥' : '♡' }}</button>
      </div>
    </div>

    <!-- 산 이름 -->
    <h3 class="mc-name">{{ mountain.name }}</h3>
    <p class="mc-region">{{ mountain.region }}</p>

    <!-- 핵심 수치 배지 -->
    <div class="mc-badges">
      <span :class="['badge', diffClass]">{{ diffLabel }}</span>
      <span class="badge info">{{ mountain.elevation_m }}m</span>
      <span class="badge info">{{ timeLabel }}</span>
      <span class="badge info">탐방로 {{ mountain.trail_count }}개</span>
    </div>

    <!-- 일몰 여유 -->
    <p v-if="mountain.sunset_note" :class="['mc-sunset-note', sunsetNoteClass]">
      🌇 {{ mountain.sunset_note }}
    </p>

    <!-- 매력 태그 (있으면 우선) / 없으면 하이라이트 -->
    <div class="mc-highlights">
      <template v-if="(mountain.tags || []).length">
        <span v-for="tag in mountain.tags.slice(0, 4)" :key="tag" class="mc-tag mc-tag-appeal">
          {{ TAG_ICONS[tag] || '' }} {{ tag }}
        </span>
      </template>
      <template v-else>
        <span v-for="h in (mountain.highlights || []).slice(0, 3)" :key="h" class="mc-tag">{{ h }}</span>
      </template>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  mountain: { type: Object, required: true },
  isSelected: { type: Boolean, default: false },
  rank: { type: Number, default: null },
  isFavorite: { type: Boolean, default: false },
});

defineEmits(['select', 'toggleFavorite']);

const DIFF_LABEL = { easy: '초급', medium: '중급', hard: '고급' };
const DIFF_CLASS = { easy: 'easy', medium: 'medium', hard: 'hard' };

const TAG_ICONS = {
  '조망': '🗻', '계곡': '💧', '단풍': '🍂', '야생화': '🌸',
  '역사문화': '🏯', '암릉': '🪨', '숲치유': '🌲', '일출·일몰': '🌅',
  '설경': '❄️', '호수·강뷰': '🌊', '억새': '🌾', '철쭉': '🌺',
  '야경': '🌃', '능선종주': '🏔', '100대명산': '🏆',
};

const diffLabel = computed(() => DIFF_LABEL[props.mountain.difficulty] || '');
const diffClass = computed(() => DIFF_CLASS[props.mountain.difficulty] || '');

const safetyColorClass = computed(() => props.mountain.safety_class || 'caution');

const timeLabel = computed(() => {
  const lo = props.mountain.walk_time_min;
  const hi = props.mountain.walk_time_max;
  const fmt = (m) => m >= 60 ? `${Math.floor(m / 60)}시간${m % 60 ? ' ' + (m % 60) + '분' : ''}` : `${m}분`;
  return `${fmt(lo)} ~ ${fmt(hi)}`;
});

const topReason = computed(() => {
  const m = props.mountain;
  const parts = [];
  if (m.difficulty === 'easy') parts.push('완만한 코스');
  if (m.national_park) parts.push('국립공원');
  if (m.distance_from_user_km != null && m.distance_from_user_km <= 50) parts.push(`${m.distance_from_user_km}km 거리`);
  if ((m.companion_fit || []).includes('vulnerable')) parts.push('취약자 동반 가능');
  return parts.join(' · ') || '현재 조건 최적 산';
});

const sunsetNoteClass = computed(() =>
  (props.mountain.sunset_note || '').startsWith('⚠️') ? 'sunset-warn' : 'sunset-ok',
);
</script>
