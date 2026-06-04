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

      <div class="code-input-row">
        <input
          v-for="(_, i) in 6" :key="i"
          :ref="(el) => { if (el) inputRefs[i] = el; }"
          v-model="digits[i]"
          type="text"
          inputmode="text"
          maxlength="1"
          class="code-digit-input"
          :class="{ filled: digits[i] }"
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
          @input="onDigitInput(i, $event)"
          @keydown="onKeyDown(i, $event)"
          @paste="onPaste($event)"
        />
      </div>

      <p v-if="error" class="guardian-entry-error">{{ error }}</p>

      <button
        class="primary-btn guardian-entry-btn"
        :disabled="!codeComplete || loading"
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
import { computed, reactive, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getSafeLinkByCode } from '../api.js';

const router = useRouter();
const digits = reactive(Array(6).fill(''));
const inputRefs = reactive([]);
const loading = ref(false);
const error = ref('');
const resolved = ref(false);

const code = computed(() => digits.join('').toUpperCase());
const codeComplete = computed(() => code.value.length === 6 && !code.value.includes(' '));

onMounted(() => { inputRefs[0]?.focus(); });

function onDigitInput(i, event) {
  const val = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  digits[i] = val.slice(-1); // 한 글자만
  if (val && i < 5) inputRefs[i + 1]?.focus();
}

function onKeyDown(i, event) {
  if (event.key === 'Backspace' && !digits[i] && i > 0) {
    digits[i - 1] = '';
    inputRefs[i - 1]?.focus();
  }
  if (event.key === 'Enter' && codeComplete.value) lookupCode();
}

function onPaste(event) {
  const text = (event.clipboardData || window.clipboardData)
    .getData('text')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 6);
  text.split('').forEach((ch, i) => { digits[i] = ch; });
  const next = Math.min(text.length, 5);
  inputRefs[next]?.focus();
  event.preventDefault();
}

async function lookupCode() {
  if (!codeComplete.value) return;
  loading.value = true;
  error.value = '';
  try {
    const session = await getSafeLinkByCode(code.value);
    resolved.value = true;
    router.replace(`/safe/${session.id}`);
  } catch {
    error.value = '코드를 찾을 수 없습니다. 산행자에게 코드를 다시 확인해 주세요.';
  } finally {
    loading.value = false;
  }
}
</script>
