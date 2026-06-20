<template>
  <!-- 플로팅 토글 버튼 -->
  <button
    class="cw-fab"
    :class="{ open: isOpen }"
    type="button"
    aria-label="AI 도우미 열기"
    @click="toggle"
  >
    <span v-if="!isOpen" class="cw-fab-icon">🤖</span>
    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
    <span v-if="unread && !isOpen" class="cw-badge">{{ unread }}</span>
  </button>

  <!-- 채팅 패널 -->
  <Transition name="cw-slide">
    <div v-if="isOpen" class="cw-panel">
      <!-- 헤더 -->
      <div class="cw-header">
        <span class="cw-header-avatar">🤖</span>
        <div class="cw-header-info">
          <p class="cw-eyebrow">AI Assistant</p>
          <h3>올라 안전 도우미</h3>
        </div>
        <button class="cw-clear-btn" type="button" @click="clearChat">초기화</button>
      </div>

      <!-- 메시지 목록 -->
      <div ref="scrollEl" class="cw-messages">
        <div v-if="!chatMessages.length" class="cw-welcome">
          <p class="cw-welcome-text">산행 안전, 코스, 날씨, 장비에 대해 무엇이든 물어보세요.</p>
          <div class="cw-suggestions">
            <button
              v-for="q in SUGGESTED" :key="q"
              class="cw-suggestion-btn" type="button"
              @click="submit(q)"
            >{{ q }}</button>
          </div>
        </div>

        <div
          v-for="(msg, i) in chatMessages" :key="i"
          :class="['cw-bubble-row', msg.role === 'user' ? 'cw-row-user' : 'cw-row-ai']"
        >
          <span v-if="msg.role === 'assistant'" class="cw-bubble-avatar">🤖</span>
          <div :class="['cw-bubble', msg.role === 'user' ? 'cw-bubble-user' : 'cw-bubble-ai']">
            {{ msg.content }}
          </div>
        </div>

        <div v-if="chatLoading" class="cw-bubble-row cw-row-ai">
          <span class="cw-bubble-avatar">🤖</span>
          <div class="cw-bubble cw-bubble-ai cw-bubble-loading">
            <span class="cw-dot"></span><span class="cw-dot"></span><span class="cw-dot"></span>
          </div>
        </div>
      </div>

      <!-- 오류 -->
      <p v-if="chatError" class="cw-error">{{ chatError }}</p>

      <!-- 입력창 -->
      <form class="cw-input-row" @submit.prevent="handleSubmit">
        <input
          ref="inputEl"
          v-model="input"
          class="cw-input"
          type="text"
          placeholder="질문을 입력하세요…"
          :disabled="chatLoading"
          maxlength="200"
          autocomplete="off"
        />
        <button class="cw-send-btn" type="submit" :disabled="!input.trim() || chatLoading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </form>
    </div>
  </Transition>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue';
import { chatMessages, chatLoading, chatError, SUGGESTED, sendMessage, clearChat } from '../composables/useChat.js';

const isOpen = ref(false);
const input = ref('');
const scrollEl = ref(null);
const inputEl = ref(null);
const unread = ref(0);

function toggle() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    unread.value = 0;
    nextTick(() => inputEl.value?.focus());
  }
}

async function submit(text) {
  const msg = text || input.value;
  if (!msg.trim()) return;
  input.value = '';
  await sendMessage(msg);
}

function handleSubmit() {
  submit(input.value);
}

watch(chatMessages, async () => {
  await nextTick();
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
  if (!isOpen.value) unread.value++;
}, { deep: true });
</script>
