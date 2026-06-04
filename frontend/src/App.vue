<template>
  <main class="app-shell">
    <!-- ─── 히어로 헤더 ──────────────────────────────────────────────────── -->
    <header class="app-hero">
      <div class="hero-nav">
        <div class="hero-nav-actions">
          <button v-if="authUser" class="hero-auth-btn" type="button" @click="showAuthModal = true">
            <span class="auth-avatar">{{ authUser.nickname[0] }}</span>
            <span class="auth-nickname">{{ authUser.nickname }}</span>
          </button>
          <button v-else class="hero-login-btn" type="button" @click="showAuthModal = true">로그인</button>
          <button class="hero-refresh-btn" type="button" title="새로고침" @click="reload">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
            </svg>
          </button>
        </div>
      </div>

      <div class="hero-body">
        <h1 class="hero-title">
          동반자와 함께하는<br>
          <span class="hero-title-accent">모든 산행을 안전하게</span>
        </h1>
        <p class="hero-desc">날씨 · 코스 · 재난 데이터를 종합해<br>출발 전 안전 등급을 진단합니다</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-num">8,000<span class="hero-stat-unit">건+</span></span>
            <span class="hero-stat-label">연간 산악구조 출동</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-num">631<span class="hero-stat-unit">개</span></span>
            <span class="hero-stat-label">실시간 분석 탐방로</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-num">3<span class="hero-stat-unit">단계</span></span>
            <span class="hero-stat-label">추천 · 주의 · 비추천</span>
          </div>
        </div>
      </div>
    </header>

    <!-- ─── 에러 배너 ──────────────────────────────────────────────────── -->
    <div v-if="globalError" class="error-banner" role="alert">
      <span>⚠️ {{ globalError }}</span>
      <button class="error-close" type="button" aria-label="닫기" @click="globalError = ''">✕</button>
    </div>

    <!-- ─── 탭바 ──────────────────────────────────────────────────────── -->
    <nav class="tabbar" aria-label="주요 화면">
      <div class="sidebar-brand">
        <img src="/logo.png" alt="올라" class="sidebar-logo-img" />
        <p class="sidebar-tagline">함께 오르는 안전 산행</p>
      </div>
      <router-link to="/guide" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        <span>안전코스</span>
      </router-link>
      <router-link to="/safe-link" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>안전공유</span>
      </router-link>
      <router-link to="/community" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>커뮤니티</span>
      </router-link>
      <router-link to="/my-page" class="tabbar-item" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </router-link>
      <router-link to="/guardian" class="tabbar-item tabbar-guardian" active-class="active">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        <span>보호자</span>
      </router-link>
    </nav>

    <!-- ─── 라우터 뷰 ─────────────────────────────────────────────────── -->
    <router-view />

    <!-- ─── 로그인/회원가입 모달 ─────────────────────────────────────── -->
    <AuthModal v-if="showAuthModal" />
  </main>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { authUser, loadMe, showAuthModal } from './composables/useAuth.js';
import { loadMyPageData } from './composables/useUserData.js';
import { guideError } from './composables/useGuide.js';
import { communityError } from './composables/useCommunity.js';
import { computed } from 'vue';
import AuthModal from './components/AuthModal.vue';

const route = useRoute();

// 전역 에러 — 어느 탭의 에러든 하나로 모음
const globalError = computed({
  get: () => guideError.value || communityError.value,
  set: (v) => { guideError.value = v; communityError.value = v; },
});

function reload() {
  window.location.reload();
}

onMounted(async () => {
  await loadMe();
  if (authUser.value) loadMyPageData();
});
</script>
