<template>
  <section class="screen-stack chat-layout ai-guide-page ai-guide-classic">
    <section class="chat-hero">
      <div class="chat-hero-content">
        <h1 class="chat-hero-title">Ola AI Guide</h1>
        <p class="chat-hero-copy">날씨, 안전, 코스 준비물까지 지금 상황에 맞춰 빠르게 안내해드릴게요.</p>
      </div>
    </section>

    <div class="chat-shell">
      <div class="chat-header">
        <div class="chat-header-left">
          <div class="chat-avatar-wrap">
            <span class="chat-avatar-emoji">Ola</span>
            <span class="chat-online-dot"></span>
          </div>
          <div>
            <h2 class="chat-title">Ola 안전 도우미</h2>
            <p class="chat-subtitle">산행 AI · 실시간 응답 중</p>
          </div>
        </div>

        <div class="chat-header-right">
          <div v-if="selectedMountain" class="chat-mountain-pill">
            <span class="chat-mountain-dot"></span>
            {{ selectedMountain.name }}
          </div>
          <button class="chat-clear-btn" type="button" @click="clearChat" title="대화 초기화">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.5"/></svg>
          </button>
        </div>
      </div>

      <div ref="scrollEl" class="chat-messages">
        <div v-if="!chatMessages.length" class="chat-welcome">
          <div class="chat-suggestion-grid">
            <button
              v-for="(item, i) in SUGGESTIONS"
              :key="i"
              class="chat-sug-card"
              :class="item.tone"
              type="button"
              @click="submit(item.text)"
            >
              <span class="sug-icon">{{ item.icon }}</span>
              <span class="sug-copy">
                <strong>{{ item.title }}</strong>
              </span>
              <span class="sug-arrow">›</span>
            </button>
          </div>
        </div>

        <template v-for="(msg, i) in chatMessages" :key="i">
          <div v-if="i === 0" class="chat-date-divider">
            <span>{{ formatDate(msg.ts) }}</span>
          </div>

          <div :class="['chat-bubble-row', msg.role === 'user' ? 'row-user' : 'row-ai']">
            <div v-if="msg.role === 'assistant'" class="bubble-avatar-wrap">
              <span class="bubble-avatar-emoji">Ola</span>
            </div>
            <div class="bubble-col">
              <div :class="['chat-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
                {{ msg.content }}
              </div>
              <span class="bubble-time">{{ formatTime(msg.ts) }}</span>
            </div>
          </div>
        </template>

        <div v-if="chatLoading" class="chat-bubble-row row-ai">
          <div class="bubble-avatar-wrap">
            <span class="bubble-avatar-emoji">Ola</span>
          </div>
          <div class="bubble-col">
            <div class="chat-bubble bubble-ai bubble-loading">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <p v-if="chatError" class="chat-error">⚠️ {{ chatError }}</p>

      <div class="chat-input-wrap">
        <form class="chat-input-form" @submit.prevent="handleSubmit">
          <textarea
            ref="inputEl"
            v-model="input"
            class="chat-input"
            placeholder="산행 안전에 대해 물어보세요..."
            :disabled="chatLoading"
            maxlength="300"
            rows="1"
            @keydown.enter.exact.prevent="handleSubmit"
            @input="autoResize"
          ></textarea>
          <button class="chat-send-btn" type="submit" :disabled="!input.trim() || chatLoading" aria-label="전송">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>
        <p class="chat-input-hint">Enter 전송 · Shift+Enter 줄바꿈</p>
      </div>

      <section class="chat-recent-section" aria-label="자주 묻는 질문">
        <div class="chat-recent-head">
          <h3>자주 묻는 질문</h3>
        </div>
        <div class="chat-recent-list">
          <button
            v-for="question in RECENT_QUESTIONS"
            :key="question"
            class="chat-recent-chip"
            type="button"
            @click="submit(question)"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="16.5" y1="16.5" x2="21" y2="21"></line>
            </svg>
            <span>{{ question }}</span>
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import { chatMessages, chatLoading, chatError, sendMessage, clearChat } from '../composables/useChat.js';
import { selectedMountain } from '../composables/useGuide.js';

const input = ref('');
const scrollEl = ref(null);
const inputEl = ref(null);

const SUGGESTIONS = [
  {
    icon: '🌤️',
    title: '지금 이 산 가도 괜찮을까요?',
    text: '지금 이 산 가도 괜찮을까요?',
    tone: 'tone-weather',
  },
  {
    icon: '⛰️',
    title: '초보자가 가기 좋은 코스는?',
    text: '초보자가 가기 좋은 코스 추천해줘',
    tone: 'tone-mountain',
  },
  {
    icon: '🌧️',
    title: '등산 중 갑자기 비가 오면 어떻게 해야 하나요?',
    text: '등산 중 갑자기 비가 오면 어떻게 해야 하나요?',
    tone: 'tone-rain',
  },
  {
    icon: '🎒',
    title: '산행 전 챙겨야 할 필수 장비는?',
    text: '산행 전 챙겨야 할 필수 장비 알려줘',
    tone: 'tone-gear',
  },
];

const RECENT_QUESTIONS = [
  '북한산 둘레길 3시간 코스 추천',
  '비 온 뒤 등산 괜찮을까?',
  '여름철 저체온증 위험은?',
  '초보자가 가기 좋은 계곡 코스',
];

function formatDate(ts) {
  if (!ts) return '';
  return new Date(ts).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' });
}

function formatTime(ts) {
  if (!ts) return '';
  return new Date(ts).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false });
}

async function submit(text) {
  const msg = text || input.value;
  if (!msg.trim()) return;
  input.value = '';
  if (inputEl.value) inputEl.value.style.height = 'auto';
  await sendMessage(msg);
}

function handleSubmit() {
  submit(input.value);
}

function autoResize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

watch(chatMessages, async () => {
  await nextTick();
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
}, { deep: true });
</script>
