<template>
  <section
    class="live-safety-hero"
    aria-label="라이브 안전현황과 테마별 산 추천"
  >
    <div
      class="live-safety-strip"
      @mouseenter="pause"
      @mouseleave="resume"
      @focusin="pause"
      @focusout="resume"
    >
      <span class="live-safety-label">
        <i aria-hidden="true"></i>
        LIVE 안전현황
      </span>
      <div class="live-safety-marquee" :class="{ paused: isPaused }">
        <div class="live-safety-track">
          <span
            v-for="item in marqueeItems"
            :key="item.loopId"
            class="live-safety-item"
            :class="{ 'cycle-end': item.isCycleEnd }"
          >
            <span class="live-safety-dot" aria-hidden="true"></span>
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </span>
        </div>
      </div>
    </div>

    <div class="theme-carousel">
      <div class="theme-card-group">
        <!-- 메인 슬라이드 -->
        <button
          class="theme-slide"
          :class="`tone-${activeSlide.tone}`"
          :style="activeSlide.image ? { backgroundImage: `linear-gradient(to top, rgba(0,0,0,0.76) 0%, rgba(0,0,0,0.18) 60%, transparent 100%), url('${activeSlide.image}')` } : undefined"
          type="button"
          @click="emitTheme(activeSlide)"
        >
          <span class="theme-label">{{ activeSlide.label }}</span>
          <strong class="theme-title">
            <template v-for="(line, lineIndex) in titleLines(activeSlide.title)" :key="`${activeSlide.id}-title-${lineIndex}`">
              <span>{{ line }}</span>
              <br v-if="lineIndex < titleLines(activeSlide.title).length - 1" />
            </template>
          </strong>
          <span class="theme-subtitle">{{ activeSlide.subtitle }}</span>
        </button>

      </div>
    </div>

    <!-- 도트 네비게이션 (모바일 전용) -->
    <div class="theme-dots" role="tablist" aria-label="테마 슬라이드 선택">
      <button
        v-for="(slide, index) in slides"
        :key="slide.id"
        type="button"
        :class="['theme-dot', { active: index === activeIndex }]"
        :aria-label="`${slide.label} 보기`"
        @click="setSlide(index)"
      ></button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';

const props = defineProps({
  safetyItems: {
    type: Array,
    default: () => [],
  },
  slides: {
    type: Array,
    default: () => [],
  },
  intervalMs: {
    type: Number,
    default: 4000,
  },
});

const emit = defineEmits(['select-theme']);

const activeIndex = ref(0);
const isPaused = ref(false);
const reduceMotion = ref(false);
let timerId = null;
let motionQuery = null;

const activeSlide = computed(() => props.slides[activeIndex.value] || {
  id: 'empty',
  tone: 'green',
  label: '',
  title: '',
  subtitle: '',
  chips: [],
});

const marqueeItems = computed(() => {
  const source = props.safetyItems.length ? props.safetyItems : [];
  return [...source, ...source].map((item, index) => ({
    ...item,
    loopId: `${item.id || item.label}-${index}`,
    isCycleEnd: source.length > 0 && (index + 1) % source.length === 0,
  }));
});

function setSlide(index) {
  if (!props.slides.length) return;
  activeIndex.value = (index + props.slides.length) % props.slides.length;
  restart();
}

function pause() {
  isPaused.value = true;
  stop();
}

function resume() {
  isPaused.value = false;
  start();
}

function emitTheme(slide) {
  emit('select-theme', slide);
}

function titleLines(title) {
  if (!title || !title.includes(',')) return [title || ''];
  const [first, ...rest] = title.split(',');
  return [first.trim() + ',', rest.join(',').trim()].filter(Boolean);
}

function start() {
  stop();
  if (reduceMotion.value || isPaused.value || props.slides.length < 2) return;
  timerId = window.setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % props.slides.length;
  }, props.intervalMs);
}

function stop() {
  if (!timerId) return;
  window.clearInterval(timerId);
  timerId = null;
}

function restart() {
  start();
}

function syncMotionPreference(event) {
  reduceMotion.value = !!event.matches;
  if (reduceMotion.value) stop();
  else start();
}

onMounted(() => {
  motionQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)') || null;
  reduceMotion.value = !!motionQuery?.matches;
  motionQuery?.addEventListener?.('change', syncMotionPreference);
  start();
});

onUnmounted(() => {
  stop();
  motionQuery?.removeEventListener?.('change', syncMotionPreference);
});
</script>
