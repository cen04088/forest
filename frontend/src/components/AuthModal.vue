<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" @click.self="showAuthModal = false">
    <div class="auth-modal">
      <div class="auth-modal-header">
        <button class="modal-close" type="button" aria-label="닫기" @click="showAuthModal = false">✕</button>
      </div>
      <div class="auth-tabs">
        <button :class="{ active: authMode === 'login' }" type="button" @click="authMode = 'login'; authError = ''">로그인</button>
        <button :class="{ active: authMode === 'register' }" type="button" @click="authMode = 'register'; authError = ''">회원가입</button>
      </div>
      <form class="auth-form" @submit.prevent="authMode === 'login' ? handleLogin() : handleRegister()">
        <div v-if="authError" class="auth-error">{{ authError }}</div>
        <label class="field">
          <span>아이디</span>
          <input v-model="authForm.username" type="text" placeholder="아이디 (3자 이상)" autocomplete="username" required />
        </label>
        <label v-if="authMode === 'register'" class="field">
          <span>닉네임</span>
          <input v-model="authForm.nickname" type="text" placeholder="닉네임 (미입력 시 아이디 사용)" />
        </label>
        <label class="field">
          <span>비밀번호</span>
          <input v-model="authForm.password" type="password" placeholder="비밀번호 (6자 이상)" autocomplete="current-password" required />
        </label>
        <label v-if="authMode === 'register'" class="field">
          <span>이메일 (선택)</span>
          <input v-model="authForm.email" type="email" placeholder="이메일" />
        </label>
        <button class="primary-btn wide-field" type="submit" :disabled="authLoading">
          {{ authLoading ? '처리 중…' : (authMode === 'login' ? '로그인' : '가입하기') }}
        </button>
        <p v-if="authUser" class="auth-logout-row">
          <button class="outline-btn" type="button" @click="handleLogout">로그아웃</button>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { authError, authForm, authLoading, authMode, authToken, authUser, login, logout, register, showAuthModal } from '../composables/useAuth.js';
import { loadMyPageData } from '../composables/useUserData.js';
import { fetchMyPosts } from '../api.js';
import { myPosts, myPostsTotal } from '../composables/useCommunity.js';

async function handleLogin() {
  await login(() => {
    loadMyPageData();
    _loadMyPosts();
  });
}

async function handleRegister() {
  await register(() => {
    loadMyPageData();
    _loadMyPosts();
  });
}

async function handleLogout() {
  await logout(() => {
    myPosts.value = [];
    myPostsTotal.value = 0;
  });
}

async function _loadMyPosts() {
  if (!authToken.value) return;
  try {
    const data = await fetchMyPosts(authToken.value);
    myPosts.value = data.posts || [];
    myPostsTotal.value = data.total || 0;
  } catch {}
}
</script>
