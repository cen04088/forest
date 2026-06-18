<template>
  <section class="screen-stack chat-layout">
    <div class="chat-shell">

      <!-- 헤더 -->
      <div class="chat-header">
        <div class="chat-header-info">
          <span class="chat-avatar">🤖</span>
          <div>
            <p class="eyebrow">AI Assistant</p>
            <h2>올라 안전 도우미</h2>
          </div>
        </div>
        <div class="chat-context-badge" v-if="selectedMountain">
          <span>📍 {{ selectedMountain.name }}</span>
        </div>
        <button class="outline-btn" style="font-size:12px;padding:5px 10px" type="button" @click="clearChat">
          초기화
        </button>
      </div>

      <!-- 메시지 목록 -->
      <div ref="scrollEl" class="chat-messages">

        <!-- 시작 안내 -->
        <div v-if="!chatMessages.length" class="chat-welcome">
          <p class="chat-welcome-text">
            산행 안전, 코스, 날씨 대응, 장비에 대해 무엇이든 물어보세요.
            <span v-if="selectedMountain"> <strong>{{ selectedMountain.name }}</strong> 관련 질문에 더 정확하게 답해드려요.</span>
          </p>
          <div class="chat-suggestions">
            <button
              v-for="q in SUGGESTED" :key="q"
              class="chat-suggestion-btn" type="button"
              @click="submit(q)"
            >{{ q }}</button>
          </div>
        </div>

        <!-- 대화 -->
        <div
          v-for="(msg, i) in chatMessages" :key="i"
          :class="['chat-bubble-row', msg.role === 'user' ? 'row-user' : 'row-ai']"
        >
          <span v-if="msg.role === 'assistant'" class="bubble-avatar">🤖</span>
          <div :class="['chat-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-ai']">
            {{ msg.content }}
          </div>
        </div>

        <!-- 로딩 -->
        <div v-if="chatLoading" class="chat-bubble-row row-ai">
          <span class="bubble-avatar">🤖</span>
          <div class="chat-bubble bubble-ai bubble-loading">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- 오류 -->
      <p v-if="chatError" class="chat-error">{{ chatError }}</p>

      <!-- 입력창 -->
      <form class="chat-input-row" @submit.prevent="handleSubmit">
        <input
          ref="inputEl"
          v-model="input"
          class="chat-input"
          type="text"
          placeholder="산행 안전에 대해 물어보세요…"
          :disabled="chatLoading"
          maxlength="200"
          autocomplete="off"
        />
        <button class="chat-send-btn" type="submit" :disabled="!input.trim() || chatLoading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </form>
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

async function submit(text) {
  const msg = text || input.value;
  if (!msg.trim()) return;
  input.value = '';
  await sendMessage(msg);
}

function handleSubmit() {
  submit(input.value);
}

// 새 메시지마다 스크롤 하단
watch(chatMessages, async () => {
  await nextTick();
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
}, { deep: true });
</script>
