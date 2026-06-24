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
          <div class="chat-header-info">
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

        <!-- 웰컴 카드 -->
        <div v-if="!chatMessages.length" class="chat-welcome">
          <div class="chat-welcome-hero">
            <div class="chat-welcome-avatar">🌲</div>
            <h3 class="chat-welcome-title">안녕하세요!</h3>
            <p class="chat-welcome-desc">
              산행 안전 · 날씨 · 장비 · 응급 처치<br>
              무엇이든 물어보세요
              <span v-if="selectedMountain" class="chat-welcome-mountain">— <strong>{{ selectedMountain.name }}</strong> 맞춤 정보도 드려요</span>
            </p>
          </div>

          <p class="chat-suggestions-label">자주 묻는 질문</p>
          <div class="chat-suggestions">
            <button
              v-for="q in SUGGESTED" :key="q"
              class="chat-suggestion-btn" type="button"
              @click="submit(q)"
            >
              <span class="suggestion-icon">{{ suggestionIcon(q) }}</span>
              <span>{{ q }}</span>
            </button>
          </div>
        </div>

        <!-- 대화 버블 -->
        <div
          v-for="(msg, i) in chatMessages" :key="i"
          :class="['chat-bubble-row', msg.role === 'user' ? 'row-user' : 'row-ai']"
        >
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

        <!-- 타이핑 표시 -->
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
            <span class="bubble-time">분석 중…</span>
          </div>
        </div>
      </div>

      <!-- 오류 -->
      <p v-if="chatError" class="chat-error">⚠️ {{ chatError }}</p>

      <!-- 입력창 -->
      <div class="chat-input-wrap">
        <form class="chat-input-row" @submit.prevent="handleSubmit">
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
        <p class="chat-input-hint">Enter로 전송 · Shift+Enter로 줄바꿈</p>
      </div>

    </div>
  </section>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import { chatMessages, chatLoading, chatError, SUGGESTED, sendMessage, clearChat } from '../composables/useChat.js';
import { selectedMountain } from '../composables/useGuide.js';

const input = ref('');
const scrollEl = ref(null);
const inputEl = ref(null);

const _iconMap = {
  '비': '🌧', '눈': '❄️', '날씨': '⛅', '기온': '🌡',
  '안전': '🦺', '응급': '🚑', '조난': '🆘', '119': '📞',
  '장비': '🎒', '등산화': '👟', '배낭': '🎒',
  '코스': '🗺', '난이도': '📊', '거리': '📏',
  '산불': '🔥', '산사태': '🌊', '낙뢰': '⚡',
};
function suggestionIcon(q) {
  for (const [k, v] of Object.entries(_iconMap)) {
    if (q.includes(k)) return v;
  }
  return '💬';
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false });
}

async function submit(text) {
  const msg = text || input.value;
  if (!msg.trim()) return;
  input.value = '';
  if (inputEl.value) { inputEl.value.style.height = 'auto'; }
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
