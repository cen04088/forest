<template>
  <main class="guardian-entry-shell">
    <header class="guardian-entry-header">
      <img src="/logo.png" alt="올라" class="guardian-entry-logo" />
      <p class="guardian-entry-sub">보호자 위치 확인</p>
    </header>

    <section class="guardian-entry-card" v-if="!resolved">
      <h2 class="guardian-entry-title">산행자 코드를 입력하세요</h2>
      <p class="guardian-entry-desc">
        산행자가 알려준 6자리 코드를 입력하면<br>현재 위치를 실시간으로 확인할 수 있습니다.
      </p>

      <!-- 숨겨진 단일 input (실제 입력 받음) -->
      <input
        ref="hiddenInput"
        class="code-hidden-input"
        type="text"
        inputmode="latin"
        autocomplete="off"
        autocorrect="off"
        autocapitalize="characters"
        spellcheck="false"
        maxlength="6"
        :value="rawCode"
        @input="onInput"
        @keydown.enter="lookupCode"
        @paste="onPaste"
      />

      <!-- 시각적 6칸 표시 (클릭하면 hidden input에 포커스) -->
      <div class="code-input-row" @click="focusInput">
        <div
          v-for="i in 6" :key="i"
          class="code-digit-input"
          :class="{ filled: rawCode.length >= i, active: rawCode.length === i - 1 }"
        >{{ rawCode[i - 1] || '' }}</div>
      </div>

      <p v-if="error" class="guardian-entry-error">{{ error }}</p>

      <button
        class="primary-btn guardian-entry-btn"
        :disabled="rawCode.length < 6 || loading"
        @click="lookupCode"
      >
        {{ loading ? '확인 중…' : '위치 확인하기' }}
      </button>

      <p class="guardian-entry-hint">
        코드는 산행자의 앱 안전공유 탭에서 확인할 수 있습니다.
      </p>
    </section>

    <div v-else class="guardian-entry-redirect">
      <p>위치 정보를 불러오는 중입니다…</p>
    </div>
  </main>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getSafeLinkByCode } from '../api.js';

const router = useRouter();
const hiddenInput = ref(null);
const rawCode = ref('');
const loading = ref(false);
const error = ref('');
const resolved = ref(false);

onMounted(() => nextTick(() => hiddenInput.value?.focus()));

function focusInput() {
  hiddenInput.value?.focus();
}

function onInput(event) {
  const clean = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
  rawCode.value = clean;
  // input 값도 동기화 (IME 등으로 어긋날 경우 대비)
  if (event.target.value !== clean) event.target.value = clean;
}

function onPaste(event) {
  event.preventDefault();
  const text = (event.clipboardData || window.clipboardData)
    .getData('text')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 6);
  rawCode.value = text;
  if (hiddenInput.value) hiddenInput.value.value = text;
}

async function lookupCode() {
  if (rawCode.value.length < 6 || loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    const session = await getSafeLinkByCode(rawCode.value);
    resolved.value = true;
    router.replace(`/safe/${session.id}`);
  } catch (err) {
    error.value = err.message || '코드를 찾을 수 없습니다. 다시 확인해 주세요.';
    rawCode.value = '';
    if (hiddenInput.value) hiddenInput.value.value = '';
    await nextTick();
    hiddenInput.value?.focus();
  } finally {
    loading.value = false;
  }
}
</script>
