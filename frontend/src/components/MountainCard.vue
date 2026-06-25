<template>
  <article
    :class="['mountain-card', isSelected ? 'selected' : '', rank === 1 ? 'top-mountain' : '']"
    role="button"
    tabindex="0"
    @click="$emit('select', mountain)"
    @keydown.enter="$emit('select', mountain)"
    @keydown.space.prevent="$emit('select', mountain)"
  >
    <div v-if="rank === 1" class="mc-top-banner">
      <span class="mc-top-badge">🏆 오늘의 추천 1위</span>
    </div>

    <span v-else-if="rank" class="rank-badge">{{ rank }}위</span>

    <div class="mc-card-body">
      <div class="mc-info">
        <div class="mc-info-head">
          <div class="mc-title-area">
            <h3 class="mc-name">{{ mountain.name }}</h3>
            <p class="mc-region">{{ mountain.region }}</p>
          </div>

          <div class="mc-meta-right">
            <button
              :class="['mc-fav-btn', { favorited: isFavorite }]"
              type="button"
              :title="isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가'"
              @click.stop="$emit('toggleFavorite', mountain)"
            >{{ isFavorite ? '♥' : '♡' }}</button>
          </div>
        </div>

        <div class="mc-badges">
          <span :class="['badge', diffClass]">{{ diffIcon }} {{ diffLabel }}</span>
          <span class="badge altitude">{{ elevationLabel }}</span>
          <span class="badge info">{{ timeLabel }}</span>
          <span class="badge info">탐방로 {{ trailCountLabel }}</span>
        </div>

        <p v-if="mountain.sunset_note" :class="['mc-sunset-note', sunsetNoteClass]">
          <span aria-hidden="true">⚠️</span>
          {{ cleanSunsetNote }}
        </p>

        <div class="mc-highlights">
          <span v-for="tag in displayTags" :key="tag" class="mc-tag">
            #{{ tag }}
          </span>
        </div>
      </div>
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
const DIFF_ICON = { easy: '▲', medium: '▲', hard: '▲' };

const diffLabel = computed(() => DIFF_LABEL[props.mountain.difficulty] || '추천');
const diffClass = computed(() => DIFF_CLASS[props.mountain.difficulty] || 'easy');
const diffIcon = computed(() => DIFF_ICON[props.mountain.difficulty] || '▲');

const elevationLabel = computed(() => {
  const elevation = props.mountain.elevation_m;
  return elevation || elevation === 0 ? `${elevation}m` : '고도 미상';
});

const timeLabel = computed(() => {
  const lo = Number(props.mountain.walk_time_min || 0);
  const hi = Number(props.mountain.walk_time_max || 0);
  const fmt = (m) => {
    if (!m) return '-';
    const h = Math.floor(m / 60);
    const min = m % 60;
    if (!h) return `${min}분`;
    return `${h}시간${min ? ` ${min}분` : ''}`;
  };
  return `${fmt(lo)} ~ ${fmt(hi)}`;
});

const trailCountLabel = computed(() => `${props.mountain.trail_count ?? 0}개`);

const distanceLabel = computed(() => {
  const distance = props.mountain.distance_from_user_km;
  if (distance == null || distance === '') return '';
  const value = Number(distance);
  if (!Number.isFinite(value)) return `${distance}km`;
  return `${Number.isInteger(value) ? value : value.toFixed(1)}km`;
});

const cleanSunsetNote = computed(() =>
  String(props.mountain.sunset_note || '').replace(/^[⚠️\s]+/, ''),
);

const sunsetNoteClass = computed(() => {
  const note = props.mountain.sunset_note || '';
  return /초과|주의|위험|부족/.test(note) ? 'sunset-warn' : 'sunset-ok';
});

const displayTags = computed(() => {
  const tags = Array.isArray(props.mountain.tags) ? props.mountain.tags : [];
  if (tags.length) return tags.slice(0, 5);
  const highlights = Array.isArray(props.mountain.highlights) ? props.mountain.highlights : [];
  return highlights.slice(0, 5);
});
</script>
