<template>
  <section class="screen-stack chat-layout">
    <div class="chat-shell">

      <!-- 헤더 -->
      <div class="chat-header">
        <div class="chat-header-left">
          <div class="chat-avatar-wrap">
            <span class="chat-avatar-emoji">🌲</span>
            <span class="chat-online-dot"></span>
          </div>
          <div>
            <h2 class="chat-title">올라 안전 도우미</h2>
            <p class="chat-subtitle">산행 AI · 항상 응답 중</p>
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

      <!-- 메시지 영역 -->
      <div ref="scrollEl" class="chat-messages">

        <!-- 웰컴 -->
        <div v-if="!chatMessages.length" class="chat-welcome">
          <div class="chat-welcome-top">
            <div class="chat-welcome-avatar">🌲</div>
            <h3 class="chat-welcome-title">무엇을 도와드릴까요?</h3>
            <p class="chat-welcome-desc">
              산행 안전 · 날씨 대응 · 장비 · 응급처치 등<br>
              등산에 관한 모든 것을 물어보세요
              <span v-if="selectedMountain" class="chat-welcome-mountain">
                <br><strong>{{ selectedMountain.name }}</strong> 맞춤 정보를 드려요
              </span>
            </p>
          </div>

          <div class="chat-suggestion-grid">
            <button
              v-for="(item, i) in SUGGESTIONS" :key="i"
              class="chat-sug-card"
              :style="{ '--sug-color': item.color }"
              type="button"
              @click="submit(item.text)"
            >
              <span class="sug-icon">{{ item.icon }}</span>
              <span class="sug-text">{{ item.text }}</span>
            </button>
          </div>
        </div>

        <!-- 대화 버블 -->
        <template v-for="(msg, i) in chatMessages" :key="i">
          <!-- 날짜 구분선 (첫 메시지에만) -->
          <div v-if="i === 0" class="chat-date-divider">
            <span>{{ formatDate(msg.ts) }}</span>
          </div>

          <div :class="['chat-bubble-row', msg.role === 'user' ? 'row-user' : 'row-ai']">
            <div v-if="msg.role === 'assistant'" class="bubble-avatar-wrap">
              <span class="bubble-avatar-emoji">🌲</span>
            </div>
            <div class="bubble-col">
              <div :class="['chat-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
                {{ msg.content }}
              </div>
              <span class="bubble-time">{{ formatTime(msg.ts) }}</span>
            </div>
          </div>
        </template>

        <!-- 타이핑 -->
        <div v-if="chatLoading" class="chat-bubble-row row-ai">
          <div class="bubble-avatar-wrap">
            <span class="bubble-avatar-emoji">🌲</span>
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

      <!-- 오류 -->
      <p v-if="chatError" class="chat-error">⚠️ {{ chatError }}</p>

      <!-- 입력창 -->
      <div class="chat-input-wrap">
        <form class="chat-input-form" @submit.prevent="handleSubmit">
          <textarea
            ref="inputEl"
            v-model="input"
            class="chat-input"
            placeholder="산행 안전에 대해 물어보세요…"
            :disabled="chatLoading"
            maxlength="300"
            rows="1"
            @keydown.enter.exact.prevent="handleSubmit"
            @input="autoResize"
          ></textarea>
          <button class="chat-send-btn" type="submit" :disabled="!input.trim() || chatLoading">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>
        <p class="chat-input-hint">Enter 전송 · Shift+Enter 줄바꿈</p>
      </div>

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
  { icon: '🌤', text: '지금 이 산 가도 괜찮을까요?',        color: '#3b82f6' },
  { icon: '🗺', text: '초보자가 가기 좋은 코스는?',          color: '#8b5cf6' },
  { icon: '🌧', text: '등산 중 갑자기 비가 오면 어떻게 해야 하나요?', color: '#06b6d4' },
  { icon: '🎒', text: '산행 전 챙겨야 할 필수 장비는?',      color: '#f59e0b' },
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

function handleSubmit() { submit(input.value); }

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
