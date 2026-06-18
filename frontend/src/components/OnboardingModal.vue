<template>
  <div class="onboarding-overlay" @click.self="close">
    <div class="onboarding-modal" role="dialog" aria-modal="true" aria-label="올라 앱 소개">

      <div class="onboarding-steps">
        <div
          v-for="(step, i) in steps"
          :key="i"
          :class="['onboarding-step', { active: i === current }]"
        >
          <div class="onboarding-icon">{{ step.icon }}</div>
          <h2 class="onboarding-title">{{ step.title }}</h2>
          <p class="onboarding-desc">{{ step.desc }}</p>
        </div>
      </div>

      <div class="onboarding-dots">
        <button
          v-for="(_, i) in steps" :key="i"
          :class="['dot', { active: i === current }]"
          type="button"
          :aria-label="`${i + 1}번째 슬라이드`"
          @click="current = i"
        />
      </div>

      <div class="onboarding-actions">
        <button v-if="current < steps.length - 1" class="primary-btn" type="button" @click="current++">
          다음
        </button>
        <button v-else class="primary-btn" type="button" @click="close">
          시작하기
        </button>
        <button class="onboarding-skip" type="button" @click="close">건너뛰기</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['close']);
const current = ref(0);

const steps = [
  {
    icon: '🏔️',
    title: '나에게 맞는 산을 찾아요',
    desc: '날짜·시간·동반자 조건을 입력하면 날씨, 산불, 재난 데이터를 종합해 지금 가기 좋은 산을 추천해 드립니다.',
  },
  {
    icon: '📍',
    title: '보호자와 위치를 공유해요',
    desc: '산행을 시작하면 6자리 코드가 생성됩니다. 보호자가 코드를 입력하면 실시간으로 위치를 확인할 수 있어요.',
  },
  {
    icon: '🔔',
    title: '보호자에게 자동으로 알려드려요',
    desc: '위치 업데이트가 10분 이상 끊기면 보호자 화면에 경고가 표시됩니다. 산행 중 만일을 대비한 안전망입니다.',
  },
];

function close() {
  localStorage.setItem('ollaOnboarded', '1');
  emit('close');
}
</script>
